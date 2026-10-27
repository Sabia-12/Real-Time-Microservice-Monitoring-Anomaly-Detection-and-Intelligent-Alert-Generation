"""
Base interface for anomaly detectors.

All detectors must implement this ABC so they can be used interchangeably
by the evaluation harness.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd


class BaseDetector(ABC):
    """
    Abstract base class for anomaly detectors.

    Subclasses must implement fit(), score(), and predict().
    """

    def __init__(self, name: str, **kwargs):
        self.name = name
        self.params = kwargs
        self._is_fitted = False

    @abstractmethod
    def fit(self, X: pd.DataFrame) -> "BaseDetector":
        """
        Fit the detector on NORMAL (training) data only.

        Args:
            X: Feature matrix of normal-behavior samples.

        Returns:
            self
        """
        ...

    @abstractmethod
    def score(self, X: pd.DataFrame) -> np.ndarray:
        """
        Compute anomaly scores for each sample.

        Higher scores = more anomalous.

        Args:
            X: Feature matrix.

        Returns:
            1-D array of anomaly scores, shape (n_samples,).
        """
        ...

    @abstractmethod
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict binary anomaly labels.

        Args:
            X: Feature matrix.

        Returns:
            1-D array of predictions: 1 = anomaly, 0 = normal.
        """
        ...

    def get_params(self) -> Dict[str, Any]:
        """Return detector parameters."""
        return {"name": self.name, **self.params}

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r})"
