# 🟦 Step 3 — Implement the real scraper and persist historical data (Issue #4)

## 🎯 Goal

In this step, we transform the project from a scaffold into a **real, modular, reproducible data pipeline**.

The scraper now:

- Collects product information from a scraping‑safe website  
  👉 https://andres-torrez.github.io/iphone-catalog/
- Monitors:
  - iPhone 15  
  - iPhone 16  
  - iPhone 17
- Extracts structured fields:
  - product title  
  - model identifier  
  - price (EUR)  
  - SKU  
  - product URL  
  - direct image URL
- Normalizes European price formats
- Maintains a **historical dataset**
- Exports data to:
  - JSON → source of truth  
  - CSV → Excel / Google Sheets friendly
- Introduces automated tests for data integrity

### ✅ After this step, the project becomes production‑style rather than a demo.

---

## 🧠 Architecture introduced

```
HTML Source
↓
Normalization
↓
Deduplication
↓
JSON / CSV Storage
```

Each responsibility is isolated, testable, and replaceable.

---

## ⚙️ Project configuration

To support reproducibility and development tooling, we added the following to `pyproject.toml`:

```toml
[project.optional-dependencies]
dev = ["pytest", "ruff"]

[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[tool.setuptools]
packages = ["scraper"]
```

### Why this matters

- Defines explicit development dependencies  
- Enables editable installs  
- Makes the package importable  
- Improves portability for other developers  

---

## 📦 Installation & execution

Install dependencies:

```bash
uv sync
uv pip install -e .
```

Run the pipeline:

```bash
uv run python -m scraper.cli run
```

Run tests:

```bash
uv run pytest -q
```

---

## 📂 Files introduced in Step 3

Each file below includes:

- Purpose  
- Path  
- Code (unchanged)

---

# 1) `scraper/storage/csv_store.py`

**Purpose:**  
Exports historical data using a fixed schema, making results stable and spreadsheet‑friendly.

```python
from __future__ import annotations

from pathlib import Path
import csv

from scraper.models import ProductSnapshot

CSV_COLUMNS = [
    "timestamp",
    "source",
    "model",
    "title",
    "sku",
    "currency",
    "price_eur",
    "product_url",
    "image_url",
]

def write_csv(path: Path, rows: list[ProductSnapshot]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        w.writeheader()
        for r in rows:
            d = r.model_dump(mode="json")
            w.writerow({k: d.get(k) for k in CSV_COLUMNS})
```

---

# 2) `scraper/http_client.py`

**Purpose:**  
Provides controlled, reproducible HTML downloads with headers and timeout.

```python
from __future__ import annotations
import httpx

def get_html(url: str, timeout_s: float = 20.0) -> str:
    headers = {
        "User-Agent": "iphone-price-monitor/1.0",
        "Accept": "text/html",
    }
    with httpx.Client(headers=headers, timeout=timeout_s) as client:
        r = client.get(url)
        r.raise_for_status()
        return r.text
```

---

# 3) `scraper/pipeline/dedupe.py`

**Purpose:**  
Removes duplicate entries based on (timestamp, source, model, price).

```python
from __future__ import annotations

from scraper.models import ProductSnapshot

def dedupe_snapshots(rows: list[ProductSnapshot]) -> list[ProductSnapshot]:
    """
    Remove duplicates by (timestamp, source, model, price_eur).
    """
    seen: set[tuple] = set()
    out: list[ProductSnapshot] = []

    for r in rows:
        key = (r.timestamp.isoformat(), r.source, r.model, r.price_eur)
        if key in seen:
            continue
        seen.add(key)
        out.append(r)

    out.sort(key=lambda x: (x.timestamp, x.model))
    return out
```

---

# 4) `scraper/pipeline/run.py`

**Purpose:**  
Orchestrates the pipeline:

```
fetch → merge history → dedupe → export
```

```python
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from scraper.models import ProductSnapshot
from scraper.pipeline.dedupe import dedupe_snapshots
from scraper.sources.github_pages_catalog import GitHubPagesCatalogSource
from scraper.storage.csv_store import write_csv
from scraper.storage.json_store import read_json_if_exists, write_json

def _dict_to_snapshot(d: dict) -> ProductSnapshot:
    return ProductSnapshot.model_validate(d)

def run_pipeline(
    base_url: str,
    out_csv: Path,
    out_json: Path,
) -> list[ProductSnapshot]:
    src = GitHubPagesCatalogSource(base_url=base_url)
    new_rows = src.fetch()

    existing_dicts = read_json_if_exists(out_json)
    existing_rows = [_dict_to_snapshot(d) for d in existing_dicts]

    combined = existing_rows + new_rows
    combined = dedupe_snapshots(combined)

    write_json(out_json, combined)
    write_csv(out_csv, combined)

    return combined
```

