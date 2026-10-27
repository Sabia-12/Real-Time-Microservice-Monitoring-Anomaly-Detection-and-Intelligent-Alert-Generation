"""
Alert deduplication module.

Suppresses repeated alert spam for the same (service, metric) within a configurable cooldown window.
Updates existing active alert duration and peak anomaly score rather than spawning duplicate alerts.
"""

import time
from typing import Optional, Tuple
from sqlalchemy.orm import Session

from backend.app.db.models import AlertModel


class AlertDeduplicator:
    """
    Manages alert deduplication based on service, metric, and cooldown window.
    """

    def __init__(self, cooldown_seconds: int = 300):
        """
        Args:
            cooldown_seconds: Time window in seconds within which duplicate anomalies
                             are merged into the existing active alert.
        """
        self.cooldown_seconds = cooldown_seconds

    def check_duplicate(
        self,
        db: Session,
        service: str,
        metric: str,
        timestamp_ms: int,
        score: float,
    ) -> Tuple[bool, Optional[AlertModel]]:
        """
        Check if an active alert already exists within the cooldown window.

        Args:
            db: Database session.
            service: Service name.
            metric: Metric name.
            timestamp_ms: Timestamp of current anomaly in Unix milliseconds.
            score: Anomaly score.

        Returns:
            (is_duplicate, existing_alert_or_None)
        """
        cooldown_ms = self.cooldown_seconds * 1000
        cutoff_time = timestamp_ms - cooldown_ms

        # Query for active alert on the same service and metric
        existing = (
            db.query(AlertModel)
            .filter(
                AlertModel.service == service,
                AlertModel.metric == metric,
                AlertModel.status == "Active",
                AlertModel.timestamp >= cutoff_time,
            )
            .order_by(AlertModel.timestamp.desc())
            .first()
        )

        if existing:
            # Update peak score if higher
            if score > (existing.anomaly_score or 0.0):
                existing.anomaly_score = score
            return True, existing

        return False, None
