# Architecture Decision Records (ADRs)

## ADR 001: Public DOT Bid Tabs as Primary Training Ground
- **Status**: Accepted
- **Context**: Access to proprietary general contractor cost data is restricted. We need high-volume, granular, line-item historical bid data with quantities and actual letting unit prices.
- **Decision**: Train v1 on state DOT public bid tabulations (starting with Oregon DOT).
- **Consequences**: Fast access to 100k+ real bidding rows with zero data acquisition cost. Clear proving ground before expanding into private vertical building data in v2.

## ADR 002: Quantile Gradient Boosting for Low/Avg/High Price Ranges
- **Status**: Accepted
- **Context**: Estimators need realistic price ranges (low/conservative/high risk) rather than arbitrary standard deviations around a single mean.
- **Decision**: Train pinball loss quantile models at $\alpha = 0.10, 0.50, 0.90$ using LightGBM / XGBoost.
- **Consequences**: Produces empirical, asymmetric, and statistically calibrated confidence intervals that reflect real-world cost distributions.

## ADR 003: FRED PPI Index for Market Price Inflation Adjustment
- **Status**: Accepted
- **Context**: Prices from 2019 are not directly comparable to 2026 without accounting for inflation in construction materials.
- **Decision**: Normalize historical bid prices to current USD using the FRED Producer Price Index for Construction Materials (`WPUSI012011`).
- **Consequences**: Honest, transparent macroeconomic adjustment without introducing overfitting time-series models in v1.

## ADR 004: PostgreSQL + pgvector for Unified Tabular & Vector Persistence
- **Status**: Accepted
- **Context**: The system needs relational tables for line items, estimates, and users, as well as vector similarity search for spec chunk grounding.
- **Decision**: Use PostgreSQL with the `pgvector` extension instead of separate relational and vector databases.
- **Consequences**: Minimizes operational footprint and enables atomic transactions across relational records and embeddings in a single `docker-compose` instance.
