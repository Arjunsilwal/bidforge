# BidForge v1 Completion Checklist

This document tracks the deliverables, technical verification, and readiness of **BidForge v1** against the master plan specification ([`BidForge_v1_Plan.md`](../BidForge_v1_Plan.md)).

---

## 1. Deliverables Matrix (In-Scope vs Status)

| Area | Plan Deliverable | Status | Implementation File(s) |
|---|---|---|---|
| **Scaffolding & Environment** | Virtualenv, dependencies, gitignore, Makefile, CI | ✅ Complete | [`.gitignore`](../.gitignore), [`Makefile`](../Makefile), [`pyproject.toml`](../pyproject.toml), [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) |
| **Ingestion Engine** | Parse spec PDF & BOQ (CSV/Excel) into canonical schema | ✅ Complete | [`data/schemas.py`](../data/schemas.py), [`data/dot_parser.py`](../data/dot_parser.py), [`api/services/ingestion.py`](../api/services/ingestion.py) |
| **Synthetic Generator** | Generate labeled test spec PDFs and BOQs | ✅ Complete | [`data/synthetic_generator.py`](../data/synthetic_generator.py) |
| **Market Price Adjustment** | FRED Construction Materials PPI ratio converter | ✅ Complete | [`data/fred_client.py`](../data/fred_client.py) |
| **Baseline Benchmarks** | Baseline A (Historical Mean) & Baseline B (Median) | ✅ Complete | [`ml/baselines.py`](../ml/baselines.py) |
| **Quantile Cost Model** | 10th (Low), 50th (Avg), 90th (High) quantile regressors | ✅ Complete | [`ml/features.py`](../ml/features.py), [`ml/train.py`](../ml/train.py) |
| **Temporal Evaluation** | MAE, MAPE, 10-90% interval coverage vs. baselines | ✅ Complete | [`ml/evaluate.py`](../ml/evaluate.py) |
| **Retrieval & Grounding (RAG)** | Spec chunk semantic matching & comparable bid lookup | ✅ Complete | [`api/services/rag.py`](../api/services/rag.py) |
| **API Backend** | FastAPI async endpoints, SQLAlchemy ORM, SQLite/Postgres | ✅ Complete | [`api/main.py`](../api/main.py), [`api/routes/estimates.py`](../api/routes/estimates.py), [`api/models.py`](../api/models.py) |
| **Review Workspace UI** | Streamlit review UI, overrides, price bands, exports | ✅ Complete | [`web/app.py`](../web/app.py) |
| **Export Service** | Formatted client-ready CSV and Excel workbooks | ✅ Complete | [`api/services/exporter.py`](../api/services/exporter.py) |
| **MLOps & Input Drift** | MLflow tracking & real-time KS distribution drift check | ✅ Complete | [`ml/registry.py`](../ml/registry.py), [`ml/drift.py`](../ml/drift.py) |
| **Containerization** | Dockerfiles for API and Web, docker-compose orchestration | ✅ Complete | [`infra/Dockerfile.api`](../infra/Dockerfile.api), [`infra/Dockerfile.web`](../infra/Dockerfile.web), [`infra/docker-compose.yml`](../infra/docker-compose.yml) |
| **Test Suite** | Comprehensive pytest suite (16 tests across all layers) | ✅ Complete (16/16 passing) | [`tests/`](../tests) |

---

## 2. Definition of Done (Section 2 of Plan)

- [x] **1. One-command local reproducibility**: `docker-compose -f infra/docker-compose.yml up` or `make run-api` / `make run-web`.
- [x] **2. Sub-30s estimate generation**: Fast vectorized inference & chunk retrieval pipeline.
- [x] **3. Baseline comparison framework**: Evaluator tracks MAE and MAPE against Historical Mean & Median.
- [x] **4. Measured, calibrated price ranges**: 10th, 50th, and 90th percentile pinball loss gradient boosting.
- [x] **5. Grounding and traceability**: Every line item links to matching spec section and comparable historical bids.
- [x] **6. Automated CI**: GitHub Actions runs `ruff check`, `ruff format --check`, `mypy`, and `pytest` on every push and pull request, across Python 3.11 and 3.12.
- [x] **7. Input-drift monitoring**: KS-test on item quantities and unseen item code detector on incoming batches.
- [x] **8. Architecture & Model Documentation**: [`docs/architecture.md`](./architecture.md) & [`docs/model_card.md`](./model_card.md).
- [ ] **9. Public URL Deployment**: Pending cloud host selection (Render, Fly.io, Railway, or VPS).

---

## 3. Next Steps (User Action Plan)

### Step 1: Acquire Real DOT Training Bid Tabs (Optional for production scale)
- Download historical letting spreadsheets from Oregon DOT (ODOT) or Washington DOT (WSDOT).
- Place raw spreadsheets into `data/raw/`.
- Run `python -m ml.train` to train models on real letting data and save checkpoints to `models/`.

### Step 2: Configure Live API Keys (Optional)
- Copy `.env.example` to `.env`.
- Add your free FRED API key (`FRED_API_KEY`) from [St. Louis Fed](https://fred.stlouisfed.org/docs/api/api_key.html).
- (Optional) Add `ANTHROPIC_API_KEY` if you want Claude narrative summaries.

### Step 3: Run & Demo Locally
- Start the API: `make run-api`
- Start the UI: `make run-web`
- In the UI at [http://localhost:8501](http://localhost:8501), click **"Instant Demo Package"** -> **"Generate & Estimate"**.
- Inspect predicted price bands, spec grounding, apply a price override, and export to Excel.

### Step 4: Deploy Live Public Demo
- Connect your GitHub repo ([`Arjunsilwal/bidforge`](https://github.com/Arjunsilwal/bidforge)) to Render / Fly.io / Railway using `infra/Dockerfile.api` and `infra/Dockerfile.web`.
