from __future__ import annotations

from scraper.models import ProductSnapshot


def dedupe_snapshots(rows: list[ProductSnapshot]) -> list[ProductSnapshot]:
    """
    Remove duplicates by (timestamp, source, model, price_eur).
    """
    seen: set[tuple] = set()
    out: list[ProductSnapshot] = []

    for r in rows:
        key = (r.timestamp.isoformat(), r.source, r.model, r.price_eur)
        if key in seen:
            continue
        seen.add(key)
        out.append(r)

    # stable sort by timestamp then model
    out.sort(key=lambda x: (x.timestamp, x.model))
    return out
