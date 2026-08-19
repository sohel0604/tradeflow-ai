"""
Auth routes — Day 15: Stub only.
Full implementation on Day 79 (register, login, refresh, logout).
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/status")
async def auth_status():
    """Placeholder — confirms auth router is registered."""
    return {"router": "auth", "status": "coming Day 79"}
