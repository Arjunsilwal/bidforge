"""
Model Evaluation & Benchmarking.
Evaluates cost models on a temporal holdout dataset, calculating:
- Mean Absolute Error (MAE)
- Mean Absolute Percentage Error (MAPE)
- Prediction Interval Coverage Probability (PICP) for 10-90% range
- Direct tabular comparison against Baselines A and B
"""

import numpy as np
import pandas as pd

from ml.baselines import HistoricalMeanBaseline, HistoricalMedianBaseline
from ml.train import QuantileCostModelTrainer


class CostModelEvaluator:
    """Evaluates cost prediction models against baselines on temporal holdouts."""

    @staticmethod
    def calculate_mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """Calculate Mean Absolute Error ($)."""
        return float(np.mean(np.abs(y_true - y_pred)))

    @staticmethod
    def calculate_mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """Calculate Mean Absolute Percentage Error (%)."""
        mask = y_true > 0
        if not np.any(mask):
            return 0.0
        return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100.0)

    @staticmethod
    def calculate_interval_coverage(
        y_true: np.ndarray, y_low: np.ndarray, y_high: np.ndarray
    ) -> float:
        """Calculate percentage of true prices that fall within the [y_low, y_high] range."""
        within_bounds = (y_true >= y_low) & (y_true <= y_high)
        return float(np.mean(within_bounds) * 100.0)

    def evaluate_all(
        self,
        train_df: pd.DataFrame,
        test_df: pd.DataFrame,
        target_col: str = "unit_price",
    ) -> pd.DataFrame:
        """Fit baselines and ML model, then compare metrics on test_df."""
        y_test = test_df[target_col].values

        # 1. Baseline A (Historical Mean)
        baseline_a = HistoricalMeanBaseline()
        baseline_a.fit(train_df, target_col=target_col)
        pred_a = baseline_a.predict(test_df).values

        # 2. Baseline B (Historical Median)
        baseline_b = HistoricalMedianBaseline()
        baseline_b.fit(train_df, target_col=target_col)
        pred_b = baseline_b.predict(test_df).values

        # 3. Quantile Cost Model
        trainer = QuantileCostModelTrainer(n_estimators=100)
        trainer.fit(train_df, target_col=target_col)
        ranges = trainer.predict_ranges(test_df)
        pred_ml = ranges["pred_avg"].values
        pred_low = ranges["pred_low"].values
        pred_high = ranges["pred_high"].values

        # Compute Metrics
        metrics = [
            {
                "Model": "Baseline A (Historical Mean)",
                "MAE ($)": round(self.calculate_mae(y_test, pred_a), 2),
                "MAPE (%)": round(self.calculate_mape(y_test, pred_a), 2),
                "10-90% Coverage (%)": "N/A",
            },
            {
                "Model": "Baseline B (Historical Median)",
                "MAE ($)": round(self.calculate_mae(y_test, pred_b), 2),
                "MAPE (%)": round(self.calculate_mape(y_test, pred_b), 2),
                "10-90% Coverage (%)": "N/A",
            },
            {
                "Model": "BidForge Quantile Model v1",
                "MAE ($)": round(self.calculate_mae(y_test, pred_ml), 2),
                "MAPE (%)": round(self.calculate_mape(y_test, pred_ml), 2),
                "10-90% Coverage (%)": f"{round(self.calculate_interval_coverage(y_test, pred_low, pred_high), 1)}%",
            },
        ]

        return pd.DataFrame(metrics)
