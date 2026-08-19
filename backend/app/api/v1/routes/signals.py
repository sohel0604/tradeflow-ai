"""
Signals routes — Day 15: Stub only.
Full implementation on Day 88 (list, detail, filter, cache).
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/status")
async def signals_status():
    """Placeholder — confirms signals router is registered."""
    return {"router": "signals", "status": "coming Day 88"}
