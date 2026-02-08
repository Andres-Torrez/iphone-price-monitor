# 🟦 Step 2 — Implement Source Adapter (GitHub Pages Catalog) (Issue #3)

## 🎯 Goal

In this step, we implement the **first real data source** using a controlled, stable, scraping‑safe website.

We scrape three product pages:

- `/iphone-15.html`
- `/iphone-16.html`
- `/iphone-17.html`

Each page exposes predictable `data-testid` selectors:

- `product-title`
- `product-price`
- `product-image`
- `product-model`
- `product-sku`

The objective is to produce **normalized, typed snapshots** ready for storage in the next step.

---

## 🧠 Architecture introduced

We apply a **Source Adapter pattern**:

```
Source Adapter
↓
Normalized ProductSnapshot list
↓
(next steps → storage & reporting)
```

### Why this matters

- New shops can be added later  
- The pipeline remains unchanged  
- Each source is isolated, testable, and maintainable  

---

## ⚙️ Expected output

After running:

```bash
uv run python -m scraper.cli scrape
```

You should obtain a JSON list with one snapshot per model containing:

- title  
- price in EUR (float)  
- SKU  
- product URL  
- image URL  
- timestamp  
- model identifier  

No files are written yet — this step only validates extraction.

---

## 📂 Files introduced in Step 2

Each file below includes:

- Purpose  
- Path  
- Code (unchanged)

---

# 1) `scraper/models.py`

**Purpose:**  
Defines a typed schema for scraped data using Pydantic.  
This ensures validation, consistency, and predictable structure across the pipeline.

```python
from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, HttpUrl, Field


class ProductSnapshot(BaseModel):
    timestamp: datetime
    source: str = Field(default="github_pages_catalog")
    model: str  # iphone_15 | iphone_16 | iphone_17
    title: str
    sku: str | None = None
    currency: str = "EUR"
    price_eur: float
    product_url: HttpUrl
    image_url: HttpUrl
```

---

# 2) `scraper/http_client.py`

**Purpose:**  
Handles HTML downloads with a defined User‑Agent and timeout.

```python
from __future__ import annotations

import httpx


def get_html(url: str, timeout_s: float = 20.0) -> str:
    headers = {
        "User-Agent": "iphone-price-monitor/1.0 (+https://github.com/your-handle)",
        "Accept": "text/html,application/xhtml+xml",
    }
    with httpx.Client(headers=headers, timeout=timeout_s, follow_redirects=True) as client:
        r = client.get(url)
        r.raise_for_status()
        return r.text
```

---

# 3) `scraper/pipeline/normalize.py`

**Purpose:**  
Converts European price strings into numeric floats.

```python
from __future__ import annotations


def parse_price_eur(text: str) -> float:
    """
    Convert strings like '799,00 €' or '799 €' into float 799.00
    """
    cleaned = (
        text.replace("€", "")
        .replace("\xa0", " ")
        .strip()
    )
    cleaned = cleaned.replace(".", "").replace(",", ".")
    cleaned = "".join(ch for ch in cleaned if ch.isdigit() or ch == ".")
    if not cleaned:
        raise ValueError(f"Could not parse price from: {text!r}")
    return float(cleaned)
```

---

# 4) `scraper/sources/base.py`

**Purpose:**  
Defines the interface every source adapter must implement.

```python
from __future__ import annotations

from abc import ABC, abstractmethod

from scraper.models import ProductSnapshot


class Source(ABC):
    @abstractmethod
    def fetch(self) -> list[ProductSnapshot]:
        """Return a list of snapshots (one per product/model)."""
        raise NotImplementedError
```

---

# 5) `scraper/sources/github_pages_catalog.py`

**Purpose:**  
Implements the adapter that extracts data from the GitHub Pages catalog.

