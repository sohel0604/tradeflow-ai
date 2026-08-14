# Day 4 Notes — August 7, 2026
## Topic: MongoDB + Redis added to Docker Compose

---

## Why do we need THREE databases?

This is the most common question. Here is the honest answer:

| Database | Type | Best for | We use it for |
|----------|------|---------|---------------|
| PostgreSQL | Relational (tables) | Structured data, relationships, transactions | Users, signals, price bars, billing |
| MongoDB | Document (JSON) | Nested/flexible data, no fixed schema | Indicators, chart patterns, AI conversations |
| Redis | In-memory (key-value) | Speed, temporary data, pub/sub | Cache, Celery queue, WebSocket fan-out |

Each database has a job it does BEST.
Using the right tool for the right job = faster, simpler code.

---

## MongoDB — Document Database

### What is a document?
Instead of rows and columns (like PostgreSQL), MongoDB stores JSON documents.

PostgreSQL row (flat):
```
| symbol | timeframe | ema_9 | ema_21 | rsi_14 | macd_line |
|--------|-----------|-------|--------|--------|-----------|
| AAPL   | 1d        | 182.3 | 180.1  | 62.4   | 1.23      |
```

MongoDB document (nested JSON):
```json
{
  "symbol": "AAPL",
  "timeframe": "1d",
  "timestamp": "2024-01-15",
  "indicators": {
    "ema": { "9": 182.3, "21": 180.1, "50": 175.2, "200": 165.0 },
    "rsi": { "14": 62.4 },
    "macd": { "line": 1.23, "signal": 0.98, "histogram": 0.25 },
    "bollinger": { "upper": 190.1, "middle": 182.0, "lower": 173.9 }
  }
}
```

The nested structure is natural for indicators.
In PostgreSQL you'd need multiple tables or a messy JSON column.
In MongoDB it just... fits.

### MongoDB terms vs PostgreSQL terms
| PostgreSQL | MongoDB |
|-----------|---------|
| Database | Database |
| Table | Collection |
| Row | Document |
| Column | Field |
| JOIN | $lookup (aggregation) |

### Our MongoDB collections
```
tradeflow database
├── indicators          ← EMA, RSI, MACD, Bollinger per symbol per day
├── chart_patterns      ← detected candlestick patterns
├── backtest_trade_logs ← full trade-by-trade log per backtest
├── ai_conversations    ← chat history with Claude AI assistant
├── workflows           ← automation workflow DAGs
└── workflow_logs       ← execution logs for each workflow
```

---

## Redis — In-Memory Store

### What makes Redis special?
Redis stores everything in RAM (memory), not on disk.
Reading from RAM: ~0.1 milliseconds
Reading from PostgreSQL: ~5-50 milliseconds

That's 50-500x faster.

### Redis is not just a cache — it does 4 jobs for us

**Job 1: Celery Broker (Task Queue)**
```
FastAPI says "fetch RELIANCE.NS data"
        ↓
Redis stores the task: { "task": "fetch", "symbol": "RELIANCE.NS" }
        ↓
Celery Worker picks it up and executes it
```
Redis is the middleman — the post office that holds messages.

**Job 2: Celery Result Backend**
```
Celery Worker finishes the task
        ↓
Stores result in Redis: { "task_id": "abc123", "status": "SUCCESS", "rows": 245 }
        ↓
FastAPI can check: "did that task finish?"
```

**Job 3: API Cache**
```
User requests GET /signals (first time)
        ↓
FastAPI queries PostgreSQL → takes 50ms
FastAPI stores result in Redis with 1hr expiry
        ↓
User requests GET /signals again (within 1 hour)
        ↓
FastAPI reads from Redis → takes 0.5ms ← 100x faster!
```

**Job 4: Pub/Sub for WebSockets (Day 92)**
```
Pipeline generates new signal
        ↓
Publishes to Redis channel "signals"
        ↓
All connected WebSocket clients receive it instantly
        ↓
Signal card appears on dashboard without page refresh
```

### Redis data structures we'll use
| Structure | Used for |
|-----------|---------|
| String | Cache API responses, store tokens |
| List | Task queues |
| Hash | Store session data |
| Pub/Sub | Real-time signal fan-out |
| Sorted Set | Rate limiting (sliding window) |

---

## What we added to docker-compose.yml today

### MongoDB service
```yaml
mongodb:
  image: mongo:7-jammy        # official MongoDB 7 image
  environment:
    MONGO_INITDB_ROOT_USERNAME: tradeflow   # admin username
    MONGO_INITDB_ROOT_PASSWORD: tradeflow123
  ports:
    - "27017:27017"            # default MongoDB port
  volumes:
    - mongo_data:/data/db      # MongoDB stores data here
  healthcheck:
    test: mongosh --eval "db.adminCommand('ping')"
```

### Redis service
```yaml
redis:
  image: redis:7-alpine
  command: redis-server --requirepass tradeflow123  # ALWAYS set a password
  ports:
    - "6379:6379"              # default Redis port
  volumes:
    - redis_data:/data         # persist Redis data to disk
  healthcheck:
    test: redis-cli -a tradeflow123 ping  # returns PONG if healthy
```

---

## Connection details (from outside Docker)

### MongoDB
```
Host:     localhost
Port:     27017
Username: tradeflow
Password: tradeflow123
Database: tradeflow
```

### Redis
```
Host:     localhost
Port:     6379
Password: tradeflow123
```

### Connection strings (used in code)
```
MongoDB: mongodb://tradeflow:tradeflow123@localhost:27017/tradeflow
Redis:   redis://:tradeflow123@localhost:6379/0
```

Inside Docker (backend talking to these services):
```
MongoDB: mongodb://tradeflow:tradeflow123@mongodb:27017/tradeflow
Redis:   redis://:tradeflow123@redis:6379/0
```

Notice: `localhost` becomes the service name (`mongodb`, `redis`) inside Docker.

---

## Commands learned today

```bash
# Start all 3 databases
docker compose up -d postgres mongodb redis

# Check all are healthy
docker compose ps

# See MongoDB logs
docker compose logs mongodb

# See Redis logs
docker compose logs redis

# Connect to Redis CLI (test it)
docker compose exec redis redis-cli -a tradeflow123 ping
# Returns: PONG ✅

# Connect to MongoDB shell
docker compose exec mongodb mongosh -u tradeflow -p tradeflow123

# Stop everything
docker compose down
```

---

## Tomorrow — Day 5
Add Nginx reverse proxy to docker-compose.yml.
Nginx sits in front of everything and routes:
- `/api/*` → FastAPI backend
- `/ws/*` → WebSocket connections
- `/` → React frontend (later)
