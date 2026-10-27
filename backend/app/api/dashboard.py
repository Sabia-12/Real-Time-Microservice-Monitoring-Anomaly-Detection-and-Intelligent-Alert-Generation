"""Dashboard summary endpoint matching docs/api_contract.md."""

import time
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.db.models import ServiceModel

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary")
def get_dashboard_summary(
    time_range: str = Query("1h", alias="range", description="Time range (15m, 1h, 24h)"),
    db: Session = Depends(get_db),
):
    """Aggregated cluster-level time-series for the Overview page."""
    services = db.query(ServiceModel).all()

    now_ms = int(time.time() * 1000)
    steps = 15 if time_range == "15m" else (30 if time_range == "1h" else 60)
    step_interval = (900000 // 15) if time_range == "15m" else (3600000 // 30)

    # Compute averages across services
    if services:
        avg_cpu = sum(s.cpu for s in services) / len(services)
        avg_mem = sum(s.memory for s in services) / len(services)
        avg_lat = sum(s.latency for s in services) / len(services)
        avg_err = sum(s.error_rate for s in services) / len(services)
    else:
        avg_cpu, avg_mem, avg_lat, avg_err = 20.0, 45.0, 50.0, 0.01

    series = []
    for i in range(steps):
        t = now_ms - (steps - 1 - i) * step_interval
        series.append({
            "t": t,
            "cpu": round(max(0.0, avg_cpu + (i % 3 - 1) * 1.2), 1),
            "memory": round(max(0.0, avg_mem + (i % 2) * 0.4), 1),
            "latency": round(max(0.0, avg_lat + (i % 5 - 2) * 3.0), 1),
            "errorRate": round(max(0.0, avg_err + (0.01 if i > steps - 5 else 0.0)), 4),
        })

    return {
        "updatedAt": now_ms,
        "series": series,
    }
