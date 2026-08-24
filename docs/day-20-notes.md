# Day 20 Notes — August 23, 2026
## Topic: Exception Handler Testing + pytest + Week 3 Complete

---

## pytest — Python's testing framework

```bash
# Run all tests
pytest tests/ -v

# Run a specific file
pytest tests/unit/test_exceptions.py -v

# Run a specific test class
pytest tests/unit/test_exceptions.py::TestNotFoundError -v

# Run a specific test
pytest tests/unit/test_exceptions.py::TestNotFoundError::test_returns_404 -v
```

`-v` = verbose mode — shows each test name and PASSED/FAILED.

---

## TestClient — testing FastAPI without a real server

```python
from fastapi.testclient import TestClient

app = FastAPI()
client = TestClient(app)

# Makes a real HTTP request to the test app — no server needed
resp = client.get("/health")
assert resp.status_code == 200
assert resp.json()["status"] == "ok"
```

`TestClient` spins up an in-memory ASGI server.
No real HTTP connections. No network. No Docker needed.
Tests run in milliseconds.

`raise_server_exceptions=False` — instead of raising Python exceptions
in the test, it returns the HTTP error response. This lets us test
500 error responses cleanly.

---

## Test class organisation

```python
class TestNotFoundError:
    def test_returns_404(self, client): ...
    def test_returns_json_error_field(self, client): ...
    def test_has_correlation_id(self, client): ...

class TestUnhandledException:
    def test_returns_500(self, client): ...
    def test_no_stack_trace_in_response(self, client): ...
```

Group tests by the thing being tested (exception type).
Each method tests ONE specific thing.
Test names read like requirements:
`test_no_stack_trace_in_response` = "it must never expose stack traces"

---

## @pytest.fixture — shared setup

```python
@pytest.fixture
def client():
    app = make_test_app()
    return TestClient(app, raise_server_exceptions=False)
```

A fixture runs before each test that declares it as a parameter.

```python
def test_returns_404(self, client):  # ← client fixture injected here
    resp = client.get("/raise-not-found")
    assert resp.status_code == 404
```

`client` is created fresh for each test — no state leaks between tests.

---

## The most important test we wrote

```python
def test_no_stack_trace_in_response(self, client):
    body = client.get("/raise-500").json()
    assert "traceback" not in body
    assert "RuntimeError" not in str(body)
    assert body["error"] == "Internal server error"
```

This test PROVES our golden rule:
**users never see stack traces.**

A stack trace in a 500 response exposes:
- File paths → attacker knows your directory structure
- Library names → attacker knows what to exploit
- Variable values → attacker might see sensitive data

Our exception handler logs the full trace internally
but returns only `"Internal server error"` to the user.

---

## What we tested today — 20 tests, 6 groups

| Test class | What it proves |
|-----------|---------------|
| `TestNotFoundError` | 404 returns correct status + JSON + correlation ID |
| `TestPermissionDeniedError` | 403 with correct message |
| `TestPlanLimitError` | 403 for Free tier limit violations |
| `TestHTTPException` | FastAPI HTTPExceptions return clean JSON |
| `TestUnhandledException` | 500 never exposes stack trace |
| `TestCorrelationIDPropagation` | Client ID echoed back, UUID generated if missing |
| `TestExceptionHierarchy` | Custom exceptions inherit from TradeFlowException |

---

## Week 3 Complete — Days 15–20

| Day | What was built |
|-----|---------------|
| 15 | FastAPI app factory + 6 route groups registered |
| 16 | CORS + RequestLoggingMiddleware + correlation IDs + exception handlers |
| 17 | pydantic-settings config + `/config-check` dev endpoint |
| 18 | Pydantic v2 schemas with field validators + PaginatedResponse[T] |
| 19 | MongoDB service layer + 3 real API endpoints |
| 20 | pytest setup + 20 exception handler tests + week review |

---

## What starts next week — Days 21–30 (Data Pipeline)

```
Day 21 → yfinance fetcher — download real OHLCV data
Day 22 → Binance fetcher — crypto OHLCV
Day 23 → Data cleaning module
Day 24 → PostgreSQL DB writer with upsert
Day 25 → Celery task: fetch + clean + store
Day 26 → Technical indicator engine (EMA, RSI, MACD etc.)
Day 27 → Store indicators in MongoDB
Day 28 → CSV upload + price bars API endpoint
Day 29 → Fetch failure alert system
Day 30 → Week 4 review + pipeline end-to-end test
```

By Day 30 you'll have REAL market data from yfinance and Binance
flowing automatically into PostgreSQL and MongoDB on a daily schedule.

---

## Your GitHub streak after 3 weeks: 20 days ✅

Every single day. Every single commit. Keep going.
