"""
Tests for Baseline A and Baseline B cost models.
"""
import pandas as pd
from ml.baselines import HistoricalMeanBaseline, HistoricalMedianBaseline


def test_baselines():
    data = [
        {"item_code": "02010", "unit_price": 100.0},
        {"item_code": "02010", "unit_price": 200.0},
        {"item_code": "02010", "unit_price": 300.0},
        {"item_code": "03010", "unit_price": 50.0},
    ]
    df = pd.DataFrame(data)

    # Test Baseline A (Mean)
    mean_baseline = HistoricalMeanBaseline()
    mean_baseline.fit(df)
    preds_mean = mean_baseline.predict(pd.DataFrame([{"item_code": "02010"}]))
    assert preds_mean.iloc[0] == 200.0

    # Test Baseline B (Median)
    median_baseline = HistoricalMedianBaseline()
    median_baseline.fit(df)
    preds_median = median_baseline.predict(pd.DataFrame([{"item_code": "02010"}]))
    assert preds_median.iloc[0] == 200.0
