from __future__ import annotations


def parse_price_eur(text: str) -> float:
    """
    Convert strings like '799,00 €' or '799 €' into float 799.00
    """
    cleaned = (
        text.replace("€", "")
        .replace("\xa0", " ")
        .strip()
    )
    # remove thousand separators if any, and normalize decimal comma to dot
    cleaned = cleaned.replace(".", "").replace(",", ".")
    # keep only digits and dot
    cleaned = "".join(ch for ch in cleaned if ch.isdigit() or ch == ".")
    if not cleaned:
        raise ValueError(f"Could not parse price from: {text!r}")
    return float(cleaned)
