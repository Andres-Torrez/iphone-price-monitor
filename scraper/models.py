from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl


class ProductSnapshot(BaseModel):
    timestamp: datetime
    source: str = Field(default="github_pages_catalog")
    model: str  # iphone_15 | iphone_16 | iphone_17
    title: str
    sku: str | None = None
    currency: str = "EUR"
    price_eur: float
    product_url: HttpUrl
    image_url: HttpUrl

    # NEW (Step 4): local cached image path
    image_path: str | None = None
