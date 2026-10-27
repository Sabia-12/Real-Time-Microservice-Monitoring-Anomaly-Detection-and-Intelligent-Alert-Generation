"""
Unit tests for Alert Engine: Deduplication, Grouping, Severity, and Enrichment.
"""

import time
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.db.session import Base
from backend.app.db.models import ServiceModel, AnomalyModel, AlertModel, IncidentModel
from backend.alerts.dedup import AlertDeduplicator
from backend.alerts.grouping import IncidentGrouper, are_services_related
from backend.alerts.severity import calculate_severity
from backend.alerts.enrichment import enrich_alert_metadata
from backend.alerts.engine import AlertEngine


@pytest.fixture
def test_db():
    """In-memory SQLite database for isolated test execution."""
    test_engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=test_engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    db = TestingSession()

    # Add a couple of initial services
    db.add(ServiceModel(id="frontend", name="frontend", description="Frontend Web UI"))
    db.add(ServiceModel(id="checkoutservice", name="checkoutservice", description="Checkout service"))
    db.add(ServiceModel(id="paymentservice", name="paymentservice", description="Payment service"))
    db.commit()

    yield db
    db.close()


class TestAlertDeduplication:
    def test_dedup_suppresses_rapid_duplicate(self, test_db):
        dedup = AlertDeduplicator(cooldown_seconds=300)
        now_ms = int(time.time() * 1000)

        # Create first alert
        alert = AlertModel(
            id="AL-001",
            title="CPU anomaly",
            severity="Warning",
            service="checkoutservice",
            metric="cpu_usage",
            timestamp=now_ms,
            status="Active",
            anomaly_score=7.5,
        )
        test_db.add(alert)
        test_db.commit()

        # Check duplicate 30 seconds later (within 300s cooldown)
        is_dup, existing = dedup.check_duplicate(
            db=test_db,
            service="checkoutservice",
            metric="cpu_usage",
            timestamp_ms=now_ms + 30000,
            score=8.5,
        )
        assert is_dup is True
        assert existing is not None
        assert existing.id == "AL-001"
        assert existing.anomaly_score == 8.5  # Updated peak score

    def test_dedup_allows_alert_after_cooldown(self, test_db):
        dedup = AlertDeduplicator(cooldown_seconds=300)
        now_ms = int(time.time() * 1000)

        alert = AlertModel(
            id="AL-002",
            title="CPU anomaly",
            severity="Warning",
            service="checkoutservice",
            metric="cpu_usage",
            timestamp=now_ms - 400000,  # 400s ago (> 300s cooldown)
            status="Active",
            anomaly_score=7.0,
        )
        test_db.add(alert)
        test_db.commit()

        is_dup, existing = dedup.check_duplicate(
            db=test_db,
            service="checkoutservice",
            metric="cpu_usage",
            timestamp_ms=now_ms,
            score=7.2,
        )
        assert is_dup is False
        assert existing is None


class TestIncidentGrouping:
    def test_related_services_detection(self):
        # frontend and checkoutservice have direct edge
        assert are_services_related("frontend", "checkoutservice") is True
        # checkoutservice and paymentservice have direct edge
        assert are_services_related("checkoutservice", "paymentservice") is True
        # frontend and paymentservice share checkoutservice in call graph
        assert are_services_related("frontend", "paymentservice") is True

    def test_alerts_grouped_into_same_incident(self, test_db):
        grouper = IncidentGrouper(time_window_seconds=120)
        now_ms = int(time.time() * 1000)

        # Alert 1 on frontend
        alert1 = AlertModel(
            id="AL-101",
            title="Latency spike",
            severity="Warning",
            service="frontend",
            metric="latency",
            timestamp=now_ms,
            status="Active",
            fault_type="delay",
        )
        test_db.add(alert1)
        test_db.flush()

        inc1 = grouper.group_alert(test_db, alert1)
        assert inc1 is not None
        assert "frontend" in inc1.services
        assert "AL-101" in inc1.alerts

        # Alert 2 on checkoutservice 20 seconds later
        alert2 = AlertModel(
            id="AL-102",
            title="Downstream latency",
            severity="Critical",
            service="checkoutservice",
            metric="request_duration",
            timestamp=now_ms + 20000,
            status="Active",
            fault_type="delay",
        )
        test_db.add(alert2)
        test_db.flush()

        inc2 = grouper.group_alert(test_db, alert2)
        # Should be merged into the same incident!
        assert inc2.id == inc1.id
        assert "frontend" in inc2.services
        assert "checkoutservice" in inc2.services
        assert "AL-101" in inc2.alerts
        assert "AL-102" in inc2.alerts
        assert inc2.severity == "Critical"  # Escalated


class TestSeverityScoring:
    def test_extreme_score_is_critical(self):
        assert calculate_severity(score=12.5) == "Critical"

    def test_packet_loss_with_high_score_is_critical(self):
        assert calculate_severity(score=7.5, fault_type="loss") == "Critical"

    def test_high_error_rate_is_critical(self):
        assert calculate_severity(score=5.0, error_rate=0.08) == "Critical"

    def test_moderate_score_is_warning(self):
        assert calculate_severity(score=6.2) == "Warning"

    def test_low_score_is_info(self):
        assert calculate_severity(score=4.5) == "Info"


class TestEnrichment:
    def test_enrichment_metadata(self):
        meta = enrich_alert_metadata(
            service="paymentservice",
            metric="cg_cpu_usage",
            observed=95.4,
            baseline=18.2,
            score=8.5,
            fault_type="cpu",
            correlated_metrics=["latency", "error_rate"],
        )
        assert "CPU" in meta["title"]
        assert "paymentservice" in meta["title"]
        assert "95.4" in meta["description"]
        assert "latency" in meta["affected_metrics"]
