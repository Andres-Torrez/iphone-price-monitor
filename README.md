Perfecto, Andrés. Aquí tienes **todo lo que me pasaste**, convertido **a Markdown limpio, ordenado y profesional**, siguiendo **exactamente el estilo** que quieres (como tu ejemplo anterior), **sin modificar nada del contenido**, solo dándole estructura, secciones, bloques de código y separación visual.

Listo para pegar directamente en tu README.

---

# ✅ Step 2 — Implement Source Adapter (GitHub Pages Catalog)

## Objective

Implement the first real scraping source using a controlled website that is stable and scraping-safe.

We will scrape 3 product pages:

- `/iphone-15.html`  
- `/iphone-16.html`  
- `/iphone-17.html`

Each page contains stable `data-testid` selectors:

- `product-title`  
- `product-price`  
- `product-image`  
- `product-model`  
- `product-sku`

---

## Architecture introduced in this step

We use a **Source Adapter** pattern:

```
Source Adapter → normalized ProductSnapshot list → (next steps: storage/report)
```

This allows adding new websites later without rewriting the pipeline.

---

## 2.1 Data model

**File:** `scraper/models.py`  
**What it does:** defines a typed structure for scraped data using Pydantic.

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

## 2.2 HTTP client

**File:** `scraper/http_client.py`  
**What it does:** downloads HTML with a stable User-Agent and reasonable timeout.

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

## 2.3 Normalization (price parsing)

**File:** `scraper/pipeline/normalize.py`  
**What it does:** converts strings like `799,00 €` into `799.00` float.

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
    # remove thousand separators if any, and normalize decimal comma to dot
    cleaned = cleaned.replace(".", "").replace(",", ".")
    # keep only digits and dot
    cleaned = "".join(ch for ch in cleaned if ch.isdigit() or ch == ".")
    if not cleaned:
        raise ValueError(f"Could not parse price from: {text!r}")
    return float(cleaned)
```

---

## 2.4 Source contract

**File:** `scraper/sources/base.py`  
**What it does:** defines a common interface for all sources (adapters).

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

## 2.5 GitHub Pages adapter implementation

**File:** `scraper/sources/github_pages_catalog.py`  
**What it does:** fetches each product page, extracts title/price/image/model/sku and returns normalized snapshots.

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

## 2.6 CLI command to validate scraping

**File:** `scraper/cli.py`  
**What it does:** adds a `scrape` command that prints the snapshots to stdout as JSON.

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

## Run

```bash
uv run python -m scraper.cli scrape
```

---

## Expected result

A JSON array with 3 objects (`iphone_15`, `iphone_16`, `iphone_17`), including:

- title  
- price_eur  
- image_url  
- sku  
- model  
- timestamp  

---

## ✅ Result of Step 2

At the end of this step we have:

- A working modular source adapter (`GitHubPagesCatalogSource`)  
- Typed data model (`ProductSnapshot`)  
- Normalization of prices  
- A CLI command that validates scraping output  

**Next step:** persist the snapshots into CSV and JSON as a historical dataset.

---

Si quieres, puedo convertir esto en una **sección completa del README**, añadirlo al índice, o integrarlo con el Paso 1 que ya formateamos.
