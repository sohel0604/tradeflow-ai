# 🚀 TradeFlow AI — 120-Day Development Plan

**Start Date:** August 4, 2026 | **End Date:** December 1, 2026
**Rule:** One day = one focused task = one GitHub commit. Build it yourself, understand it fully.

---

## 📊 Quick Progress Board

| Month | Days | Dates | Focus |
|-------|------|-------|-------|
| Month 1 | 1–30 | Aug 4 – Sep 2 | Docker, DB, Python backend, Data pipeline |
| Month 2 | 31–60 | Sep 3 – Oct 2 | Celery, Indicators, Backtest engine, Patterns |
| Month 3 | 61–90 | Oct 3 – Nov 1 | Claude AI, Charts, Email, Telegram, Auth, Payments |
| Month 4 | 91–120 | Nov 2 – Dec 1 | REST API, WebSockets, React frontend, Live charts |

**Legend:** ✅ Done | 🔄 In Progress | 🔲 Not Started

---

## 🗓️ MONTH 1 — Foundation & Data Pipeline
### Aug 4 – Sep 2, 2026

---

### WEEK 1 — Project Setup & Docker (Aug 4–10)

---

#### 🔲 Day 1 — Aug 4, 2026 — Project Scaffold & GitHub Setup

**Concept:** Monorepo structure, Git basics, GitHub repo creation

**What to build today:**
- Create GitHub repo `tradeflow-ai` (public or private)
- Create this folder structure locally:
```
tradeflow-ai/
├── backend/
├── frontend/
├── nginx/
├── infra/
├── tests/
├── docs/
└── TASK_TRACKER.md
```
- Write `README.md` with one-line project description
- Write `.gitignore` for Python + Node + Docker

**Files to create:**
- `README.md`
- `.gitignore`
- `docs/day-01-notes.md` — write 5 things you learned today

**Git commit:**
```bash
git add .
git commit -m "feat: project scaffold monorepo structure and github setup"
git push origin main
```

---

#### 🔲 Day 2 — Aug 5, 2026 — Docker Fundamentals + Backend Dockerfile

**Concept:** Docker images, containers, Dockerfile syntax

**What to build today:**
- Install Docker Desktop on your Mac
- Understand: image vs container, layers, volumes, port mapping
- Write `backend/Dockerfile` — Python 3.11-slim base image

**Files to create:**
- `backend/Dockerfile`
- `docs/day-02-notes.md` — explain in your own words: what is Docker?

**Git commit:**
```bash
git commit -m "feat: backend dockerfile python 3.11 slim"
```

---

#### 🔲 Day 3 — Aug 6, 2026 — Docker Compose: PostgreSQL

**Concept:** docker-compose.yml, services, volumes, health checks

**What to build today:**
- Write `docker-compose.yml` with only PostgreSQL 15
- Add named volume `postgres_data`
- Add health check: `pg_isready`
- Run it: `docker compose up` → verify PostgreSQL starts

**Files to create/edit:**
- `docker-compose.yml` (PostgreSQL service only)

**Git commit:**
```bash
git commit -m "feat: docker-compose postgresql 15 with health check"
```

---

#### 🔲 Day 4 — Aug 7, 2026 — Docker Compose: MongoDB + Redis

**Concept:** Multi-service orchestration, depends_on, Redis auth

**What to build today:**
- Add MongoDB 7 service to docker-compose.yml
- Add Redis 7 service with password
- Health checks for both
- Run all 3 together: `docker compose up`

**Files to edit:**
- `docker-compose.yml` (add MongoDB + Redis)

**Git commit:**
```bash
git commit -m "feat: add mongodb 7 and redis 7 to docker-compose"
```

---

#### 🔲 Day 5 — Aug 8, 2026 — Nginx Reverse Proxy

**Concept:** Reverse proxy, upstream routing, WebSocket proxying

**What to build today:**
- Write `nginx/nginx.conf` — route `/api/` to backend, `/ws/` for WebSocket
- Write `nginx/Dockerfile`
- Add Nginx service to docker-compose.yml
- Test: `curl http://localhost:80`

**Files to create:**
- `nginx/nginx.conf`
- `nginx/Dockerfile`

**Files to edit:**
- `docker-compose.yml` (add nginx service)

**Git commit:**
```bash
git commit -m "feat: nginx reverse proxy with api and websocket routing"
```

---

#### 🔲 Day 6 — Aug 9, 2026 — Environment Variables & Secrets

**Concept:** 12-factor app, .env pattern, never commit secrets

**What to build today:**
- Write `.env.example` with every variable name documented (no real values)
- Write `.env` locally (never committed) with dev values
- Verify `.env` is in `.gitignore`
- Understand: what happens if you commit a secret key

**Files to create:**
- `.env.example`

**Git commit:**
```bash
git commit -m "docs: env example with all variable names documented"
```

---

#### 🔲 Day 7 — Aug 10, 2026 — Full Stack: All 7 Services Running

**Concept:** Docker networking, service discovery by name, Celery + Flower

**What to build today:**
- Add to docker-compose.yml: FastAPI backend, Celery worker, Celery Beat, Flower
- Run `docker compose up --build` — all 7 services must start
- Verify: `curl http://localhost:8000/health` returns a response
- Open Flower at `http://localhost:5555`

**Files to edit:**
- `docker-compose.yml` (add backend, celery_worker, celery_beat, flower)

**Git commit:**
```bash
git commit -m "feat: full local stack all 7 services docker-compose verified"
```

---

### WEEK 2 — PostgreSQL & SQLAlchemy (Aug 11–17)

---

#### 🔲 Day 8 — Aug 11, 2026 — SQL Fundamentals

**Concept:** Relational databases, SQL basics, primary keys, indexes

**What to build today:**
- Connect to PostgreSQL: `docker compose exec postgres psql -U tradeflow`
- Practice 10 SQL queries: CREATE TABLE, INSERT, SELECT, WHERE, JOIN
- Understand: PRIMARY KEY, UNIQUE, INDEX, FOREIGN KEY
- Write your practice queries to a file

**Files to create:**
- `docs/sql-practice.sql` — your 10 practice queries with comments

**Git commit:**
```bash
git commit -m "docs: sql fundamentals practice queries with comments"
```

---

#### 🔲 Day 9 — Aug 12, 2026 — SQLAlchemy ORM Setup

**Concept:** ORM pattern, async SQLAlchemy, asyncpg driver, connection pooling

**What to build today:**
- Install: `sqlalchemy`, `asyncpg`, `psycopg2-binary`
- Write `backend/app/core/database.py`:
  - Async engine with `create_async_engine`
  - Session factory with `async_sessionmaker`
  - `Base` class for all models
  - `get_db()` FastAPI dependency

**Files to create:**
- `backend/app/core/__init__.py`
- `backend/app/core/database.py`

**Git commit:**
```bash
git commit -m "feat: sqlalchemy async engine session factory and base model"
```

---

#### 🔲 Day 10 — Aug 13, 2026 — price_bars & fetch_logs Models

**Concept:** Table design, composite unique constraints, UUID primary keys, indexes

**What to build today:**
- Write `backend/app/models/price.py`:
  - `PriceBar` model — symbol, timeframe, timestamp, OHLCV, asset_type
  - Unique constraint on (symbol, timeframe, timestamp)
  - Indexes on symbol+timeframe, timestamp, asset_type
  - `FetchLog` model — tracks every fetch attempt

**Files to create:**
- `backend/app/models/__init__.py`
- `backend/app/models/price.py`

**Git commit:**
```bash
git commit -m "feat: price_bars and fetch_logs sqlalchemy models with constraints"
```

---

#### 🔲 Day 11 — Aug 14, 2026 — User & Auth Models

**Concept:** Foreign keys, CASCADE delete, relationships, why we never store plaintext passwords

**What to build today:**
- Write `backend/app/models/user.py`:
  - `User` model — email, hashed_password, plan, notification settings
  - `AuthToken` model — refresh token storage with revocation
  - `ApiKey` model — bcrypt-hashed API keys
  - `BrokerCredential` model — encrypted broker API keys

**Files to create:**
- `backend/app/models/user.py`

**Git commit:**
```bash
git commit -m "feat: user auth_tokens api_keys broker_credentials models"
```

---

