# 🟦 Step 4 — Download & Cache Product Images Locally (Issue #5)

## 🎯 Goal

In this step, we add a **media pipeline layer** to:

- Download the product image from `image_url`
- Save it locally under `assets/images/`
- Reuse (cache) the image if it already exists (avoid repeated downloads)
- Add a new field to the dataset:
  - `image_path` → local path later used by the HTML dashboard

### ✅ Expected outcome

- The scraper no longer depends on external resources to display images  
- The final dashboard can render images **offline** (from the repo)

---

## ⚙️ Expected output

After running:

```bash
uv run python -m scraper.cli run
```

You should now have, in addition to:

```
data/processed/prices.csv
data/processed/prices.json
```

The following cached images:

```
assets/images/iphone_15.png
assets/images/iphone_16.png
assets/images/iphone_17.png
```

And the JSON/CSV will now include:

```
image_path
```

---

## 📂 Files modified in this step

### `scraper/media/images.py`

**What it does:**

- Downloads images using `httpx`
- Generates a stable filename per model (cache key)
- Returns the local path (`image_path`)
- Includes retries + exponential backoff to avoid Windows network errors (WinError 10054)

---

### `scraper/models.py`

**What it does:**

- Adds the `image_path` field to the `ProductSnapshot` model

---

### `scraper/pipeline/run.py`

**What it does:**

- After scraping, downloads/caches images
- Enriches each snapshot with `image_path`
- Continues the usual flow: merge + dedupe + export CSV/JSON

---

### `scraper/storage/csv_store.py`

**What it does:**

- Adds `image_path` to the exported CSV columns

---

### `scraper/http_client.py` (required improvement)

**What it does:**

- Adds retries/backoff for HTML downloads due to WinError 10054 on Windows

---

# ✅ Full Code (Step 4)

---

## 1) `scraper/models.py` (add `image_path`)

```python
from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl


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

    # NEW (Step 4): local cached image path
    image_path: str | None = None
```

---

## 2) `scraper/media/images.py` (new, robust version)

```python
from __future__ import annotations

from pathlib import Path
import re
import time
import random

import httpx


def _safe_filename(name: str) -> str:
    """
    Convert model name like 'iphone_15' to 'iphone_15.png' (safe)
    """
    name = name.strip().lower()
    name = re.sub(r"[^a-z0-9_\-]+", "-", name)
    return f"{name}.png"


def download_image(url: str, out_path: Path, timeout_s: float = 30.0, retries: int = 4) -> None:
    """
    Robust image download with retries + exponential backoff.
    Helps avoid intermittent WinError 10054 / TLS resets on Windows networks.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)

    headers = {
        "User-Agent": "iphone-price-monitor/1.0 (+https://github.com/your-handle)",
        "Accept": "image/*",
    }

    last_exc: Exception | None = None

    for attempt in range(retries + 1):
        try:
            with httpx.Client(
                headers=headers,
                timeout=timeout_s,
                follow_redirects=True,
                http1=True,
                http2=False,
            ) as client:
                r = client.get(url)
                r.raise_for_status()
                out_path.write_bytes(r.content)
                return

        except (
            httpx.ConnectError,
            httpx.ReadError,
            httpx.RemoteProtocolError,
            httpx.ReadTimeout,
        ) as exc:
            last_exc = exc
            if attempt >= retries:
                break

            sleep_s = (2 ** attempt) * 0.6 + random.random() * 0.4
            time.sleep(sleep_s)

    raise RuntimeError(f"Failed to download image after {retries} retries: {url}") from last_exc


def ensure_cached_image(image_url: str, model: str, images_dir: Path) -> Path:
    """
    Returns local path for an image. Downloads only if file does not exist.
    """
    filename = _safe_filename(model)
    target = images_dir / filename

    if target.exists() and target.stat().st_size > 0:
        return target

    download_image(image_url, target)
    return target
```

---

## 3) `scraper/storage/csv_store.py` (add `image_path` column)

Update `CSV_COLUMNS`:

```python
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
    "image_path",  # NEW
]
```

The rest of the file stays the same.

---

## 4) `scraper/pipeline/run.py` (enrich with `image_path`)

