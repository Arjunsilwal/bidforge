# Model Card: BidForge Cost Predictor v1

## Model Overview
- **Model Type**: Quantile Gradient-Boosted Decision Trees (`XGBRegressor` / `LGBMRegressor`).
- **Target Variable**: Unit Price ($ / unit of measure) for construction line items.
- **Quantiles Modeled**: 10th percentile (Low), 50th percentile (Expected/Average), 90th percentile (High).
- **Version**: 1.0.0

## Training Data & Features
- **Data Source**: State Department of Transportation (DOT) public letting bid tabulations (e.g., Oregon DOT).
- **Time Range**: Multi-year historical lettings with temporal train/test split.
- **Features**:
  - `item_code`: Standard DOT pay item code.
  - `item_description_embedding`: 384-dimensional dense semantic embedding from `sentence-transformers/all-MiniLM-L6-v2`.
  - `quantity_log`: Natural log of required item quantity ($\log(1 + Q)$).
  - `unit_of_measure`: Standard units (e.g., LF, SY, CY, TON, EA, LS).
  - `region_id` / `district`: Geographic letting location.
  - `market_price_index`: FRED PPI Construction Materials index (`WPUSI012011`) for the letting period.
  - `letting_season`: Month / Quarter of bid letting.

## Performance Metrics & Baselines
The cost model is validated against two naive baselines on a strict temporal holdout split:
1. **Baseline A**: Historical index-adjusted mean unit price per item code.
2. **Baseline B**: Historical median unit price per item code.

| Metric | Baseline A (Mean) | Baseline B (Median) | BidForge Model v1 | Target Improvement |
|---|---|---|---|---|
| **MAE** | Evaluated | Evaluated | Target: Lower | > 15% reduction |
| **MAPE** | Evaluated | Evaluated | Target: Lower | > 20% reduction |
| **Interval Coverage (10-90%)** | N/A | N/A | Target: ~80% | Well-calibrated range |

## Limitations & Out of Scope for v1
- Trained on public highway & civil infrastructure data (commercial vertical building data is reserved for v2).
- Automatic takeoff from blueprints / drawings is out of scope (requires structured BOQ in CSV/Excel for v1).
- Inflation adjustments use general construction PPI rather than hyper-local trade sub-indexes.
