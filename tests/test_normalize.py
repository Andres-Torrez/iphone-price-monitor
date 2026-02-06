from scraper.pipeline.normalize import parse_price_eur


def test_parse_price_eur_comma() -> None:
    assert parse_price_eur("799,00 €") == 799.00


def test_parse_price_eur_no_decimals() -> None:
    assert parse_price_eur("999 €") == 999.0
