"""
Feature Engineering Pipeline for Construction Cost Prediction.
Extracts tabular numerical features, categorical target encodings,
and semantic text embeddings for line item descriptions.
"""
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.preprocessing import OneHotEncoder, StandardScaler


class CostFeaturePipeline(BaseEstimator, TransformerMixin):
    """
    Transforms raw line item attributes into a dense numeric feature matrix for gradient boosting:
    - log(quantity) transformation (to capture economies of scale)
    - One-hot / frequency encoding for units of measure and geographic regions
    - Market price index ratio
    - Text semantic embeddings for item descriptions (optional/pluggable)
    """

    def __init__(self, use_text_embeddings: bool = False, embedding_dim: int = 384):
        self.use_text_embeddings = use_text_embeddings
        self.embedding_dim = embedding_dim
        self.scaler = StandardScaler()
        self.encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
        self.fitted_ = False
        self.item_code_means_: Dict[str, float] = {}
        self.global_mean_: float = 0.0

    def fit(self, df: pd.DataFrame, y: Optional[pd.Series] = None) -> "CostFeaturePipeline":
        """Fit encoders and target mean statistics on training data."""
        # Calculate target mean per item code for target encoding
        if y is not None and "item_code" in df.columns:
            self.global_mean_ = float(y.mean())
            self.item_code_means_ = y.groupby(df["item_code"]).mean().to_dict()

        cat_cols = self._get_cat_cols(df)
        if cat_cols:
            self.encoder.fit(df[cat_cols].astype(str))

        self.fitted_ = True
        return self

    def transform(self, df: pd.DataFrame) -> np.ndarray:
        """Transform incoming DataFrame to numeric feature matrix."""
        if not self.fitted_:
            raise RuntimeError("CostFeaturePipeline must be fitted before calling transform.")

        df = df.copy()
        feature_blocks = []

        # 1. Log quantity feature
        qty = np.log1p(np.maximum(df.get("quantity", 1.0).values, 0.0)).reshape(-1, 1)
        feature_blocks.append(qty)

        # 2. Market price index feature (relative to standard base 300.0)
        idx_val = (df.get("market_index_value", 300.0).values / 300.0).reshape(-1, 1)
        feature_blocks.append(idx_val)

        # 3. Item code target encoding feature
        if "item_code" in df.columns:
            item_encoded = df["item_code"].map(lambda c: self.item_code_means_.get(str(c), self.global_mean_)).values.reshape(-1, 1)
            # Log transform the price target encoding
            item_encoded_log = np.log1p(np.maximum(item_encoded, 0.0))
            feature_blocks.append(item_encoded_log)

        # 4. Categorical one-hot features (UOM, region)
        cat_cols = self._get_cat_cols(df)
        if cat_cols:
            cat_features = self.encoder.transform(df[cat_cols].astype(str))
            feature_blocks.append(cat_features)

        # Concatenate all blocks into single matrix
        X = np.hstack(feature_blocks)
        return X

    def _get_cat_cols(self, df: pd.DataFrame) -> List[str]:
        """Find categorical columns present in DataFrame."""
        possible = ["unit_of_measure", "region"]
        return [c for c in possible if c in df.columns]
