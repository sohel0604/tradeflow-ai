# Day 12 Notes — August 15, 2026
## Topic: Business Logic Models

---

## What we built today

7 more models covering every core feature of TradeFlow AI:

```
backtest_results        ← outcome of strategy backtests
user_strategy_configs   ← per-user strategy parameter overrides
signals                 ← AI-generated BUY/SELL/HOLD decisions
user_watchlist          ← which instruments each user follows
subscriptions           ← billing plan (free/pro/business)
paper_portfolios        ← virtual trading accounts
paper_positions         ← open paper trades
paper_trades            ← closed paper trades (P&L history)
```

---

## Complete table map after Day 12

```
users
├── auth_tokens           (FK: user_id → users.id CASCADE)
├── api_keys              (FK: user_id → users.id CASCADE)
├── broker_credentials    (FK: user_id → users.id CASCADE)
├── user_watchlist        (FK: user_id → users.id CASCADE)
├── subscriptions         (FK: user_id → users.id CASCADE)
├── user_strategy_configs (FK: user_id → users.id CASCADE)
├── paper_portfolios      (FK: user_id → users.id CASCADE)
│   └── paper_positions   (FK: portfolio_id → paper_portfolios.id)
│       └── paper_trades  (FK: position_id → paper_positions.id)
│
price_bars                (no user FK — shared data)
fetch_logs                (no user FK — ops data)
backtest_results          (no user FK — shared strategy results)
signals                   (no user FK — shared signals)
```

---

## JSON columns — flexible data in PostgreSQL

```python
parameters = Column(JSON, nullable=True)
# Store: {"fast_period": 9, "slow_period": 21}

pattern_tags = Column(JSON, nullable=True)
# Store: ["hammer", "ema_crossover", "rsi_oversold"]
```

PostgreSQL's `JSON` type stores any valid JSON.
We use it when the structure varies between rows.
For example, EMA crossover parameters look different
from Bollinger Band parameters.

When to use JSON column vs separate table:
- Use JSON when the data is just "metadata" for a row
- Use a separate table when you need to query INTO the data
  (e.g. filtering signals by a specific pattern_tag)

---

## BacktestResult — the quality gate

```python
passed = Column(Boolean, default=False)
```

The pipeline runs a check after every backtest:
```python
result.passed = (
    result.win_rate >= 0.50 and   # wins more than it loses
    result.avg_rr   >= 1.5        # average win is 1.5x bigger than average loss
)
```

BOTH conditions must be true (AND, not OR).
A strategy with 90% win rate but avg_rr of 0.1 would FAIL.
A strategy with 80% avg_rr but 30% win rate would FAIL.
Only well-rounded strategies generate signals.

---

## Signal — lifecycle

```python
outcome = Column(String(10), default="OPEN")
```

Every signal starts as OPEN.
The daily outcome checker (Day 66) runs after each price fetch:

```python
if today.low <= signal.stop_loss:
    signal.outcome = "LOSS"
elif today.high >= signal.take_profit_1:
    signal.outcome = "WIN"
elif days_since_signal > 20:
    signal.outcome = "EXPIRED"
```

If BOTH stop-loss and take-profit are hit on the same bar
→ we assume LOSS (conservative — better to undercount wins).

---

## PaperPortfolio vs PaperPosition vs PaperTrade

Three tables, three different questions they answer:

| Table | Question it answers |
|-------|-------------------|
| `paper_portfolios` | "What is the user's current total balance?" |
| `paper_positions` | "What trades are currently open?" |
| `paper_trades` | "What trades were closed and what was the P&L?" |

```
paper_portfolios.current_balance
    = starting_balance + SUM(paper_trades.pnl)
```

When a position closes:
1. Create a PaperTrade row (permanent record)
2. Update PaperPortfolio.current_balance
3. Update PaperPosition.status = "CLOSED"

---

## onupdate — auto timestamp on change

```python
updated_at = Column(
    DateTime(timezone=True),
    onupdate=datetime.utcnow,
)
```

`onupdate` runs the function automatically every time
SQLAlchemy updates that row.
No need to manually set `updated_at` in your code.

Compare to `default` which only runs on INSERT.
`onupdate` runs on every UPDATE.

---

## UniqueConstraint naming convention

```python
UniqueConstraint("symbol", "strategy", "signal_date",
                 name="uq_signal_symbol_strategy_date")
```

Naming pattern: `uq_tablename_column1_column2`

Why name it?
- Alembic uses the name to identify constraints in migrations
- If you rename it, Alembic drops the old and creates the new
- Without a name, Alembic generates a random one — hard to manage

---

## Tomorrow — Day 13
Alembic migrations setup.
We write the initial migration that creates ALL tables in PostgreSQL.
`alembic upgrade head` will run all our models through
and create the real tables in the database.