#### 🔲 Day 12 — Aug 15, 2026 — Business Logic Models

**Concept:** JSON columns, composite indexes, one-to-many relationships

**What to build today:**
- Write `backend/app/models/signal.py` — signals table
- Write `backend/app/models/backtest.py` — backtest_results + user_strategy_configs
- Write `backend/app/models/watchlist.py` — user_watchlist
- Write `backend/app/models/billing.py` — subscriptions
- Write `backend/app/models/paper_trading.py` — paper_portfolios, paper_positions, paper_trades
- Update `backend/app/models/__init__.py` to import all models

**Files to create:**
- `backend/app/models/signal.py`
- `backend/app/models/backtest.py`
- `backend/app/models/watchlist.py`
- `backend/app/models/billing.py`
- `backend/app/models/paper_trading.py`

**Git commit:**
```bash
git commit -m "feat: signals backtest watchlist billing paper_trading models"
```

---

#### 🔲 Day 13 — Aug 16, 2026 — Alembic Migrations Setup

**Concept:** Database migrations, version control for schema, upgrade/downgrade

**What to build today:**
- Install `alembic`
- Run `alembic init alembic` inside `/backend`
- Configure `alembic/env.py` to use our models and settings
- Write initial migration `001_initial_schema.py` — all tables

**Files to create:**
- `backend/alembic.ini`
- `backend/alembic/env.py`
- `backend/alembic/script.py.mako`
- `backend/alembic/versions/001_initial_schema.py`

**Git commit:**
```bash
git commit -m "feat: alembic setup with initial migration all tables"
```

---

#### 🔲 Day 14 — Aug 17, 2026 — Run Migrations & Verify Schema

**Concept:** Running migrations, verifying tables, testing constraints, rollback

**What to build today:**
- Run: `docker compose exec backend alembic upgrade head`
- Verify all tables exist: connect to psql and run `\dt`
- Test unique constraint: try inserting a duplicate row → should fail
- Test rollback: `alembic downgrade -1` then re-apply

**Files to create:**
- `docs/day-14-db-verification.md` — screenshot or output of `\dt` and constraint test

**Git commit:**
```bash
git commit -m "feat: all migrations run verified constraints and indexes working"
```

---

### WEEK 3 — FastAPI Backend Foundation (Aug 18–24)

---

#### 🔲 Day 15 — Aug 18, 2026 — FastAPI App Setup

**Concept:** FastAPI basics, routes, Pydantic, automatic OpenAPI docs

**What to build today:**
- Write `backend/app/main.py` — FastAPI app factory
- Write `GET /health` endpoint returning `{"status": "ok"}`
- Write `backend/app/__init__.py`
- Install: `fastapi`, `uvicorn[standard]`
- Test: `http://localhost:8000/docs` shows Swagger UI

**Files to create:**
- `backend/app/__init__.py`
- `backend/app/main.py`
- `backend/requirements.txt` (add fastapi, uvicorn)

**Git commit:**
```bash
git commit -m "feat: fastapi app factory health endpoint and openapi docs"
```

---

#### 🔲 Day 16 — Aug 19, 2026 — Middleware: CORS, Logging, Correlation IDs

**Concept:** Middleware pattern, CORS, correlation IDs, request/response logging

**What to build today:**
- Add `CORSMiddleware` — restrict to `http://localhost:3000` in dev
- Write custom middleware — generate UUID correlation ID per request
- Log every request: method, path, status code, latency ms
- Add `X-Correlation-ID` header to every response

**Files to edit:**
- `backend/app/main.py` (add middleware)

**Git commit:**
```bash
git commit -m "feat: cors logging and correlation id middleware"
```

---

#### 🔲 Day 17 — Aug 20, 2026 — Config with pydantic-settings

**Concept:** 12-factor config, pydantic-settings, lru_cache, type coercion from env

**What to build today:**
- Install `pydantic-settings`
- Write `backend/app/core/config.py` — `Settings` class with every env var typed
- Use `@lru_cache` on `get_settings()` so it's only loaded once
- Add computed property: `allowed_origins_list` splits comma-separated string

**Files to create:**
- `backend/app/core/config.py`

**Git commit:**
```bash
git commit -m "feat: pydantic-settings config all env vars typed with lru_cache"
```

---

#### 🔲 Day 18 — Aug 21, 2026 — Structured Logging with structlog

**Concept:** Structured JSON logs, log levels, never log secrets

**What to build today:**
- Install `structlog`
- Write `backend/app/core/logging.py` — JSON logs in prod, pretty in dev
- Configure log level from env var
- Suppress noisy third-party loggers (uvicorn, sqlalchemy)
- Rule: NEVER log passwords, tokens, or API keys

**Files to create:**
- `backend/app/core/logging.py`

**Git commit:**
```bash
git commit -m "feat: structlog structured json logging configured"
```

---

#### 🔲 Day 19 — Aug 22, 2026 — Pydantic v2 Schemas

**Concept:** Request/response validation, field validators, generic types

**What to build today:**
- Write schemas for price data responses
- Write `PaginatedResponse[T]` generic schema
- Add field validators: price > 0, confidence in [0.0, 1.0]
- Understand: `model_validator` vs `field_validator`

**Files to create:**
- `backend/app/schemas/__init__.py`
- `backend/app/schemas/price.py`
- `backend/app/schemas/common.py` (PaginatedResponse)

**Git commit:**
```bash
git commit -m "feat: pydantic v2 schemas price and paginated response"
```

---

#### 🔲 Day 20 — Aug 23, 2026 — Async MongoDB Connection

**Concept:** Motor async driver, MongoDB collections, async I/O

**What to build today:**
- Install `motor`
- Extend `backend/app/core/database.py` — add Motor client
- Write helper functions for each collection: `get_indicators_collection()`, `get_chart_patterns_collection()` etc.
- Write `GET /health/db` that pings both PostgreSQL and MongoDB

**Files to edit:**
- `backend/app/core/database.py` (add MongoDB)
- `backend/app/main.py` (add /health/db route)

**Git commit:**
```bash
git commit -m "feat: motor async mongodb client and db health check endpoint"
```

---

#### 🔲 Day 21 — Aug 24, 2026 — Global Exception Handler & Error Responses

**Concept:** HTTP status codes, never expose stack traces, consistent error format

**What to build today:**
- Write global `@app.exception_handler(Exception)` — clean JSON, no stack trace
- Write 404 handler for unknown routes
- All errors return: `{"error": "...", "correlation_id": "..."}`
- Test: trigger a 500 intentionally — verify clean response

**Files to edit:**
- `backend/app/main.py` (add exception handlers)

**Files to create:**
- `backend/app/core/exceptions.py` — custom exception classes

**Git commit:**
```bash
git commit -m "feat: global exception handlers consistent json error format"
```

---

### WEEK 4 — Data Pipeline Core (Aug 25 – Sep 2)

---

#### 🔲 Day 22 — Aug 25, 2026 — yfinance Fetcher: Base & Normalisation

**Concept:** yfinance library, ticker formats, data normalisation, UTC timestamps

**What to build today:**
- Install `yfinance`, `pandas`, `numpy`
- Write `backend/app/services/__init__.py`
- Write `backend/app/services/data/__init__.py`
- Write `backend/app/services/data/base.py` — `BaseDataFetcher` abstract class
- Start `backend/app/services/data/yfinance_fetcher.py`:
  - `fetch()` method — returns standardised DataFrame
  - `_normalise()` — lowercase columns, float64, UTC timestamps
  - `validate_symbol()` — check if symbol exists

**Files to create:**
- `backend/app/services/__init__.py`
- `backend/app/services/data/__init__.py`
- `backend/app/services/data/base.py`
- `backend/app/services/data/yfinance_fetcher.py`

**Git commit:**
```bash
git commit -m "feat: yfinance fetcher base class and normalisation"
```

---

#### 🔲 Day 23 — Aug 26, 2026 — yfinance Fetcher: Symbol Lists & Timeframes

**Concept:** Asset types, intraday limits, idempotency

**What to build today:**
- Complete `yfinance_fetcher.py`:
  - Add interval mapping: `{"1d": "1d", "1h": "1h", "15m": "15m"}`
  - Add period limits for intraday (15m = 60 days max)
  - Define symbol lists: Indian equities, US equities, Forex, Commodities
