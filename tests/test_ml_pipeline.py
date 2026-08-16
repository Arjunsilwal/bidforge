"""
Unit tests for Machine Learning Feature Pipeline, Quantile Training, and Evaluation.
"""
import numpy as np
import pandas as pd
from ml.features import CostFeaturePipeline
from ml.train import QuantileCostModelTrainer
from ml.evaluate import CostModelEvaluator


def test_feature_pipeline():
    train_data = pd.DataFrame({
        "quantity": [10.0, 100.0, 1000.0],
        "market_index_value": [300.0, 310.0, 320.0],
        "item_code": ["02010", "02020", "02010"],
        "unit_of_measure": ["LS", "CY", "LS"],
        "region": ["D1", "D2", "D1"],
    })
    y = pd.Series([1000.0, 45.0, 950.0])

    pipeline = CostFeaturePipeline()
    pipeline.fit(train_data, y)
    X = pipeline.transform(train_data)

    assert isinstance(X, np.ndarray)
    assert X.shape[0] == 3
    assert X.shape[1] > 3  # Multiple feature dimensions extracted


def test_quantile_cost_model_training_and_monotonicity():
    train_data = pd.DataFrame({
        "quantity": [5.0, 20.0, 50.0, 100.0, 500.0, 1000.0] * 3,
        "market_index_value": [300.0] * 18,
        "item_code": ["02010", "02020", "03010"] * 6,
        "unit_of_measure": ["LS", "CY", "TON"] * 6,
        "region": ["D1", "D2", "D1"] * 6,
        "unit_price": [5000.0, 40.0, 25.0, 4800.0, 35.0, 22.0] * 3,
    })

    trainer = QuantileCostModelTrainer(n_estimators=20, max_depth=3)
    trainer.fit(train_data)

    test_data = pd.DataFrame({
        "quantity": [15.0, 200.0],
        "market_index_value": [300.0, 300.0],
        "item_code": ["02010", "03010"],
        "unit_of_measure": ["LS", "TON"],
        "region": ["D1", "D1"],
    })

    preds = trainer.predict_ranges(test_data)
    assert "pred_low" in preds.columns
    assert "pred_avg" in preds.columns
    assert "pred_high" in preds.columns

    # Verify monotonicity: low <= avg <= high for all rows
    for _, row in preds.iterrows():
        assert row["pred_low"] <= row["pred_avg"]
        assert row["pred_avg"] <= row["pred_high"]
        assert row["pred_low"] > 0


def test_evaluator_metrics():
    evaluator = CostModelEvaluator()
    y_true = np.array([100.0, 200.0, 300.0])
    y_pred = np.array([110.0, 190.0, 330.0])
    y_low = np.array([90.0, 180.0, 280.0])
    y_high = np.array([120.0, 220.0, 350.0])

    mae = evaluator.calculate_mae(y_true, y_pred)
    mape = evaluator.calculate_mape(y_true, y_pred)
    coverage = evaluator.calculate_interval_coverage(y_true, y_low, y_high)

    assert round(mae, 2) == 16.67
    assert mape > 0
    assert coverage == 100.0  # All points fall inside [y_low, y_high]
