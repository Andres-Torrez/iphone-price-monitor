# 🟦 Step 1 — Project Setup, Environment & CLI Foundation

# 📱 iPhone Price Monitor

A professional scraping project designed to demonstrate:

- Clean and modular architecture  
- Step‑by‑step reproducible documentation  
- Modern dependency management with `uv`  
- A complete pipeline: scrape → history → HTML report  
- A foundation ready for Docker and automation  

This repository is built as a **portfolio‑grade engineering project**, not a one‑off script.

---

## 🎯 Objective

Track the price evolution of:

- iPhone 15  
- iPhone 16  
- iPhone 17  

Store historical records and later generate a visual HTML dashboard.

Scraping‑safe source (fully controlled):

https://andres-torrez.github.io/iphone-catalog/

---

## 🧭 Roadmap

Progress is divided into milestones managed through the Kanban board.

- ✅ Repository + Kanban + Issues  
- ✅ Environment scaffold  
- ✅ Minimal CLI  
- ⏳ Source adapters  
- ⏳ Historical storage  
- ⏳ Image caching  
- ⏳ HTML report  
- ⏳ Tests & lint  
- ⏳ Docker  
- ⏳ Automation  

---

# 🚀 1 — Initialize development environment

## 1.1 Install uv

Official guide:  
https://docs.astral.sh/uv/

---

## 1.2 Initialize the repository

```bash
uv init
```

---

## 1.3 (Recommended) Pin Python version

Example:

```bash
uv python pin 3.12
```

---

## 1.4 Install runtime and dev dependencies

```bash
uv add httpx selectolax pydantic jinja2
uv add --dev pytest ruff
```

---

# 📁 2 — Create folders and base files

We now create the scalable architecture of the project.

```bash
mkdir -p scraper/sources scraper/storage scraper/report/templates scraper/pipeline scraper/media
mkdir -p data/raw data/processed reports assets/images assets/docs tests .github/workflows
```

Create base files:

```bash
touch scraper/__init__.py scraper/cli.py scraper/config.py scraper/models.py scraper/http_client.py
touch scraper/sources/__init__.py scraper/sources/base.py scraper/sources/github_pages_catalog.py
touch scraper/storage/__init__.py scraper/storage/csv_store.py scraper/storage/json_store.py
touch scraper/report/__init__.py scraper/report/render.py scraper/report/templates/index.html.j2
touch scraper/pipeline/__init__.py scraper/pipeline/run.py scraper/pipeline/normalize.py scraper/pipeline/dedupe.py
touch scraper/media/__init__.py scraper/media/images.py
touch tests/test_normalize.py tests/test_dedupe.py
touch .gitignore
```

---

# ⚙️ 3 — Project configuration (`pyproject.toml`)

After creating the structure, the project is defined by the following configuration.

This is the exact file currently used in the repository:

```toml
[project]
name = "iphone-price-monitor"
version = "0.1.0"
description = "Add your description here"
readme = "README.md"
requires-python = ">=3.13"
dependencies = [
    "httpx>=0.28.1",
    "jinja2>=3.1.6",
    "pydantic>=2.12.5",
    "selectolax>=0.4.6",
]

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP"]

[dependency-groups]
dev = [
    "pytest>=9.0.2",
    "ruff>=0.14.14",
]
```

### Why this configuration matters

- Defines runtime dependencies  
- Defines development tools  
- Allows reproducible environments  
- Makes the project installable  
- Enables editable installs  

---

# 🧪 4 — Implement and validate the CLI

The CLI is the entry point of the application.

At this stage it only verifies that:

- ✔ Python runs  
- ✔ Imports resolve  
- ✔ The project wiring works  

### Current `scraper/cli.py`

```python
from __future__ import annotations

import argparse
from datetime import UTC, datetime


def cmd_healthcheck() -> None:
    now = datetime.now(UTC).isoformat()
    print(f"[ok] scraper CLI is working | utc={now}")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="scraper",
        description="iPhone Price Monitor CLI",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("healthcheck", help="Validate the CLI runs")

    args = parser.parse_args()

    if args.command == "healthcheck":
        cmd_healthcheck()
    else:
        raise SystemExit("Unknown command")


if __name__ == "__main__":
    main()
```

---

# ▶️ Run the CLI

```bash
uv run python -m scraper.cli healthcheck
```

Expected output:

```
[ok] scraper CLI is working | utc=...
```

---

# 🧹 5 — Lint the project

```bash
uv run ruff check .
```

---

# 📂 Output directories (future steps)

| Output              | Location                     |
|--------------------|------------------------------|
| CSV history        | data/processed/prices.csv    |
| JSON history       | data/processed/prices.json   |
| Downloaded images  | assets/images/               |
| HTML report        | reports/index.html           |

---

# ✅ What we achieved

At the end of this milestone we now have:

- ✔ Reproducible environment  
- ✔ Scalable architecture  
- ✔ Dependency management  
- ✔ CLI entry point  
- ✔ Lint configuration  


Si quieres, puedo dejarlo con índice automático, badges, o incluso un diseño más visual.