- Test manually: fetch `RELIANCE.NS`, `AAPL`, `EURUSD=X`, `GC=F`

**Files to edit:**
- `backend/app/services/data/yfinance_fetcher.py`

**Git commit:**
```bash
git commit -m "feat: yfinance symbol lists all asset types and timeframe limits"
```

---

#### 🔲 Day 24 — Aug 27, 2026 — Binance REST API Fetcher

**Concept:** REST API pagination, rate limiting, Binance kline format

**What to build today:**
- Write `backend/app/services/data/binance_fetcher.py`:
  - `_fetch_all_klines()` — paginate until all candles fetched
  - `_to_dataframe()` — convert 12-element kline list to standard schema
  - `validate_symbol()` — check if Binance symbol exists
  - Default crypto symbols: BTCUSDT, ETHUSDT, BNBUSDT etc.
- Test: fetch BTCUSDT daily — verify 1000+ rows

**Files to create:**
- `backend/app/services/data/binance_fetcher.py`

**Git commit:**
```bash
git commit -m "feat: binance rest fetcher with pagination crypto ohlcv"
```

---

#### 🔲 Day 25 — Aug 28, 2026 — Data Cleaning Module

**Concept:** pandas time series, gap detection, forward-fill, deduplication

**What to build today:**
- Write `backend/app/services/data/cleaner.py`:
  - `_normalise_timestamps()` — ensure UTC
  - `_normalise_dtypes()` — enforce float64
  - `_remove_duplicates()` — on symbol+timeframe+timestamp
  - `_fill_gaps()` — forward-fill missing daily bars
  - `_drop_invalid()` — remove NaN or zero price rows

**Files to create:**
- `backend/app/services/data/cleaner.py`

**Git commit:**
```bash
git commit -m "feat: data cleaner gap fill dedup normalisation"
```

---

#### 🔲 Day 26 — Aug 29, 2026 — DB Writer: Upsert to PostgreSQL

**Concept:** SQL upsert, ON CONFLICT DO NOTHING, idempotency, sync SQLAlchemy for Celery

**What to build today:**
- Write `backend/app/services/data/db_writer.py`:
  - `get_sync_session()` — synchronous session for Celery tasks
  - `upsert_price_bars(df)` — bulk insert, skip duplicates
  - `log_fetch(symbol, timeframe, status, rows, error, source)` — always log

**Files to create:**
- `backend/app/services/data/db_writer.py`

**Git commit:**
```bash
git commit -m "feat: db writer idempotent upsert and fetch logging"
```

---

#### 🔲 Day 27 — Aug 30, 2026 — Fetch Tests: Live Data Verification

**Concept:** Manual integration testing, psql queries, data inspection

**What to build today:**
- Write `tests/unit/test_fetchers.py` — mock-based unit tests for both fetchers
- Write `tests/unit/test_cleaner.py` — unit tests for all cleaning steps
- Run tests locally: `pytest tests/unit/ -v`
- Manually fetch 5 real symbols and inspect in psql

**Files to create:**
- `tests/__init__.py`
- `tests/unit/__init__.py`
- `tests/unit/test_fetchers.py`
- `tests/unit/test_cleaner.py`

**Git commit:**
```bash
git commit -m "test: fetcher and cleaner unit tests all passing"
```

---

#### 🔲 Day 28 — Aug 31, 2026 — CSV Upload Endpoint

**Concept:** FastAPI file uploads, UploadFile, CSV validation, 10MB limit

**What to build today:**
- Write `backend/app/api/__init__.py`
- Write `backend/app/api/v1/__init__.py`
- Write `backend/app/api/v1/routes/__init__.py`
- Write `backend/app/api/v1/routes/data.py`:
  - `POST /api/v1/data/upload-csv` — validate columns, clean, insert
  - `GET /api/v1/data/bars/{symbol}` — return OHLCV for charts
  - `GET /api/v1/instruments/search` — autocomplete search
- Register router in `main.py`

**Files to create:**
- `backend/app/api/__init__.py`
- `backend/app/api/v1/__init__.py`
- `backend/app/api/v1/routes/__init__.py`
- `backend/app/api/v1/routes/data.py`

**Git commit:**
```bash
git commit -m "feat: csv upload endpoint with validation and price bars api"
```

---

#### 🔲 Day 29 — Sep 1, 2026 — Indicator Tests & Docs

**Concept:** Test-driven thinking, writing tests before moving forward

**What to build today:**
- Write `tests/unit/test_indicators.py` (will use when we build indicators on Day 40)
- Write `docs/architecture.md` — draw the data pipeline flow in text/ASCII
- Write `docs/data-pipeline.md` — explain each stage with examples
- Review all code written so far — fix any bugs or TODOs

**Files to create:**
- `tests/unit/test_indicators.py`
- `docs/architecture.md`
- `docs/data-pipeline.md`

**Git commit:**
```bash
git commit -m "docs: architecture diagram and data pipeline documentation"
```

---

#### 🔲 Day 30 — Sep 2, 2026 — Month 1 Review & Cleanup

**Concept:** Code review, refactoring, documentation

**What to build today:**
- Run `git log --oneline` — verify 30 commits
- Review every file written this month — add missing docstrings
- Fix any import errors: `python -c "from app.main import app"`
- Update `README.md` with current status
- Write `docs/month-1-review.md` — what you learned this month

**Files to create/edit:**
- `docs/month-1-review.md`
- `README.md` (update status)

**Git commit:**
```bash
git commit -m "docs: month 1 review cleanup docstrings and readme update"
```

---

---

## 🗓️ MONTH 2 — Celery, Indicators & Backtest Engine
### Sep 3 – Oct 2, 2026

---

### WEEK 5 — Celery Task Queue (Sep 3–10)

---

#### 🔲 Day 31 — Sep 3, 2026 — Celery App Factory

**Concept:** Task queues, Celery architecture, Redis as broker

**What to build today:**
- Install: `celery`, `redis`, `flower`
- Write `backend/app/celery_app.py`:
  - Celery factory with Redis broker + result backend
  - Named queues: `default`, `pipeline`, `alerts`, `signals`
  - Task routes, serialisation config, timezone = Asia/Kolkata
  - `task_acks_late=True`, `worker_prefetch_multiplier=1`

**Files to create:**
- `backend/app/celery_app.py`

**Git commit:**
```bash
git commit -m "feat: celery app factory named queues redis broker"
```

---

#### 🔲 Day 32 — Sep 4, 2026 — yfinance Fetch Celery Task

**Concept:** `@celery_app.task(bind=True)`, retry, exponential backoff

**What to build today:**
- Write `backend/app/tasks/__init__.py`
- Write `backend/app/tasks/pipeline.py`:
  - `fetch_yfinance_symbol` task — fetch, clean, store one symbol+timeframe
  - Retry on failure: max 3, exponential backoff `2 ** retries * 30`
  - Log start, success, failure with structlog

**Files to create:**
- `backend/app/tasks/__init__.py`
- `backend/app/tasks/pipeline.py`

**Git commit:**
```bash
git commit -m "feat: yfinance fetch celery task with retry and backoff"
```

---

#### 🔲 Day 33 — Sep 5, 2026 — Binance Fetch Celery Task

**Concept:** Task isolation — one symbol failing must not stop others

**What to build today:**
- Add `fetch_binance_symbol` task to `pipeline.py`
- Same retry pattern as yfinance task
- Test manually via celery CLI: trigger task, see result in Flower
- Test failure: trigger with invalid symbol → verify FAILED in Flower

**Files to edit:**
- `backend/app/tasks/pipeline.py`

**Git commit:**
```bash
git commit -m "feat: binance fetch celery task with error isolation"
```

---

#### 🔲 Day 34 — Sep 6, 2026 — Celery Beat Schedule

**Concept:** Celery Beat daemon, crontab scheduling, UTC vs IST

**What to build today:**
- Add `beat_schedule` to `celery_app.py`:
  - `run_full_pipeline` at 00:30 UTC (= 06:00 IST) every day
  - `check_signal_outcomes` at 01:00 UTC
  - `check_fetch_failures` at 01:30 UTC
- Start Beat: `celery -A app.celery_app beat`
- Test: temporarily change schedule to every 1 minute — verify it fires

