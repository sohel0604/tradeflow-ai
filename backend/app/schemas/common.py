"""
TradeFlow AI — Common Schemas
Day 18: Reusable response types used across all routes.

These are the building blocks every other schema inherits from or uses:
- PaginatedResponse[T]  → paginated list of any item type
- SuccessResponse       → simple {"message": "..."} responses
- ErrorResponse         → consistent error format
- HealthResponse        → /health endpoint response
"""
from typing import Generic, List, TypeVar
from pydantic import BaseModel, Field

# T can be any Pydantic model — makes PaginatedResponse reusable
T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Standard paginated response for any list endpoint.

    Usage:
        @router.get("/signals")
        async def list_signals() -> PaginatedResponse[SignalResponse]:
            ...

    Response JSON:
        {
            "items": [...],
            "total": 150,
            "page": 1,
            "page_size": 20,
            "pages": 8
        }
    """
    items: List[T]
    total: int = Field(description="Total number of items across all pages")
    page: int = Field(ge=1, description="Current page number (1-indexed)")
    page_size: int = Field(ge=1, le=100, description="Items per page")
    pages: int = Field(description="Total number of pages")

    @classmethod
    def create(
        cls,
        items: List[T],
        total: int,
        page: int,
        page_size: int,
    ) -> "PaginatedResponse[T]":
        """
        Helper to build a paginated response without
        manually calculating total pages every time.
        """
        import math
        pages = math.ceil(total / page_size) if page_size > 0 else 0
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )


class SuccessResponse(BaseModel):
    """
    Simple success message for operations that don't return data.

    Used for: delete operations, link/unlink actions, trigger actions.

    Example:
        DELETE /api/v1/watchlist/RELIANCE.NS
        → {"message": "RELIANCE.NS removed from watchlist"}
    """
    message: str


class ErrorResponse(BaseModel):
    """
    Standard error response shape.
    All exception handlers return this format.

    Example:
        {"error": "Not found", "correlation_id": "abc-123"}
    """
    error: str
    correlation_id: str = "unknown"
    detail: str | None = None


class HealthResponse(BaseModel):
    """Response schema for GET /health."""
    status: str
    service: str
    version: str
    env: str


class DatabaseHealthResponse(BaseModel):
    """Response schema for GET /health/db."""

    class DatabaseStatus(BaseModel):
        postgres: str
        mongodb: str

    status: str
    databases: DatabaseStatus
