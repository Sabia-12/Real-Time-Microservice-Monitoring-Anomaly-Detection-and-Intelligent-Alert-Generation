"""
Unit tests for preprocessing and detection modules.

Uses synthetic data to test independently of the RE2-OB dataset download.
"""

import numpy as np
import pandas as pd
import pytest

# ── Schema tests ──────────────────────────────────────────────────────


class TestSchema:
    def test_categorize_metric_cpu(self):
        from backend.preprocessing.schema import categorize_metric
        assert categorize_metric("frontend_cg_cpu_usage_total") == "cpu"

    def test_categorize_metric_memory(self):
        from backend.preprocessing.schema import categorize_metric
        assert categorize_metric("cartservice_cg_mem_usage") == "memory"

    def test_categorize_metric_network(self):
        from backend.preprocessing.schema import categorize_metric
        assert categorize_metric("frontend_net_rx_bytes") == "network"

    def test_categorize_metric_unknown(self):
        from backend.preprocessing.schema import categorize_metric
        assert categorize_metric("some_random_metric") == "other"

    def test_extract_service(self):
        from backend.preprocessing.schema import extract_service_from_column
        assert extract_service_from_column("frontend_cg_cpu_usage_total") == "frontend"
        assert extract_service_from_column("productcatalogservice_cg_mem_usage") == "productcatalogservice"
        assert extract_service_from_column("unknown_metric") == "unknown"

    def test_case_metadata_from_dirname(self):
        from backend.preprocessing.schema import CaseMetadata
        meta = CaseMetadata.from_directory_name("re2ob_adservice_cpu_1")
        assert meta.service == "adservice"
        assert meta.fault_type == "cpu"
        assert meta.instance == 1

    def test_case_metadata_multiword_service(self):
        from backend.preprocessing.schema import CaseMetadata
        meta = CaseMetadata.from_directory_name("re2ob_productcatalogservice_mem_2")
        assert meta.service == "productcatalogservice"
        assert meta.fault_type == "mem"
        assert meta.instance == 2


# ── Cleaner tests ─────────────────────────────────────────────────────


class TestCleaner:
    @pytest.fixture
    def sample_df(self):
        """Create a sample metrics DataFrame."""
        np.random.seed(42)
        n = 100
        return pd.DataFrame({
            "time": np.arange(1000, 1000 + n * 5, 5),
            "metric_a": np.random.randn(n),
            "metric_b": np.random.randn(n) + 5,
            "metric_c": np.zeros(n),  # constant - should be dropped
            "metric_d": np.full(n, np.nan),  # all NaN - should be dropped
        })

    def test_clean_drops_nan_columns(self, sample_df):
        from backend.preprocessing.cleaner import clean_metrics
        df_clean, report = clean_metrics(sample_df)
        assert "metric_d" not in df_clean.columns
        assert "metric_d" in report["dropped_nan_columns"]

    def test_clean_drops_constant_columns(self, sample_df):
        from backend.preprocessing.cleaner import clean_metrics
        df_clean, report = clean_metrics(sample_df)
        assert "metric_c" not in df_clean.columns
        assert "metric_c" in report["dropped_constant_columns"]

    def test_clean_preserves_time(self, sample_df):
        from backend.preprocessing.cleaner import clean_metrics
        df_clean, _ = clean_metrics(sample_df)
        assert "time" in df_clean.columns

    def test_clean_interpolates_nans(self):
        from backend.preprocessing.cleaner import clean_metrics
        df = pd.DataFrame({
            "time": [1, 2, 3, 4, 5],
            "metric": [1.0, np.nan, 3.0, np.nan, 5.0],
        })
        df_clean, report = clean_metrics(df)
        assert df_clean["metric"].isna().sum() == 0
        assert report["interpolated_cells"] > 0

    def test_normalize_zscore(self):
        from backend.preprocessing.cleaner import normalize_metrics
        df = pd.DataFrame({
            "time": [1, 2, 3, 4, 5],
            "metric_a": [10.0, 20.0, 30.0, 40.0, 50.0],
        })
        norm_df, stats = normalize_metrics(df, method="zscore")
        assert abs(norm_df["metric_a"].mean()) < 1e-10
        assert abs(norm_df["metric_a"].std() - 1.0) < 0.1
        assert "time" in norm_df.columns  # time should be preserved

    def test_normalize_uses_fit_stats(self):
        from backend.preprocessing.cleaner import normalize_metrics
        train_df = pd.DataFrame({"metric_a": [10.0, 20.0, 30.0]})
        _, stats = normalize_metrics(train_df, method="zscore", exclude_columns=[])

        eval_df = pd.DataFrame({"metric_a": [100.0]})
        norm_eval, _ = normalize_metrics(eval_df, method="zscore", exclude_columns=[], fit_stats=stats)
        # 100 should be far from the training mean of 20
        assert norm_eval["metric_a"].iloc[0] > 5.0


