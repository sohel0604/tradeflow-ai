# Day 7 Notes — August 10, 2026
## Topic: All 7 Services Running Together

---

## What we proved today

One command → 7 services → fully working stack:

```
docker compose up --build

✅ tradeflow_postgres     → PostgreSQL 15    (healthy)  port 5432
✅ tradeflow_mongodb      → MongoDB 7        (healthy)  port 27017
✅ tradeflow_redis        → Redis 7          (healthy)  port 6379
✅ tradeflow_backend      → FastAPI           running   port 8000
✅ tradeflow_celery_beat  → Celery Beat       running
✅ tradeflow_celery_worker→ Celery Worker     running
✅ tradeflow_flower       → Flower dashboard  running   port 5555
✅ tradeflow_nginx        → Nginx proxy       running   port 80
```

And we verified:
```
curl http://localhost:8000/health  → {"status":"ok"} via FastAPI direct
curl http://localhost:80/health    → {"status":"ok"} via Nginx → FastAPI
```

---

## What each new service does

### FastAPI Backend (`backend`)
```yaml
command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
- `uvicorn` — ASGI server that runs FastAPI
- `--host 0.0.0.0` — listen on ALL network interfaces (not just localhost)
  Without this, FastAPI inside Docker can't be reached from outside
- `--port 8000` — port inside the container
- `--reload` — restart when code changes (dev only, never in production)

### Celery Worker (`celery_worker`)
```yaml
command: celery -A app.celery_app worker --loglevel=info --concurrency=4 -Q default,pipeline,signals,alerts
```
- `-A app.celery_app` — tells Celery where to find our app
- `worker` — this process is a worker (picks up and runs tasks)
- `--concurrency=4` — runs 4 tasks simultaneously
- `-Q default,pipeline,signals,alerts` — which queues to listen to

### Celery Beat (`celery_beat`)
```yaml
command: celery -A app.celery_app beat --loglevel=info
```
- `beat` — this process is the scheduler
- Reads the `beat_schedule` from `celery_app.py`
- Fires tasks at the right time (06:00 IST daily)
- **Only ONE beat should EVER run** — running two causes duplicate tasks

### Flower (`flower`)
```yaml
command: celery -A app.celery_app flower --port=5555
```
- Web UI for monitoring Celery tasks
- Open http://localhost:5555 in your browser
- Shows: workers online, tasks running, task history, queue depths

---

## depends_on with health checks

```yaml
backend:
  depends_on:
    postgres:
      condition: service_healthy   ← wait until PostgreSQL is HEALTHY
    mongodb:
      condition: service_healthy   ← wait until MongoDB is HEALTHY
    redis:
      condition: service_healthy   ← wait until Redis is HEALTHY
```

vs just:
```yaml
depends_on:
  - postgres   ← only waits until postgres STARTS (not healthy!)
```

Using `condition: service_healthy` means our backend only starts
AFTER all databases have passed their health checks.
This prevents the backend crashing on startup because the DB isn't ready.

---

## volumes — live code reloading

```yaml
backend:
  volumes:
    - ./backend:/app
```

This mounts your local `./backend` folder INSIDE the container at `/app`.

Effect:
1. You edit a file on your Mac
2. The file instantly changes inside the container too
3. `--reload` detects the change
4. FastAPI restarts automatically

No need to rebuild the Docker image every time you change code.
Only rebuild when you change `requirements.txt` or `Dockerfile`.

---

## env_file — loading .env into containers

```yaml
backend:
  env_file: .env
```

This passes ALL variables from `.env` into the container as environment variables.
The container can then read them with `os.getenv("POSTGRES_PASSWORD")`.

---

## The startup order

Docker compose follows the dependency chain:

```
Step 1: Start postgres, mongodb, redis (no dependencies)
Step 2: Wait for all three to be HEALTHY
Step 3: Start backend, celery_worker, celery_beat, flower
Step 4: Wait for backend to start
Step 5: Start nginx
```

This ensures no service starts before what it needs is ready.

---

## URLs available right now

| URL | What you see |
|-----|-------------|
| http://localhost:8000/health | `{"status":"ok"}` — FastAPI direct |
| http://localhost:8000/docs | Swagger UI — interactive API docs |
| http://localhost:80/health | Same, through Nginx |
| http://localhost:5555 | Flower — Celery task monitor |

---

## Week 1 complete!

```
Day 1  ✅  GitHub repo + folder structure
Day 2  ✅  Backend Dockerfile
Day 3  ✅  PostgreSQL in Docker Compose
Day 4  ✅  MongoDB + Redis in Docker Compose
Day 5  ✅  Nginx reverse proxy
Day 6  ✅  Environment variables + secrets
Day 7  ✅  All 7 services running + verified
```

The entire infrastructure foundation is done.
From Day 8 we start building the actual application:
PostgreSQL schema, SQLAlchemy models, Alembic migrations.

---

## Tomorrow — Day 8
SQL fundamentals — practice real SQL queries against our PostgreSQL.
Understanding the database layer before we write Python code on top of it.
