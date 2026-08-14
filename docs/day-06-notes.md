# Day 6 Notes — August 9, 2026
## Topic: Environment Variables & Secrets Management

---

## Why environment variables?

Imagine you hardcode your database password in your code:

```python
# BAD — never do this
db = connect(password="tradeflow123")
```

Problems:
1. You commit it to GitHub → password is PUBLIC forever
2. You have different passwords for dev vs production → you'd need to change code
3. A teammate clones the repo → they have your production password

Environment variables solve all 3 problems:

```python
# GOOD — read from environment
import os
db = connect(password=os.getenv("POSTGRES_PASSWORD"))
```

Now the password lives in `.env` (not in code),
`.env` is in `.gitignore` (never committed),
and you can have different `.env` files for dev vs production.

---

## The two file system

| File | Committed? | Contains | Purpose |
|------|-----------|---------|---------|
| `.env.example` | ✅ YES | Variable NAMES + fake values | Documents what's needed |
| `.env` | ❌ NO | Real secret values | Your actual config |

When a new developer joins the team:
```bash
git clone https://github.com/you/tradeflow-ai
cp .env.example .env
# Fill in real values → ready to run
```

---

## What's in our .env file

### App config
```
APP_ENV=development       ← tells the app which mode it's in
APP_SECRET_KEY=...        ← used to sign cookies and sessions
DEBUG=true                ← shows detailed errors in dev, NEVER in prod
LOG_LEVEL=INFO            ← how verbose the logs are
```

### Database connection strings
```
DATABASE_URL=postgresql+asyncpg://user:pass@host:port/db
```
This is the full connection string — one variable contains everything.
The `+asyncpg` part tells SQLAlchemy to use the async driver.

### Why two DATABASE_URL variables?
```
DATABASE_URL      → used by FastAPI (async)
DATABASE_URL_SYNC → used by Alembic migrations and Celery (sync)
```
Alembic and Celery can't use async drivers — they need the sync version.
So we keep both.

### The ${VAR:-default} pattern in docker-compose.yml
```yaml
POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-tradeflow123}
```
This means:
- Use `POSTGRES_PASSWORD` from `.env` if it exists
- If `.env` doesn't exist → use `tradeflow123` as fallback

This way docker-compose always works even without a `.env` file.

---

## How to generate secure secret keys

Never use a simple string like "mysecret" for JWT or app secret keys.
Use Python's `secrets` module — cryptographically secure random bytes:

```bash
# Generate APP_SECRET_KEY (32 bytes = 64 hex chars)
python3 -c "import secrets; print(secrets.token_hex(32))"
# Example: 556457b8e1b4ab8cf43ad20703470d3d...

# Generate JWT_SECRET_KEY (64 bytes = 128 hex chars)
python3 -c "import secrets; print(secrets.token_hex(64))"

# Generate ENCRYPTION_KEY (for AES-256 broker credential encryption)
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Why long random keys?
- A short key like "secret" could be brute-forced in seconds
- A 32-byte random hex key would take longer than the age of the universe

---

## .gitignore — what we protect

Our `.gitignore` protects these critical files:

```
.env              ← database passwords, API keys, JWT secrets
.env.local        ← local overrides
.env.production   ← production secrets
*.pem             ← SSL certificates
*.key             ← private keys
credentials.json  ← Google/AWS service account files
```

And these noisy generated files:
```
__pycache__/      ← Python compiled files (auto-regenerated)
node_modules/     ← 100k+ Node packages (reinstalled with npm install)
.DS_Store         ← Mac Finder metadata (useless to everyone else)
*.log             ← Log files (grow forever, contain sensitive data)
.terraform/       ← Terraform working directory (large, auto-generated)
*.tfstate         ← Terraform state (contains secrets!)
```

---

## The golden rule of secrets

```
If it's secret → it goes in .env
If it's in .env → it's in .gitignore
If it was ever committed → rotate it immediately
```

**What to do if you accidentally commit a secret:**
1. Immediately rotate/regenerate the key or password
2. Remove it from the repo history (git filter-branch or BFG Repo-Cleaner)
3. Assume it was compromised — act accordingly

GitHub even scans for exposed secrets automatically and alerts you.

---

## How Docker reads .env

When you run `docker compose up`, Docker automatically reads `.env`
from the same folder as `docker-compose.yml`.

```
docker-compose.yml → reads → .env → passes variables to containers
```

You can verify this:
```bash
docker compose config
# Shows the final resolved config with all variables substituted
```

---

## Connection strings — quick reference

| Service | Inside Docker | Outside Docker (your Mac) |
|---------|--------------|--------------------------|
| PostgreSQL | `postgresql://tradeflow:tradeflow123@postgres:5432/tradeflow` | `postgresql://tradeflow:tradeflow123@localhost:5432/tradeflow` |
| MongoDB | `mongodb://tradeflow:tradeflow123@mongodb:27017/tradeflow` | `mongodb://tradeflow:tradeflow123@localhost:27017/tradeflow` |
| Redis | `redis://:tradeflow123@redis:6379/0` | `redis://:tradeflow123@localhost:6379/0` |

The only difference: `postgres`/`mongodb`/`redis` becomes `localhost`.

---

## Tomorrow — Day 7
The BIG day — we add FastAPI backend, Celery worker,
Celery Beat, and Flower to docker-compose.yml.
All 7 services running together for the first time!
`docker compose up --build` → everything works ← that's the goal.
