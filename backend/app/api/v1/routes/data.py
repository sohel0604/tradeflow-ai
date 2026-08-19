"""
Data routes — Day 15: Stub only.
Full implementation on Day 28 (CSV upload, price bars, instrument search).
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/status")
async def data_status():
    """Placeholder — confirms data router is registered."""
    return {"router": "data", "status": "coming Day 28"}
