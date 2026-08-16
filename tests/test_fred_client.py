"""
Unit tests for FRED Price Index Client.
"""
from datetime import date
from data.fred_client import FredPriceIndexClient


def test_fred_fallback_series():
    client = FredPriceIndexClient(api_key="")
    df = client.fetch_series(start_date="2022-01-01")
    assert not df.empty
    assert "date" in df.columns
    assert "index_value" in df.columns
    assert df["index_value"].iloc[-1] > df["index_value"].iloc[0]


def test_fred_price_adjustment():
    client = FredPriceIndexClient(api_key="")
    client.cache["2020-01"] = 200.0
    client.cache["2026-08"] = 300.0

    # Historical price: $100 in 2020-01 adjusted to 2026-08
    adjusted = client.adjust_price(
        historical_price=100.0,
        historical_date=date(2020, 1, 15),
        target_date=date(2026, 8, 15),
    )
    # Ratio is 300/200 = 1.5 -> $150.0
    assert adjusted == 150.0