**Files to edit:**
- `backend/app/celery_app.py` (add beat_schedule)

**Git commit:**
```bash
git commit -m "feat: celery beat 0630 IST daily pipeline schedule"
```

---

#### 🔲 Day 35 — Sep 7, 2026 — Pipeline Orchestrator: Parallel Fan-Out

**Concept:** `group()` for parallelism, `chord()` for completion callback

**What to build today:**
- Add `run_full_pipeline` task to `pipeline.py`:
  - Build a `group()` of all symbols × all timeframes
  - Fan out in parallel — multiple workers process simultaneously
  - Use `chord()` — trigger indicator compute after all fetches done
- Verify in Flower: multiple tasks running simultaneously

**Files to edit:**
- `backend/app/tasks/pipeline.py`

**Git commit:**
```bash
git commit -m "feat: pipeline orchestrator celery group parallel fan-out"
```

---

#### 🔲 Day 36 — Sep 8, 2026 — Ops Alert Task

**Concept:** SQL window functions, consecutive failure detection, Slack webhook

**What to build today:**
- Write `backend/app/tasks/alerts.py`:
  - `check_fetch_failures` — SQL query to find 2+ consecutive failure days
  - `send_ops_alert` — POST to Slack webhook, fallback to SendGrid email
- Test: manually insert 2 FAILED rows for a symbol → alert fires

**Files to create:**
- `backend/app/tasks/alerts.py`

**Git commit:**
```bash
git commit -m "feat: ops alert consecutive failure detection slack email"
```

---

#### 🔲 Day 37 — Sep 9, 2026 — Celery Flower Deep Dive

**Concept:** Queue monitoring, task inspection, worker health

**What to build today:**
- Set up Flower basic auth (username + password via env var)
- Run the full pipeline and watch all tasks in Flower in real time
- Use `celery inspect active` and `celery inspect scheduled` from CLI
- Write `docs/celery-monitoring.md` — explain each Flower dashboard panel

**Files to create:**
- `docs/celery-monitoring.md`

**Files to edit:**
- `docker-compose.yml` (add Flower auth env vars)

**Git commit:**
```bash
git commit -m "docs: celery flower monitoring guide and auth setup"
```

---

#### 🔲 Day 38 — Sep 10, 2026 — Celery Week Review + Signal Outcome Task Stub

**Concept:** Code review, stubs for future tasks

**What to build today:**
- Write `check_signal_outcomes` stub task in `pipeline.py` (full logic in Phase 10)
- Write `tests/unit/test_pipeline_tasks.py` — mock-based tests for pipeline tasks
- Verify full pipeline runs end-to-end: `run_full_pipeline → fetch → store → log`
- Fix any issues found during testing

**Files to create:**
- `tests/unit/test_pipeline_tasks.py`

**Files to edit:**
- `backend/app/tasks/pipeline.py` (add stub)

**Git commit:**
```bash
git commit -m "test: pipeline task unit tests and signal outcome stub"
```

---

### WEEK 6 — Technical Indicators (Sep 11–18)

---

#### 🔲 Day 39 — Sep 11, 2026 — EMA Indicators

**Concept:** Exponential Moving Average, trend following, EMA-200 requires 200 bars

**What to build today:**
- Install `ta` library: `pip install ta`
- Write `backend/app/services/data/indicators.py`:
  - `IndicatorEngine` class
  - `_safe_ema()` — returns NaN if insufficient bars
  - Compute: EMA-9, EMA-21, EMA-50, EMA-200

**Files to create:**
- `backend/app/services/data/indicators.py`

**Git commit:**
```bash
git commit -m "feat: ema 9 21 50 200 indicator engine"
```

---

#### 🔲 Day 40 — Sep 12, 2026 — RSI, MACD, Bollinger, ATR, OBV

**Concept:** Momentum oscillators, volatility bands, volume indicators

**What to build today:**
- Complete `indicators.py`:
  - RSI-14 (range 0–100)
  - MACD: line, signal, histogram
  - Bollinger Bands: upper, middle, lower, bandwidth, %B
  - ATR-14
  - OBV
- Write `to_mongo_documents()` — convert NaN to None for clean MongoDB storage

**Files to edit:**
- `backend/app/services/data/indicators.py`

**Git commit:**
```bash
git commit -m "feat: rsi macd bollinger atr obv indicators with mongo serialiser"
```

---

#### 🔲 Day 41 — Sep 13, 2026 — Indicator Celery Task + MongoDB Storage

**Concept:** MongoDB upsert, compound document key, Celery task chaining

**What to build today:**
- Add `compute_indicators_for_symbol` task to `pipeline.py`:
  - Load price bars from PostgreSQL
  - Compute all indicators
  - Upsert into MongoDB `indicators` collection keyed by symbol+timeframe+timestamp

**Files to edit:**
- `backend/app/tasks/pipeline.py`

**Git commit:**
```bash
git commit -m "feat: indicator computation celery task with mongodb storage"
```

---

#### 🔲 Day 42 — Sep 14, 2026 — Indicator Unit Tests

**Concept:** pytest, known-input known-output, edge cases

**What to build today:**
- Complete `tests/unit/test_indicators.py` — at minimum 10 tests:
  - EMA-200 is all NaN with < 200 bars
  - RSI stays in 0–100 range
  - Empty DataFrame returns empty
  - All indicator columns present in output
  - MongoDB documents have correct structure
- Run: `pytest tests/unit/test_indicators.py -v` — all pass

**Files to edit:**
- `tests/unit/test_indicators.py`

**Git commit:**
```bash
git commit -m "test: indicator engine 10 unit tests all passing"
```

---

#### 🔲 Day 43 — Sep 15, 2026 — End-to-End Pipeline Integration Test

**Concept:** Integration testing, tracing data through all stages

**What to build today:**
- Write `tests/integration/test_pipeline.py`:
  - Run fetch → clean → store → compute indicators for BTCUSDT
  - Verify row count in `price_bars`
  - Verify documents in MongoDB `indicators`
  - Verify SUCCESS in `fetch_logs`
- Run the full pipeline for 5 symbols: RELIANCE.NS, TCS.NS, BTCUSDT, ETHUSDT, EURUSD=X

**Files to create:**
- `tests/integration/__init__.py`
- `tests/integration/test_pipeline.py`

**Git commit:**
```bash
git commit -m "test: end-to-end pipeline integration test 5 symbols"
```

---

#### 🔲 Day 44 — Sep 16, 2026 — TA-Lib Install + Pattern Scanner

**Concept:** TA-Lib C library, Python bindings, candlestick pattern values (100/-100/0)

**What to build today:**
- Install TA-Lib C library in Docker container (add to Dockerfile)
- Install Python bindings: `pip install TA-Lib`
- Write `backend/app/services/patterns/__init__.py`
- Write `backend/app/services/patterns/talib_scanner.py`:
  - Scan 7 patterns: CDLDOJI, CDLHAMMER, CDLENGULFING, CDLMORNINGSTAR, CDLEVENINGSTAR, CDLSHOOTINGSTAR, CDLHANGINGMAN
  - Store in MongoDB `chart_patterns` collection

**Files to create:**
- `backend/app/services/patterns/__init__.py`
- `backend/app/services/patterns/talib_scanner.py`

**Files to edit:**
- `backend/Dockerfile` (add TA-Lib C library compile step)
- `backend/requirements.txt` (add TA-Lib)

**Git commit:**
```bash
git commit -m "feat: talib pattern scanner 7 candlestick patterns mongodb"
```

---

#### 🔲 Day 45 — Sep 17, 2026 — Structural Patterns: Head & Shoulders

**Concept:** Pivot point detection, multi-candle pattern recognition

**What to build today:**
- Write `backend/app/services/patterns/structural_scanner.py`:
  - `detect_pivot_points()` — local highs and lows with rolling window
  - `detect_head_and_shoulders()` — 3 peaks, middle is highest
  - `detect_inverse_head_and_shoulders()` — 3 troughs, middle is lowest
- Test on known historical data (e.g., NIFTY 2022 bear market)

**Files to create:**
- `backend/app/services/patterns/structural_scanner.py`

**Git commit:**
```bash
git commit -m "feat: head and shoulders structural pattern pivot detection"
```

---

#### 🔲 Day 46 — Sep 18, 2026 — Double Top & Double Bottom

