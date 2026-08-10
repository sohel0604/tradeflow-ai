# TradeFlow AI

An AI-powered trading signal platform for Indian & US equities, Crypto, Forex, and Commodities.

Built in 120 days — one commit per day.

## What this platform does
- Fetches daily OHLCV data for 50+ instruments
- Computes technical indicators (EMA, RSI, MACD, Bollinger Bands, ATR, OBV)
- Detects candlestick and structural chart patterns
- Backtests 4 strategies and filters by win rate + risk-reward
- Uses Claude AI to generate BUY/SELL/HOLD signals with reasoning
- Delivers signals via Email, Telegram, Slack, and REST webhook
- Full React dashboard with live charts and WebSocket updates
- Paper trading module with P&L tracking

## Tech Stack

| Layer | Technology |
|---|---|
| Backend API | FastAPI + Python 3.11 |
| Task Queue | Celery + Redis |
| Scheduler | Celery Beat (06:00 IST daily) |
| Primary DB | PostgreSQL 15 |
| Document DB | MongoDB 7 |
| Cache / Broker | Redis 7 |
| Reverse Proxy | Nginx |
| AI | Anthropic Claude |
| Frontend | React 18 + TypeScript + Tailwind |
| Charts | Lightweight Charts (TradingView OSS) |

## Project Structure

```
tradeflow-ai/
├── backend/       — FastAPI app, Celery tasks, services
├── frontend/      — React 18 + TypeScript + Tailwind
├── nginx/         — Reverse proxy config
├── infra/         — Kubernetes manifests + Terraform
├── tests/         — Unit + integration + e2e tests
├── docs/          — Learning notes and architecture docs
└── TASK_TRACKER.md — 120-day development plan
```

## Development Progress

| Phase | Days | Status |
|---|---|---|
| Phase 1 — Docker & DB | Days 1–14 | 🔄 In Progress |
| Phase 2 — FastAPI + Data Pipeline | Days 15–30 | 🔲 Not Started |
| Phase 3 — Celery + Indicators + Backtest | Days 31–60 | 🔲 Not Started |
| Phase 4 — AI + Delivery + Auth | Days 61–90 | 🔲 Not Started |
| Phase 5 — REST API + React Frontend | Days 91–120 | 🔲 Not Started |

---

*Started: August 4, 2026*
