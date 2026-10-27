"""
Data cleaning and preprocessing for RE2-OB metric DataFrames.

Handles missing values, constant columns, and data quality issues.
"""

import logging
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def clean_metrics(
    df: pd.DataFrame,
    drop_constant: bool = True,
    interpolation_method: str = "linear",
    interpolation_limit: int = 5,
    fill_remaining: str = "ffill_bfill",
) -> Tuple[pd.DataFrame, dict]:
    """
    Clean a metrics DataFrame from an RE2-OB case.

    Steps:
        1. Sort by time.
        2. Drop fully-NaN columns.
        3. Drop constant columns (zero variance).
        4. Interpolate missing values (linear, limited to short gaps).
        5. Forward-fill then back-fill any remaining NaNs.
        6. Report cleaning stats.

    Args:
        df: Raw metrics DataFrame with 'time' column.
        drop_constant: Whether to drop zero-variance columns.
        interpolation_method: Pandas interpolation method.
        interpolation_limit: Max consecutive NaNs to interpolate.
        fill_remaining: Strategy for remaining NaNs after interpolation.

    Returns:
        Tuple of (cleaned_df, cleaning_report_dict).
    """
    report = {
        "original_shape": df.shape,
        "dropped_nan_columns": [],
        "dropped_constant_columns": [],
        "interpolated_cells": 0,
        "remaining_nan_cells": 0,
    }

    result = df.copy()

    # 1. Sort by time
    if "time" in result.columns:
        result = result.sort_values("time").reset_index(drop=True)

    # Separate time column
    time_col = None
    if "time" in result.columns:
        time_col = result["time"].copy()
        metric_df = result.drop(columns=["time"])
    else:
        metric_df = result

    # 2. Drop fully-NaN columns
    nan_cols = metric_df.columns[metric_df.isna().all()].tolist()
    if nan_cols:
        metric_df = metric_df.drop(columns=nan_cols)
        report["dropped_nan_columns"] = nan_cols
        logger.info("Dropped %d fully-NaN columns", len(nan_cols))

    # 3. Drop constant columns (zero variance)
    if drop_constant:
        # A column is constant if std == 0 (ignoring NaN)
        stds = metric_df.std(skipna=True)
        const_cols = stds[stds == 0].index.tolist()
        if const_cols:
            metric_df = metric_df.drop(columns=const_cols)
            report["dropped_constant_columns"] = const_cols
            logger.info("Dropped %d constant columns", len(const_cols))

    # 4. Count pre-interpolation NaNs
    pre_nans = metric_df.isna().sum().sum()

    # 5. Interpolate
    metric_df = metric_df.interpolate(
        method=interpolation_method,
        limit=interpolation_limit,
        axis=0,
    )
    post_interp_nans = metric_df.isna().sum().sum()
    report["interpolated_cells"] = int(pre_nans - post_interp_nans)

    # 6. Fill remaining NaNs
    if fill_remaining == "ffill_bfill":
        metric_df = metric_df.ffill().bfill()
    elif fill_remaining == "zero":
        metric_df = metric_df.fillna(0)
    elif fill_remaining == "drop":
        metric_df = metric_df.dropna()

    report["remaining_nan_cells"] = int(metric_df.isna().sum().sum())
    report["final_shape"] = (
        len(metric_df) + (1 if time_col is not None else 0),  # not right, let me fix
        len(metric_df.columns) + (1 if time_col is not None else 0),
    )

    # Reassemble with time
    if time_col is not None:
        # Align time_col index with metric_df
        if len(time_col) == len(metric_df):
            metric_df.insert(0, "time", time_col.values)
        else:
            # metric_df might have fewer rows if dropna was used
            metric_df = metric_df.reset_index(drop=True)
            time_aligned = time_col.iloc[metric_df.index].reset_index(drop=True)
            metric_df.insert(0, "time", time_aligned)

    report["final_shape"] = metric_df.shape
    logger.info(
        "Cleaning: %s -> %s, interpolated %d cells, %d NaNs remaining",
        report["original_shape"],
        report["final_shape"],
        report["interpolated_cells"],
        report["remaining_nan_cells"],
    )

    return metric_df, report


def normalize_metrics(
    df: pd.DataFrame,
    method: str = "zscore",
    exclude_columns: Optional[List[str]] = None,
    fit_stats: Optional[dict] = None,
) -> Tuple[pd.DataFrame, dict]:
    """
    Normalize metric columns.

    IMPORTANT: To avoid data leakage, call with fit_stats=None on training
    data to compute stats, then pass those stats when normalizing eval data.

    Args:
        df: Cleaned metrics DataFrame.
        method: 'zscore' (mean=0, std=1) or 'minmax' ([0,1]).
        exclude_columns: Columns to exclude from normalization (e.g., 'time').
        fit_stats: Pre-computed normalization statistics from training data.
            If None, stats are fitted on this DataFrame.

    Returns:
        Tuple of (normalized_df, fit_stats_dict).
    """
    if exclude_columns is None:
        exclude_columns = ["time"]

    result = df.copy()
    metric_cols = [c for c in result.columns if c not in exclude_columns]

    if fit_stats is None:
        # Fit on this data
        fit_stats = {}
        if method == "zscore":
            fit_stats["means"] = result[metric_cols].mean().to_dict()
            fit_stats["stds"] = result[metric_cols].std().to_dict()
        elif method == "minmax":
            fit_stats["mins"] = result[metric_cols].min().to_dict()
            fit_stats["maxs"] = result[metric_cols].max().to_dict()
        fit_stats["method"] = method
        fit_stats["columns"] = metric_cols

    # Apply normalization
    if method == "zscore":
        for col in metric_cols:
            mean = fit_stats["means"].get(col, 0)
            std = fit_stats["stds"].get(col, 1)
            if std == 0 or np.isnan(std):
                std = 1.0  # Avoid division by zero
            result[col] = (result[col] - mean) / std
    elif method == "minmax":
        for col in metric_cols:
            min_val = fit_stats["mins"].get(col, 0)
            max_val = fit_stats["maxs"].get(col, 1)
            range_val = max_val - min_val
            if range_val == 0:
                range_val = 1.0
            result[col] = (result[col] - min_val) / range_val

    return result, fit_stats
