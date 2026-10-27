"""
Incident grouping module based on Online Boutique topology and temporal proximity.

Groups related service alerts occurring within a temporal correlation window into a unified incident.
"""

import time
import uuid
from typing import Dict, List, Optional, Set
from sqlalchemy.orm import Session

from backend.app.db.models import AlertModel, IncidentModel


# Real call graph of Google Online Boutique
ONLINE_BOUTIQUE_GRAPH: Dict[str, List[str]] = {
    "frontend": [
        "checkoutservice",
        "productcatalogservice",
        "recommendationservice",
        "cartservice",
        "shippingservice",
        "currencyservice",
        "adservice",
    ],
    "checkoutservice": [
        "paymentservice",
        "emailservice",
        "cartservice",
        "shippingservice",
        "currencyservice",
        "productcatalogservice",
    ],
    "recommendationservice": [
        "productcatalogservice",
    ],
    "cartservice": [],
    "paymentservice": [],
    "shippingservice": [],
    "emailservice": [],
    "currencyservice": [],
    "productcatalogservice": [],
    "adservice": [],
}


def are_services_related(svc_a: str, svc_b: str) -> bool:
    """
    Check if two services are topologically connected in Online Boutique.
    Returns True if:
        1. They are the same service.
        2. There is a direct call relationship (A -> B or B -> A).
        3. They share a direct upstream dependency (e.g. both called by checkoutservice or frontend).
    """
    if svc_a == svc_b:
        return True

    # Direct edges
    if svc_b in ONLINE_BOUTIQUE_GRAPH.get(svc_a, []):
        return True
    if svc_a in ONLINE_BOUTIQUE_GRAPH.get(svc_b, []):
        return True

    # Shared callers
    for caller, downstream in ONLINE_BOUTIQUE_GRAPH.items():
        if svc_a in downstream and svc_b in downstream:
            return True

    # 2-hop reachability (A -> X -> B or B -> X -> A)
    for mid in ONLINE_BOUTIQUE_GRAPH.get(svc_a, []):
        if svc_b in ONLINE_BOUTIQUE_GRAPH.get(mid, []):
            return True
    for mid in ONLINE_BOUTIQUE_GRAPH.get(svc_b, []):
        if svc_a in ONLINE_BOUTIQUE_GRAPH.get(mid, []):
            return True

    return False


class IncidentGrouper:
    """
    Groups alerts into incidents using topology and a temporal window.
    """

    def __init__(self, time_window_seconds: int = 120):
        """
        Args:
            time_window_seconds: Max seconds between alerts to be considered part of the same incident.
        """
        self.time_window_seconds = time_window_seconds

    def group_alert(
        self,
        db: Session,
        alert: AlertModel,
    ) -> IncidentModel:
        """
        Assign an alert to an existing ongoing incident or create a new incident.

        Args:
            db: Database session.
            alert: The newly generated alert.

        Returns:
            The IncidentModel that the alert belongs to.
        """
        time_window_ms = self.time_window_seconds * 1000
        cutoff_start = alert.timestamp - time_window_ms

        # Look for ongoing incidents active in the temporal window
        active_incidents = (
            db.query(IncidentModel)
            .filter(
                IncidentModel.ongoing == True,
                IncidentModel.start >= cutoff_start,
            )
            .order_by(IncidentModel.start.desc())
            .all()
        )

        target_incident: Optional[IncidentModel] = None

        for inc in active_incidents:
            # Check if any service in the incident is topologically related to the alert's service
            if any(are_services_related(alert.service, s) for s in inc.services):
                target_incident = inc
                break

        if target_incident:
            # Add alert to existing incident
            curr_alerts = set(target_incident.alerts)
            curr_alerts.add(alert.id)
            target_incident.alerts = sorted(list(curr_alerts))

            curr_services = set(target_incident.services)
            curr_services.add(alert.service)
            target_incident.services = sorted(list(curr_services))

            if alert.fault_type:
                curr_faults = set(target_incident.fault_types)
                curr_faults.add(alert.fault_type)
                target_incident.fault_types = sorted(list(curr_faults))

            # Recalculate duration and severity
            duration_ms = max(0, alert.timestamp - target_incident.start)
            target_incident.duration_min = max(1, int(duration_ms / 60000))

            if alert.severity == "Critical":
                target_incident.severity = "Critical"

            # Update category description
            target_incident.category = self._generate_category(
                target_incident.services, target_incident.fault_types
            )

            alert.incident_id = target_incident.id
            return target_incident
        else:
            # Create a new incident
            inc_id = f"INC-{int(time.time() * 1000) % 10000:04d}"
            # Ensure unique id
            while db.query(IncidentModel).filter(IncidentModel.id == inc_id).first():
                inc_id = f"INC-{int(time.time() * 1000 + 7) % 10000:04d}"

            fault_types = [alert.fault_type] if alert.fault_type else []
            new_incident = IncidentModel(
                id=inc_id,
                start=alert.timestamp,
                end=None,
                ongoing=True,
                duration_min=1,
                services=[alert.service],
                severity=alert.severity,
                alerts=[alert.id],
                status="Ongoing",
                fault_types=fault_types,
                category=self._generate_category([alert.service], fault_types),
            )
            db.add(new_incident)
            db.flush()

            alert.incident_id = new_incident.id
            return new_incident

    def _generate_category(self, services: List[str], fault_types: List[str]) -> str:
        """Generate human-readable incident category summary."""
        fault_desc = ", ".join(fault_types) if fault_types else "anomaly"
        if len(services) > 1:
            return f"Cascading microservice degradation ({fault_desc}) across {len(services)} services: {', '.join(services[:3])}"
        elif len(services) == 1:
            return f"{services[0].capitalize()} service degradation ({fault_desc})"
        return "Microservice anomaly incident"
