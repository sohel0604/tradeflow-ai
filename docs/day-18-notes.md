# Day 18 Notes — August 21, 2026
## Topic: Pydantic v2 Schemas

---

## Schemas vs Models — the most important distinction

Two completely different things with similar names:

| | SQLAlchemy Model | Pydantic Schema |
|--|--|--|
| **File** | `app/models/price.py` | `app/schemas/price.py` |
| **Purpose** | Defines the DATABASE table | Defines the API input/output |
| **Used by** | Alembic migrations, DB queries | FastAPI routes, validation |
| **Library** | SQLAlchemy | Pydantic |
| **Example** | `class PriceBar(Base)` | `class PriceBarResponse(BaseModel)` |

They are separate because what the DB stores
and what the API exposes are different concerns.

DB model has `hashed_password` — API schema never exposes it.
API schema has computed `pages` field — DB has no such column.

---

## Pydantic v2 BaseModel — the foundation

```python
from pydantic import BaseModel, Field

class PriceBarBase(BaseModel):
    symbol: str = Field(min_length=1, max_length=50)
    open: float = Field(gt=0)    # gt = greater than
    high: float = Field(gt=0)
    volume: float = Field(ge=0)  # ge = greater than or equal
```

When FastAPI receives a request body matching this schema:
1. Parses the JSON
2. Validates each field against the type and Field constraints
3. Returns 422 with field-level errors if validation fails
4. Passes a validated Python object to your route handler

You never need to write `if price < 0: return error`.
Pydantic handles all validation automatically.

---

## Field() — validation constraints

```python
Field(gt=0)          # greater than 0       (price must be positive)
Field(ge=0)          # greater than or equal (volume can be 0)
Field(ge=0.0, le=1.0) # between 0 and 1     (confidence score)
Field(min_length=1)   # string not empty
Field(max_length=50)  # string max length
Field(ge=1, le=100)   # page size between 1 and 100
```

These constraints appear in:
- Runtime validation (422 on violation)
- OpenAPI docs at /docs (shown as constraints)
- IDE autocomplete (type-safe usage)

---

## @field_validator — custom validation logic

```python
@field_validator("high")
@classmethod
def high_must_be_above_low(cls, v: float, info) -> float:
    low = info.data.get("low")  # access other field values
    if low is not None and v < low:
        raise ValueError(f"high ({v}) must be >= low ({low})")
    return v
```

`@field_validator("field_name")` runs AFTER the field's type is validated.
Use it for cross-field validation (high > low, end_date > start_date etc.)

`info.data` contains previously validated fields.
Fields are validated in order — `low` must be declared before `high`
for `info.data.get("low")` to work.

---

## Generic PaginatedResponse[T]

```python
from typing import Generic, TypeVar
T = TypeVar("T")

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    pages: int
```

`Generic[T]` means this schema works with ANY item type:
```python
PaginatedResponse[SignalListItem]   # for signals
PaginatedResponse[PriceBarResponse] # for price bars
PaginatedResponse[BacktestResult]   # for backtest results
```

One schema, infinite reuse.
FastAPI renders the correct OpenAPI type in /docs automatically.

Route declaration:
```python
@router.get("/signals")
async def list_signals() -> PaginatedResponse[SignalListItem]:
    ...
```

---

## model_config = {"from_attributes": True}

```python
class PriceBarResponse(BaseModel):
    id: UUID
    symbol: str
    ...
    model_config = {"from_attributes": True}
```

Without this:
```python
bar = PriceBarResponse(bar_orm_object)  # FAILS — can't read ORM attributes
```

With this:
```python
bar = PriceBarResponse.model_validate(bar_orm_object)  # WORKS
```

`from_attributes=True` tells Pydantic:
"Read values from object attributes, not just from dicts."

SQLAlchemy returns ORM objects. Pydantic reads their attributes.
This is the bridge between the DB layer and the API layer.

---

## Literal types — safer than plain str

```python
# Without Literal — any string accepted
direction: str  # "BUY", "SELL", "HOLD", or "banana" ← not good

# With Literal — only these values accepted
Direction = Literal["BUY", "SELL", "HOLD"]
direction: Direction  # "banana" → 422 validation error
```

In OpenAPI docs, Literal types show as dropdowns.
Users can only choose from the valid options.

---

## ChartBarResponse — API adapts to frontend needs

```python
class ChartBarResponse(BaseModel):
    time: int    # Unix timestamp ← Lightweight Charts needs this format
    open: float
    high: float
    low: float
    close: float
    volume: float
```

The DB stores `timestamp: DateTime(timezone=True)`.
The Lightweight Charts library needs `time: int` (Unix seconds).

The schema converts between them:
```python
@classmethod
def from_price_bar(cls, bar) -> "ChartBarResponse":
    return cls(
        time=int(bar.timestamp.timestamp()),  # datetime → unix int
        ...
    )
```

The route handler calls `ChartBarResponse.from_price_bar(bar)`
and the frontend gets exactly what it expects.
The DB schema stays clean. The API schema adapts.

---

## Schemas folder structure after Day 18

```
backend/app/schemas/
├── __init__.py     ← re-exports all schemas
├── common.py       ← PaginatedResponse, SuccessResponse, ErrorResponse
├── price.py        ← PriceBarResponse, ChartBarResponse, CSVUploadResponse
├── signal.py       ← SignalResponse, SignalListItem, SignalFilterParams
└── backtest.py     ← BacktestResultResponse, OnDemandBacktestRequest
```

---

## Tomorrow — Day 19
Async MongoDB connection — writing to and reading from
the `indicators` and `chart_patterns` collections.
The data pipeline will store indicator results in MongoDB
and we need to be able to query them from the API.
