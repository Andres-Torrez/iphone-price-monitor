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