**Concept:** Support/resistance levels, price tolerance matching

**What to build today:**
- Add to `structural_scanner.py`:
  - `detect_double_top()` — two pivot highs within ±2% of each other
  - `detect_double_bottom()` — two pivot lows within ±2% of each other
- Add pattern scan as a Celery task stage after indicator computation
- Update `pipeline.py` to include pattern scan in the chain

**Files to edit:**
- `backend/app/services/patterns/structural_scanner.py`
- `backend/app/tasks/pipeline.py`

**Git commit:**
```bash
git commit -m "feat: double top double bottom patterns and pipeline integration"
```

---

### WEEK 7 — Backtest Engine (Sep 19–25)

---

#### 🔲 Day 47 — Sep 19, 2026 — Backtest Theory + vectorbt Setup

**Concept:** Backtesting, look-ahead bias, vectorbt, 6 metrics

**What to build today:**
- Install `vectorbt`
- Write `docs/backtesting-theory.md` — explain all 6 metrics with formulas
- Write `backend/app/services/backtest/__init__.py`
- Write `backend/app/services/backtest/base.py`:
  - `Strategy` abstract base class
  - `generate_signals(df) -> pd.Series` interface
  - `run_backtest()` — runs vectorbt, computes all 6 metrics
  - Capital: INR 1,00,000, position size: 1%

**Files to create:**
- `backend/app/services/backtest/__init__.py`
- `backend/app/services/backtest/base.py`
- `docs/backtesting-theory.md`

**Git commit:**
```bash
git commit -m "feat: vectorbt setup base strategy class 6 metrics"
```

---

#### 🔲 Day 48 — Sep 20, 2026 — EMA Crossover Strategy

**Concept:** Crossover detection with shift(1) to prevent look-ahead bias

**What to build today:**
- Write `backend/app/services/backtest/strategies/ema_crossover.py`:
  - `EMACrossoverStrategy` class
  - `generate_signals()` — BUY when fast EMA crosses above slow EMA
  - Configurable fast_period, slow_period (default 9/21)
  - No future data leakage — verified with shift(1)

**Files to create:**
- `backend/app/services/backtest/strategies/__init__.py`
- `backend/app/services/backtest/strategies/ema_crossover.py`

**Git commit:**
```bash
git commit -m "feat: ema crossover strategy no look-ahead bias verified"
```

---

#### 🔲 Day 49 — Sep 21, 2026 — RSI Reversal Strategy

**Concept:** Threshold confirmation — entry on close BACK through level

**What to build today:**
- Write `backend/app/services/backtest/strategies/rsi_reversal.py`:
  - BUY: RSI drops below 30 AND closes back above 30 on same bar
  - SELL: RSI rises above 70 AND closes back below 70
  - Configurable oversold (default 30) and overbought (default 70) thresholds

**Files to create:**
- `backend/app/services/backtest/strategies/rsi_reversal.py`

**Git commit:**
```bash
git commit -m "feat: rsi reversal strategy threshold confirmation logic"
```

---

#### 🔲 Day 50 — Sep 22, 2026 — MACD & Bollinger Strategies

**Concept:** Histogram sign change, bandwidth percentile squeeze

**What to build today:**
- Write `backend/app/services/backtest/strategies/macd_crossover.py`:
  - BUY: histogram crosses zero (negative → positive)
  - SELL: histogram crosses zero (positive → negative)
- Write `backend/app/services/backtest/strategies/bollinger_squeeze.py`:
  - Squeeze: bandwidth < 20th percentile of last 126 bars
  - BUY: close above upper band after squeeze
  - SELL: close below lower band after squeeze

**Files to create:**
- `backend/app/services/backtest/strategies/macd_crossover.py`
- `backend/app/services/backtest/strategies/bollinger_squeeze.py`

**Git commit:**
```bash
git commit -m "feat: macd crossover and bollinger squeeze strategies"
```

---

#### 🔲 Day 51 — Sep 23, 2026 — Statistical Filter

**Concept:** Quality gate, win_rate ≥ 50% AND avg_rr ≥ 1.5

**What to build today:**
- Write `backend/app/services/backtest/filter.py`:
  - `apply_statistical_filter(result) -> bool`
  - Returns True only if BOTH conditions met simultaneously
- Add `passed` flag storage to backtest results in `backtest_results` table
- Only `passed=True` results feed into AI signal generation

**Files to create:**
- `backend/app/services/backtest/filter.py`

**Git commit:**
```bash
git commit -m "feat: statistical filter win_rate and rr gate passed flag"
```

---

#### 🔲 Day 52 — Sep 24, 2026 — Candlestick Pattern Backtest

**Concept:** Treating patterns as strategy signals, same backtest framework

**What to build today:**
- Write `backend/app/services/backtest/strategies/pattern_strategy.py`:
  - `CandlestickPatternStrategy` — takes pattern_name as constructor arg
  - BUY on bullish pattern (signal=100), SELL on bearish (signal=-100)
  - Run for all 7 TA-Lib patterns + Head&Shoulders + Double Top/Bottom
- Apply statistical filter to all pattern backtests

**Files to create:**
- `backend/app/services/backtest/strategies/pattern_strategy.py`

**Git commit:**
```bash
git commit -m "feat: candlestick pattern strategy backtest with filter"
```

---

#### 🔲 Day 53 — Sep 25, 2026 — Backtest Celery Task + Storage

**Concept:** Parallel backtesting with Celery group, upsert on re-run

**What to build today:**
- Write `backend/app/tasks/backtest.py`:
  - `run_backtest_for_symbol` Celery task — all strategies for one symbol
  - `run_all_backtests` — `group()` fan-out across all symbols
  - Store results in `backtest_results` table
- Add to pipeline chain: after pattern scan → backtests → signal gen

**Files to create:**
- `backend/app/tasks/backtest.py`

**Files to edit:**
- `backend/app/tasks/pipeline.py` (add backtest to chain)

**Git commit:**
```bash
git commit -m "feat: backtest celery task parallel execution and storage"
```

---

### WEEK 8 — Patterns, Tests & Month 2 Review (Sep 26 – Oct 2)

---

#### 🔲 Day 54 — Sep 26, 2026 — Backtest Strategy Tests

**Concept:** Unit testing financial strategies, known-input known-output

**What to build today:**
- Write `tests/unit/test_strategies.py`:
  - Test EMA crossover signals on synthetic data
  - Test RSI reversal only fires on confirmation candle (not first touch)
  - Test MACD histogram sign change detection
  - Test statistical filter: True/False for boundary cases
- Run: `pytest tests/unit/test_strategies.py -v` — all pass

**Files to create:**
- `tests/unit/test_strategies.py`

**Git commit:**
```bash
git commit -m "test: backtest strategy unit tests all passing"
```

---

#### 🔲 Day 55 — Sep 27, 2026 — CLI Backtest Tool

**Concept:** argparse, terminal output formatting

**What to build today:**
- Write `backend/backtest_cli.py`:
  - `--symbol RELIANCE.NS`
  - `--strategy ema|rsi|macd|bollinger|all`
  - `--date-range 2023-01-01 2024-01-01`
  - Prints formatted metrics table to terminal
- Test: `python backtest_cli.py --symbol BTCUSDT --strategy all`

**Files to create:**
- `backend/backtest_cli.py`

**Git commit:**
```bash
git commit -m "feat: cli backtest tool symbol strategy date-range args"
```

---

#### 🔲 Day 56 — Sep 28, 2026 — User Strategy Config

**Concept:** Per-user parameter overrides, fallback to defaults

**What to build today:**
- Write `backend/app/services/backtest/user_config.py`:
  - `get_user_strategy_params(user_id, strategy_name) -> dict`
  - Returns user's custom params from `user_strategy_configs` table
  - Falls back to defaults if not found
- Parameter validation: EMA period ≥ 1, RSI thresholds 1–99

**Files to create:**
- `backend/app/services/backtest/user_config.py`

**Git commit:**
```bash
git commit -m "feat: user strategy config overrides with default fallback"
```

---

#### 🔲 Day 57 — Sep 29, 2026 — Integration Test: Full Month 2 Pipeline

**Concept:** End-to-end: fetch → clean → indicators → patterns → backtest → filter

