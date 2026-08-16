"""
Tests for Input Drift Detection.
"""
import pandas as pd
from ml.drift import InputDriftDetector


def test_drift_detector():
    baseline_data = pd.DataFrame({
        "quantity": [10.0, 20.0, 30.0, 40.0, 50.0],
        "item_code": ["02010", "02020", "02030", "02010", "02020"],
    })
    detector = InputDriftDetector(baseline_data)

    # Similar incoming data
    similar_data = pd.DataFrame({
        "quantity": [15.0, 25.0, 35.0],
        "item_code": ["02010", "02020", "02030"],
    })
    report = detector.check_drift(similar_data)
    assert not report["drift_detected"]
    assert report["novel_item_code_pct"] == 0.0

    # Unseen novel codes data
    novel_data = pd.DataFrame({
        "quantity": [15.0, 25.0],
        "item_code": ["99999", "88888"],
    })
    novel_report = detector.check_drift(novel_data)
    assert novel_report["drift_detected"]
    assert novel_report["novel_item_code_pct"] == 100.0
