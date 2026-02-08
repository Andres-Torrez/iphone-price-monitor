# scripts/run_all.ps1
$ErrorActionPreference = "Stop"

uv sync
uv run pytest -q
uv run python -m scraper.cli run

Write-Host "[ok] tests + pipeline completed"