**What to build today:**
- Write `tests/integration/test_backtest_pipeline.py`
- Run full pipeline for BTCUSDT and RELIANCE.NS
- Verify: `backtest_results` has rows for all 4+ strategies
- Verify: statistical filter correctly tags passed=True/False
- Verify: MongoDB `chart_patterns` has pattern scan results

**Files to create:**
- `tests/integration/test_backtest_pipeline.py`

**Git commit:**
```bash
git commit -m "test: full month 2 backtest pipeline integration test"
```

---

#### 🔲 Day 58 — Sep 30, 2026 — Requirements & Docker Rebuild

**Concept:** Python dependency management, pinning versions

**What to build today:**
- Complete `backend/requirements.txt` with all packages used so far (pinned versions)
- Rebuild Docker image: `docker compose build --no-cache backend`
- Verify all imports work inside container
- Write `docs/month-2-review.md`

**Files to edit:**
- `backend/requirements.txt`

**Files to create:**
- `docs/month-2-review.md`

**Git commit:**
```bash
git commit -m "chore: pin all requirements month 2 docker rebuild verified"
```

---

#### 🔲 Day 59 — Oct 1, 2026 — Backtest Explorer API Stubs

**Concept:** API route stubs — placeholder routes before full implementation

**What to build today:**
- Write `backend/app/api/v1/routes/backtest.py`:
  - Stub: `GET /api/v1/backtest/results`
  - Stub: `GET /api/v1/backtest/trade-log/{backtest_id}`
  - Stub: `POST /api/v1/backtest/run`
  - Stub: `GET /api/v1/backtest/status/{task_id}`
- Register router in `main.py`

**Files to create:**
- `backend/app/api/v1/routes/backtest.py`

**Files to edit:**
- `backend/app/main.py` (register backtest router)

**Git commit:**
```bash
git commit -m "feat: backtest api route stubs registered in main"
```

---

#### 🔲 Day 60 — Oct 2, 2026 — Month 2 Final Review

**Concept:** Code quality, missing tests, documentation gaps

**What to build today:**
- Run `git log --oneline | wc -l` — verify 60 commits
- Run full test suite: `pytest tests/ -v` — all pass
- Fix any failing tests or import errors
- Update `README.md` with Month 2 progress
- Write `docs/what-i-learned-months-1-2.md`

**Files to create:**
- `docs/what-i-learned-months-1-2.md`

**Git commit:**
```bash
git commit -m "docs: month 2 final review tests passing readme updated"
```

---

---

## 🗓️ MONTH 3 — AI Signal Engine, Delivery & Auth
### Oct 3 – Nov 1, 2026

---

#### 🔲 Day 61 — Oct 3 — LLM Concepts + Anthropic SDK

**What to build:** `backend/app/services/ai/__init__.py`, `backend/app/services/ai/claude_client.py` — basic Claude API call
**Commit:** `feat: anthropic claude sdk client basic test call`

---

#### 🔲 Day 62 — Oct 4 — Signal Generation Prompt

**What to build:** `backend/app/services/ai/prompts.py` — full signal prompt template with indicator snapshot + last 20 bars + backtest summary
**Commit:** `feat: claude signal generation prompt template`

---

#### 🔲 Day 63 — Oct 5 — Claude Response Parser

**What to build:** `backend/app/services/ai/parser.py` — `ClaudeSignalResponse` Pydantic model, parse and validate JSON response from Claude
**Commit:** `feat: claude response parser with pydantic validation`

---

#### 🔲 Day 64 — Oct 6 — Retry Logic with Tenacity

**What to build:** Wrap Claude API call in `@retry(stop=stop_after_attempt(3), wait=wait_exponential())` in `claude_client.py`
**Commit:** `feat: tenacity retry on claude api 3 attempts exponential backoff`

---

#### 🔲 Day 65 — Oct 7 — Signal Generation Celery Task

**What to build:** `backend/app/tasks/signals.py` — `generate_signals_for_symbol` task, query passed=True results, call Claude, store signal
**Commit:** `feat: signal generation celery task passed strategies only`

---

#### 🔲 Day 66 — Oct 8 — Signal Storage + Outcome Stub

**What to build:** Complete signal storage in `signals` table; add `check_signal_outcomes` full implementation in `pipeline.py`
**Commit:** `feat: signal storage deduplication and outcome checker`

---

#### 🔲 Day 67 — Oct 9 — mplfinance Chart Setup

**What to build:** `backend/app/services/charts/__init__.py`, `backend/app/services/charts/generator.py` — basic candlestick chart for 60 bars
**Commit:** `feat: mplfinance candlestick chart basic 60 bar render`

---

#### 🔲 Day 68 — Oct 10 — Chart: EMA Overlays + Signal Levels

**What to build:** Complete `generator.py` — add EMA-21/50 overlays, horizontal dashed lines for entry/SL/TP1/TP2, direction label, stats
**Commit:** `feat: chart ema overlays signal levels direction label`

---

#### 🔲 Day 69 — Oct 11 — Chart Pipeline Integration

**What to build:** Hook chart generation into signal task; serve from `/charts/` via FastAPI StaticFiles; store URL in signals table
**Commit:** `feat: chart generation integrated in signal pipeline`

---

#### 🔲 Day 70 — Oct 12 — AWS S3 Setup + Chart Upload

**What to build:** `backend/app/utils/__init__.py`, `backend/app/utils/storage.py` — `upload_chart_to_s3()` with boto3; env toggle USE_S3
**Commit:** `feat: s3 chart upload with environment aware storage toggle`

---

#### 🔲 Day 71 — Oct 13 — Rolling Win Rate Task

**What to build:** `backend/app/tasks/analytics.py` — `compute_live_win_rates` task; 90-day window per strategy; store in `strategy_live_stats`
**Commit:** `feat: rolling 90 day live win rate computation per strategy`

---

#### 🔲 Day 72 — Oct 14 — SendGrid: Transactional Emails

**What to build:** `backend/app/services/notifications/__init__.py`, `backend/app/services/notifications/email.py` — welcome, password reset, subscription emails
**Commit:** `feat: sendgrid transactional emails welcome reset subscription`

---

#### 🔲 Day 73 — Oct 15 — Daily Signal Digest Email

**What to build:** `send_daily_digest` Celery task in `alerts.py` — HTML template, per-user filtering, scheduled 06:30 IST
**Commit:** `feat: daily signal digest email celery task 0630 IST`

---

#### 🔲 Day 74 — Oct 16 — Telegram Bot

**What to build:** `backend/app/services/notifications/telegram.py` — bot setup, `send_signal_via_telegram()`, MarkdownV2 formatting, chart photo
**Commit:** `feat: telegram bot signal delivery with chart photo`

---

#### 🔲 Day 75 — Oct 17 — Telegram Deep-Link Account Linking

**What to build:** One-time token generation; `/start TOKEN` handler links chat_id to user; `/stop` unlinks
**Commit:** `feat: telegram deep link account linking one-time token`

---

#### 🔲 Day 76 — Oct 18 — Slack Webhook Delivery

**What to build:** `backend/app/services/notifications/slack.py` — Block Kit message, failure tracking, disable after 3 failures
**Commit:** `feat: slack webhook block kit delivery with failure handling`

---

#### 🔲 Day 77 — Oct 19 — REST Webhook + HMAC Signature

**What to build:** `backend/app/services/notifications/webhook.py` — POST signal JSON to user endpoint, HMAC-SHA256 signature header, retry 3x
**Commit:** `feat: rest webhook hmac sha256 signature and retry`

---

#### 🔲 Day 78 — Oct 20 — JWT: Token Functions

**What to build:** `backend/app/core/security.py` — `create_access_token()`, `create_refresh_token()`, `verify_token()` using python-jose + bcrypt
**Commit:** `feat: jwt token creation verification access and refresh`

---

#### 🔲 Day 79 — Oct 21 — Auth: Register + Login Endpoints

**What to build:** `backend/app/api/v1/routes/auth.py` — `POST /auth/register`, `POST /auth/login`, email verification flow
**Commit:** `feat: register login and email verification endpoints`

---

#### 🔲 Day 80 — Oct 22 — Auth: Refresh + Logout + Password Reset

**What to build:** Complete `auth.py` — `POST /auth/refresh`, `POST /auth/logout`, `POST /auth/forgot-password`, `POST /auth/reset-password`
**Commit:** `feat: refresh token logout password reset endpoints`