# ── Feature engine tests ─────────────────────────────────────────────


class TestFeatureEngine:
    @pytest.fixture
    def sample_df(self):
        np.random.seed(42)
        n = 50
        return pd.DataFrame({
            "time": np.arange(1000, 1000 + n * 5, 5),
            "metric_a": np.random.randn(n),
            "metric_b": np.random.randn(n) + 2,
        })

    def test_window_features_shape(self, sample_df):
        from backend.preprocessing.feature_engine import compute_window_features
        result = compute_window_features(sample_df, window_sizes=[5])
        # Original: time + 2 metrics
        # Added per metric: _diff, _rmean_5, _rstd_5, _rmin_5, _rmax_5 = 5 each
        # Total metric-related cols: 2 original + 2*5 = 12, plus time = 13
        assert len(result.columns) == 13
        assert "metric_a_rmean_5" in result.columns
        assert "metric_b_rstd_5" in result.columns

    def test_label_timeseries(self, sample_df):
        from backend.preprocessing.feature_engine import label_timeseries
        inject_time = 1100.0  # 20 samples in
        labeled = label_timeseries(sample_df, inject_time)
        assert "label" in labeled.columns
        assert labeled["label"].sum() > 0
        assert (labeled[labeled["time"] < 1100]["label"] == 0).all()
        assert (labeled[labeled["time"] >= 1100]["label"] == 1).all()

    def test_build_feature_matrix(self, sample_df):
        from backend.preprocessing.feature_engine import build_feature_matrix
        X, y, t = build_feature_matrix(sample_df, inject_time=1100.0)
        assert len(X) == len(y) == len(t)
        assert "time" not in X.columns
        assert "label" not in X.columns
        assert y.dtype == int


# ── Splitter tests ────────────────────────────────────────────────────


class TestSplitter:
    @pytest.fixture
    def case_names(self):
        return [
            "re2ob_adservice_cpu_1",
            "re2ob_adservice_cpu_2",
            "re2ob_adservice_cpu_3",
            "re2ob_frontend_mem_1",
            "re2ob_frontend_mem_2",
            "re2ob_frontend_delay_1",
            "re2ob_frontend_delay_2",
            "re2ob_cartservice_disk_1",
            "re2ob_cartservice_loss_1",
            "re2ob_cartservice_socket_1",
        ]

    def test_split_by_instance(self, case_names):
        from backend.preprocessing.splitter import split_cases_by_instance
        train, eval_ = split_cases_by_instance(case_names, eval_instances=(3,))
        assert "re2ob_adservice_cpu_3" in eval_
        assert "re2ob_adservice_cpu_1" in train
        assert len(train) + len(eval_) == len(case_names)

    def test_stratified_split(self, case_names):
        from backend.preprocessing.splitter import split_cases_stratified
        train, eval_ = split_cases_stratified(case_names, eval_ratio=0.3, seed=42)
        assert len(eval_) >= 1
        assert len(train) + len(eval_) == len(case_names)
        # No overlap
        assert set(train).isdisjoint(set(eval_))


# ── Detector tests ────────────────────────────────────────────────────


