"""
MLflow Experiment Tracking and Model Registry Management.
"""
from typing import Dict, Any, Optional
import os
import mlflow
from ml.train import QuantileCostModelTrainer


class ModelRegistryManager:
    """Wrapper for MLflow run tracking, parameter logging, and model registry promotions."""

    def __init__(self, tracking_uri: Optional[str] = None, experiment_name: str = "bidforge-cost-model-v1"):
        self.tracking_uri = tracking_uri or os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
        self.experiment_name = experiment_name
        mlflow.set_tracking_uri(self.tracking_uri)
        mlflow.set_experiment(self.experiment_name)

    def log_training_run(
        self,
        params: Dict[str, Any],
        metrics: Dict[str, float],
        model_trainer: QuantileCostModelTrainer,
        run_name: Optional[str] = None,
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

            return run.info.run_id
