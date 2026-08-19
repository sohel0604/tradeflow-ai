"""
Backtest routes — Day 15: Stub only.
Full implementation on Day 91 (results, trade-log, on-demand run).
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/status")
async def backtest_status():
    """Placeholder — confirms backtest router is registered."""
    return {"router": "backtest", "status": "coming Day 91"}
