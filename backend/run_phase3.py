"""
Phase 3 Runner: Download RE2-OB data, run preprocessing + detection evaluation.

Usage:
    cd msm
    .venv\Scripts\python.exe -m backend.run_phase3
"""

import json
import logging
import sys
import time
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def step1_download_data():
    """Download RE2-OB dataset from HuggingFace."""
    from backend.preprocessing.loader import download_re2ob_dataset, list_cases

    logger.info("=" * 60)
    logger.info("STEP 1: Download RE2-OB dataset")
    logger.info("=" * 60)

    data_dir = download_re2ob_dataset()
    cases = list_cases(data_dir)
    logger.info("Downloaded %d cases to %s", len(cases), data_dir)

    return data_dir


def step2_inspect_data(data_dir: Path):
    """Inspect a few representative cases to verify data format."""
    from backend.preprocessing.loader import load_case

    logger.info("=" * 60)
    logger.info("STEP 2: Inspect representative cases")
    logger.info("=" * 60)

    # Pick one case per fault type
    from backend.preprocessing.schema import FAULT_TYPES
    from backend.preprocessing.loader import list_cases

    cases = list_cases(data_dir)
    inspected = set()

    for case_name in cases:
        parts = case_name.split("_")
        fault = parts[-2]
        if fault not in inspected:
            inspected.add(fault)
            try:
                df, meta = load_case(case_name, data_dir)
                logger.info(
                    "\n  Case: %s\n"
                    "  Service: %s, Fault: %s, Instance: %d\n"
                    "  Shape: %s\n"
                    "  Columns: %s\n"
                    "  Time range: %.0f - %.0f (%.0f seconds)\n"
                    "  Inject time: %.0f\n"
                    "  Has logs: %s, Has traces: %s\n"
                    "  NaN counts: %d total\n"
                    "  Sample columns (first 10): %s",
                    meta.case_id,
                    meta.service, meta.fault_type, meta.instance,
                    df.shape,
                    len(df.columns),
                    df["time"].min(), df["time"].max(), meta.duration_seconds,
                    meta.inject_time,
                    meta.has_logs, meta.has_traces,
                    df.isna().sum().sum(),
                    df.columns[:10].tolist(),
                )
            except Exception as e:
                logger.error("Failed to inspect %s: %s", case_name, e)

    return inspected


def step3_test_pipeline(data_dir: Path):
    """Test the full pipeline on a single case."""
    from backend.preprocessing.loader import load_case, list_cases
    from backend.preprocessing.cleaner import clean_metrics, normalize_metrics
    from backend.preprocessing.feature_engine import build_feature_matrix

    logger.info("=" * 60)
    logger.info("STEP 3: Test pipeline on a single case")
    logger.info("=" * 60)

    cases = list_cases(data_dir)
    test_case = cases[0]

    df, meta = load_case(test_case, data_dir)
    logger.info("Loaded: %s (%s)", test_case, df.shape)

    # Clean
    df_clean, report = clean_metrics(df)
    logger.info("Cleaned: %s, report: %s", df_clean.shape, report)

    # Features
    X, y, timestamps = build_feature_matrix(df_clean, meta.inject_time)
    logger.info("Features: X=%s, y=%s, normal=%d, faulty=%d",
                X.shape, y.shape, (y == 0).sum(), (y == 1).sum())

    # Quick z-score test
    from backend.detection.zscore import RollingZScoreDetector

    normal_mask = y == 0
    X_normal = X[normal_mask]

    detector = RollingZScoreDetector(threshold=3.0)
    detector.fit(X_normal)

    scores = detector.score(X)
    preds = detector.predict(X)

    logger.info(
        "Z-Score test: %d anomalies detected out of %d samples, "
        "mean score=%.3f, max score=%.3f",
        preds.sum(), len(preds), scores.mean(), scores.max(),
    )

    return True


