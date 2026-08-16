# BidForge

> **AI Preconstruction Estimating Engine** — Turning bid packages (specifications + bill of quantities) into defensible, traceable draft estimates with calibrated cost distributions and historical grounding.

[![CI](https://github.com/Arjunsilwal/bidforge/actions/workflows/ci.yml/badge.svg)](https://github.com/Arjunsilwal/bidforge/actions/workflows/ci.yml)
[![Python 3.11 | 3.12](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)

---

## Overview

BidForge v1 ingests a bid package consisting of:
1. **Scope/Spec PDF document** (parsed into searchable semantic chunks)
2. **Bill of Quantities (BOQ)** in CSV or Excel format

It produces a structured draft estimate where every predicted line item includes:
- **Calibrated Unit Price Range**: Low (10th percentile), Expected/Average (50th percentile), and High (90th percentile)
- **Extended Cost**: Computed using predicted price and project quantity
- **Historical Grounding**: Traceable links to comparable state DOT historical bids
- **Spec Section Reference**: Semantic retrieval connecting the line item to the exact spec clause
- **Human-in-the-Loop Review Workspace**: Interactive UI to inspect, override, approve, and export to Excel/CSV

---

## System Architecture

```
Upload Spec (PDF) + Bill of Quantities (CSV/Excel)
                     |
                     v
           Ingestion Service
 (PDF text chunking + canonical line item parsing)
                     |
                     v
        Quantile Cost Predictor (ML)
 (XGBoost / LightGBM 10th, 50th, 90th percentiles)
                     |
                     v
             Retrieval (RAG)
(Comparable historical bids + relevant spec sections)
                     |
                     v
            Estimate Assembler
  (Structured draft estimate + line justifications)
                     |
                     v
       Review Workspace & Export UI
   (Human review, price override, Excel export)
```

---

## Quickstart

### Prerequisites
- Python 3.11+ (CI covers 3.11 and 3.12), or Docker & Docker Compose
- PostgreSQL with `pgvector` extension (optional if using SQLite for local tests)

### 1. Setup Local Environment
```bash
# Clone the repository
git clone https://github.com/Arjunsilwal/bidforge.git
cd bidforge

# Create environment and install dependencies
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
# Terminal 1: Run FastAPI backend
make run-api

# Terminal 2: Run Streamlit review workspace
make run-web
```

---

## Project Structure

```
bidforge/
├── data/              # Ingestion, canonical schemas, FRED client, synthetic data generator
├── ml/                # Feature engineering, quantile cost models, baselines, MLflow, drift
├── api/               # FastAPI backend app, routes, models, schemas, and RAG services
├── web/               # Review workspace UI (Streamlit / React)
├── infra/             # Dockerfiles, docker-compose.yml, CI configs
├── notebooks/         # Exploratory data analysis & model experiments
├── tests/             # Pytest test suite for schemas, ML baselines, API, and drift
├── docs/              # Architecture diagrams, model cards, ADRs
├── BidForge_v1_Plan.md# Complete v1 master project specification
├── Makefile           # One-command setup, test, train, run, and deploy scripts
├── pyproject.toml     # Project metadata and tooling configurations
├── requirements.txt   # Locked Python package dependencies
└── README.md
```

---

## MLOps & Rigor

- **Strict Temporal Holdout**: Models are evaluated only on future lettings to avoid lookahead bias.
- **Quantile Calibration**: Empirically measured 10-90% prediction intervals.
- **Baselines Comparison**: Evaluated against historical mean and median unit price baselines.
- **Input Drift Detection**: Continuous distribution checks on incoming inference items against training baselines.

---

## Security posture

**v1 ships no authentication.** Every API endpoint is unauthenticated, including the
write paths (`POST /upload`, `PATCH .../line-items/...`, `POST .../approve`) and the
export endpoints. Multi-tenant auth is deferred to v2 by design, which has one hard
consequence: **do not expose this deployment to the open internet with real bid data in
it.** Anyone who can reach the API can read, alter, and approve every estimate. For the
public demo, run it with synthetic data only, or put it behind an authenticating proxy.

What v1 *does* defend against:

| Control | Where |
|---|---|
| Spreadsheet formula injection (`=`, `+`, `-`, `@` cells) neutralized on export | `api/services/exporter.py` |
| Upload size capped at 10 MB per file, rejected with `413` before parsing | `api/routes/estimates.py` |
| Parser exceptions logged server-side, generic message returned to the client | `api/routes/estimates.py` |
| CORS restricted to `ALLOWED_ORIGINS`; never falls back to `*` | `api/main.py`, `api/config.py` |
| Request inputs bounded (lengths, `item_count`, finite non-negative prices) | `api/routes/estimates.py`, `api/schemas.py` |
| Containers run as an unprivileged user with `no-new-privileges` | `infra/Dockerfile.*`, `infra/docker-compose.yml` |
| Postgres and MLflow bound to loopback, not published to the network | `infra/docker-compose.yml` |
| `POSTGRES_PASSWORD` required — no default credential | `infra/docker-compose.yml` |
| Secrets, `.git`, and local state excluded from image builds | `.dockerignore` |

Queries go through the SQLAlchemy ORM with bound parameters throughout, so there is no
string-built SQL.

Before deploying publicly, add: authentication and per-user authorization, rate
limiting, a request-body cap at the reverse proxy, and TLS termination.

---

## License
MIT License
