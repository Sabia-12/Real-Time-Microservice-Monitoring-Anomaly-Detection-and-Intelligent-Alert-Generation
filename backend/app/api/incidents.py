"""Incident endpoints matching docs/api_contract.md."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.db.models import IncidentModel

router = APIRouter(prefix="/incidents", tags=["Incidents"])


@router.get("")
def list_incidents(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    status: Optional[str] = None,
    severity: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """List all incidents (grouped alerts)."""
    query = db.query(IncidentModel)
    if status:
        query = query.filter(IncidentModel.status == status)
    if severity:
        query = query.filter(IncidentModel.severity == severity)

    incidents = (
        query.order_by(IncidentModel.start.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [inc.to_dict() for inc in incidents]
