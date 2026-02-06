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

    p_scrape = sub.add_parser("scrape", help="Scrape product snapshots from the configured source")
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
