"""
Rolling Z-Score baseline anomaly detector.

Simple statistical approach: flag samples where any metric's z-score
(relative to training statistics) exceeds a threshold.
"""

import logging
from typing import Optional

import numpy as np
import pandas as pd

from .base import BaseDetector

logger = logging.getLogger(__name__)


class RollingZScoreDetector(BaseDetector):
    """
    Baseline detector using per-feature z-scores.

    For each feature, computes z = (x - mean) / std using training stats.
    A sample is anomalous if any feature exceeds the threshold, or if
    the mean absolute z-score exceeds the aggregate threshold.
    """

    def __init__(
        self,
        threshold: float = 3.0,
        aggregate_threshold: Optional[float] = None,
        use_max: bool = True,
        name: str = "RollingZScore",
    ):
        """
        Args:
            threshold: Z-score threshold for per-feature anomaly.
            aggregate_threshold: If set, use mean |z| > threshold instead.
            use_max: If True, use max |z| for scoring; else use mean |z|.
            name: Detector name.
        """
        super().__init__(
            name=name,
            threshold=threshold,
            aggregate_threshold=aggregate_threshold,
            use_max=use_max,
        )
        self.threshold = threshold
        self.aggregate_threshold = aggregate_threshold
        self.use_max = use_max
        self._means: Optional[pd.Series] = None
        self._stds: Optional[pd.Series] = None

    def fit(self, X: pd.DataFrame) -> "RollingZScoreDetector":
        """Fit on normal data: compute per-feature mean and std."""
        self._means = X.mean()
        self._stds = X.std().replace(0, 1.0)  # Avoid division by zero
        self._is_fitted = True

        logger.info(
            "ZScore fit: %d features, mean of means=%.4f",
            len(self._means), self._means.mean(),
        )
        return self

    def score(self, X: pd.DataFrame) -> np.ndarray:
        """
        Compute anomaly scores as max|z| or mean|z| across features.

        Returns:
            1-D array of scores (higher = more anomalous).
        """
        if not self._is_fitted:
            raise RuntimeError("Detector not fitted. Call fit() first.")

        # Align columns
        common_cols = X.columns.intersection(self._means.index)
        z_scores = (X[common_cols] - self._means[common_cols]) / self._stds[common_cols]
        abs_z = z_scores.abs()

        if self.use_max:
            scores = abs_z.max(axis=1).values
        else:
            scores = abs_z.mean(axis=1).values

        return scores

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict anomalies: 1 if score exceeds threshold.

        Returns:
            1-D array of binary predictions.
        """
        scores = self.score(X)
        threshold = self.aggregate_threshold if self.aggregate_threshold else self.threshold
        return (scores > threshold).astype(int)
