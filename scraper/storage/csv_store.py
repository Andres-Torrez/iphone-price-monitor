from __future__ import annotations

from pathlib import Path
import csv

from scraper.models import ProductSnapshot


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


def write_csv(path: Path, rows: list[ProductSnapshot]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        w.writeheader()
        for r in rows:
            d = r.model_dump(mode="json")
            w.writerow({k: d.get(k) for k in CSV_COLUMNS})
