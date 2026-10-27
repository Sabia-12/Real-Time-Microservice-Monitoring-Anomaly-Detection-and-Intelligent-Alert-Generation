"""
Detailed feature and threshold ablation for RE2-OB anomaly detection.
Compares:
1. Instantaneous vs Window features
2. Threshold sensitivity for Z-score detector
3. Per-fault-type breakdown
"""

import json
from pathlib import Path
import numpy as np
import pandas as pd

from backend.detection.zscore import RollingZScoreDetector
from backend.detection.sklearn_detectors import IsolationForestDetector
from backend.detection.harness import prepare_dataset, evaluate_detector_on_prepared_data


def run_ablation():
    results_dir = Path("data-analysis/evaluation")
    results_dir.mkdir(parents=True, exist_ok=True)

    print("=== Feature Ablation ===")
    configs = [
        ("instantaneous_only", False, True),
        ("window_only", True, False),
        ("combined", True, True),
    ]

    ablation_results = {}

    for name, use_window, use_inst in configs:
        print(f"\nEvaluating configuration: {name}")
        dataset = prepare_dataset(
            window_sizes=[5, 10] if use_window else [],
            include_instantaneous=use_inst,
            max_features=40,
        )

        detectors = [
            RollingZScoreDetector(threshold=2.0, use_max=False, name=f"ZScore-mean-2.0_{name}"),
            RollingZScoreDetector(threshold=2.5, use_max=False, name=f"ZScore-mean-2.5_{name}"),
            RollingZScoreDetector(threshold=3.0, use_max=False, name=f"ZScore-mean-3.0_{name}"),
            RollingZScoreDetector(threshold=5.0, use_max=True, name=f"ZScore-max-5.0_{name}"),
            RollingZScoreDetector(threshold=7.0, use_max=True, name=f"ZScore-max-7.0_{name}"),
            RollingZScoreDetector(threshold=10.0, use_max=True, name=f"ZScore-max-10.0_{name}"),
        ]

        cfg_results = []
        for det in detectors:
            res = evaluate_detector_on_prepared_data(det, dataset)
            s = res["summary"]
            cfg_results.append({
                "detector": det.name,
                "f1": s.get("mean_f1", 0),
                "precision": s.get("mean_precision", 0),
                "recall": s.get("mean_recall", 0),
                "fpr": s.get("mean_fpr", 0),
                "delay": s.get("mean_detection_delay_s"),
                "by_fault": s.get("by_fault_type", {}),
            })
            print(f"  {det.name:<25} F1={s.get('mean_f1', 0):.3f} P={s.get('mean_precision', 0):.3f} "
                  f"R={s.get('mean_recall', 0):.3f} FPR={s.get('mean_fpr', 0):.3f} "
                  f"Delay={str(s.get('mean_detection_delay_s'))[:5]}s")

        ablation_results[name] = cfg_results

    with open(results_dir / "ablation_results.json", "w") as f:
        json.dump(ablation_results, f, indent=2)

    print("\nAblation complete. Saved to data-analysis/evaluation/ablation_results.json")


if __name__ == "__main__":
    run_ablation()
