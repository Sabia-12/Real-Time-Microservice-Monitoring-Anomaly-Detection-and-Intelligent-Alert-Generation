"""
Feature engineering for anomaly detection.

Extracts sliding-window statistical features from time-series metric data,
and creates labels from fault injection timestamps.
"""

import logging
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def compute_window_features(
    df: pd.DataFrame,
    window_sizes: Optional[List[int]] = None,
    exclude_columns: Optional[List[str]] = None,
) -> pd.DataFrame:
    """
    Compute sliding-window statistical features for each metric column.

    For each metric and each window size, computes:
        - rolling mean
        - rolling std
        - rolling min
        - rolling max
        - rate of change (diff)

    Args:
        df: Cleaned metrics DataFrame with a 'time' column.
        window_sizes: List of window sizes in number of rows.
            Defaults to [5, 10] (matching ~25s and ~50s at 5s intervals).
        exclude_columns: Columns to exclude from feature extraction.

    Returns:
        DataFrame with original columns plus window features.
    """
    if window_sizes is None:
        window_sizes = [5, 10]

    if exclude_columns is None:
        exclude_columns = ["time"]

    metric_cols = [c for c in df.columns if c not in exclude_columns]
    new_cols = {}

    for col in metric_cols:
        series = df[col]

        # Rate of change (instantaneous feature)
        new_cols[f"{col}_diff"] = series.diff().fillna(0)

        for w in window_sizes:
            if w > len(df):
                continue

            # Rolling statistics
            rolling = series.rolling(window=w, min_periods=1)
            new_cols[f"{col}_rmean_{w}"] = rolling.mean()
            new_cols[f"{col}_rstd_{w}"] = rolling.std().fillna(0)
            new_cols[f"{col}_rmin_{w}"] = rolling.min()
            new_cols[f"{col}_rmax_{w}"] = rolling.max()

    new_df = pd.DataFrame(new_cols, index=df.index)
    result = pd.concat([df, new_df], axis=1)

    logger.info(
        "Window features: %d cols -> %d cols (windows=%s)",
        len(metric_cols),
        len(result.columns) - len(exclude_columns),
        window_sizes,
    )

    return result


def label_timeseries(
    df: pd.DataFrame,
    inject_time: float,
    pre_fault_margin: float = 0.0,
    time_column: str = "time",
) -> pd.DataFrame:
    """
    Add binary anomaly labels based on fault injection timestamp.

    Rows at or after inject_time are labeled 1 (faulty), before are 0 (normal).

    Args:
        df: DataFrame with a time column.
        inject_time: Unix timestamp of fault injection.
        pre_fault_margin: Seconds before inject_time to still label as normal.
            Use 0 for strict labeling.
        time_column: Name of the time column.

    Returns:
        DataFrame with added 'label' column (0=normal, 1=faulty).
    """
    result = df.copy()
    threshold = inject_time - pre_fault_margin
    result["label"] = (result[time_column] >= threshold).astype(int)

    n_normal = (result["label"] == 0).sum()
    n_faulty = (result["label"] == 1).sum()
    logger.info(
        "Labeled: %d normal, %d faulty (inject_time=%.0f)",
        n_normal, n_faulty, inject_time,
    )

    return result


def build_feature_matrix(
    df: pd.DataFrame,
    inject_time: float,
    window_sizes: Optional[List[int]] = None,
    exclude_columns: Optional[List[str]] = None,
    include_instantaneous: bool = True,
) -> Tuple[pd.DataFrame, pd.Series, pd.Series]:
    """
    Full feature engineering pipeline for a single case.

    1. Compute window features.
    2. Label time series.
    3. Separate features (X), labels (y), and timestamps (t).

    Args:
        df: Cleaned metrics DataFrame.
        inject_time: Fault injection timestamp.
        window_sizes: Window sizes for rolling features.
        exclude_columns: Columns to exclude.
        include_instantaneous: Whether to include original instantaneous metrics.

    Returns:
        Tuple of (X, y, timestamps) where:
            X: Feature matrix (DataFrame).
            y: Binary labels (Series).
            timestamps: Time values (Series).
    """
    if exclude_columns is None:
        exclude_columns = ["time"]

    # Compute window features
    featured = compute_window_features(df, window_sizes, exclude_columns)

    # Label
    labeled = label_timeseries(featured, inject_time)

    # Separate
    timestamps = labeled["time"]
    y = labeled["label"]
    drop_cols = ["time", "label"]

    if not include_instantaneous:
        # Keep only window-derived features (those with _rmean_, _rstd_, etc.)
        original_metrics = [c for c in df.columns if c not in exclude_columns]
        drop_cols.extend(original_metrics)

    X = labeled.drop(columns=[c for c in drop_cols if c in labeled.columns])

    # Replace any remaining NaN/inf
    X = X.replace([np.inf, -np.inf], np.nan).fillna(0)

    logger.info(
        "Feature matrix: %d samples x %d features, %d positive labels",
        len(X), len(X.columns), y.sum(),
    )

    return X, y, timestamps
