"""
Evaluation harness: orchestrates the full preprocessing → detection → evaluation
pipeline across all RE2-OB cases.
"""

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from ..preprocessing.loader import list_cases, load_case
from ..preprocessing.cleaner import clean_metrics, normalize_metrics
from ..preprocessing.feature_engine import build_feature_matrix
from ..preprocessing.splitter import split_cases_stratified, get_split_summary
from .base import BaseDetector
from .metrics import evaluate_case, aggregate_results

logger = logging.getLogger(__name__)


def prepare_dataset(
    data_dir: Optional[Path] = None,
    eval_ratio: float = 0.3,
    seed: int = 42,
    window_sizes: Optional[List[int]] = None,
    normalize: bool = True,
    include_instantaneous: bool = True,
    max_features: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Prepare and preprocess the training and evaluation datasets once.

    Args:
        data_dir: Path to raw RE2-OB directory.
        eval_ratio: Fraction of cases for evaluation.
        seed: Random seed.
        window_sizes: Window sizes for rolling feature extraction.
        normalize: Whether to normalize features using training statistics.
        include_instantaneous: Whether to include raw metric columns as features.
        max_features: Limit features to top N by variance.

    Returns:
        A dictionary containing:
            - split_info
            - train_cases
            - eval_cases
            - selected_features
            - X_train_normal (DataFrame ready for fit)
            - eval_records (List of dicts with X_eval, y, timestamps, meta for each eval case)
            - window_sizes
            - normalize
            - include_instantaneous
    """
    if window_sizes is None:
        window_sizes = [5, 10]

    all_cases = list_cases(data_dir)
    if not all_cases:
        raise ValueError(f"No RE2-OB cases found in {data_dir}")

    train_cases, eval_cases = split_cases_stratified(all_cases, eval_ratio, seed)
    split_info = get_split_summary(train_cases, eval_cases)

    logger.info("Preparing dataset: %d train cases, %d eval cases", len(train_cases), len(eval_cases))

    # Process training cases
    train_normal_features = []
    for case_name in train_cases:
        try:
            df, meta = load_case(case_name, data_dir)
            df_clean, _ = clean_metrics(df)
            X, y, _ = build_feature_matrix(
                df_clean,
                meta.inject_time,
                window_sizes=window_sizes,
                include_instantaneous=include_instantaneous,
            )
            normal_mask = y == 0
            if normal_mask.sum() > 0:
                train_normal_features.append(X[normal_mask])
        except Exception as e:
            logger.error("Error processing train case %s: %s", case_name, e)

    if not train_normal_features:
        raise ValueError("No training data collected!")

    X_train_normal = pd.concat(train_normal_features, ignore_index=True)

    # Feature selection / variance filter
    if max_features and len(X_train_normal.columns) > max_features:
        variances = X_train_normal.var().sort_values(ascending=False)
        top_features = variances.head(max_features).index.tolist()
        X_train_normal = X_train_normal[top_features]
        logger.info("Limited to top %d features by variance", max_features)

    selected_features = X_train_normal.columns.tolist()

    # Normalization statistics
    fit_stats = None
    if normalize:
        X_train_normal, fit_stats = normalize_metrics(
            X_train_normal, method="zscore", exclude_columns=[]
        )

    X_train_normal = X_train_normal.replace([np.inf, -np.inf], np.nan).fillna(0)
    logger.info("Prepared training matrix: %d samples, %d features", len(X_train_normal), len(selected_features))

    # Process evaluation cases once
    eval_records = []
    for case_name in eval_cases:
        try:
            df, meta = load_case(case_name, data_dir)
            df_clean, _ = clean_metrics(df)
            X, y, timestamps = build_feature_matrix(
                df_clean,
                meta.inject_time,
                window_sizes=window_sizes,
                include_instantaneous=include_instantaneous,
            )

            common_features = [f for f in selected_features if f in X.columns]
            missing_features = [f for f in selected_features if f not in X.columns]

            X_eval = X[common_features].copy()
            for f in missing_features:
                X_eval[f] = 0.0
            X_eval = X_eval[selected_features]

            if normalize and fit_stats:
                X_eval, _ = normalize_metrics(
                    X_eval, method="zscore", exclude_columns=[], fit_stats=fit_stats
                )

            X_eval = X_eval.replace([np.inf, -np.inf], np.nan).fillna(0)

            eval_records.append({
                "case_name": case_name,
                "meta": meta,
                "X_eval": X_eval,
                "y": y,
                "timestamps": timestamps,
            })
        except Exception as e:
            logger.error("Error preprocessing eval case %s: %s", case_name, e)
            eval_records.append({
                "case_name": case_name,
                "error": str(e),
            })

    return {
        "split_info": split_info,
        "train_cases": train_cases,
        "eval_cases": eval_cases,
        "selected_features": selected_features,
        "X_train_normal": X_train_normal,
        "eval_records": eval_records,
        "window_sizes": window_sizes,
        "normalize": normalize,
        "include_instantaneous": include_instantaneous,
    }


def evaluate_detector_on_prepared_data(
    detector: BaseDetector,
    dataset: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Fit and evaluate a detector on an already prepared dataset.
    """
    start_time = time.time()
    X_train_normal = dataset["X_train_normal"]
    eval_records = dataset["eval_records"]

    # 1. Fit detector
    detector.fit(X_train_normal)

    # 2. Evaluate on preprocessed eval cases
    case_results = []
    for rec in eval_records:
        if "error" in rec:
            case_results.append({
                "case_id": rec["case_name"],
                "error": rec["error"],
                "precision": 0, "recall": 0, "f1": 0, "fpr": 0,
            })
            continue

        case_name = rec["case_name"]
        meta = rec["meta"]
        X_eval = rec["X_eval"]
        y = rec["y"]
        timestamps = rec["timestamps"]

        try:
            scores = detector.score(X_eval)
            predictions = detector.predict(X_eval)

            result = evaluate_case(
                y_true=y.values,
                y_pred=predictions,
                scores=scores,
                timestamps=timestamps.values,
                inject_time=meta.inject_time,
                case_id=case_name,
            )
            result["service"] = meta.service
            result["fault_type"] = meta.fault_type
            case_results.append(result)
        except Exception as e:
            logger.error("Error evaluating detector on case %s: %s", case_name, e)
            case_results.append({
                "case_id": case_name,
                "error": str(e),
                "precision": 0, "recall": 0, "f1": 0, "fpr": 0,
            })

    summary = aggregate_results(case_results)
    elapsed = time.time() - start_time

    return {
        "detector": detector.name,
        "detector_params": detector.get_params(),
        "split": dataset["split_info"],
        "case_results": case_results,
        "summary": summary,
        "elapsed_seconds": elapsed,
        "feature_count": len(dataset["selected_features"]),
        "window_sizes": dataset["window_sizes"],
        "normalize": dataset["normalize"],
        "include_instantaneous": dataset["include_instantaneous"],
    }


def run_evaluation(
    detector: BaseDetector,
    data_dir: Optional[Path] = None,
    eval_ratio: float = 0.3,
    seed: int = 42,
    window_sizes: Optional[List[int]] = None,
    normalize: bool = True,
    include_instantaneous: bool = True,
    max_features: Optional[int] = None,
    prepared_dataset: Optional[Dict[str, Any]] = None,
) -> Dict:
    """
    Run full evaluation of a detector on RE2-OB dataset.
    """
    if prepared_dataset is None:
        prepared_dataset = prepare_dataset(
            data_dir=data_dir,
            eval_ratio=eval_ratio,
            seed=seed,
            window_sizes=window_sizes,
            normalize=normalize,
            include_instantaneous=include_instantaneous,
            max_features=max_features,
        )

    return evaluate_detector_on_prepared_data(detector, prepared_dataset)


def compare_detectors(
    detectors: List[BaseDetector],
    data_dir: Optional[Path] = None,
    eval_ratio: float = 0.3,
    seed: int = 42,
    window_sizes: Optional[List[int]] = None,
    normalize: bool = True,
    include_instantaneous: bool = True,
    max_features: Optional[int] = None,
    **kwargs,
) -> List[Dict]:
    """
    Run evaluation for multiple detectors and compare results.
    Prepares dataset once to maximize performance.
    """
    logger.info("Preparing dataset once for %d detectors...", len(detectors))
    dataset = prepare_dataset(
        data_dir=data_dir,
        eval_ratio=eval_ratio,
        seed=seed,
        window_sizes=window_sizes,
        normalize=normalize,
        include_instantaneous=include_instantaneous,
        max_features=max_features,
    )

    all_results = []
    for detector in detectors:
        logger.info("\n%s\nEvaluating: %s\n%s", "=" * 60, detector.name, "=" * 60)
        try:
            result = evaluate_detector_on_prepared_data(detector, dataset)
            all_results.append(result)

            s = result["summary"]
            logger.info(
                "%s summary: F1=%.3f P=%.3f R=%.3f FPR=%.3f delay=%.1fs",
                detector.name,
                s.get("mean_f1", 0) or 0,
                s.get("mean_precision", 0) or 0,
                s.get("mean_recall", 0) or 0,
                s.get("mean_fpr", 0) or 0,
                s.get("mean_detection_delay_s", 0) or 0,
            )
        except Exception as e:
            logger.error("Failed to evaluate %s: %s", detector.name, e)
            all_results.append({
                "detector": detector.name,
                "error": str(e),
            })

    return all_results
