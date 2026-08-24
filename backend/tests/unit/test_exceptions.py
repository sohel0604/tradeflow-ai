"""
Day 20 — Exception Handler Tests.

Tests every exception path:
  - Custom TradeFlowException subtypes
  - 404 HTTPException
  - Pydantic validation error (422)
  - Unhandled exception → clean 500 JSON

Run with:
    docker compose exec backend pytest tests/unit/test_exceptions.py -v
"""
import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI, HTTPException

from app.core.exceptions import (
    TradeFlowException,
    NotFoundError,
    PermissionDeniedError,
    PlanLimitError,
    tradeflow_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    global_exception_handler,
)
from app.core.middleware import RequestLoggingMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException


# ---------------------------------------------------------------------------
# Build a minimal test app — same exception handlers as main.py
# We don't import main.py directly to avoid DB startup in tests
# ---------------------------------------------------------------------------
def make_test_app() -> FastAPI:
    app = FastAPI()

    app.add_middleware(RequestLoggingMiddleware)
    app.add_exception_handler(TradeFlowException, tradeflow_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, global_exception_handler)

    @app.get("/raise-not-found")
    async def raise_not_found():
        raise NotFoundError("Signal", "abc-123")

    @app.get("/raise-permission")
    async def raise_permission():
        raise PermissionDeniedError("Pro plan required")

    @app.get("/raise-plan-limit")
    async def raise_plan_limit():
        raise PlanLimitError("Free tier limit: max 3 symbols")

    @app.get("/raise-http-404")
    async def raise_http_404():
        raise HTTPException(status_code=404, detail="Resource not found")

    @app.get("/raise-500")
    async def raise_500():
        raise RuntimeError("Something totally unexpected happened")

    @app.get("/raise-tradeflow")
    async def raise_tradeflow():
        raise TradeFlowException(
            message="Custom error",
            status_code=400,
            detail="Extra context",
        )

    return app


@pytest.fixture
def client():
    app = make_test_app()
    return TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestNotFoundError:
    def test_returns_404(self, client):
        resp = client.get("/raise-not-found")
        assert resp.status_code == 404

    def test_returns_json_error_field(self, client):
        resp = client.get("/raise-not-found")
        body = resp.json()
        assert "error" in body
        assert "abc-123" in body["error"]

    def test_has_correlation_id(self, client):
        resp = client.get("/raise-not-found")
        assert "correlation_id" in resp.json()

    def test_correlation_id_in_response_header(self, client):
        resp = client.get("/raise-not-found")
        assert "x-correlation-id" in resp.headers


class TestPermissionDeniedError:
    def test_returns_403(self, client):
        resp = client.get("/raise-permission")
        assert resp.status_code == 403

    def test_error_message(self, client):
        body = client.get("/raise-permission").json()
        assert "Pro plan required" in body["error"]


class TestPlanLimitError:
    def test_returns_403(self, client):
        resp = client.get("/raise-plan-limit")
        assert resp.status_code == 403

    def test_error_message_contains_limit(self, client):
        body = client.get("/raise-plan-limit").json()
        assert "Free tier" in body["error"]


class TestHTTPException:
    def test_404_returns_clean_json(self, client):
        resp = client.get("/raise-http-404")
        assert resp.status_code == 404
        body = resp.json()
        assert body["error"] == "Resource not found"
        assert "traceback" not in body   # NEVER expose stack trace

    def test_unknown_route_404(self, client):
        resp = client.get("/this-does-not-exist")
        assert resp.status_code == 404
        assert "error" in resp.json()


class TestUnhandledException:
    def test_returns_500(self, client):
        resp = client.get("/raise-500")
        assert resp.status_code == 500

    def test_no_stack_trace_in_response(self, client):
        body = client.get("/raise-500").json()
        assert "traceback" not in body
        assert "RuntimeError" not in str(body)
        assert body["error"] == "Internal server error"

    def test_has_correlation_id(self, client):
        body = client.get("/raise-500").json()
        assert "correlation_id" in body


class TestTradeFlowException:
    def test_custom_status_code(self, client):
        resp = client.get("/raise-tradeflow")
        assert resp.status_code == 400

    def test_detail_field_present(self, client):
        body = client.get("/raise-tradeflow").json()
        assert body["error"] == "Custom error"
        assert body["detail"] == "Extra context"


class TestCorrelationIDPropagation:
    def test_sent_correlation_id_echoed_back(self, client):
        """
        When a client sends X-Correlation-ID, we echo it back.
        This lets clients trace their requests through our logs.
        """
        custom_id = "my-trace-id-12345"
        resp = client.get(
            "/raise-not-found",
            headers={"X-Correlation-ID": custom_id}
        )
        assert resp.headers.get("x-correlation-id") == custom_id

    def test_auto_generated_when_not_sent(self, client):
        """When no X-Correlation-ID header, we generate one."""
        resp = client.get("/raise-not-found")
        corr_id = resp.headers.get("x-correlation-id", "")
        assert len(corr_id) > 0
        # Should look like a UUID
        assert "-" in corr_id


class TestExceptionHierarchy:
    def test_not_found_is_tradeflow_exception(self):
        exc = NotFoundError("Signal")
        assert isinstance(exc, TradeFlowException)
        assert exc.status_code == 404

    def test_permission_denied_is_tradeflow_exception(self):
        exc = PermissionDeniedError()
        assert isinstance(exc, TradeFlowException)
        assert exc.status_code == 403

    def test_plan_limit_is_tradeflow_exception(self):
        exc = PlanLimitError("limit reached")
        assert isinstance(exc, TradeFlowException)
        assert exc.status_code == 403
