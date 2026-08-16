# BidForge Notebooks

This directory contains exploratory data analysis (EDA) and experimental model prototyping notebooks.

## Suggested Notebooks
- `01_odot_bidtabs_eda.ipynb`: Ingestion and exploratory analysis of Oregon DOT historical letting data (price distributions, quantity effects, inflation trends).
- `02_fred_ppi_index_analysis.ipynb`: Visualizing construction materials PPI and validating historical price deflator adjustments.
- `03_quantile_model_experiments.ipynb`: Comparing LightGBM / XGBoost pinball loss quantile regressors against Baselines A & B.

> **Note**: Notebooks are exploratory. Production feature pipelines and model code reside in `ml/` and `data/`.