def step4_full_evaluation(data_dir: Path):
    """Run full evaluation with all detectors."""
    from backend.detection.zscore import RollingZScoreDetector
    from backend.detection.sklearn_detectors import (
        IsolationForestDetector,
        OneClassSVMDetector,
        LOFDetector,
        EllipticEnvelopeDetector,
    )
    from backend.detection.harness import compare_detectors

    logger.info("=" * 60)
    logger.info("STEP 4: Full evaluation with all detectors")
    logger.info("=" * 60)

    detectors = [
        RollingZScoreDetector(threshold=3.0, name="ZScore-max-3.0"),
        RollingZScoreDetector(threshold=2.5, use_max=False, name="ZScore-mean-2.5"),
        IsolationForestDetector(contamination=0.1, name="IForest-0.1"),
        IsolationForestDetector(contamination=0.2, name="IForest-0.2"),
        OneClassSVMDetector(nu=0.1, name="OCSVM-0.1"),
        LOFDetector(n_neighbors=20, contamination=0.1, name="LOF-20-0.1"),
    ]

    # Run with max_features to handle high dimensionality
    results = compare_detectors(
        detectors,
        data_dir=data_dir,
        max_features=50,
        window_sizes=[5, 10],
    )

    # Save results
    output_dir = Path(__file__).resolve().parent.parent / "data-analysis" / "evaluation"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "phase3_results.json"

    # Make results JSON-serializable
    def make_serializable(obj):
        if isinstance(obj, dict):
            return {k: make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [make_serializable(v) for v in obj]
        elif isinstance(obj, (int, float, str, bool, type(None))):
            return obj
        else:
            return str(obj)

    with open(output_file, "w") as f:
        json.dump(make_serializable(results), f, indent=2)

    logger.info("Results saved to %s", output_file)

    # Print summary table
    logger.info("\n" + "=" * 80)
    logger.info("DETECTOR COMPARISON SUMMARY")
    logger.info("=" * 80)
    logger.info(
        "%-20s %8s %8s %8s %8s %10s %8s",
        "Detector", "F1", "Prec", "Recall", "FPR", "Delay(s)", "Cases",
    )
    logger.info("-" * 80)

    for r in results:
        if "error" in r:
            logger.info("%-20s ERROR: %s", r["detector"], r["error"])
            continue
        s = r.get("summary", {})
        logger.info(
            "%-20s %8.3f %8.3f %8.3f %8.3f %10s %8d",
            r["detector"],
            s.get("mean_f1", 0) or 0,
            s.get("mean_precision", 0) or 0,
            s.get("mean_recall", 0) or 0,
            s.get("mean_fpr", 0) or 0,
            f"{s.get('mean_detection_delay_s', 'N/A')}",
            s.get("total_cases", 0),
        )

    # Print per-fault-type breakdown for best detector
    best = max(
        [r for r in results if "error" not in r],
        key=lambda r: r.get("summary", {}).get("mean_f1", 0) or 0,
        default=None,
    )
    if best:
        logger.info("\n\nBest detector: %s", best["detector"])
        by_fault = best.get("summary", {}).get("by_fault_type", {})
        if by_fault:
            logger.info("\nPer fault-type breakdown:")
            logger.info("%-10s %6s %8s %8s %8s %8s %10s",
                        "Fault", "Count", "F1", "Prec", "Recall", "FPR", "Delay(s)")
            logger.info("-" * 70)
            for fault, stats in sorted(by_fault.items()):
                logger.info(
                    "%-10s %6d %8.3f %8.3f %8.3f %8.3f %10s",
                    fault,
                    stats["count"],
                    stats["mean_f1"],
                    stats["mean_precision"],
                    stats["mean_recall"],
                    stats["mean_fpr"],
                    f"{stats['mean_delay']:.1f}" if stats["mean_delay"] is not None else "N/A",
                )

    return results


def main():
    """Run all Phase 3 steps."""
    start = time.time()

    logger.info("=" * 60)
    logger.info("PHASE 3: Preprocessing + Anomaly Detection (RE2-OB)")
    logger.info("=" * 60)

    # Step 1: Download
    data_dir = step1_download_data()

    # Step 2: Inspect
    step2_inspect_data(data_dir)

    # Step 3: Test pipeline
    step3_test_pipeline(data_dir)

    # Step 4: Full evaluation
    results = step4_full_evaluation(data_dir)

    elapsed = time.time() - start
    logger.info("\nPhase 3 complete in %.1f seconds (%.1f minutes)", elapsed, elapsed / 60)


if __name__ == "__main__":
    main()
