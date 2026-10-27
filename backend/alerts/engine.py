"""
AlertEngine: Central coordinator for anomaly ingestion, deduplication, enrichment,
severity calculation, incident grouping, and database persistence.
"""

import logging
import time
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from backend.app.db.models import AnomalyModel, AlertModel, IncidentModel, ServiceModel
from .dedup import AlertDeduplicator
from .grouping import IncidentGrouper
from .severity import calculate_severity
from .enrichment import enrich_alert_metadata

logger = logging.getLogger(__name__)


class AlertEngine:
    """
    Coordinates alerting workflow:
    Anomaly Event -> Deduplication Check -> Severity & Enrichment -> Alert -> Incident Grouping
    """

    def __init__(
        self,
        cooldown_seconds: int = 300,
        incident_window_seconds: int = 120,
    ):
        self.deduplicator = AlertDeduplicator(cooldown_seconds=cooldown_seconds)
        self.grouper = IncidentGrouper(time_window_seconds=incident_window_seconds)

    def process_anomaly_event(
        self,
        db: Session,
        service: str,
        metric: str,
        observed: float,
        baseline: float,
        score: float,
        timestamp_ms: Optional[int] = None,
        fault_type: Optional[str] = None,
        unit: str = "",
        error_rate: float = 0.0,
        latency: float = 0.0,
        log_snippet: Optional[str] = None,
        trace_snippet: Optional[str] = None,
        correlated_metrics: Optional[List[str]] = None,
    ) -> Tuple[AnomalyModel, AlertModel, IncidentModel, bool]:
        """
        Process a detected anomaly event.

        Returns:
            Tuple of (anomaly_model, alert_model, incident_model, is_new_alert)
        """
        if timestamp_ms is None:
            timestamp_ms = int(time.time() * 1000)

        # 1. Calculate severity
        severity = calculate_severity(
            score=score,
            fault_type=fault_type,
            metric_name=metric,
            observed=observed,
            error_rate=error_rate,
            latency=latency,
        )

        # 2. Record Anomaly record
        anom_id = f"AN-{int(timestamp_ms) % 100000:05d}"
        while db.query(AnomalyModel).filter(AnomalyModel.id == anom_id).first():
            anom_id = f"AN-{(int(timestamp_ms) + 11) % 100000:05d}"

        anomaly = AnomalyModel(
            id=anom_id,
            service=service,
            metric=metric,
            unit=unit,
            observed=observed,
            baseline=baseline,
            severity=severity,
            detected_at=timestamp_ms,
            score=score,
            status="Open",
            fault_type=fault_type,
            anomaly_score=score,
        )
        db.add(anomaly)

        # 3. Check for deduplication
        is_dup, existing_alert = self.deduplicator.check_duplicate(
            db=db,
            service=service,
            metric=metric,
            timestamp_ms=timestamp_ms,
            score=score,
        )

        if is_dup and existing_alert:
            # Alert is already active; existing_alert peak score was updated by dedup
            alert = existing_alert
            is_new_alert = False

            # Find its incident
            incident = (
                db.query(IncidentModel)
                .filter(IncidentModel.id == alert.incident_id)
                .first()
            )
            if not incident:
                incident = self.grouper.group_alert(db, alert)
        else:
            # 4. Generate new Alert
            alert_id = f"AL-{int(timestamp_ms) % 100000:05d}"
            while db.query(AlertModel).filter(AlertModel.id == alert_id).first():
                alert_id = f"AL-{(int(timestamp_ms) + 13) % 100000:05d}"

            enrichment = enrich_alert_metadata(
                service=service,
                metric=metric,
                observed=observed,
                baseline=baseline,
                score=score,
                fault_type=fault_type,
                log_snippet=log_snippet,
                trace_snippet=trace_snippet,
                correlated_metrics=correlated_metrics,
            )

            alert = AlertModel(
                id=alert_id,
                title=enrichment["title"],
                severity=severity,
                service=service,
                metric=metric,
                timestamp=timestamp_ms,
                status="Active",
                fault_type=fault_type,
                description=enrichment["description"],
                evidence=enrichment["evidence"],
                affected_metrics=enrichment["affected_metrics"],
                anomaly_score=score,
            )
            db.add(alert)
            db.flush()

            # 5. Group into incident
            incident = self.grouper.group_alert(db, alert)
            is_new_alert = True

        # 6. Update Service status
        svc = db.query(ServiceModel).filter(ServiceModel.id == service).first()
        if svc:
            svc.updated_at = timestamp_ms
            if severity == "Critical":
                svc.status = "Critical"
            elif severity == "Warning" and svc.status != "Critical":
                svc.status = "Warning"
            if fault_type:
                svc.fault_type = fault_type

        db.commit()
        return anomaly, alert, incident, is_new_alert