---

#### 🔲 Day 81 — Oct 23 — Rate Limiting Middleware

**What to build:** `backend/app/core/rate_limiter.py` — Redis sliding window counter, per-plan limits (Free=100, Pro=500, Business=2000/min)
**Commit:** `feat: redis sliding window rate limiting per plan tier`

---

#### 🔲 Day 82 — Oct 24 — Stripe Checkout + Webhook

**What to build:** `backend/app/api/v1/routes/billing.py` — `POST /billing/checkout`, webhook handler for payment events, idempotency
**Commit:** `feat: stripe checkout and webhook plan upgrade handler`

---

#### 🔲 Day 83 — Oct 25 — Razorpay Integration

**What to build:** Add Razorpay to `billing.py` — order creation, `payment.captured` webhook, INR subscriptions
**Commit:** `feat: razorpay upi payment integration indian users`

---

#### 🔲 Day 84 — Oct 26 — Plan Tier Middleware

**What to build:** `backend/app/core/dependencies.py` — `get_current_user()`, `require_plan("pro")` FastAPI dependency; apply to protected routes
**Commit:** `feat: plan tier enforcement dependency injection`

---

#### 🔲 Day 85 — Oct 27 — API Key Auth

**What to build:** `backend/app/api/v1/routes/account.py` — generate/revoke API keys; update auth middleware to accept `X-API-Key` header
**Commit:** `feat: api key generation revocation and header auth`

---

#### 🔲 Day 86 — Oct 28 — Broker Credential Endpoints

**What to build:** Complete `account.py` — `POST /account/broker/link`, `DELETE /account/broker/unlink`, `GET /account/broker`; AES-256 encryption
**Commit:** `feat: broker credential encrypted storage endpoints`

---

#### 🔲 Day 87 — Oct 29 — Auth + Billing Tests

**What to build:** `tests/integration/test_auth_billing.py` — register, login, upgrade, rate limit, JWT expiry
**Commit:** `test: auth and billing integration tests`

---

#### 🔲 Day 88 — Oct 30 — Signals API: List + Detail

**What to build:** Complete `backend/app/api/v1/routes/signals.py` — `GET /signals` paginated with 5 filters, `GET /signals/:id` with Redis cache
**Commit:** `feat: signals list and detail api with redis cache`

---

#### 🔲 Day 89 — Oct 31 — Watchlist API

**What to build:** `backend/app/api/v1/routes/watchlist.py` — CRUD endpoints, ticker validation, Free tier limit (3 max), async backfill trigger
**Commit:** `feat: watchlist crud api tier limits ticker validation`

---

#### 🔲 Day 90 — Nov 1 — Month 3 Review + Full Backend Test

**What to build:** Run all tests; fix any failures; write `docs/month-3-review.md`; verify 90 total commits
**Commit:** `docs: month 3 review all tests passing backend complete`

---

## 🗓️ MONTH 4 — REST API Completion & React Frontend
### Nov 2 – Dec 1, 2026

---

#### 🔲 Day 91 — Nov 2 — Backtest Explorer API (Full)

**What to build:** Complete `backtest.py` routes — results with filters, trade log from MongoDB, on-demand run (Business tier), status polling
**Commit:** `feat: backtest explorer api results trade-log on-demand`

---

#### 🔲 Day 92 — Nov 3 — WebSocket: Signal Push

**What to build:** `backend/app/api/v1/routes/websocket.py` — `/ws/signals`, `ConnectionManager` class, Redis pub/sub → browser fan-out, JWT auth on handshake
**Commit:** `feat: websocket signal push redis pubsub fan-out`

---

#### 🔲 Day 93 — Nov 4 — WebSocket: Live Charts (Crypto)

**What to build:** `/ws/live-charts/{symbol}` — connect to Binance kline stream as background task, relay to browser clients
**Commit:** `feat: live chart websocket crypto binance kline stream`

---

#### 🔲 Day 94 — Nov 5 — Dhan Broker: Live Tick Streaming

**What to build:** `backend/app/services/broker/__init__.py`, `backend/app/services/broker/dhan.py` — `DhanLiveDataSource`, tick-to-bar aggregation, reconnect on disconnect
**Commit:** `feat: dhan broker tick streaming 1min bar aggregation`

---

#### 🔲 Day 95 — Nov 6 — Full API Integration Test

**What to build:** `tests/integration/test_full_api.py` — 20 tests covering all endpoints; all must pass
**Commit:** `test: full api integration suite 20 tests passing`

---

#### 🔲 Day 96 — Nov 7 — OpenAPI Docs Cleanup

**What to build:** Add docstrings to all routes, set `response_model` on every endpoint, add tags, review `/docs`
**Commit:** `docs: openapi spec all endpoints documented with response models`

---

#### 🔲 Day 97 — Nov 8 — Day 100 Prep: Backend Final Verification

**What to build:** Rebuild Docker, run all tests inside container, fix any environment issues
**Commit:** `chore: backend final docker rebuild all tests passing in container`

---

#### 🔲 Day 98 — Nov 9 — React + Vite + TypeScript Scaffold

**What to build:** `frontend/` — `npm create vite@latest . -- --template react-ts`; install Tailwind, React Router, Axios, Zustand
**Commit:** `feat: react 18 vite typescript frontend scaffold`

---

#### 🔲 Day 99 — Nov 10 — Tailwind Design System

**What to build:** `frontend/tailwind.config.js` — TradeFlow color tokens (`#0F1117`, `#1A1D27`, `#E8EAED`); `<Card />`, `<Badge />` components
**Commit:** `feat: tailwind design tokens and base components`

---

#### 🔲 Day 100 — Nov 11 — 🎉 Day 100 Milestone: React Router + Auth Store

**What to build:** All routes in React Router v6; `src/store/authStore.ts` with Zustand; `<ProtectedRoute />`
**Commit:** `feat: day 100 react router all routes auth store protected routes`

---

#### 🔲 Day 101 — Nov 12 — Axios Interceptor + Login/Register Pages

**What to build:** `src/utils/api.ts` — Axios instance, JWT request interceptor, 401 refresh interceptor; login + register page UI
**Commit:** `feat: axios jwt interceptor login register pages`

---

#### 🔲 Day 102 — Nov 13 — Dashboard: Signal Card Grid

**What to build:** `src/pages/Dashboard.tsx`, `src/components/SignalCard.tsx` — responsive grid, fetch signals on mount, loading skeleton, filter bar
**Commit:** `feat: dashboard signal card grid with filters skeleton`

---

#### 🔲 Day 103 — Nov 14 — Signal Detail Page

**What to build:** `src/pages/SignalDetail.tsx` — full chart PNG, price levels table, Claude reasoning, 6 metrics, share button
**Commit:** `feat: signal detail page chart stats reasoning share`

---

#### 🔲 Day 104 — Nov 15 — Lightweight Charts Integration

**What to build:** `src/components/LiveChart.tsx` — `lightweight-charts`, candlestick series, historical bars on mount, zoom + pan
**Commit:** `feat: lightweight charts interactive candlestick component`

---

#### 🔲 Day 105 — Nov 16 — Chart: EMA Overlays + Pattern Markers + Live WebSocket

**What to build:** Complete `LiveChart.tsx` — EMA-21/50 line series, pattern markers, WebSocket hook for live candle updates
**Commit:** `feat: chart ema overlays pattern markers live websocket updates`

---

#### 🔲 Day 106 — Nov 17 — Backtest Explorer Page

**What to build:** `src/pages/BacktestExplorer.tsx` — Recharts equity curve, sortable trade log table, CSV export
**Commit:** `feat: backtest explorer equity curve trade log csv export`

---

#### 🔲 Day 107 — Nov 18 — Watchlist Page

**What to build:** `src/pages/Watchlist.tsx` — debounced search (300ms), add/remove instruments, Free tier limit counter, upgrade prompt
**Commit:** `feat: watchlist page debounced search tier limit indicator`

---

#### 🔲 Day 108 — Nov 19 — Settings + Billing Page

**What to build:** `src/pages/Settings.tsx` — profile, plan badge, Stripe checkout redirect, Telegram connect, Slack webhook input
**Commit:** `feat: settings and billing page stripe checkout telegram connect`

