# 🟦6 — Add Automated Tests for Normalization and Deduplication (Issue #7)

## 🎯 Goal

Now that the pipeline can:

- scrape  
- normalize  
- merge with history  
- deduplicate  
- store  
- cache images  
- generate reports  

…it’s time to ensure future changes **do not silently break data integrity**.

This milestone introduces automated validation using `pytest`.

We focus on the two most critical transformations:

1. Price normalization  
2. Snapshot deduplication  

If either of these breaks → historical data becomes unreliable.

---

## 🧠 Why tests at this stage?

**Before:**  
We trusted the logic manually.

**After:**  
The system verifies itself every time the test suite or CI runs.

This enables:

- safe refactoring  
- confident feature additions  
- easier collaboration  
- a professional engineering workflow  

---

## 📂 Files added in this milestone

```
tests/
├── test_normalize.py
└── test_dedupe.py
```

No production code is modified.

---

# 6.1 — Test price normalization

## What we verify

European price formats must be converted into deterministic floats.

Examples:

| Input           | Output   |
|----------------|----------|
| `799,00 €`     | `799.0`  |
| `999 €`        | `999.0`  |
| `1.099,99 €`   | `1099.99`|
| NBSP values    | parsed correctly |
| invalid values | raise error |

---

## `tests/test_normalize.py`

```python
from scraper.pipeline.normalize import parse_price_eur


def test_parse_price_eur_comma_decimals() -> None:
    assert parse_price_eur("799,00 €") == 799.00


def test_parse_price_eur_no_decimals() -> None:
    assert parse_price_eur("999 €") == 999.0


def test_parse_price_eur_thousands_separator() -> None:
    assert parse_price_eur("1.099,99 €") == 1099.99


def test_parse_price_eur_nbsp() -> None:
    assert parse_price_eur("799,00\xa0€") == 799.00


def test_parse_price_eur_invalid() -> None:
    try:
        parse_price_eur("free")
        raise AssertionError("Expected ValueError")
    except ValueError:
        pass
```

---

# 6.2 — Test snapshot deduplication

## What we verify

The deduplication layer must:

- remove exact duplicates  
- keep rows when the price changes  
- return a stable ordering  

If this logic breaks, historical analytics become corrupted.

---

## `tests/test_dedupe.py`

```python
from datetime import datetime, timezone

from scraper.models import ProductSnapshot
from scraper.pipeline.dedupe import dedupe_snapshots


def _snap(ts: datetime, model: str, price: float) -> ProductSnapshot:
    return ProductSnapshot(
        timestamp=ts,
        model=model,
        title=f"{model}",
        sku="X",
        price_eur=price,
        product_url="https://example.com/a",
        image_url="https://example.com/a.png",
    )


def test_dedupe_removes_exact_duplicates() -> None:
    ts = datetime(2026, 2, 5, tzinfo=timezone.utc)
    a = _snap(ts, "iphone_15", 799.0)
    b = _snap(ts, "iphone_15", 799.0)
    out = dedupe_snapshots([a, b])
    assert len(out) == 1


def test_dedupe_keeps_price_changes() -> None:
    ts = datetime(2026, 2, 5, tzinfo=timezone.utc)
    a = _snap(ts, "iphone_15", 799.0)
    b = _snap(ts, "iphone_15", 749.0)
    out = dedupe_snapshots([a, b])
    assert len(out) == 2


def test_dedupe_is_stably_sorted() -> None:
    ts1 = datetime(2026, 2, 5, tzinfo=timezone.utc)
    ts2 = datetime(2026, 2, 6, tzinfo=timezone.utc)

    rows = [
        _snap(ts2, "iphone_16", 999.0),
        _snap(ts1, "iphone_17", 1099.0),
        _snap(ts1, "iphone_15", 799.0),
    ]
    out = dedupe_snapshots(rows)

    assert [r.model for r in out] == ["iphone_15", "iphone_17", "iphone_16"]
```

---

## ▶️ Run the tests

```bash
uv run pytest -q
```

Expected result:

```
✓ all tests passed
```

---

## 🧪 When should tests be executed?

- before pushing  
- inside CI  
- after refactoring  
- when adding new sources  

---

## ✅ What we achieved

By completing this milestone:

- ✔ critical transformations are validated  
- ✔ regressions are detected early  
- ✔ refactoring becomes safer  
- ✔ contributors understand expected behavior  
- ✔ the project moves closer to production standards  
