# Day 13 Notes — August 16, 2026
## Topic: Alembic Migrations

---

## What is a database migration?

Your database schema changes over time.
You add a column, rename a table, add an index.

Without migrations — chaos:
- "Did you run that ALTER TABLE command?"
- "Which version of the schema is production on?"
- "How do I recreate the DB from scratch?"

With Alembic migrations — order:
- Every schema change is a numbered Python file
- `alembic upgrade head` applies all pending changes
- `alembic downgrade -1` rolls back the last change
- New developer joins → runs `alembic upgrade head` → perfect schema instantly

Alembic is like Git, but for your database schema.

---

## Files we created today

```
backend/
├── alembic.ini                         ← configuration
├── alembic/
│   ├── env.py                          ← connects Alembic to our models
│   ├── script.py.mako                  ← template for new migration files
│   └── versions/
│       └── 0001_initial_schema.py      ← our first migration
```

---

## alembic.ini — the config file

```ini
[alembic]
script_location = alembic          # where migration files live
file_template = %%(rev)s_%%(slug)s # naming: 0001_initial_schema.py
sqlalchemy.url = postgresql://...  # overridden by env.py from settings
```

---

## env.py — the brain of Alembic

Three key things env.py does:

### 1. Load all models
```python
import app.models  # imports __init__.py → imports all 14 models
target_metadata = Base.metadata  # Alembic reads all table definitions
```

Without this import, Alembic doesn't know any tables exist.
It would generate a migration that drops everything.

### 2. Use our settings for DB URL
```python
config.set_main_option("sqlalchemy.url", settings.database_url_sync)
```

Reads from `.env` → uses the correct database.
No hardcoded credentials.

### 3. Two modes
```python
if context.is_offline_mode():
    run_migrations_offline()  # generates SQL script
else:
    run_migrations_online()   # runs against real DB
```

**Online mode** (normal): connects to DB, applies changes immediately.
**Offline mode**: generates a `.sql` file you can review before running.
```bash
alembic upgrade head --sql > migration.sql
cat migration.sql  # review the SQL before running
```

---

## Migration file structure

```python
revision = "0001"           # this migration's ID
down_revision = None        # what came before (None = first migration)

def upgrade() -> None:
    # CREATE TABLE, ADD COLUMN, CREATE INDEX etc.
    op.create_table("users", ...)
    op.create_index(...)

def downgrade() -> None:
    # Reverse of upgrade — DROP TABLE etc.
    op.drop_table("users")
```

The `down_revision` links migrations like a linked list:
```
0001 → 0002 → 0003 → 0004
None    0001    0002    0003
```

`alembic upgrade head` applies them left to right.
`alembic downgrade -1` goes right to left.

---

## The 5 Alembic commands you'll use every day

```bash
# Apply all pending migrations (most common command)
alembic upgrade head

# Undo last migration (if you made a mistake)
alembic downgrade -1

# See which migration is currently applied
alembic current

# See full migration history
alembic history

# Auto-generate a new migration from model changes
# Use this from Day 14+ when you add new columns
alembic revision --autogenerate -m "add column to users"
```

---

## alembic_version table — how Alembic tracks state

```sql
SELECT * FROM alembic_version;
--  version_num
-- -------------
--  0001
```

Alembic stores the current revision in this table.
When you run `upgrade head`, it checks this table,
finds the current version, and applies all newer migrations.

It's just one row in one table — that's how the whole
tracking system works.

---

## Why we write migrations manually (not auto-generated)

Alembic can auto-generate migrations with:
```bash
alembic revision --autogenerate -m "description"
```

This compares your SQLAlchemy models to the live DB
and generates the diff.

We wrote the first migration manually because:
1. It's educational — you learn exactly what SQL is generated
2. Auto-generate sometimes misses things (custom constraints, indexes)
3. Manual migrations are clearer and easier to review

From Day 14+ when we add individual columns,
we'll use `--autogenerate` for speed.

---

## What was proven today

```bash
alembic upgrade head
# INFO Running upgrade  -> 0001, Initial schema — all 14 tables ✅

SELECT COUNT(*) FROM information_schema.tables
WHERE table_schema='public';
# 15 tables (14 ours + alembic_version) ✅

alembic downgrade -1
# INFO Running downgrade 0001 -> ... ✅

alembic upgrade head
# INFO Running upgrade  -> 0001 again ✅
```

Your database schema is now version-controlled.
Anyone who clones this repo runs ONE command
and gets a perfect database instantly.

---

## Tomorrow — Day 14
Run the migrations verification — connect to psql and
inspect the real tables, constraints, and indexes.
Then clean up the practice_price_bars table from Day 8.
Week 2 complete!
