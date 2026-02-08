# 🟦 8 — Automation: local dev loop + GitHub Actions scheduled runs

## 🎯 Goal

Automate the pipeline execution in two environments:

1) **Local (developer mode, visible in VS Code)**
   - Runs every 2 minutes for fast iteration
   - Executes: dependency sync → tests → pipeline

2) **Remote (GitHub Actions)**
   - Runs on a schedule (minimum practical frequency ~5 minutes)
   - Executes: dependency sync → tests → pipeline
   - Uploads generated outputs as artifacts (CSV/JSON/HTML/images)
   - Also supports manual runs via `workflow_dispatch`

This makes the project feel “alive”: it updates itself and validates data integrity continuously.

---

## 🧠 Important note on scheduling frequency

### Local
- We can run every **2 minutes** because it’s fully controlled by the developer machine.

### GitHub Actions
- GitHub scheduled workflows are **not designed for 2-minute intervals**.
- The minimum practical interval is **~5 minutes**, and timing may drift due to queueing.
- Scheduled workflows only run from the **default branch** (usually `main`).

For immediate testing on GitHub, use the manual trigger: **Run workflow**.

---

## 9.1 Local automation (Windows / VS Code)

### File: `scripts/dev_loop.ps1`

Runs an infinite loop every 120 seconds:

- `uv sync`
- `pytest`
- `scraper.cli run`

```powershell
$ErrorActionPreference = "Stop"

while ($true) {
    Write-Host "======================================="
    Write-Host "DEV LOOP @ $(Get-Date -Format u)"
    Write-Host "======================================="

    Write-Host "[1/3] Sync deps..."
    uv sync

    Write-Host "[2/3] Running tests..."
    uv run pytest -q
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[x] Tests failed. Fix before next run." -ForegroundColor Red
        exit 1
    }

    Write-Host "[3/3] Running pipeline..."
    uv run python -m scraper.cli run

    Write-Host "Sleeping 120 seconds..."
    Start-Sleep -Seconds 120
}

Run it (VS Code terminal)
powershell -ExecutionPolicy Bypass -File scripts/dev_loop.ps1


Stop it anytime with Ctrl + C.

9.2 Remote automation (GitHub Actions)
File: .github/workflows/scheduled.yml

This workflow:

syncs dependencies with uv

runs tests

runs the pipeline

uploads outputs as artifacts

name: scheduled-pipeline

on:
  workflow_dispatch: {}
  schedule:
    - cron: "*/5 * * * *"

jobs:
  run-pipeline:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v3

      - name: Install Python
        run: uv python install 3.12

      - name: Sync deps
        run: uv sync

      - name: Run tests
        run: uv run pytest -q

      - name: Run pipeline
        run: uv run python -m scraper.cli run

      - name: Upload artifacts (CSV/JSON/HTML/images)
        uses: actions/upload-artifact@v4
        with:
          name: iphone-monitor-output
          path: |
            data/processed/prices.csv
            data/processed/prices.json
            reports/index.html
            reports/styles.css
            assets/images
          if-no-files-found: warn

🔎 How to verify it works
Manual (instant)

GitHub → Actions → scheduled-pipeline → Run workflow

Scheduled

Wait a few minutes and check the Actions list.
Note: schedule runs only from the default branch (main).

✅ What we achieved

✔ Fast local iteration loop (every 2 minutes) visible in VS Code

✔ Automated validation via tests before each run

✔ Scheduled remote runs in GitHub Actions

✔ Reproducible outputs downloadable as artifacts

✔ Professional automation workflow without auto-committing generated files
