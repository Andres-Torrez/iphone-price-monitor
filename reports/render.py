from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape


def load_prices(path: Path) -> list[dict]:
    """
    Load the historical dataset from JSON.
    Returns [] if the file does not exist yet.
    """
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def prepare_context(rows: list[dict]) -> dict:
    """
    Build template context:
    - by_model: model -> list of snapshots sorted by timestamp
    - latest: model -> latest snapshot enriched with delta vs previous
    - last_updated: max timestamp across all rows (string)
    """
    by_model: dict[str, list[dict]] = defaultdict(list)

    for r in rows:
        by_model[r.get("model", "unknown")].append(r)

    for model in by_model:
        by_model[model].sort(key=lambda x: x.get("timestamp", ""))

    # Last updated (for the header)
    last_updated = ""
    if rows:
        last_updated = max(r.get("timestamp", "") for r in rows)

    # Latest per model + delta
    latest: dict[str, dict] = {}
    for model, items in by_model.items():
        if not items:
            continue

        current = items[-1]
        prev = items[-2] if len(items) > 1 else None

        delta = None
        if prev:
            try:
                delta = round(float(current["price_eur"]) - float(prev["price_eur"]), 2)
            except Exception:
                delta = None

        latest[model] = {**current, "delta": delta}

    return {"by_model": dict(by_model), "latest": latest, "last_updated": last_updated}


def render_report(prices_json: Path, out_html: Path, templates_dir: Path) -> None:
    """
    Render reports/index.html from scraper/report/templates/index.html.j2
    and copy styles.css next to the output HTML.
    """
    rows = load_prices(prices_json)
    ctx = prepare_context(rows)

    env = Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=select_autoescape(["html"]),
    )

    tpl = env.get_template("index.html.j2")
    html = tpl.render(**ctx)

    out_html.parent.mkdir(parents=True, exist_ok=True)
    out_html.write_text(html, encoding="utf-8")

    # Copy CSS next to the HTML output so the report is self-contained
    css_src = templates_dir / "styles.css"
    css_dst = out_html.parent / "styles.css"
    if css_src.exists():
        css_dst.write_text(css_src.read_text(encoding="utf-8"), encoding="utf-8")
