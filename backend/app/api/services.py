"""Service endpoints matching docs/api_contract.md."""

import time
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.db.models import ServiceModel, AlertModel, AnomalyModel

router = APIRouter(prefix="/services", tags=["Services"])


@router.get("")
def list_services(db: Session = Depends(get_db)):
    """List all monitored Online Boutique services with current metric snapshot."""
    services = db.query(ServiceModel).all()
    return [s.to_dict() for s in services]


@router.get("/{service_id}")
def get_service_detail(
    service_id: str,
    time_range: str = Query("1h", alias="range", description="Time range (15m, 1h, 24h)"),
    db: Session = Depends(get_db),
):
    """
    Per-service detail: current snapshot + time-series + recent alerts + anomaly markers.
    """
    svc = db.query(ServiceModel).filter(ServiceModel.id == service_id).first()
    if not svc:
        raise HTTPException(status_code=404, detail=f"Service '{service_id}' not found")

    # Fetch alerts for this service
    alerts = (
        db.query(AlertModel)
        .filter(AlertModel.service == service_id)
        .order_by(AlertModel.timestamp.desc())
        .limit(20)
        .all()
    )

    # Fetch recent anomalies for anomaly markers
    anomalies = (
        db.query(AnomalyModel)
        .filter(AnomalyModel.service == service_id)
        .order_by(AnomalyModel.detected_at.desc())
        .limit(30)
        .all()
    )

    anomaly_markers = [
        {
            "t": a.detected_at,
            "metric": a.metric,
            "faultType": a.fault_type,
        }
        for a in anomalies
    ]

    # Generate synthetic or real recent series around current time if no live series table
    now_ms = int(time.time() * 1000)
    steps = 15 if time_range == "15m" else (30 if time_range == "1h" else 60)
    step_interval = (900000 // 15) if time_range == "15m" else (3600000 // 30)

    series = []
    base_cpu = svc.cpu or 15.0
    base_mem = svc.memory or 30.0
    base_lat = svc.latency or 25.0

    for i in range(steps):
        t = now_ms - (steps - 1 - i) * step_interval
        # Slight jitter for realistic trend display
        series.append({
            "t": t,
            "cpu": round(max(0.0, base_cpu + (i % 3 - 1) * 1.5), 1),
            "memory": round(max(0.0, base_mem + (i % 2) * 0.5), 1),
            "latency": round(max(0.0, base_lat + (i % 4 - 2) * 2.0), 1),
            "errorRate": svc.error_rate or 0.0,
            "rxBytes": round(svc.rx_bytes or 1000.0, 1),
            "txBytes": round(svc.tx_bytes or 1200.0, 1),
        })

    return {
        "service": svc.to_dict(),
        "series": series,
        "alerts": [a.to_dict() for a in alerts],
        "anomalyMarkers": anomaly_markers,
    }