class TestZScoreDetector:
    @pytest.fixture
    def normal_data(self):
        np.random.seed(42)
        return pd.DataFrame({
            "f1": np.random.randn(100),
            "f2": np.random.randn(100) + 5,
        })

    @pytest.fixture
    def anomalous_data(self):
        np.random.seed(99)
        return pd.DataFrame({
            "f1": np.random.randn(10) + 10,  # Shifted far from normal
            "f2": np.random.randn(10) + 15,
        })

    def test_fit_predict(self, normal_data, anomalous_data):
        from backend.detection.zscore import RollingZScoreDetector
        detector = RollingZScoreDetector(threshold=3.0)
        detector.fit(normal_data)
        preds = detector.predict(anomalous_data)
        # Anomalous data should be mostly flagged
        assert preds.sum() >= 5  # At least half detected

    def test_score_shape(self, normal_data):
        from backend.detection.zscore import RollingZScoreDetector
        detector = RollingZScoreDetector()
        detector.fit(normal_data)
        scores = detector.score(normal_data)
        assert len(scores) == len(normal_data)


class TestSklearnDetectors:
    @pytest.fixture
    def normal_data(self):
        np.random.seed(42)
        return pd.DataFrame({
            "f1": np.random.randn(200),
            "f2": np.random.randn(200),
        })

    @pytest.fixture
    def anomalous_data(self):
        return pd.DataFrame({
            "f1": [10.0, 11.0, 12.0],
            "f2": [10.0, 11.0, 12.0],
        })

    def test_isolation_forest(self, normal_data, anomalous_data):
        from backend.detection.sklearn_detectors import IsolationForestDetector
        d = IsolationForestDetector(contamination=0.1)
        d.fit(normal_data)
        preds = d.predict(anomalous_data)
        assert preds.sum() >= 2

    def test_ocsvm(self, normal_data, anomalous_data):
        from backend.detection.sklearn_detectors import OneClassSVMDetector
        d = OneClassSVMDetector(nu=0.1)
        d.fit(normal_data)
        preds = d.predict(anomalous_data)
        assert preds.sum() >= 2

    def test_lof(self, normal_data, anomalous_data):
        from backend.detection.sklearn_detectors import LOFDetector
        d = LOFDetector(n_neighbors=20, contamination=0.1)
        d.fit(normal_data)
        preds = d.predict(anomalous_data)
        assert preds.sum() >= 2


# ── Metrics tests ─────────────────────────────────────────────────────


class TestMetrics:
    def test_perfect_classification(self):
        from backend.detection.metrics import compute_pointwise_metrics
        y_true = np.array([0, 0, 0, 1, 1, 1])
        y_pred = np.array([0, 0, 0, 1, 1, 1])
        m = compute_pointwise_metrics(y_true, y_pred)
        assert m["precision"] == 1.0
        assert m["recall"] == 1.0
        assert m["f1"] == 1.0
        assert m["fpr"] == 0.0

    def test_all_false_positives(self):
        from backend.detection.metrics import compute_pointwise_metrics
        y_true = np.array([0, 0, 0, 0])
        y_pred = np.array([1, 1, 1, 1])
        m = compute_pointwise_metrics(y_true, y_pred)
        assert m["precision"] == 0.0
        assert m["fpr"] == 1.0

    def test_detection_delay(self):
        from backend.detection.metrics import compute_detection_delay
        y_true = np.array([0, 0, 1, 1, 1])
        y_pred = np.array([0, 0, 0, 1, 1])
        timestamps = np.array([100, 105, 110, 115, 120])
        inject_time = 110.0
        delay = compute_detection_delay(y_true, y_pred, timestamps, inject_time)
        assert delay == 5.0  # First TP at 115, inject at 110

    def test_detection_delay_no_detection(self):
        from backend.detection.metrics import compute_detection_delay
        y_true = np.array([0, 0, 1, 1])
        y_pred = np.array([0, 0, 0, 0])
        timestamps = np.array([100, 105, 110, 115])
        delay = compute_detection_delay(y_true, y_pred, timestamps, 110.0)
        assert delay is None
