"""
Account routes — Day 15: Stub only.
Full implementation on Day 95 (profile, broker credentials, API keys).
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/status")
async def account_status():
    """Placeholder — confirms account router is registered."""
    return {"router": "account", "status": "coming Day 95"}