```python
from __future__ import annotations

from pathlib import Path

from scraper.models import ProductSnapshot
from scraper.pipeline.dedupe import dedupe_snapshots
from scraper.sources.github_pages_catalog import GitHubPagesCatalogSource
from scraper.storage.csv_store import write_csv
from scraper.storage.json_store import read_json_if_exists, write_json
from scraper.media.images import ensure_cached_image  # IMPORTANT import


def _dict_to_snapshot(d: dict) -> ProductSnapshot:
    return ProductSnapshot.model_validate(d)


def run_pipeline(
    base_url: str,
    out_csv: Path,
    out_json: Path,
    images_dir: Path,
) -> list[ProductSnapshot]:
    src = GitHubPagesCatalogSource(base_url=base_url)
    new_rows = src.fetch()

    # Step 4: cache images and add image_path
    enriched_new_rows: list[ProductSnapshot] = []
    for s in new_rows:
        local_img = ensure_cached_image(str(s.image_url), s.model, images_dir)
        enriched_new_rows.append(s.model_copy(update={"image_path": str(local_img)}))

    existing_dicts = read_json_if_exists(out_json)
    existing_rows = [_dict_to_snapshot(d) for d in existing_dicts]

    combined = existing_rows + enriched_new_rows
    combined = dedupe_snapshots(combined)

    write_json(out_json, combined)
    write_csv(out_csv, combined)

    return combined
```

---

## 5) `scraper/cli.py` (pass `images_dir`)

Define default:

```python
DEFAULT_IMAGES_DIR = Path("assets/images")
```

Add to parser:

```python
p_run.add_argument("--images-dir", default=str(DEFAULT_IMAGES_DIR))
```

Ensure the command signature:

```python
def cmd_run(base_url: str, out_csv: Path, out_json: Path, images_dir: Path) -> None:
    combined = run_pipeline(
        base_url=base_url,
        out_csv=out_csv,
        out_json=out_json,
        images_dir=images_dir,
    )

    print(f"[ok] stored snapshots: {len(combined)}")
    print(f"[ok] csv:  {out_csv}")
    print(f"[ok] json: {out_json}")
    print(f"[ok] images cached in: {images_dir}")
```

Dispatcher:

```python
elif args.command == "run":
    cmd_run(
        base_url=args.base_url,
        out_csv=Path(args.out_csv),
        out_json=Path(args.out_json),
        images_dir=Path(args.images_dir),
    )
```

---

# ▶️ Run Step 4

```bash
uv run python -m scraper.cli run
```

Verify images:

```bash
ls -la assets/images/
```

Verify `image_path` in JSON:

```bash
cat data/processed/prices.json
```

---

# 🧪 Real Debugging (errors found and how they were fixed)

### **Error 1 — `images_dir` not recognized**

**Symptom:**

```
TypeError: cmd_run() got an unexpected keyword argument 'images_dir'
```

**Cause:**

- `images_dir` was added in the CLI call  
- But the function signature of `cmd_run()` did not include it

**Fix:**

- Add `images_dir: Path` to `cmd_run()`
- Add `--images-dir` to the parser
- Pass `Path(args.images_dir)` in the dispatcher

---

### **Error 2 — WinError 10054 (TLS reset)**

**Symptom:**

```
httpx.ConnectError: [WinError 10054] connection forcibly closed by remote host
```

**Cause:**

- Common TLS interruptions on Windows (proxy/antivirus/network)
- Intermittent HTTPS resets when downloading from GitHub Pages

**Fix:**

- Added retries + exponential backoff
- Forced `http1=True` and `http2=False`
- Applied to both HTML and image downloads

---

### **Error 3 — `ensure_cached_image` not defined**

**Symptom:**

```
NameError: name 'ensure_cached_image' is not defined
```

**Cause:**

- `ensure_cached_image()` was used in `run.py`
- But the import was missing

**Fix:**

```python
from scraper.media.images import ensure_cached_image
```

---

# ✅ What Step 4 accomplishes

After completing this step, the project now:

- ✔️ Downloads product images from `image_url`  
- ✔️ Caches images locally (no re-download if already present)  
- ✔️ Adds `image_path` to the dataset (CSV/JSON)  
- ✔️ Is more robust on Windows (retries/backoff)  
- ✔️ Prepares the project for the final HTML dashboard (Step 5/6)

---

Si quieres, puedo traducir también el Step 3, Step 2, Step 1 o ayudarte a unificar todo el README en un formato profesional.

---