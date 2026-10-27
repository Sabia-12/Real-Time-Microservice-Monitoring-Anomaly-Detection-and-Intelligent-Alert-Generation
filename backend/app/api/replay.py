"""Replay control endpoints for historical RE2-OB streaming."""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query

from backend.preprocessing.loader import list_cases, DEFAULT_DATA_DIR
from backend.app.replay import replay_manager

router = APIRouter(prefix="/replay", tags=["Replay"])


@router.get("/cases")
def get_available_cases():
    """List all available RE2-OB cases that can be replayed."""
    cases = list_cases()
    return {"total": len(cases), "cases": cases}


@router.get("/status")
def get_replay_status():
    """Get current historical replay streamer status."""
    return replay_manager.status


@router.post("/start")
def start_replay(
    case_id: str = Query(..., description="RE2-OB case name, e.g. re2ob_checkoutservice_cpu_1"),
    speed: float = Query(5.0, description="Speed multiplier (e.g. 1.0, 5.0, 10.0)"),
):
    """Start streaming an RE2-OB case through the pipeline."""
    available = list_cases()
    if case_id not in available:
        raise HTTPException(
            status_code=404,
            detail=f"Case '{case_id}' not found in data/raw. Available cases: {len(available)}",
        )

    replay_manager.start(case_id=case_id, speed=speed)
    return {
        "status": "started",
        "case_id": case_id,
        "speed": speed,
    }


@router.post("/stop")
def stop_replay():
    """Stop the ongoing historical replay."""
    replay_manager.stop()
    return {"status": "stopped"}
