"""Alert endpoints matching docs/api_contract.md."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.db.models import AlertModel

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("")
def list_alerts(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    status: Optional[str] = None,
    service: Optional[str] = None,
    severity: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """List all alerts with optional filtering."""
    query = db.query(AlertModel)
    if status:
        query = query.filter(AlertModel.status == status)
    if service:
        query = query.filter(AlertModel.service == service)
    if severity:
        query = query.filter(AlertModel.severity == severity)

    alerts = (
        query.order_by(AlertModel.timestamp.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [a.to_dict() for a in alerts]


@router.post("/{alert_id}/acknowledge")
def acknowledge_alert(alert_id: str, db: Session = Depends(get_db)):
    """Mark alert as acknowledged."""
    alert = db.query(AlertModel).filter(AlertModel.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert '{alert_id}' not found")

    alert.status = "Acknowledged"
    db.commit()
    return alert.to_dict()


@router.post("/{alert_id}/resolve")
def resolve_alert(alert_id: str, db: Session = Depends(get_db)):
    """Mark alert as resolved."""
    alert = db.query(AlertModel).filter(AlertModel.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert '{alert_id}' not found")

    alert.status = "Resolved"
    db.commit()
    return alert.to_dict()
