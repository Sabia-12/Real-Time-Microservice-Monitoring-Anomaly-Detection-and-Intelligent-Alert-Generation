"""Detection package: anomaly detectors and evaluation."""

from .base import BaseDetector
from .zscore import RollingZScoreDetector
from .sklearn_detectors import (
    IsolationForestDetector,
    OneClassSVMDetector,
    LOFDetector,
    EllipticEnvelopeDetector,
)
from .harness import run_evaluation, compare_detectors
from .metrics import compute_pointwise_metrics, evaluate_case, aggregate_results
