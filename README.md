# 🟦 Step 3 — Implement the real scraper and persist historical data

## 🎯 Goal

The goal of this step is to build a real, modular, and reproducible scraper that:

- Scrapes product data from a scraping-safe website  
  https://andres-torrez.github.io/iphone-catalog/
- Monitors the following models:
  - iPhone 15  
  - iPhone 16  
  - iPhone 17
- Extracts structured data:
  - product title  
  - model identifier  
  - price (EUR)  
  - SKU  
  - product URL  
  - direct product image URL
- Normalizes European price formats
- Maintains a historical price dataset
- Exports data to:
  - JSON (source of truth)
  - CSV (Excel / Sheets friendly)
- Includes automated tests to guarantee data quality

At the end of this step, the project transitions from a demo to a production‑ready data pipeline.

---

## ⚙️ Project configuration

To support local development, testing, and reproducibility, the following configuration was added to `pyproject.toml`:

```toml
[project.optional-dependencies]
dev = ["pytest", "ruff"]

[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[tool.setuptools]
packages = ["scraper"]
```

### Why this configuration?

- Defines explicit development dependencies  
- Enables editable installs for local development  
- Ensures the scraper package is correctly discoverable  
- Improves portability and reuse of the project  

---

## 📦 Installation and execution

```bash
uv sync
uv pip install -e .
```

Run the full pipeline:

```bash
uv run python -m scraper.cli run
```

Run tests:

```bash
uv run pytest -q
```

---

## 🧠 Architecture introduced in Step 3

```
HTML Source
   ↓
Normalization
   ↓
Deduplication
   ↓
JSON / CSV Storage
```

Each responsibility is isolated and testable.

---

# 📂 Files and Code (Step 3)

Below is each numbered file, with:

- **Correct file path**  
- **Accurate Purpose summary**  
- **Your original code untouched**

---

## 1) `scraper/storage/csv_store.py`

**Purpose:**  
Writes the historical dataset to CSV using a fixed column schema. Ensures reproducible, Excel‑friendly exports.

**Path:**  
`scraper/storage/csv_store.py`

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

## 2) `scraper/http_client.py`

**Purpose:**  
Provides a stable HTTP client for downloading HTML pages with a custom User‑Agent and timeout.

**Path:**  
`scraper/http_client.py`

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

## 3) `scraper/pipeline/dedupe.py`

**Purpose:**  
Removes duplicate snapshots based on `(timestamp, source, model, price_eur)` and returns a stable, sorted list.

**Path:**  
`scraper/pipeline/dedupe.py`

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

    # stable sort by timestamp then model
    out.sort(key=lambda x: (x.timestamp, x.model))
    return out
```

---

## 4) `scraper/pipeline/run.py`

**Purpose:**  
Runs the full pipeline: fetch → merge with history → dedupe → write JSON + CSV.

**Path:**  
`scraper/pipeline/run.py`

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
    # Pydantic reconstructs the datetime correctly if ISO formatted
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

## 5) `scraper/cli.py` — Add the `run` command

**Purpose:**  
Adds a CLI command that runs the full pipeline and stores historical data.

**Path:**  
`scraper/cli.py`

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

## 6) Run the pipeline and verify files

```bash
uv run python -m scraper.cli run
```

---

# 🧪 Tests

Tests validate price normalization and deduplication to ensure data integrity over time.

---

## 7) `tests/test_normalize.py`

**Purpose:**  
Ensures European price formats are parsed correctly.

**Path:**  
`tests/test_normalize.py`

```python
from scraper.pipeline.normalize import parse_price_eur

def test_parse_price_eur_comma() -> None:
    assert parse_price_eur("799,00 €") == 799.00

def test_parse_price_eur_no_decimals() -> None:
    assert parse_price_eur("999 €") == 999.0
```

---

## `tests/test_dedupe.py`

**Purpose:**  
Ensures duplicate snapshots are removed correctly.

**Path:**  
`tests/test_dedupe.py`

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

---

Run tests:

```bash
uv run pytest -q
```

## ✅ What was achieved in Step 3

By completing this step, the project now:

✔ Scrapes real product data  
✔ Uses a clean, extensible architecture  
✔ Maintains historical price data  
✔ Exports CSV and JSON  
✔ Includes automated tests  
✔ Runs with a single reproducible command  
✔ Is ready for automation, Docker, and reporting  

---