---

#### 🔲 Day 109 — Nov 20 — Dark Mode Toggle

**What to build:** Dark mode toggle in nav; `dark:` Tailwind classes on all components; localStorage persistence; OS preference default
**Commit:** `feat: dark mode toggle os preference localStorage persistence`

---

#### 🔲 Day 110 — Nov 21 — Mobile Responsive Layout

**What to build:** Bottom tab bar for mobile (< 768px); audit all pages at 375px width; fix overflow; 44×44px tap targets
**Commit:** `feat: mobile responsive bottom tab bar 375px viewport`

---

#### 🔲 Day 111 — Nov 22 — Live WebSocket on Dashboard

**What to build:** `src/hooks/useSignalWebSocket.ts` — connect, receive new signals, prepend to dashboard grid, animate appearance
**Commit:** `feat: live websocket signal updates dashboard real-time`

---

#### 🔲 Day 112 — Nov 23 — Frontend Unit Tests

**What to build:** `vitest` setup; test `<SignalCard />`, `<Badge />`, auth store, Axios interceptor
**Commit:** `test: frontend vitest unit tests components and store`

---

#### 🔲 Day 113 — Nov 24 — Pricing Page

**What to build:** `src/pages/Pricing.tsx` — plan comparison table (Free/Pro/Business), feature checklist, Stripe/Razorpay CTA buttons
**Commit:** `feat: pricing page plan comparison stripe razorpay cta`

---

#### 🔲 Day 114 — Nov 25 — SEBI Disclaimer + ToS + Privacy Policy Pages

**What to build:** SEBI disclaimer on every signal card and detail page; `src/pages/Terms.tsx`; `src/pages/Privacy.tsx`
**Commit:** `feat: sebi disclaimer terms of service privacy policy pages`

---

#### 🔲 Day 115 — Nov 26 — Frontend E2E Test Setup (Playwright)

**What to build:** Install Playwright; write `tests/e2e/test_dashboard.spec.ts` — login, view signals, check signal detail
**Commit:** `test: playwright e2e dashboard login signal flow`

---

#### 🔲 Day 116 — Nov 27 — GitHub Actions CI Pipeline

**What to build:** `.github/workflows/ci.yml` — lint (ruff + eslint), pytest, vitest, Docker build on every push to main
**Commit:** `feat: github actions ci lint test build pipeline`

---

#### 🔲 Day 117 — Nov 28 — Kubernetes Manifests: Backend + Celery

**What to build:** `infra/k8s/backend-deployment.yaml`, `infra/k8s/celery-worker-deployment.yaml`, `infra/k8s/namespace.yaml`
**Commit:** `feat: kubernetes deployments backend and celery worker`

---

#### 🔲 Day 118 — Nov 29 — Kubernetes Manifests: StatefulSets + HPA

**What to build:** `infra/k8s/postgres-statefulset.yaml`, `infra/k8s/redis-statefulset.yaml`, `infra/k8s/hpa.yaml` (FastAPI scales on CPU > 70%)
**Commit:** `feat: kubernetes statefulsets and horizontal pod autoscaler`

---

#### 🔲 Day 119 — Nov 30 — Prometheus + Grafana Setup

**What to build:** `infra/k8s/prometheus.yaml`, `infra/k8s/grafana.yaml`; FastAPI `/metrics` endpoint with prometheus-fastapi-instrumentator
**Commit:** `feat: prometheus grafana monitoring setup fastapi metrics`

---

#### 🔲 Day 120 — Dec 1, 2026 — 🏁 FINAL DAY: Launch Checklist & Reflection

**What to build today:**
- Run complete end-to-end test: pipeline → signal → email + Telegram + dashboard
- Verify: `git log --oneline | wc -l` shows **120 commits**
- Write `docs/day-120-reflection.md` — everything you built, everything you learned
- Update `README.md` — complete project overview with live demo instructions

**Commit:**
```bash
git commit -m "feat: day 120 complete full stack ai trading platform launched 🚀"
```

---

## 🗓️ Days 121–150 — Continue the Streak

| Day | Date | What to Build |
|-----|------|---------------|
| 121 | Dec 2 | AI Assistant: `POST /assistant/chat` endpoint with Claude |
| 122 | Dec 3 | AI Assistant: conversation history in MongoDB |
| 123 | Dec 4 | AI Assistant: React chat bubble UI component |
| 124 | Dec 5 | Voice input: Whisper transcription endpoint |
| 125 | Dec 6 | Image upload: chart analysis via Claude Vision |
| 126 | Dec 7 | PDF upload: Q&A via Claude with S3 storage |
| 127 | Dec 8 | Workflow builder: `POST /workflows` prompt-to-DAG |
| 128 | Dec 9 | Workflow canvas: React Flow node editor |
| 129 | Dec 10 | Workflow execution engine Celery task |
| 130 | Dec 11 | Workflow management UI |
| 131 | Dec 12 | Paper trading: portfolio + position models |
| 132 | Dec 13 | Paper trading: Take This Trade button on signal card |
| 133 | Dec 14 | Paper trading: auto-close SL/TP detection |
| 134 | Dec 15 | Paper trading: manual close endpoint |
| 135 | Dec 16 | Paper trading: dashboard UI |
| 136 | Dec 17 | Paper trading: analytics (win rate, equity curve) |
| 137 | Dec 18 | Terraform: AWS EKS cluster provisioning |
| 138 | Dec 19 | Terraform: RDS PostgreSQL + ElastiCache Redis |
| 139 | Dec 20 | GitHub Actions: CD pipeline with kubectl deploy |
| 140 | Dec 21 | Nginx Ingress: SSL via cert-manager Let's Encrypt |
| 141 | Dec 22 | Load testing: k6 scripts 500 concurrent users |
| 142 | Dec 23 | Security audit: OWASP Top 10 checklist |
| 143 | Dec 24 | Broker API: Zerodha Kite Connect OAuth |
| 144 | Dec 25 | Broker API: place live order from signal card |
| 145 | Dec 26 | Options chain: TrueData feed integration |
| 146 | Dec 27 | Black-Scholes pricing model implementation |
| 147 | Dec 28 | Options strategy simulator: iron condor, straddle |
| 148 | Dec 29 | Mobile app: React Native scaffold iOS + Android |
| 149 | Dec 30 | Mobile app: push notifications FCM + APNs |
| 150 | Dec 31 | Year-end review + plan for Year 2 |

---

## 📌 Daily Git Habit

```bash
# Every single day before sleeping — no exceptions
git add .
git commit -m "feat/fix/docs/test/chore: what you built today"
git push origin main
```

| Prefix | Use When |
|--------|----------|
| `feat:` | New feature or file |
| `fix:` | Bug fix |
| `docs:` | Notes, README, learning logs |
| `test:` | Test files |
| `refactor:` | Improving existing code |
| `chore:` | Config, deps, tooling |

---

## 🧠 Skills You'll Have After 120 Days

| Skill Area | What You'll Know |
|------------|-----------------|
| **Python** | Async, type hints, OOP, decorators, context managers |
| **FastAPI** | Routes, middleware, WebSockets, dependencies, Pydantic v2 |
| **Databases** | PostgreSQL schema design, SQLAlchemy ORM, Alembic, MongoDB, Redis |
| **Data Engineering** | pandas, time series, OHLCV pipelines, yfinance, Binance API |
| **Task Queues** | Celery workers, Beat scheduler, group/chord, Flower monitoring |
| **AI/LLM** | Claude API, prompt engineering, structured JSON output, retry |
| **Finance** | EMA, RSI, MACD, Bollinger Bands, candlestick patterns, backtesting |
| **Frontend** | React 18, TypeScript, Tailwind, Zustand, Axios, WebSockets |
| **Charts** | Lightweight Charts (TradingView), Recharts, mplfinance |
| **Auth & Security** | JWT, bcrypt, OAuth, rate limiting, HMAC-SHA256 |
| **Payments** | Stripe, Razorpay, webhook security, idempotency |
| **Cloud** | AWS S3, boto3, Docker, Nginx |
| **DevOps** | GitHub Actions CI/CD, Kubernetes basics, Prometheus/Grafana |

---

*Start Date: August 4, 2026 | Total: 120 daily commits → 1 complete AI trading platform*
