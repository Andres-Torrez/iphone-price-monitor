from datetime import datetime, timezone

from scraper.models import ProductSnapshot
from scraper.pipeline.dedupe import dedupe_snapshots


def test_dedupe_by_key() -> None:
    ts = datetime(2026, 2, 5, tzinfo=timezone.utc)
    a = ProductSnapshot(
        timestamp=ts,
        model="iphone_15",
        title="iPhone 15",
        sku="X",
        price_eur=799.0,
        product_url="https://example.com/a",
        image_url="https://example.com/a.png",
    )
    b = ProductSnapshot(
        timestamp=ts,
        model="iphone_15",
        title="iPhone 15",
        sku="X",
        price_eur=799.0,
        product_url="https://example.com/a",
        image_url="https://example.com/a.png",
    )
    out = dedupe_snapshots([a, b])
    assert len(out) == 1
