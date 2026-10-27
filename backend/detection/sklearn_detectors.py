"""
scikit-learn based anomaly detectors: Isolation Forest, One-Class SVM,
Local Outlier Factor, and Elliptic Envelope.

All follow the BaseDetector interface. They are fitted on normal data
and predict anomalies on new data.
"""

import logging
from typing import Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.svm import OneClassSVM
from sklearn.neighbors import LocalOutlierFactor
from sklearn.covariance import EllipticEnvelope

from .base import BaseDetector

logger = logging.getLogger(__name__)


class IsolationForestDetector(BaseDetector):
    """Isolation Forest anomaly detector."""

    def __init__(
        self,
        contamination: float = 0.1,
        n_estimators: int = 100,
        max_samples: str = "auto",
        random_state: int = 42,
        name: str = "IsolationForest",
    ):
        super().__init__(
            name=name,
            contamination=contamination,
            n_estimators=n_estimators,
            random_state=random_state,
        )
        self.model = IsolationForest(
            contamination=contamination,
            n_estimators=n_estimators,
            max_samples=max_samples,
            random_state=random_state,
        )

    def fit(self, X: pd.DataFrame) -> "IsolationForestDetector":
        """Fit on normal data."""
        self.model.fit(X.values)
        self._is_fitted = True
        logger.info("IsolationForest fit: %d samples, %d features", *X.shape)
        return self

    def score(self, X: pd.DataFrame) -> np.ndarray:
        """Anomaly scores (negated decision function: higher = more anomalous)."""
        if not self._is_fitted:
            raise RuntimeError("Detector not fitted.")
        # sklearn's decision_function: more negative = more anomalous
        # We negate so higher = more anomalous
        return -self.model.decision_function(X.values)

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Predict: 1 = anomaly, 0 = normal."""
        if not self._is_fitted:
            raise RuntimeError("Detector not fitted.")
        preds = self.model.predict(X.values)
        # sklearn uses -1 for anomaly, 1 for normal
        return (preds == -1).astype(int)


class OneClassSVMDetector(BaseDetector):
    """One-Class SVM anomaly detector."""

    def __init__(
        self,
        kernel: str = "rbf",
        gamma: str = "scale",
        nu: float = 0.1,
        name: str = "OneClassSVM",
    ):
        super().__init__(name=name, kernel=kernel, gamma=gamma, nu=nu)
        self.model = OneClassSVM(kernel=kernel, gamma=gamma, nu=nu)

    def fit(self, X: pd.DataFrame) -> "OneClassSVMDetector":
        """Fit on normal data."""
        self.model.fit(X.values)
        self._is_fitted = True
        logger.info("OneClassSVM fit: %d samples, %d features", *X.shape)
        return self

    def score(self, X: pd.DataFrame) -> np.ndarray:
        """Anomaly scores (negated decision function)."""
        if not self._is_fitted:
            raise RuntimeError("Detector not fitted.")
        return -self.model.decision_function(X.values)

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Predict: 1 = anomaly, 0 = normal."""
        if not self._is_fitted:
            raise RuntimeError("Detector not fitted.")
        preds = self.model.predict(X.values)
        return (preds == -1).astype(int)


class LOFDetector(BaseDetector):
    """
    Local Outlier Factor anomaly detector.

    Note: LOF's predict() in sklearn only works in novelty detection mode
    (novelty=True), which means fit on normal data, predict on new data.
    """

    def __init__(
        self,
        n_neighbors: int = 20,
        contamination: float = 0.1,
        name: str = "LOF",
    ):
        super().__init__(name=name, n_neighbors=n_neighbors, contamination=contamination)
        self.model = LocalOutlierFactor(
            n_neighbors=n_neighbors,
            contamination=contamination,
            novelty=True,  # Required for predict() on new data
        )

    def fit(self, X: pd.DataFrame) -> "LOFDetector":
        """Fit on normal data."""
        self.model.fit(X.values)
        self._is_fitted = True
        logger.info("LOF fit: %d samples, %d features", *X.shape)
        return self

    def score(self, X: pd.DataFrame) -> np.ndarray:
        """Anomaly scores (negated decision function)."""
        if not self._is_fitted:
            raise RuntimeError("Detector not fitted.")
        return -self.model.decision_function(X.values)

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Predict: 1 = anomaly, 0 = normal."""
        if not self._is_fitted:
            raise RuntimeError("Detector not fitted.")
        preds = self.model.predict(X.values)
        return (preds == -1).astype(int)


class EllipticEnvelopeDetector(BaseDetector):
    """Elliptic Envelope (Gaussian-based) anomaly detector."""

    def __init__(
        self,
        contamination: float = 0.1,
        random_state: int = 42,
        name: str = "EllipticEnvelope",
    ):
        super().__init__(name=name, contamination=contamination, random_state=random_state)
        self.model = EllipticEnvelope(
            contamination=contamination,
            random_state=random_state,
        )

    def fit(self, X: pd.DataFrame) -> "EllipticEnvelopeDetector":
        """Fit on normal data."""
        self.model.fit(X.values)
        self._is_fitted = True
        logger.info("EllipticEnvelope fit: %d samples, %d features", *X.shape)
        return self

    def score(self, X: pd.DataFrame) -> np.ndarray:
        """Anomaly scores (negated decision function)."""
        if not self._is_fitted:
            raise RuntimeError("Detector not fitted.")
        return -self.model.decision_function(X.values)

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Predict: 1 = anomaly, 0 = normal."""
        if not self._is_fitted:
            raise RuntimeError("Detector not fitted.")
        preds = self.model.predict(X.values)
        return (preds == -1).astype(int)
