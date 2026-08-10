# Day 1 Notes — August 4, 2026
## Topic: Project Scaffold & Git Setup

---

## What I learned today

### 1. Monorepo Structure
A monorepo means all parts of the project live in ONE repository:
- `backend/` — the Python API and data pipeline
- `frontend/` — the React dashboard
- `nginx/` — the reverse proxy that routes requests
- `infra/` — Kubernetes and Terraform for cloud deployment
- `tests/` — all test files
- `docs/` — learning notes like this one

**Why monorepo?**
Everything is in one place. One `git clone` gives you the whole project.
Easy to see how backend and frontend interact.

---

### 2. Git Basics
```bash
git init                    # initialise a new repo
git add .                   # stage all changes
git commit -m "message"     # save a snapshot
git push origin main        # upload to GitHub
```

**The golden rule:** commit every single day.
Each commit is a checkpoint you can always go back to.

---

### 3. .gitignore — What NOT to commit
The `.gitignore` file tells Git which files to ignore.

Most important things to NEVER commit:
- `.env` — contains your real API keys and passwords
- `node_modules/` — 100,000+ files, can be reinstalled with `npm install`
- `__pycache__/` — compiled Python files, auto-generated
- `*.log` — log files, grow forever and contain sensitive data

---

### 4. README.md
The README is the front page of your project on GitHub.
It should answer: What is this? How do I run it? What does it do?

---

### 5. Project Goal
TradeFlow AI will:
1. Pull market data (stocks, crypto, forex, commodities)
2. Run technical analysis (EMA, RSI, MACD, patterns)
3. Backtest strategies to find what actually works
4. Use Claude AI to generate trade signals with reasoning
5. Deliver signals via Email, Telegram, Slack
6. Show everything on a React dashboard with live charts

**120 days. One commit per day. Let's build it.**

---

## Tomorrow — Day 2
Install Docker Desktop and write the backend Dockerfile.
