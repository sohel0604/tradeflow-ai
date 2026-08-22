"""
TradeFlow AI — Custom Exceptions & Global Handlers
Day 16: Never expose stack traces. Always return clean JSON.

Two types of errors:
1. Expected errors  → HTTPException (404, 403, 422 etc.) — handled normally
2. Unexpected errors → Exception (500) — caught here, returns clean JSON

Response format for ALL errors:
{
    "error": "Human readable message",
    "detail": "Optional extra context",
    "correlation_id": "abc123"   ← from request header
}
"""
import structlog
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = structlog.get_logger(__name__)


# =============================================================================
# Base exception for all TradeFlow errors
# Lets us add custom fields (error_code, user-facing message) later
# =============================================================================
class TradeFlowException(Exception):
    """Base exception for all TradeFlow-specific errors."""
    def __init__(self, message: str, status_code: int = 400, detail: str = None):
        self.message = message
        self.status_code = status_code
        self.detail = detail
        super().__init__(message)


class NotFoundError(TradeFlowException):
    def __init__(self, resource: str, id: str = None):
        msg = f"{resource} not found"
        if id:
            msg = f"{resource} '{id}' not found"
        super().__init__(msg, status_code=404)


class PermissionDeniedError(TradeFlowException):
    def __init__(self, message: str = "Permission denied"):
        super().__init__(message, status_code=403)


class PlanLimitError(TradeFlowException):
    """Raised when a Free tier user tries to exceed plan limits."""
    def __init__(self, message: str):
        super().__init__(message, status_code=403)


# =============================================================================
# Global exception handlers — registered in main.py
# =============================================================================

async def tradeflow_exception_handler(
    request: Request,
    exc: TradeFlowException,
) -> JSONResponse:
    """Handle our custom exceptions — clean JSON response."""
    correlation_id = request.headers.get("X-Correlation-ID", "unknown")

    logger.warning(
        "application_error",
        error=exc.message,
        status_code=exc.status_code,
        path=request.url.path,
    )

    body = {
        "error": exc.message,
        "correlation_id": correlation_id,
    }
    if exc.detail:
        body["detail"] = exc.detail

    return JSONResponse(status_code=exc.status_code, content=body)


async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    """Handle FastAPI HTTPExceptions (404, 403 etc.)."""
    correlation_id = request.headers.get("X-Correlation-ID", "unknown")

    logger.warning(
        "http_error",
        status_code=exc.status_code,
        detail=str(exc.detail),
        path=request.url.path,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": str(exc.detail),
            "correlation_id": correlation_id,
        },
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """
    Handle Pydantic validation errors (422 Unprocessable Entity).
    Converts Pydantic's error format into our standard format.

    Example: missing required field → clear error message.
    """
    correlation_id = request.headers.get("X-Correlation-ID", "unknown")

    # Extract field-level errors from Pydantic
    errors = []
    for error in exc.errors():
        field = " → ".join(str(loc) for loc in error["loc"])
        errors.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"],
        })

    logger.warning(
        "validation_error",
        errors=errors,
        path=request.url.path,
    )

    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation failed",
            "fields": errors,
            "correlation_id": correlation_id,
        },
    )


async def global_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """
    Catch-all for any unhandled exception.
    NEVER expose the stack trace — log it internally, return clean JSON.

    If a user sees a 500 error, they get:
    {"error": "Internal server error", "correlation_id": "abc123"}

    NOT:
    {"traceback": "File main.py line 42 in ..."}  ← never do this
    """
    correlation_id = request.headers.get("X-Correlation-ID", "unknown")

    # Log the FULL exception internally (we need it for debugging)
    logger.error(
        "unhandled_exception",
        error=str(exc),
        error_type=type(exc).__name__,
        path=request.url.path,
        exc_info=True,      # includes stack trace in the LOG (not response)
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "correlation_id": correlation_id,
        },
    )
