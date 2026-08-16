"""
MLflow Experiment Tracking and Model Registry Management.
"""

import os
from typing import Any

import mlflow

from ml.train import QuantileCostModelTrainer


class ModelRegistryManager:
    """Wrapper for MLflow run tracking, parameter logging, and model registry promotions."""

    def __init__(
        self, tracking_uri: str | None = None, experiment_name: str = "bidforge-cost-model-v1"
    ):
        # `or` rather than a getenv default so an empty MLFLOW_TRACKING_URI also
        # falls back instead of configuring MLflow with an empty URI.
        self.tracking_uri: str = (
            tracking_uri or os.getenv("MLFLOW_TRACKING_URI") or "http://localhost:5000"
        )
        self.experiment_name = experiment_name
        mlflow.set_tracking_uri(self.tracking_uri)
        mlflow.set_experiment(self.experiment_name)

    def log_training_run(
        self,
        params: dict[str, Any],
        metrics: dict[str, float],
        model_trainer: QuantileCostModelTrainer,
        run_name: str | None = None,
    ) -> str:
        """Log parameters, evaluation metrics, and model artifacts to MLflow."""
        with mlflow.start_run(run_name=run_name) as run:
            # Log params
            mlflow.log_params(params)
            # Log metrics
            mlflow.log_metrics(metrics)

            # Save local temp artifacts and log
            temp_dir = "./tmp_model_artifacts"
            model_trainer.save(temp_dir)
            mlflow.log_artifacts(temp_dir, artifact_path="cost_models")

            return str(run.info.run_id)
