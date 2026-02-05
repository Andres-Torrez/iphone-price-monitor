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

At the end of this step, the project transitions from a demo to a production-ready data pipeline.

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

## 📂 Files and code (Step 3)

---

### `scraper/models.py`

**Purpose:**  
Defines the canonical data model used across the entire pipeline.

```python
from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl

class ProductSnapshot(BaseModel):
    timestamp: datetime
    source: str = Field(default="github_pages_catalog")
    model: str
    title: str
    sku: str | None = None
    currency: str = "EUR"
    price_eur: float
    product_url: HttpUrl
    image_url: HttpUrl
```

---

### `scraper/http_client.py`

**Purpose:**  
Centralized HTTP layer for downloading HTML pages.

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

### `scraper/sources/base.py`

**Purpose:**  
Defines the source adapter contract.

```python
from abc import ABC, abstractmethod
from scraper.models import ProductSnapshot

class Source(ABC):
    @abstractmethod
    def fetch(self) -> list[ProductSnapshot]:
        pass
```

---

### `scraper/pipeline/normalize.py`

**Purpose:**  
Normalizes European price strings into floats.

```python
def parse_price_eur(text: str) -> float:
    cleaned = text.replace("€", "").replace("\xa0", "").strip()
    cleaned = cleaned.replace(".", "").replace(",", ".")
    return float(cleaned)
```

---

### `scraper/sources/github_pages_catalog.py`

**Purpose:**  
Implements the real scraper for the GitHub Pages catalog.

```python
from datetime import datetime, timezone
from urllib.parse import urljoin
from selectolax.parser import HTMLParser
from scraper.http_client import get_html
from scraper.pipeline.normalize import parse_price_eur
from scraper.models import ProductSnapshot
from scraper.sources.base import Source

class GitHubPagesCatalogSource(Source):
    def __init__(self, base_url: str):
        self.base_url = base_url if base_url.endswith("/") else base_url + "/"

    def fetch(self) -> list[ProductSnapshot]:
        paths = ["iphone-15.html", "iphone-16.html", "iphone-17.html"]
        now = datetime.now(timezone.utc)
        results = []

        for path in paths:
            url = urljoin(self.base_url, path)
            tree = HTMLParser(get_html(url))

            results.append(
                ProductSnapshot(
                    timestamp=now,
                    model=tree.css_first('[data-testid="product-model"]').text(),
                    title=tree.css_first('[data-testid="product-title"]').text(),
                    price_eur=parse_price_eur(
                        tree.css_first('[data-testid="product-price"]').text()
                    ),
                    sku=tree.css_first('[data-testid="product-sku"]').text(),
                    product_url=url,
                    image_url=urljoin(
                        self.base_url,
                        tree.css_first('[data-testid="product-image"]').attributes["src"],
                    ),
                )
            )
        return results
```

---

### `scraper/pipeline/dedupe.py`

**Purpose:**  
Removes duplicate snapshots from the historical dataset.

```python
from scraper.models import ProductSnapshot

def dedupe_snapshots(rows: list[ProductSnapshot]) -> list[ProductSnapshot]:
    seen = set()
    output = []

    for r in rows:
        key = (r.timestamp.isoformat(), r.model, r.price_eur)
        if key not in seen:
            seen.add(key)
            output.append(r)

    return sorted(output, key=lambda x: (x.timestamp, x.model))
```

---

### `scraper/storage/json_store.py`

**Purpose:**  
JSON persistence layer (source of truth).

```python
from pathlib import Path
import json

def read_json_if_exists(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return json.loads(path.read_text())

def write_json(path: Path, data: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))
```

---

### `scraper/storage/csv_store.py`

**Purpose:**  
CSV export for easy inspection and analysis.

```python
import csv
from pathlib import Path

def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
```

---

### `scraper/pipeline/run.py`

**Purpose:**  
Orchestrates the full scraping pipeline.

```python
from pathlib import Path
from scraper.sources.github_pages_catalog import GitHubPagesCatalogSource
from scraper.pipeline.dedupe import dedupe_snapshots
from scraper.storage.json_store import read_json_if_exists, write_json
from scraper.storage.csv_store import write_csv

def run_pipeline(base_url: str, out_json: Path, out_csv: Path):
    source = GitHubPagesCatalogSource(base_url)
    new_data = [s.model_dump() for s in source.fetch()]
    existing = read_json_if_exists(out_json)
    combined = dedupe_snapshots(existing + new_data)

    write_json(out_json, combined)
    write_csv(out_csv, combined)
```

---

### `scraper/cli.py`

**Purpose:**  
Command-line interface for reproducible execution.

```python
import argparse
from pathlib import Path
from scraper.pipeline.run import run_pipeline

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("run", nargs="?")
    args = parser.parse_args()

    run_pipeline(
        "https://andres-torrez.github.io/iphone-catalog/",
        Path("data/processed/prices.json"),
        Path("data/processed/prices.csv"),
    )

if __name__ == "__main__":
    main()
```

---

## 🧪 Tests

Tests validate price normalization and deduplication to ensure data integrity over time.

---

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