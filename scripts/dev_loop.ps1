# scripts/dev_loop.ps1
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