```python
from __future__ import annotations

from datetime import datetime, timezone
from urllib.parse import urljoin

from selectolax.parser import HTMLParser

from scraper.http_client import get_html
from scraper.models import ProductSnapshot
from scraper.pipeline.normalize import parse_price_eur
from scraper.sources.base import Source


class GitHubPagesCatalogSource(Source):
    def __init__(self, base_url: str) -> None:
        # base_url example: "https://andres-torrez.github.io/iphone-catalog/"
        self.base_url = base_url if base_url.endswith("/") else base_url + "/"

    def fetch(self) -> list[ProductSnapshot]:
        product_paths = ["iphone-15.html", "iphone-16.html", "iphone-17.html"]
        out: list[ProductSnapshot] = []
        now = datetime.now(timezone.utc)

        for path in product_paths:
            product_url = urljoin(self.base_url, path)
            html = get_html(product_url)
            tree = HTMLParser(html)

            title = self._text(tree, '[data-testid="product-title"]')
            model = self._text(tree, '[data-testid="product-model"]')
            price_text = self._text(tree, '[data-testid="product-price"]')
            sku = self._text_optional(tree, '[data-testid="product-sku"]')

            img_src = self._attr(tree, '[data-testid="product-image"]', "src")
            image_url = urljoin(self.base_url, img_src)

            price_eur = parse_price_eur(price_text)

            out.append(
                ProductSnapshot(
                    timestamp=now,
                    model=model,
                    title=title,
                    sku=sku,
                    price_eur=price_eur,
                    product_url=product_url,
                    image_url=image_url,
                )
            )

        return out

    @staticmethod
    def _text(tree: HTMLParser, css: str) -> str:
        node = tree.css_first(css)
        if node is None:
            raise ValueError(f"Missing required element: {css}")
        return node.text(strip=True)

    @staticmethod
    def _text_optional(tree: HTMLParser, css: str) -> str | None:
        node = tree.css_first(css)
        return node.text(strip=True) if node else None

    @staticmethod
    def _attr(tree: HTMLParser, css: str, attr: str) -> str:
        node = tree.css_first(css)
        if node is None:
            raise ValueError(f"Missing required element: {css}")
        val = node.attributes.get(attr)
        if not val:
            raise ValueError(f"Missing attribute {attr!r} in {css}")
        return val
```


---

# 6) `scraper/cli.py`

**Purpose:**  
Adds commands to validate scraping independently from storage.

```python
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone

from scraper.sources.github_pages_catalog import GitHubPagesCatalogSource


def cmd_healthcheck() -> None:
    now = datetime.now(timezone.utc).isoformat()
    print(f"[ok] scraper CLI is working | utc={now}")


def cmd_scrape(base_url: str) -> None:
    src = GitHubPagesCatalogSource(base_url=base_url)
    snapshots = src.fetch()
    payload = [s.model_dump(mode="json") for s in snapshots]
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(prog="scraper", description="iPhone Price Monitor CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("healthcheck", help="Validate the CLI runs")

    p_scrape = sub.add_parser("scrape", help="Scrape product snapshots from the configured source")
    p_scrape.add_argument(
        "--base-url",
        default="https://andres-torrez.github.io/iphone-catalog/",
        help="Base URL of the catalog site (must end with / or will be normalized).",
    )

    args = parser.parse_args()

    if args.command == "healthcheck":
        cmd_healthcheck()
    elif args.command == "scrape":
        cmd_scrape(base_url=args.base_url)
    else:
        raise SystemExit("Unknown command")


if __name__ == "__main__":
    main()
```


---

# ▶️ Run Step 2

```bash
uv run python -m scraper.cli scrape
```

---

## ✅ Expected result

You should see a JSON array with three objects:

- `iphone_15`
- `iphone_16`
- `iphone_17`

Each containing:

- title  
- price_eur  
- image_url  
- sku  
- model  
- timestamp  

---

# 🧪 Validation philosophy

At this stage we verify:

- selectors work  
- parsing works  
- normalization works  
- the schema is correct  

We intentionally **do not store anything yet**.  
Persistence comes in **Step 3**.

---

# ✅ What was achieved in Step 2

By completing this step, the project now has:

- ✔ A working modular source adapter  
- ✔ A typed data contract  
- ✔ Price normalization  
- ✔ A CLI command to validate scraping  
- ✔ A solid foundation for historical storage  


Si quieres, sigo con Step 1 o preparo un README final unificado y profesional.
