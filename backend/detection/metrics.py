"""
Evaluation metrics for time-series anomaly detection.

Computes precision, recall, F1, false-alarm rate, and detection delay
with time-series-aware matching.
"""

import logging
from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def compute_pointwise_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
) -> Dict[str, float]:
    """
    Compute point-wise classification metrics.

    Args:
        y_true: Ground truth labels (0=normal, 1=anomaly).
        y_pred: Predicted labels (0=normal, 1=anomaly).

    Returns:
        Dictionary with precision, recall, f1, accuracy, fpr (false positive rate).
    """
    y_true = np.asarray(y_true, dtype=int)
    y_pred = np.asarray(y_pred, dtype=int)

    tp = int(np.sum((y_pred == 1) & (y_true == 1)))
    fp = int(np.sum((y_pred == 1) & (y_true == 0)))
    tn = int(np.sum((y_pred == 0) & (y_true == 0)))
    fn = int(np.sum((y_pred == 0) & (y_true == 1)))

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    accuracy = (tp + tn) / (tp + fp + tn + fn) if (tp + fp + tn + fn) > 0 else 0.0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0

    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "accuracy": accuracy,
        "fpr": fpr,  # False Positive Rate (false alarm rate)
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
    }


def compute_detection_delay(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    timestamps: np.ndarray,
    inject_time: float,
) -> Optional[float]:
    """
    Compute detection delay: time from fault injection to first true positive.

    Args:
        y_true: Ground truth labels.
        y_pred: Predicted labels.
        timestamps: Unix timestamps for each sample.
        inject_time: Fault injection timestamp.

    Returns:
        Detection delay in seconds, or None if no true positive was found.
    """
    y_true = np.asarray(y_true, dtype=int)
    y_pred = np.asarray(y_pred, dtype=int)
    timestamps = np.asarray(timestamps, dtype=float)

    # Find first true positive after injection
    tp_mask = (y_pred == 1) & (y_true == 1) & (timestamps >= inject_time)

    if not np.any(tp_mask):
        return None

    first_tp_time = timestamps[tp_mask].min()
    delay = first_tp_time - inject_time

    return float(delay)


def evaluate_case(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    scores: np.ndarray,
    timestamps: np.ndarray,
    inject_time: float,
    case_id: str = "",
) -> Dict:
    """
    Full evaluation for a single case.

    Args:
        y_true: Ground truth labels.
        y_pred: Predicted labels.
        scores: Anomaly scores.
        timestamps: Unix timestamps.
        inject_time: Fault injection timestamp.
        case_id: Case identifier for logging.

    Returns:
        Dictionary with all metrics.
    """
    metrics = compute_pointwise_metrics(y_true, y_pred)
    delay = compute_detection_delay(y_true, y_pred, timestamps, inject_time)

    metrics["detection_delay_s"] = delay
    metrics["case_id"] = case_id
    metrics["mean_score"] = float(np.mean(scores))
    metrics["max_score"] = float(np.max(scores))
    metrics["n_samples"] = len(y_true)
    metrics["n_anomaly_true"] = int(np.sum(y_true == 1))
    metrics["n_anomaly_pred"] = int(np.sum(y_pred == 1))

    logger.info(
        "Case %s: P=%.3f R=%.3f F1=%.3f FPR=%.3f delay=%s",
        case_id,
        metrics["precision"],
        metrics["recall"],
        metrics["f1"],
        metrics["fpr"],
        f"{delay:.1f}s" if delay is not None else "N/A",
    )

    return metrics


def aggregate_results(
    case_results: list,
) -> Dict:
    """
    Aggregate per-case results into summary statistics.

    Args:
        case_results: List of per-case metric dictionaries.

    Returns:
        Summary dictionary with means, stds, and per-fault-type breakdowns.
    """
    if not case_results:
        return {}

    df = pd.DataFrame(case_results)

    # Overall means
    numeric_cols = ["precision", "recall", "f1", "fpr", "detection_delay_s"]
    summary = {}
    for col in numeric_cols:
        if col in df.columns:
            values = df[col].dropna()
            summary[f"mean_{col}"] = float(values.mean()) if len(values) > 0 else None
            summary[f"std_{col}"] = float(values.std()) if len(values) > 0 else None

    summary["total_cases"] = len(df)
    summary["detected_cases"] = int(df["detection_delay_s"].notna().sum())
    summary["detection_rate"] = (
        summary["detected_cases"] / summary["total_cases"]
        if summary["total_cases"] > 0 else 0.0
    )

    # Per fault-type breakdown
    if "case_id" in df.columns:
        df["fault_type"] = df["case_id"].apply(lambda x: x.split("_")[-2])
        fault_summary = {}
        for fault, group in df.groupby("fault_type"):
            fault_summary[fault] = {
                "count": len(group),
                "mean_f1": float(group["f1"].mean()),
                "mean_recall": float(group["recall"].mean()),
                "mean_precision": float(group["precision"].mean()),
                "mean_fpr": float(group["fpr"].mean()),
                "detected": int(group["detection_delay_s"].notna().sum()),
                "mean_delay": (
                    float(group["detection_delay_s"].dropna().mean())
                    if group["detection_delay_s"].notna().any() else None
                ),
            }
        summary["by_fault_type"] = fault_summary

    return summary
