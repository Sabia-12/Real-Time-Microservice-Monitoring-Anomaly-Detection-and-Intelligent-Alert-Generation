"""Health check endpoint."""

from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("")
def get_health():
    """Liveness & health probe."""
    return {"status": "ok", "version": "0.1.0"}