---

# 5) `scraper/cli.py`

**Purpose:**  
Provides user‑friendly entrypoints to run scraping and persistence.

```python
from __future__ import annotations

import argparse
import json
from pathlib import Path
from datetime import datetime, timezone

from scraper.pipeline.run import run_pipeline
from scraper.sources.github_pages_catalog import GitHubPagesCatalogSource

DEFAULT_BASE_URL = "https://andres-torrez.github.io/iphone-catalog/"
DEFAULT_CSV = Path("data/processed/prices.csv")
DEFAULT_JSON = Path("data/processed/prices.json")

def cmd_healthcheck() -> None:
    now = datetime.now(timezone.utc).isoformat()
    print(f"[ok] scraper CLI is working | utc={now}")

def cmd_scrape(base_url: str) -> None:
    src = GitHubPagesCatalogSource(base_url=base_url)
    snapshots = src.fetch()
    payload = [s.model_dump(mode="json") for s in snapshots]
    print(json.dumps(payload, ensure_ascii=False, indent=2))

def cmd_run(base_url: str, out_csv: Path, out_json: Path) -> None:
    combined = run_pipeline(base_url=base_url, out_csv=out_csv, out_json=out_json)

    print(f"[ok] stored snapshots: {len(combined)}")
    print(f"[ok] csv:  {out_csv}")
    print(f"[ok] json: {out_json}")

def main() -> None:
    parser = argparse.ArgumentParser(prog="scraper", description="iPhone Price Monitor CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("healthcheck", help="Validate the CLI runs")

    p_scrape = sub.add_parser("scrape", help="Scrape product snapshots and print JSON")
    p_scrape.add_argument("--base-url", default=DEFAULT_BASE_URL)

    p_run = sub.add_parser("run", help="Scrape + store history (CSV/JSON)")
    p_run.add_argument("--base-url", default=DEFAULT_BASE_URL)
    p_run.add_argument("--out-csv", default=str(DEFAULT_CSV))
    p_run.add_argument("--out-json", default=str(DEFAULT_JSON))

    args = parser.parse_args()

    if args.command == "healthcheck":
        cmd_healthcheck()
    elif args.command == "scrape":
        cmd_scrape(base_url=args.base_url)
    elif args.command == "run":
        cmd_run(
            base_url=args.base_url,
            out_csv=Path(args.out_csv),
            out_json=Path(args.out_json),
        )
    else:
        raise SystemExit("Unknown command")

if __name__ == "__main__":
    main()
```

---

## ▶️ Run the pipeline

```bash
uv run python -m scraper.cli run
```

After execution, you should see:

```
data/processed/prices.csv
data/processed/prices.json
```

---

# 🧪 Tests introduced

These tests ensure the pipeline can evolve safely.

---

## `tests/test_normalize.py`

Validates European price parsing.

```python
from scraper.pipeline.normalize import parse_price_eur

def test_parse_price_eur_comma() -> None:
    assert parse_price_eur("799,00 €") == 799.00

def test_parse_price_eur_no_decimals() -> None:
    assert parse_price_eur("999 €") == 999.0
```

---

## `tests/test_dedupe.py`

Validates deduplication logic.

```python
from datetime import datetime, timezone

from scraper.models import ProductSnapshot
from scraper.pipeline.dedupe import dedupe_snapshots


def test_dedupe_by_key() -> None:
    ts = datetime(2026, 2, 5, tzinfo=timezone.utc)
    a = ProductSnapshot(
        timestamp=ts,
        model="iphone_15",
        title="iPhone 15",
        sku="X",
        price_eur=799.0,
        product_url="https://example.com/a",
        image_url="https://example.com/a.png",
    )
    b = ProductSnapshot(
        timestamp=ts,
        model="iphone_15",
        title="iPhone 15",
        sku="X",
        price_eur=799.0,
        product_url="https://example.com/a",
        image_url="https://example.com/a.png",
    )
    out = dedupe_snapshots([a, b])
    assert len(out) == 1
```


Run tests:

```bash
uv run pytest -q
```

---

# ✅ What was achieved in Step 3

By completing this step, the project now:

- ✔ Scrapes real product data  
- ✔ Uses a clean, extensible architecture  
- ✔ Maintains historical information  
- ✔ Exports CSV and JSON  
- ✔ Includes automated tests  
- ✔ Runs with a single command  
- ✔ Is ready for media caching and reporting  
