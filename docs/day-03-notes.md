# Day 3 Notes — August 6, 2026
## Topic: Docker Compose + PostgreSQL 15

---

## What is Docker Compose?

Yesterday we wrote a `Dockerfile` for ONE service (backend).
But our project needs SEVEN services running together:
- FastAPI backend
- Celery worker
- Celery Beat
- PostgreSQL
- MongoDB
- Redis
- Nginx

Running 7 separate `docker run` commands is painful.
**Docker Compose** lets you define all services in one file
and start them all with a single command: `docker compose up`

---

## docker-compose.yml Structure

```yaml
version: "3.9"        # compose file format version

services:             # list of containers to run
  postgres:           # service name (also its hostname on the network)
    image: ...        # which Docker image to use
    environment: ...  # environment variables
    ports: ...        # host:container port mapping
    volumes: ...      # persistent storage
    healthcheck: ...  # how to check if service is healthy
    networks: ...     # which network to join

volumes:              # named volumes (persistent storage)
  postgres_data:

networks:             # private network for services to talk
  tradeflow_net:
```

---

## Breaking down our PostgreSQL service

```yaml
postgres:
  image: postgres:15-alpine
```
`postgres:15-alpine` = official PostgreSQL 15 image, Alpine Linux base (tiny size)
We don't need to write a Dockerfile for PostgreSQL — the official image handles everything.

```yaml
  environment:
    POSTGRES_DB: ${POSTGRES_DB:-tradeflow}
```
`${POSTGRES_DB:-tradeflow}` means:
- Use the `POSTGRES_DB` value from our `.env` file
- If it's not set, default to `tradeflow`
This is how we inject configuration without hardcoding it.

```yaml
  ports:
    - "5432:5432"
```
Format is `HOST_PORT:CONTAINER_PORT`
- Left side `5432` = port on YOUR Mac
- Right side `5432` = port inside the container
So you can connect from your Mac at `localhost:5432`

```yaml
  volumes:
    - postgres_data:/var/lib/postgresql/data
```
`postgres_data` is a named volume — Docker manages it.
PostgreSQL stores its data at `/var/lib/postgresql/data` inside the container.
Without this volume, ALL DATA IS LOST every time you stop the container.
With this volume, data persists forever (even after `docker compose down`).

```yaml
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U tradeflow -d tradeflow"]
    interval: 10s
    timeout: 5s
    retries: 5
```
Docker will run `pg_isready` every 10 seconds.
If it fails 5 times in a row → container is marked UNHEALTHY.
Other services that `depends_on: postgres` will wait until it's healthy.
This prevents race conditions (backend starting before DB is ready).

---

## Networks — How services talk to each other

All services are on `tradeflow_net` (a private Docker network).
Inside this network, services find each other by **service name**.

So our backend will connect to PostgreSQL using:
```
host = "postgres"   (not localhost!)
port = 5432
```

Outside Docker (from your Mac terminal), you use:
```
host = "localhost"
port = 5432
```

---

## What is .env.example?

We have TWO files:
| File | Committed to Git? | Contains |
|------|------------------|---------|
| `.env.example` | ✅ YES | Variable names, fake/default values |
| `.env` | ❌ NO (in .gitignore) | Real secret values |

Why? So anyone cloning the repo knows what variables they need,
without exposing your real passwords and API keys.

---

## Commands learned today

```bash
# Start PostgreSQL
docker compose up postgres

# Start PostgreSQL in background (detached mode)
docker compose up -d postgres

# See logs
docker compose logs postgres

# Connect to PostgreSQL directly
docker compose exec postgres psql -U tradeflow -d tradeflow

# Stop everything
docker compose down

# Stop and DELETE all data volumes (fresh start)
docker compose down -v
```

---

## Tomorrow — Day 4
Add MongoDB 7 and Redis 7 to docker-compose.yml.
Both have the same patterns you learned today — just different images.
