from __future__ import annotations

from datetime import UTC, datetime
from urllib.parse import urljoin

from selectolax.parser import HTMLParser

from scraper.http_client import get_html
from scraper.models import ProductSnapshot
from scraper.pipeline.normalize import parse_price_eur
from scraper.sources.base import Source


class GitHubPagesCatalogSource(Source):
    def __init__(self, base_url: str) -> None:
        # base_url example: "https://andres-torrez.github.io/iphone-catalog/"
        self.base_url = base_url if base_url.endswith("/") else base_url + "/"

    def fetch(self) -> list[ProductSnapshot]:
        product_paths = ["iphone-15.html", "iphone-16.html", "iphone-17.html"]
        out: list[ProductSnapshot] = []
        now = datetime.now(UTC)

        for path in product_paths:
            product_url = urljoin(self.base_url, path)
            html = get_html(product_url)
            tree = HTMLParser(html)

            title = self._text(tree, '[data-testid="product-title"]')
            model = self._text(tree, '[data-testid="product-model"]')
            price_text = self._text(tree, '[data-testid="product-price"]')
            sku = self._text_optional(tree, '[data-testid="product-sku"]')

            img_src = self._attr(tree, '[data-testid="product-image"]', "src")
            image_url = urljoin(self.base_url, img_src)

            price_eur = parse_price_eur(price_text)

            out.append(
                ProductSnapshot(
                    timestamp=now,
                    model=model,
                    title=title,
                    sku=sku,
                    price_eur=price_eur,
                    product_url=product_url,
                    image_url=image_url,
                )
            )

        return out

    @staticmethod
    def _text(tree: HTMLParser, css: str) -> str:
        node = tree.css_first(css)
        if node is None:
            raise ValueError(f"Missing required element: {css}")
        return node.text(strip=True)

    @staticmethod
    def _text_optional(tree: HTMLParser, css: str) -> str | None:
        node = tree.css_first(css)
        return node.text(strip=True) if node else None

    @staticmethod
    def _attr(tree: HTMLParser, css: str, attr: str) -> str:
        node = tree.css_first(css)
        if node is None:
            raise ValueError(f"Missing required element: {css}")
        val = node.attributes.get(attr)
        if not val:
            raise ValueError(f"Missing attribute {attr!r} in {css}")
        return val
