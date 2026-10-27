"""Preprocessing package for RE2-OB data."""

from .loader import load_case, load_all_cases, list_cases, download_re2ob_dataset
from .cleaner import clean_metrics, normalize_metrics
from .feature_engine import compute_window_features, label_timeseries, build_feature_matrix
from .splitter import split_cases_stratified, split_cases_by_instance
from .schema import (
    CaseMetadata,
    ONLINE_BOUTIQUE_SERVICES,
    FAULT_TYPES,
    METRIC_CATEGORIES,
    categorize_metric,
    extract_service_from_column,
)
