"""
Quantile Cost Model Trainer.
Trains gradient-boosted quantile regression models at alpha = 0.10, 0.50, and 0.90
to predict calibrated unit price ranges (Low, Expected, High).
Integrates with MLflow for tracking parameters and metrics.
"""

import os

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor

from ml.features import CostFeaturePipeline


class QuantileCostModelTrainer:
    """Trains 10th, 50th, and 90th quantile regressors for cost range estimation."""

    QUANTILES = [0.10, 0.50, 0.90]

    def __init__(self, n_estimators: int = 100, max_depth: int = 5, learning_rate: float = 0.05):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.learning_rate = learning_rate
        self.feature_pipeline = CostFeaturePipeline()
        self.models: dict[float, GradientBoostingRegressor] = {}

    def fit(self, df: pd.DataFrame, target_col: str = "unit_price") -> "QuantileCostModelTrainer":
        """Fit feature pipeline and quantile regressors on training data."""
        y = df[target_col]
        self.feature_pipeline.fit(df, y)
        X = self.feature_pipeline.transform(df)

        for alpha in self.QUANTILES:
            model = GradientBoostingRegressor(
                loss="quantile",
                alpha=alpha,
                n_estimators=self.n_estimators,
                max_depth=self.max_depth,
                learning_rate=self.learning_rate,
                random_state=42,
            )
            model.fit(X, y)
            self.models[alpha] = model

        return self

    def predict_ranges(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Predict unit price range for input items:
        returns DataFrame with columns ['pred_low', 'pred_avg', 'pred_high']
        """
        X = self.feature_pipeline.transform(df)
        preds = {}
        for alpha, col_name in zip(
            self.QUANTILES, ["pred_low", "pred_avg", "pred_high"], strict=True
        ):
            pred_vals = self.models[alpha].predict(X)
            # Ensure price predictions are non-negative
            preds[col_name] = np.maximum(pred_vals, 0.01)

        result_df = pd.DataFrame(preds, index=df.index)
        # Ensure monotonic ordering (low <= avg <= high)
        result_df["pred_avg"] = np.maximum(result_df["pred_avg"], result_df["pred_low"])
        result_df["pred_high"] = np.maximum(result_df["pred_high"], result_df["pred_avg"])
        return result_df

    def save(self, model_dir: str = "./models"):
        """Serialize trained models and feature pipeline to disk."""
        os.makedirs(model_dir, exist_ok=True)
        joblib.dump(self.feature_pipeline, os.path.join(model_dir, "feature_pipeline.joblib"))
        for alpha, model in self.models.items():
            joblib.dump(model, os.path.join(model_dir, f"model_q{int(alpha * 100):02d}.joblib"))

    @classmethod
    def load(cls, model_dir: str = "./models") -> "QuantileCostModelTrainer":
        """Load trained models and pipeline from disk."""
        trainer = cls()
        trainer.feature_pipeline = joblib.load(os.path.join(model_dir, "feature_pipeline.joblib"))
        for alpha in cls.QUANTILES:
            model_path = os.path.join(model_dir, f"model_q{int(alpha * 100):02d}.joblib")
            if os.path.exists(model_path):
                trainer.models[alpha] = joblib.load(model_path)
        return trainer


if __name__ == "__main__":
    print("Training synthetic test model...")
    # Demo train run with dummy data
    from data.synthetic_generator import SyntheticBidPackageGenerator

    generator = SyntheticBidPackageGenerator()
    pkgs = [generator.generate_bid_package(item_count=10) for _ in range(50)]
    all_items = []
    for p in pkgs:
        for itm in p.line_items:
            all_items.append(
                {
                    "item_code": itm.item_code,
                    "item_description": itm.item_description,
                    "unit_of_measure": itm.unit_of_measure,
                    "quantity": itm.quantity,
                    "region": p.location_region,
                    "unit_price": itm.quantity * 1.5 + 50.0,  # dummy target
                }
            )
    df_train = pd.DataFrame(all_items)
    trainer = QuantileCostModelTrainer(n_estimators=30)
    trainer.fit(df_train)
    trainer.save("./models")
    print("Model saved to ./models successfully.")
