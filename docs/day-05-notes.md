# Day 5 Notes — August 8, 2026
## Topic: Nginx Reverse Proxy

---

## What is a Reverse Proxy?

You already know what a proxy is — it sits between you and the internet.
A **reverse proxy** is the opposite — it sits between the internet and YOUR servers.

```
Without Nginx:
User → directly hits FastAPI on port 8000

With Nginx:
User → hits Nginx on port 80 → Nginx forwards to FastAPI on port 8000
```

Why add this extra step? Because Nginx does things FastAPI shouldn't have to:

| Job | Why Nginx does it, not FastAPI |
|-----|-------------------------------|
| SSL/HTTPS | Nginx handles encryption — FastAPI stays simple |
| Static files | Nginx serves files 10x faster than Python |
| Load balancing | Nginx splits traffic across multiple FastAPI pods |
| Rate limiting | Block bad actors before they hit your app |
| Compression | Nginx compresses responses — less bandwidth |
| Port management | Users hit port 80, not 8000 |

---

## How Nginx routes requests

Think of Nginx as a traffic cop:

```
Incoming request
      ↓
Nginx reads the URL path
      ↓
/api/*    → send to FastAPI backend:8000
/ws/*     → send to FastAPI (WebSocket) backend:8000
/charts/* → send to FastAPI static files backend:8000
/health   → send to FastAPI backend:8000
/         → return JSON message (frontend added later)
```

This is called **location routing** — matching URL patterns to destinations.

---

## Breaking down nginx.conf

### upstream block
```nginx
upstream backend {
    server backend:8000;
}
```
This names our backend server group "backend".
`backend:8000` — service name `backend` (Docker hostname) on port 8000.
In production we'd list multiple servers here for load balancing:
```nginx
upstream backend {
    server backend1:8000;
    server backend2:8000;
    server backend3:8000;
}
```

### proxy_pass
```nginx
location /api/ {
    proxy_pass http://backend;
}
```
Every request to `/api/anything` gets forwarded to our FastAPI server.
The response comes back from FastAPI → Nginx → User.
The user never knows FastAPI exists.

### Proxy headers — why they matter
```nginx
proxy_set_header X-Real-IP         $remote_addr;
proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto $scheme;
```
Without these headers, FastAPI would think ALL requests come from Nginx
(because they do — from FastAPI's perspective).
These headers tell FastAPI the REAL user's IP address and protocol.
Important for: rate limiting per IP, security logs, analytics.

### WebSocket special config
```nginx
location /ws/ {
    proxy_http_version 1.1;
    proxy_set_header Upgrade    $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_read_timeout 3600s;
}
```
WebSockets are different from regular HTTP requests:
- Regular HTTP: request → response → connection closes
- WebSocket: connection opens → stays open → both sides send messages

The `Upgrade` and `Connection` headers tell Nginx:
"This is a WebSocket — don't close it after the first response."

`proxy_read_timeout 3600s` = keep the connection alive for 1 hour.
Without this, Nginx would close the WebSocket after 60 seconds (default).

### Gzip compression
```nginx
gzip on;
gzip_types application/json application/javascript text/css;
```
Before sending a response, Nginx compresses it.
A 100KB JSON response might compress to 15KB — 85% smaller!
The browser automatically decompresses it.
Result: pages load faster, less bandwidth used.

---

## Port mapping explained

```
Your browser → http://localhost:80  (or just http://localhost)
                       ↓
              Nginx container port 80
                       ↓
              Routes to backend:8000
                       ↓
              FastAPI container port 8000
```

In docker-compose.yml:
```yaml
nginx:
  ports:
    - "80:80"     # your Mac port 80 → container port 80
```

The databases (PostgreSQL, MongoDB, Redis) also have port mappings:
```yaml
postgres:
  ports:
    - "5432:5432"  # so TablePlus/pgAdmin can connect
```
But in production, databases should have NO port mapping —
they should only be accessible from inside Docker, never from the internet.

---

## depends_on — start order

```yaml
nginx:
  depends_on:
    - postgres
    - mongodb
    - redis
```
This tells Docker: "start nginx AFTER postgres, mongodb, redis are started."
Note: "started" is not the same as "healthy" — we'll fix this on Day 7
when we add the backend service with proper health check dependencies.

---

## What we have now

```
Port 80   → Nginx (routes everything)
Port 5432 → PostgreSQL
Port 27017 → MongoDB
Port 6379  → Redis
```

When we add the FastAPI backend on Day 7:
```
Port 80   → Nginx → Port 8000 → FastAPI
Port 5555 → Flower (Celery monitor)
```

---

## Tomorrow — Day 6
Write `.env.example` cleanup and `.gitignore` final review.
Make sure everything is documented and secured before
we start writing actual Python code on Day 7+.
