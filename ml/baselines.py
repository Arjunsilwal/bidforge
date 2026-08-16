"""
Naive Heuristic Baselines for Cost Estimation.
Baseline A: Historical index-adjusted mean unit price per item code.
Baseline B: Historical median unit price per item code.
"""
from typing import Dict
import pandas as pd


class HistoricalMeanBaseline:
    """Baseline A: Historical Mean unit price grouped by item code."""

    def __init__(self):
        self.item_means: Dict[str, float] = {}
        self.global_mean: float = 0.0

    def fit(self, df: pd.DataFrame, target_col: str = "unit_price") -> "HistoricalMeanBaseline":
        """Compute mean price per item code."""
        price_col = "adjusted_unit_price" if "adjusted_unit_price" in df.columns else target_col
        self.global_mean = float(df[price_col].mean())
        self.item_means = df.groupby("item_code")[price_col].mean().to_dict()
        return self

    def predict(self, df: pd.DataFrame) -> pd.Series:
        """Predict mean unit price for each item code, falling back to global mean."""
        return df["item_code"].map(lambda code: self.item_means.get(str(code), self.global_mean))


class HistoricalMedianBaseline:
    """Baseline B: Historical Median unit price grouped by item code."""

    def __init__(self):
        self.item_medians: Dict[str, float] = {}
        self.global_median: float = 0.0

    def fit(self, df: pd.DataFrame, target_col: str = "unit_price") -> "HistoricalMedianBaseline":
        """Compute median price per item code."""
        price_col = "adjusted_unit_price" if "adjusted_unit_price" in df.columns else target_col
        self.global_median = float(df[price_col].median())
        self.item_medians = df.groupby("item_code")[price_col].median().to_dict()
        return self

    def predict(self, df: pd.DataFrame) -> pd.Series:
        """Predict median unit price for each item code, falling back to global median."""
        return df["item_code"].map(lambda code: self.item_medians.get(str(code), self.global_median))
