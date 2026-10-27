"""Anomaly endpoints matching docs/api_contract.md."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.db.models import AnomalyModel

router = APIRouter(prefix="/anomalies", tags=["Anomalies"])


@router.get("")
def list_anomalies(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    service: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """List all detected anomalies."""
    query = db.query(AnomalyModel)
    if service:
        query = query.filter(AnomalyModel.service == service)
    if status:
        query = query.filter(AnomalyModel.status == status)

    anomalies = (
        query.order_by(AnomalyModel.detected_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [a.to_dict() for a in anomalies]
