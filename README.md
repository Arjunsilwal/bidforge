# BidForge

> **AI Preconstruction Estimating Engine** — Turning bid packages (specifications + bill of quantities) into defensible, traceable draft estimates with calibrated cost distributions and historical grounding.

[![CI](https://github.com/Arjunsilwal/bidforge/actions/workflows/ci.yml/badge.svg)](https://github.com/Arjunsilwal/bidforge/actions/workflows/ci.yml)
[![Python 3.11 | 3.12](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)

---

## Overview

BidForge v1 turns a complex preconstruction bid package into a structured, defensible draft estimate in seconds.

### Inputs
1. **Scope/Spec Document** (PDF or Text) — parsed into semantic chunks
2. **Bill of Quantities (BOQ)** (CSV or Excel) — parsed into a canonical line-item schema

### Outputs
- **Calibrated Unit Price Bands**: 10th percentile (Low), 50th percentile (Expected/Average), and 90th percentile (High)
- **Extended Cost Calculations**: Computed per line item and aggregated for project totals
- **Historical Grounding (RAG)**: Traceable links to comparable state DOT historical letting bids
- **Spec Grounding (RAG)**: Semantic matching to the exact specification clauses and divisions
- **Review Workspace UI**: Human-in-the-loop workspace to inspect, override unit prices, approve estimates, and export directly to client-ready Excel and CSV formats

---

## System Architecture

```
Upload Spec (PDF) + Bill of Quantities (CSV/Excel)
                     │
                     ▼
           Ingestion Service
 (PDF text chunking + canonical line item parsing)
                     │
                     ▼
        Quantile Cost Predictor (ML)
 (XGBoost / LightGBM 10th, 50th, 90th percentiles)
                     │
                     ▼
             Retrieval (RAG)
(Comparable historical bids + relevant spec sections)
                     │
                     ▼
            Estimate Assembler
  (Structured draft estimate + line justifications)
                     │
                     ▼
       Review Workspace & Export UI
   (Human review, price override, Excel export)
```

---

## Documentation

- [Architecture & System Flow](docs/architecture.md) — Detailed technical specifications, data pipelines, and database design
- [Model Card](docs/model_card.md) — Features, baselines comparison (Mean vs. Median), metrics, and limitations
- [Architecture Decision Records (ADRs)](docs/decisions.md) — Technical tradeoffs and decisions log
- [v1 Completion Checklist](docs/V1_COMPLETION_CHECKLIST.md) — Deliverables matrix, Definition of Done status, and roadmap
- [Master v1 Plan](BidForge_v1_Plan.md) — Original scope contract and multi-phase build plan

---

## Quickstart

### Prerequisites
- Python 3.11+ (CI validates against Python 3.11 and 3.12)
- Docker & Docker Compose (optional for containerized execution)

### 1. Setup Local Environment
```bash
# Clone repository
git clone https://github.com/Arjunsilwal/bidforge.git
cd bidforge

# Create virtual environment and install dependencies
make setup
source .venv/bin/activate

# Configure environment variables
cp .env.example .env
```

### 2. Run with Docker Compose
```bash
make docker-up
```
- **FastAPI Backend & Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Review Workspace UI**: [http://localhost:8501](http://localhost:8501)
- **MLflow Tracking Dashboard**: [http://localhost:5000](http://localhost:5000)

### 3. Run Locally (Without Docker)
```bash
# Terminal 1: Launch FastAPI backend
make run-api

# Terminal 2: Launch Streamlit review workspace
make run-web
```

---

## Testing & Quality

Run the complete test suite (16 tests covering schemas, ML baselines, RAG retrieval, drift detection, and API endpoints):

```bash
# Run pytest test suite
make test

# Run linter and formatter checks
make lint

# Run static type checking
make typecheck
```

---

## Project Structure

```
bidforge/
├── api/               # FastAPI application, routes, ORM models, schemas, and RAG services
│   ├── routes/        # Estimate upload, review, override, and export endpoints
│   └── services/      # Ingestion, RAG grounding, estimator, and exporter
├── data/              # Canonical schemas, DOT bid tab parser, FRED client, synthetic generator
├── docs/              # Architecture diagrams, model cards, ADRs, and v1 completion checklist
├── infra/             # Dockerfiles, docker-compose.yml, and deployment configurations
├── ml/                # Feature engineering, quantile cost models, baselines, MLflow, drift
├── notebooks/         # Exploratory data analysis & model experiments
├── tests/             # Pytest test suite (16 unit & integration tests)
├── web/               # Streamlit review workspace UI
├── .github/workflows/ # GitHub Actions CI matrix (Python 3.11, 3.12)
├── BidForge_v1_Plan.md# Complete v1 master project specification
├── Makefile           # One-command CLI (setup, test, train, run, and docker-up)
├── pyproject.toml     # Project metadata and tooling configurations
├── requirements.txt   # Locked Python package dependencies
└── README.md
```

---

## MLOps & Rigor

- **Strict Temporal Holdout**: Models are evaluated strictly on future lettings to eliminate lookahead bias.
- **Quantile Calibration**: Empirically measured 10th-90th prediction intervals.
- **Baselines Comparison**: Evaluated against historical mean and median unit price benchmarks.
- **Input Drift Detection**: Continuous distribution checks (Kolmogorov-Smirnov test and novel item code tracking) on inference batches against training baselines.
- **FRED Macroeconomic Deflator**: Normalizes historical prices to present-day dollars using the FRED Construction Materials PPI (`WPUSI012011`).

---

## Security Posture

**v1 ships no multi-tenant authentication** (deferred to v2 by design). For public demo deployments, use synthetic data or place behind an authenticating reverse proxy.

What v1 implements:
- **Spreadsheet Formula Injection Defense**: Neutralizes `=, +, -, @` prefix characters upon Excel/CSV export (`api/services/exporter.py`).
- **File Upload Limits**: Capped at 10 MB per file, returning `413 Payload Too Large` before parsing.
- **CORS Allowlist**: Restricted explicitly to `ALLOWED_ORIGINS` from environment settings.
- **Bound Parameter ORM Queries**: All database operations use SQLAlchemy ORM parameter binding to prevent SQL injection.
- **Unprivileged Containers**: Non-root container user execution in Dockerfiles.

---

## License
MIT License
