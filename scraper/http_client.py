from __future__ import annotations

import random
import time

import httpx

DEFAULT_HEADERS = {
    "User-Agent": "iphone-price-monitor/1.0 (+https://github.com/your-handle)",
    "Accept": "text/html,application/xhtml+xml",
}


def get_html(url: str, timeout_s: float = 20.0, retries: int = 4) -> str:
    """
    Robust HTML fetch with retries + exponential backoff.
    Helps avoid intermittent WinError 10054 / TLS resets on Windows networks.
    """
    last_exc: Exception | None = None

    for attempt in range(retries + 1):
        try:
            with httpx.Client(
                headers=DEFAULT_HEADERS,
                timeout=timeout_s,
                follow_redirects=True,
                http1=True,  # force HTTP/1.1
                http2=False,
            ) as client:
                r = client.get(url)
                r.raise_for_status()
                return r.text

        except (
            httpx.ConnectError,
            httpx.ReadError,
            httpx.RemoteProtocolError,
            httpx.ReadTimeout,
        ) as exc:
            last_exc = exc
            if attempt >= retries:
                break

            # exponential backoff + jitter
            sleep_s = (2**attempt) * 0.6 + random.random() * 0.4
            time.sleep(sleep_s)

    raise RuntimeError(f"Failed to fetch HTML after {retries} retries: {url}") from last_exc
