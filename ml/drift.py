"""
Input Feature Drift Detector.
Computes statistical distance between incoming inference requests and training distributions
(e.g., Kolmogorov-Smirnov test for continuous features, PSI or Chi-square for categoricals).
"""
from typing import Dict, Any, List
import numpy as np
import pandas as pd
from scipy.stats import ks_2samp


class InputDriftDetector:
    """Monitors incoming line items for statistical distribution drift against baseline."""

    def __init__(self, baseline_df: pd.DataFrame, significance_level: float = 0.05):
        self.baseline_quantities = baseline_df.get("quantity", pd.Series([1.0])).dropna().values
        self.baseline_item_codes = set(baseline_df.get("item_code", pd.Series([])).astype(str).unique())
        self.significance_level = significance_level

    def check_drift(self, incoming_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Evaluate drift on incoming batch:
        - Quantity distribution KS-test
        - Out-of-vocabulary item codes percentage
        """
        drift_report = {
            "drift_detected": False,
            "quantity_ks_pvalue": 1.0,
            "novel_item_code_pct": 0.0,
            "warnings": [],
        }

        # 1. Check quantity distribution drift via KS-test
        if "quantity" in incoming_df.columns and len(incoming_df["quantity"]) > 1:
            incoming_quantities = incoming_df["quantity"].dropna().values
            if len(self.baseline_quantities) > 1 and len(incoming_quantities) > 1:
                stat, p_val = ks_2samp(self.baseline_quantities, incoming_quantities)
                drift_report["quantity_ks_pvalue"] = float(p_val)
                if p_val < self.significance_level:
                    drift_report["drift_detected"] = True
                    drift_report["warnings"].append(
                        f"Quantity distribution drift detected (KS p-value: {p_val:.4f} < {self.significance_level})"
                    )

        # 2. Check novel item codes
        if "item_code" in incoming_df.columns and self.baseline_item_codes:
            incoming_codes = incoming_df["item_code"].astype(str).unique()
            novel = [c for c in incoming_codes if c not in self.baseline_item_codes]
            novel_pct = (len(novel) / max(len(incoming_codes), 1)) * 100.0
            drift_report["novel_item_code_pct"] = round(novel_pct, 2)
            if novel_pct > 30.0:
                drift_report["drift_detected"] = True
                drift_report["warnings"].append(
                    f"High percentage of novel item codes ({novel_pct:.1f}% unseen in training baseline)"
                )

        return drift_report
