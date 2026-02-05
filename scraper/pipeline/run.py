from __future__ import annotations

from datetime import datetime
from pathlib import Path

from scraper.models import ProductSnapshot
from scraper.pipeline.dedupe import dedupe_snapshots
from scraper.sources.github_pages_catalog import GitHubPagesCatalogSource
from scraper.storage.csv_store import write_csv
from scraper.storage.json_store import read_json_if_exists, write_json


def _dict_to_snapshot(d: dict) -> ProductSnapshot:
    # Pydantic reconstruye el datetime bien si está en ISO
    return ProductSnapshot.model_validate(d)


def run_pipeline(
    base_url: str,
    out_csv: Path,
    out_json: Path,
) -> list[ProductSnapshot]:
    src = GitHubPagesCatalogSource(base_url=base_url)
    new_rows = src.fetch()

    existing_dicts = read_json_if_exists(out_json)
    existing_rows = [_dict_to_snapshot(d) for d in existing_dicts]

    combined = existing_rows + new_rows
    combined = dedupe_snapshots(combined)

    write_json(out_json, combined)
    write_csv(out_csv, combined)

    return combined
