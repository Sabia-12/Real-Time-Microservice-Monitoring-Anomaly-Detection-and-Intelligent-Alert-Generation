"""
SQLAlchemy models for Online Boutique monitoring entities.
"""

import json
import time
from typing import Any, Dict, List, Optional

from sqlalchemy import Boolean, Column, Float, Integer, String, Text
from .session import Base


class ServiceModel(Base):
    __tablename__ = "services"

    id = Column(String(64), primary_key=True)
    name = Column(String(64), nullable=False)
    description = Column(String(256), nullable=False)
    status = Column(String(32), default="Healthy")  # Healthy, Warning, Critical
    cpu = Column(Float, default=0.0)
    memory = Column(Float, default=0.0)
    latency = Column(Float, default=0.0)
    error_rate = Column(Float, default=0.0)
    rx_bytes = Column(Float, default=0.0)
    tx_bytes = Column(Float, default=0.0)
    fault_type = Column(String(32), nullable=True)
    updated_at = Column(Integer, default=lambda: int(time.time() * 1000))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "cpu": round(self.cpu, 2),
            "memory": round(self.memory, 2),
            "latency": round(self.latency, 2),
            "errorRate": round(self.error_rate, 4),
            "rxBytes": round(self.rx_bytes, 1),
            "txBytes": round(self.tx_bytes, 1),
            "faultType": self.fault_type,
            "updatedAt": self.updated_at,
        }


class AnomalyModel(Base):
    __tablename__ = "anomalies"

    id = Column(String(64), primary_key=True)
    service = Column(String(64), nullable=False, index=True)
    metric = Column(String(128), nullable=False)
    unit = Column(String(32), default="")
    observed = Column(Float, default=0.0)
    baseline = Column(Float, default=0.0)
    severity = Column(String(32), default="Warning")  # Critical, Warning, Info
    detected_at = Column(Integer, nullable=False, index=True)
    score = Column(Float, default=0.0)
    status = Column(String(32), default="Open")  # Open, Under review, Closed, Dismissed
    fault_type = Column(String(32), nullable=True)
    anomaly_score = Column(Float, default=0.0)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "service": self.service,
            "metric": self.metric,
            "unit": self.unit,
            "observed": round(self.observed, 2),
            "baseline": round(self.baseline, 2),
            "severity": self.severity,
            "detectedAt": self.detected_at,
            "score": round(self.score, 3),
            "status": self.status,
            "faultType": self.fault_type,
            "anomalyScore": round(self.anomaly_score, 3),
        }


class AlertModel(Base):
    __tablename__ = "alerts"

    id = Column(String(64), primary_key=True)
    title = Column(String(256), nullable=False)
    severity = Column(String(32), default="Warning")  # Critical, Warning, Info
    service = Column(String(64), nullable=False, index=True)
    metric = Column(String(128), nullable=False)
    timestamp = Column(Integer, nullable=False, index=True)
    status = Column(String(32), default="Active")  # Active, Acknowledged, Resolved
    fault_type = Column(String(32), nullable=True)
    description = Column(Text, default="")
    evidence = Column(Text, default="")
    affected_metrics_json = Column(Text, default="[]")
    anomaly_score = Column(Float, default=0.0)
    incident_id = Column(String(64), nullable=True, index=True)

    @property
    def affected_metrics(self) -> List[str]:
        try:
            return json.loads(self.affected_metrics_json or "[]")
        except Exception:
            return []

    @affected_metrics.setter
    def affected_metrics(self, value: List[str]):
        self.affected_metrics_json = json.dumps(value)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "severity": self.severity,
            "service": self.service,
            "metric": self.metric,
            "timestamp": self.timestamp,
            "status": self.status,
            "faultType": self.fault_type,
            "description": self.description,
            "evidence": self.evidence,
            "affectedMetrics": self.affected_metrics,
            "anomalyScore": round(self.anomaly_score, 3),
            "incidentId": self.incident_id,
        }


class IncidentModel(Base):
    __tablename__ = "incidents"

    id = Column(String(64), primary_key=True)
    start = Column(Integer, nullable=False, index=True)
    end = Column(Integer, nullable=True)
    ongoing = Column(Boolean, default=True)
    duration_min = Column(Integer, default=1)
    services_json = Column(Text, default="[]")
    severity = Column(String(32), default="Warning")
    alerts_json = Column(Text, default="[]")
    status = Column(String(32), default="Ongoing")  # Ongoing, Resolved, Closed
    fault_types_json = Column(Text, default="[]")
    category = Column(String(256), default="")

    @property
    def services(self) -> List[str]:
        try:
            return json.loads(self.services_json or "[]")
        except Exception:
            return []

    @services.setter
    def services(self, value: List[str]):
        self.services_json = json.dumps(value)

    @property
    def alerts(self) -> List[str]:
        try:
            return json.loads(self.alerts_json or "[]")
        except Exception:
            return []

    @alerts.setter
    def alerts(self, value: List[str]):
        self.alerts_json = json.dumps(value)

    @property
    def fault_types(self) -> List[str]:
        try:
            return json.loads(self.fault_types_json or "[]")
        except Exception:
            return []

    @fault_types.setter
    def fault_types(self, value: List[str]):
        self.fault_types_json = json.dumps(value)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "start": self.start,
            "end": self.end,
            "ongoing": self.ongoing,
            "durationMin": self.duration_min,
            "services": self.services,
            "severity": self.severity,
            "alerts": self.alerts,
            "status": self.status,
            "faultTypes": self.fault_types,
            "category": self.category,
        }
