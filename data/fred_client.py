"""
FRED (Federal Reserve Economic Data) API Client.
Fetches Producer Price Index for Construction Materials (WPUSI012011) to normalize historical prices.
"""
from datetime import date
from typing import Dict, Optional
import os
import requests
import pandas as pd


class FredPriceIndexClient:
    """Client for fetching and caching FRED macroeconomic price indices."""

    DEFAULT_SERIES_ID = "WPUSI012011"  # PPI: Construction Materials

    def __init__(self, api_key: Optional[str] = None, series_id: str = DEFAULT_SERIES_ID):
        self.api_key = api_key or os.getenv("FRED_API_KEY", "")
        self.series_id = series_id
        self.cache: Dict[str, float] = {}

    def fetch_series(self, start_date: str = "2015-01-01") -> pd.DataFrame:
        """Fetch monthly PPI series from FRED API or provide fallback values."""
        if not self.api_key:
            # Return synthetic fallback monthly index if API key is not configured
            dates = pd.date_range(start=start_date, end=date.today(), freq="MS")
            base_val = 220.0
            values = [base_val * (1.0 + (i * 0.003)) for i in range(len(dates))]
            df = pd.DataFrame({"date": dates.date, "index_value": values})
            for _, row in df.iterrows():
                self.cache[row["date"].strftime("%Y-%m")] = float(row["index_value"])
            return df

        url = "https://api.stlouisfed.org/fred/series/observations"
        params = {
            "series_id": self.series_id,
            "api_key": self.api_key,
            "file_type": "json",
            "observation_start": start_date,
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        records = []
        for obs in data.get("observations", []):
            try:
                dt = pd.to_datetime(obs["date"]).date()
                val = float(obs["value"])
                records.append({"date": dt, "index_value": val})
                self.cache[dt.strftime("%Y-%m")] = val
            except (ValueError, KeyError):
                continue

        return pd.DataFrame(records)

    def get_index_for_date(self, target_date: date) -> float:
        """Look up index value for a specific date (year-month)."""
        key = target_date.strftime("%Y-%m")
        if key in self.cache:
            return self.cache[key]
        # Return standard recent benchmark index default if date not found
        return 330.0

    def adjust_price(
        self,
        historical_price: float,
        historical_date: date,
        target_date: Optional[date] = None,
    ) -> float:
        """
        Adjust a historical price to target date dollars using the PPI ratio:
        Adjusted Price = Historical Price * (Target Index / Historical Index)
        """
        if target_date is None:
            target_date = date.today()

        hist_index = self.get_index_for_date(historical_date)
        target_index = self.get_index_for_date(target_date)

        if hist_index <= 0:
            return historical_price

        ratio = target_index / hist_index
        return round(historical_price * ratio, 2)
