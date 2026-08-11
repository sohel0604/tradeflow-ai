# =============================================================================
# TradeFlow AI — Backend Dockerfile
# Base image: Python 3.11 slim (small footprint, official image)
# =============================================================================

# Step 1: Start from the official Python 3.11 slim image
# "slim" means it has the minimum OS packages — keeps image size small
FROM python:3.11-slim

# Step 2: Set environment variables
# PYTHONDONTWRITEBYTECODE=1 → don't create .pyc compiled files inside container
# PYTHONUNBUFFERED=1        → print logs immediately (don't buffer them)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Step 3: Set the working directory inside the container
# All future commands (COPY, RUN, CMD) will run from /app
WORKDIR /app

# Step 4: Install system dependencies
# We need gcc and libpq-dev to compile some Python packages (psycopg2)
# --no-install-recommends keeps the image lean
# We clean up apt cache at the end to reduce image size
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Step 5: Copy requirements first (before copying code)
# Why? Docker caches layers. If requirements.txt hasn't changed,
# Docker skips the pip install step on rebuilds — much faster!
COPY requirements.txt .

# Step 6: Install Python dependencies
# --no-cache-dir → don't store pip's download cache (saves space)
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Step 7: Copy the rest of the application code
COPY . .

# Step 8: Create the charts output directory
RUN mkdir -p /app/charts

# Step 9: Expose port 8000 (FastAPI will listen here)
# This is documentation — it doesn't actually open the port
# Port mapping happens in docker-compose.yml
EXPOSE 8000

# Step 10: Default command to run when the container starts
# This starts the FastAPI development server with hot-reload
# In production we'll use gunicorn instead of --reload
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
