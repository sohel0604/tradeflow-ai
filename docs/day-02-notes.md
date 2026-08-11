# Day 2 Notes — August 5, 2026
## Topic: Docker Fundamentals + Backend Dockerfile

---

## What is Docker and why do we use it?

Imagine you build the app on your Mac. It works perfectly.
You send it to a friend. It breaks on their Windows machine.
"Works on my machine" — the most common problem in software.

**Docker solves this.**

Docker packages your app + its exact environment (OS, Python version,
all dependencies) into a single box called a **container**.
That box runs the same everywhere — your Mac, a server, a cloud VM.

---

## Key Concepts

### Image vs Container

| Term | What it is | Real world analogy |
|------|-----------|-------------------|
| **Image** | A blueprint/template | A recipe |
| **Container** | A running instance of an image | The cooked meal |

- One image can spawn many containers
- Images are built from a `Dockerfile`
- Containers are what actually run

### Dockerfile — How to build an image
A Dockerfile is a set of instructions Docker follows to build your image.

```dockerfile
FROM python:3.11-slim    # start from an existing base image
WORKDIR /app             # set the working directory
COPY requirements.txt .  # copy files into the image
RUN pip install -r requirements.txt  # run a command while building
COPY . .                 # copy all code
CMD ["uvicorn", "app.main:app"]  # command to run when container starts
```

### Why copy requirements.txt BEFORE the code?
Docker builds images in **layers**. Each instruction is a layer.
If a layer hasn't changed, Docker uses its **cache** (super fast).

If you copy everything at once:
- Every code change → reinstall ALL packages (slow, 2–3 minutes)

If you copy requirements.txt first:
- Code change → only copy new code (fast, 5 seconds)
- Package change → reinstall packages (slow, but only when packages change)

This is called the **Docker layer caching trick** — every professional uses it.

---

## What we built today

### `backend/Dockerfile`
A 10-step Dockerfile for our Python backend:

1. `FROM python:3.11-slim` — small official Python image
2. Set `PYTHONDONTWRITEBYTECODE` and `PYTHONUNBUFFERED`
3. `WORKDIR /app` — all commands run from here
4. Install system deps: `gcc`, `libpq-dev` (needed for PostgreSQL)
5. `COPY requirements.txt .` — copy requirements FIRST (caching)
6. `RUN pip install` — install Python packages
7. `COPY . .` — copy all application code
8. `RUN mkdir -p /app/charts` — create output folder
9. `EXPOSE 8000` — documentation (FastAPI port)
10. `CMD ["uvicorn", ...]` — start the server

### `backend/requirements.txt`
Only `fastapi` and `uvicorn` for now.
We add packages day by day as we build each feature.
This keeps things simple — you understand every package we add.

---

## Important Environment Variables we set

| Variable | Value | Why |
|----------|-------|-----|
| `PYTHONDONTWRITEBYTECODE` | 1 | No `.pyc` clutter inside container |
| `PYTHONUNBUFFERED` | 1 | Logs print immediately (no buffering) |

---

## Commands you'll use with Docker

```bash
# Build the image
docker build -t tradeflow-backend ./backend

# Run a container from the image
docker run -p 8000:8000 tradeflow-backend

# See running containers
docker ps

# See all images
docker images

# Stop a container
docker stop <container_id>

# Remove an image
docker rmi tradeflow-backend
```

We won't use these directly much — `docker compose` handles all of this.
But it's good to know what's happening under the hood.

---

## Tomorrow — Day 3
Write `docker-compose.yml` with PostgreSQL 15.
We'll start our first database service.
