"""
Watchlist routes — Day 15: Stub only.
Full implementation on Day 89 (add, remove, search, tier limits).
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/status")
async def watchlist_status():
    """Placeholder — confirms watchlist router is registered."""
    return {"router": "watchlist", "status": "coming Day 89"}
