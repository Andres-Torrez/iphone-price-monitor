from __future__ import annotations

import json
from pathlib import Path

from scraper.models import ProductSnapshot


def write_json(path: Path, rows: list[ProductSnapshot]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [r.model_dump(mode="json") for r in rows]
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def read_json_if_exists(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))
