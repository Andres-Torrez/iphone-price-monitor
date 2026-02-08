from __future__ import annotations

import random
import re
import time
from pathlib import Path

import httpx


def _safe_filename(name: str) -> str:
    """
    Convert model name like 'iphone_15' to 'iphone_15.png' (safe)
    """
    name = name.strip().lower()
    name = re.sub(r"[^a-z0-9_\-]+", "-", name)
    return f"{name}.png"


def download_image(url: str, out_path: Path, timeout_s: float = 30.0, retries: int = 4) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)

    headers = {
        "User-Agent": "iphone-price-monitor/1.0 (+https://github.com/your-handle)",
        "Accept": "image/*",
    }

    last_exc: Exception | None = None

    for attempt in range(retries + 1):
        try:
            with httpx.Client(
                headers=headers,
                timeout=timeout_s,
                follow_redirects=True,
                http1=True,
                http2=False,
            ) as client:
                r = client.get(url)
                r.raise_for_status()
                out_path.write_bytes(r.content)
                return

        except (
            httpx.ConnectError,
            httpx.ReadError,
            httpx.RemoteProtocolError,
            httpx.ReadTimeout,
        ) as exc:
            last_exc = exc
            if attempt >= retries:
                break
            sleep_s = (2**attempt) * 0.6 + random.random() * 0.4
            time.sleep(sleep_s)

    raise RuntimeError(f"Failed to download image after {retries} retries: {url}") from last_exc


def ensure_cached_image(image_url: str, model: str, images_dir: Path) -> Path:
    """
    Returns local path for an image. Downloads only if file does not exist.
    """
    filename = _safe_filename(model)
    target = images_dir / filename

    if target.exists() and target.stat().st_size > 0:
        return target

    download_image(image_url, target)
    return target
