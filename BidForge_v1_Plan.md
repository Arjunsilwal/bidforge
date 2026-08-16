# BidForge v1 Plan

An AI preconstruction estimating engine. v1 turns a bid package (a scope or spec document plus a bill of quantities) into a structured, defensible draft estimate, with every predicted line item traceable to comparable historical bids and the relevant spec text. Fully containerized, deployed live, with a trained cost model at its core.

This document is the contract with yourself. The "Out of scope" list is as important as the "In scope" list, because the fastest way to fail is to try to build v3 before v1 ships.

---

## 1. What v1 is (and is not)

**v1 is** a working, deployed, Dockerized system where a user uploads a project spec (PDF) and a bill of quantities (CSV or Excel), and gets back a structured draft estimate: each line item with a predicted unit price, an extended cost, a low/average/high range, and a short justification linked to comparable historical bids and the matching spec section. A trained cost model does the core prediction and beats naive baselines on held-out data.

**v1 is not** an automatic takeoff from drawings, a fine-tuned LLM, an agent, or a multi-tenant SaaS with billing. Those are real, but they are later versions. Building any of them now guarantees v1 never ships.

### In scope for v1

| Area | v1 deliverable |
|---|---|
| Ingestion | Parse a spec/scope PDF (text) and a bill of quantities (CSV/Excel) into a canonical line-item schema |
| Cost model | Trained model predicting unit price per line item, with a low/avg/high range. This is the flagship data science artifact |
| Retrieval (RAG) | Pull the relevant spec section and comparable historical bids for each line item, for traceability |
| Market adjustment | Convert historical prices to current dollars using a public construction price index |
| Output | Structured estimate exportable to CSV/Excel, plus a summary and per-line justification |
| Serving | FastAPI backend, async parsing job, Postgres storage, Dockerized with docker-compose |
| MLOps | MLflow experiment tracking, model registry, GitHub Actions CI, basic input-drift logging |
| UI | A review workspace where a human can inspect, adjust, and approve line items |
| Deploy | One live public URL, reproducible with `docker-compose up` |

### Explicitly out of scope for v1 (deferred, with target version)

| Deferred item | Why it waits | Target |
|---|---|---|
| Computer vision takeoff from drawings (auto quantities) | Hardest single piece, a project on its own | v3 |
| Time-series price forecasting model | v1 uses a simple, defensible index adjustment instead | v2 |
| LLM fine-tuning | Retrieval plus a trained cost model gets you most of the value | v2+ |
| Agentic multi-step workflows | Adds complexity without proving the core thesis | v3 |
| Multi-tenant auth, accounts, billing | Not needed to demonstrate the system or get pilots | v2 |
| Commercial building cost data | v1 proves the engine on free public data first (see Section 3) | v2 |

---

## 2. Definition of done for v1

v1 is finished when all of these are true:

1. There is a live, public URL where a stranger can run the demo end to end.
2. Uploading a bid package returns a structured draft estimate in under about 30 seconds for a typical package.
3. The cost model beats two baselines (historical average per item, and median per item) on a temporal holdout, and you can state the MAE and MAPE per item category.
4. The model outputs calibrated low/average/high ranges (measured, not guessed).
5. Every estimated line links to comparable historical bids and the relevant spec text.
6. `docker-compose up` brings up the whole stack locally with one command.
7. CI runs on every push: lint, type check, and tests all pass.
8. Input-drift logging records the feature distribution of each request and flags when it drifts from the training baseline.
9. The README contains an architecture diagram, a model card (data, features, metrics, limitations), and a short "what I would do differently" retrospective.

If you hit these nine, you have a portfolio piece in the top few percent and a genuine company MVP.

---

## 3. Data strategy

The whole project lives or dies on data, so this is the section to get right first.

### Primary training data: state DOT bid tabulations (free, public, structured)

State Departments of Transportation publish complete bid tabulations for public letting: every contract, every pay item, quantity, unit price, and bidder rank. Several states offer this as downloadable spreadsheets or searchable databases. Oregon (ODOT) publishes clean spreadsheets with bid date, contract number, region, item description, quantity, and price. Washington (WSDOT) runs a Unit Bid Analysis database. Texas (TxDOT) has a bid tabulations dashboard. Aggregators like BidTabs.us expose several states in one place.

Start with a single state whose data is cleanest to parse (Oregon spreadsheets are a good first target). Get the full pipeline working on one state, then add states only if you want more volume. Do not try to normalize twenty states at once. That is a v2 problem.

Fields you will build the canonical schema around: item code, item description (text), unit of measure, quantity, unit price, letting date, region or district, and contract identifier.

### Market adjustment: FRED (free API)

The Federal Reserve Economic Data service (FRED) publishes producer price indexes for construction materials, free with an API key. Use the relevant index to convert a historical unit price to current dollars before comparison. This is the honest, defensible stand-in for the price forecasting model that arrives in v2.

### Spec documents and test inputs: synthetic generator

You need spec PDFs and bill-of-quantities files to feed the system. Write a small synthetic bid-package generator: it samples real item codes and quantities from the DOT data, assembles a plausible bill of quantities, and produces a matching spec document (you can template these from public DOT standard specifications, which are freely available). This gives you unlimited, realistic, labeled test inputs, and the generator itself is a nice engineering artifact.

### Strategic note on the commercial wedge

A commercial tool already serves the DOT highway niche, so do not plan to compete there. DOT data is your free proving ground: it is the perfect public dataset to build and demonstrate the engine. Your eventual commercial differentiation (v2 and beyond) is vertical building estimation (a specific trade or building type), where the data is proprietary and the market gap is still open. Say this out loud in your README and interviews. It shows you understand the difference between a training dataset and a market.

---

## 4. Architecture (v1 slice)

The flow is: ingest, extract, predict, ground, review, export. The MLOps layer wraps all of it.

```
Upload (spec PDF + bill of quantities)
        |
        v
Ingestion service  --> canonical line-item schema (Postgres)
        |
        v
Cost predictor (trained model)  -->  unit price + low/avg/high per line
        |
        v
Retrieval (RAG)  -->  comparable historical bids + matching spec section
        |
        v
Estimate assembler  -->  structured draft estimate (+ justification)
        |
        v
Review workspace (human in the loop)  -->  approve / adjust  -->  export CSV/Excel

Cross-cutting: Docker, docker-compose, MLflow, GitHub Actions CI, drift logging
```

---

## 5. Tech stack (concrete choices)

Pick these unless you have a strong reason not to. Decisiveness beats optionality for a v1.

| Layer | Choice | Notes |
|---|---|---|
| Language | Python 3.12 | |
| Dependency mgmt | uv (or Poetry) | Fast, reproducible, lockfile committed |
| Data wrangling | pandas or polars | polars if you want the speed and a talking point |
| Modeling | scikit-learn plus XGBoost or LightGBM | Gradient-boosted trees for the tabular core |
| Text features | sentence-transformers (small model) | Embed item descriptions and spec chunks |
| Experiment tracking | MLflow | Runs, params, metrics, model registry |
| PDF parsing | pdfplumber or PyMuPDF | Text first; table extraction optional |
| Vector store | pgvector (Postgres extension) | Keeps the stack to one database. Chroma or FAISS is fine too |
| API | FastAPI plus Uvicorn, Pydantic | |
| Persistence | Postgres plus SQLAlchemy plus Alembic | Alembic for migrations |
| Async jobs | FastAPI BackgroundTasks for v1 | Move to Celery or RQ plus Redis only if you need it |
| LLM (optional) | Anthropic API for one-line justifications | Must degrade gracefully if unavailable |
| Frontend | React plus Vite plus TypeScript plus Tailwind | Stronger software engineering signal (see note) |
| Container | Docker plus docker-compose | One command to run everything |
| CI | GitHub Actions | ruff, mypy, pytest on every push |
| Quality | pytest, ruff, mypy, pre-commit | |
| Deploy | Render, Railway, or Fly.io | A small VPS also works. A Hugging Face Space can host a demo variant |

Frontend note: React is the stronger portfolio signal for software engineering roles, but if time is tight, a Streamlit review UI backed by the same FastAPI service is an acceptable v1 stand-in. Build the real API either way, so the UI is swappable.

---

## 6. The cost model (your data science centerpiece)

This is the part interviewers for data scientist roles will dig into, so build it properly.

**Baselines (build these first, always).**
- Baseline A: historical average unit price per item code (index-adjusted to the target date).
- Baseline B: median unit price per item code.
These are the "engineer's estimate" naive methods. Your model has to beat them, and quantifying by how much is the whole story.

**Model v1.**
Gradient-boosted trees (XGBoost or LightGBM) predicting unit price, with features:
- item category (target-encoded or embedded)
- item description text (sentence-transformer embedding, so non-standard descriptions still map to something)
- quantity (log-transformed, because unit price usually falls as quantity rises)
- region or district
- letting date converted to a market index value (from FRED)
- project size and season

For the low/average/high range, train quantile models (for example gradient-boosted quantile regression at the 10th, 50th, and 90th percentiles), rather than faking a range.

**Evaluation (the part that signals maturity).**
- Use a temporal split: train on older lettings, test on the most recent ones. Never a random split, because that leaks the future.
- Report MAE, MAPE, and "within X percent" accuracy, broken out per item category.
- Report calibration of the ranges: does the 10 to 90 band actually contain about 80 percent of true prices?
- Compare every number against Baselines A and B in one table.

**Model card.** Write a short model card: data sources and dates, features, metrics against baselines, and honest limitations (single state, no drawing-based quantities, index-based market adjustment). This one file does a lot of work in interviews.

---

## 7. Repository structure

```
bidforge/
  data/            ingestion, cleaning, synthetic bid-package generator
  ml/              features, training, evaluation, model card, MLflow
  api/             FastAPI app, routes, schemas, jobs, persistence
  web/             React (or Streamlit) review workspace
  infra/           Dockerfiles, docker-compose.yml, CI config
  notebooks/       EDA, model experiments (kept tidy, not the source of truth)
  tests/           pytest suite
  docs/            architecture diagram, model card, decisions log
  Makefile         make setup / train / test / run / deploy
  README.md
```

---

## 8. Build plan (8 weeks, part-time)

Adjust the pace to your availability. The order matters more than the calendar.

| Week | Focus | Output |
|---|---|---|
| 0 | Scaffold | Repo, Makefile, pre-commit, docker-compose with Postgres, empty CI that passes |
| 1 | Data acquisition and EDA | One state of DOT bid tabs downloaded, cleaned, loaded; canonical schema; FRED index wired in; EDA notebook |
| 2 | Baselines and cost model | Baselines A and B, then cost model v1 with temporal eval, tracked in MLflow |
| 3 | Ranges and RAG | Quantile ranges; spec chunking and retrieval; comparable-bid lookup; synthetic bid-package generator |
| 4 | API core | FastAPI upload endpoint, async parse job, prediction, estimate assembly, persistence, CSV/Excel export |
| 5 | Review workspace | UI to view, adjust, approve line items and export |
| 6 | Containerize and monitor | Everything in Docker via compose; input-drift logging; model registry promotion flow |
| 7 | Deploy and harden | Live public URL; error handling; graceful LLM fallback; end-to-end tests in CI |
| 8 | Document and tell the story | README, architecture diagram, model card, short demo video, interview talking points, retrospective |

---

## 9. MLOps and deployment details

- MLflow tracks every training run (params, metrics, artifacts) and holds the model registry. Promotion from "staging" to "production" is an explicit, logged step.
- Drift logging: on each request, record the feature distribution (item mix, quantity ranges, regions, dates) and compare against the training baseline using a simple statistical distance. Log a warning when it drifts. You do not need a fancy platform for v1; a logged metric plus a threshold is enough to demonstrate you understand the problem.
- CI runs ruff, mypy, and pytest on every push. A green badge in the README is a small thing that signals a lot.
- Deployment target: Render, Railway, or Fly.io for the full stack, or a small VPS. Keep a lightweight demo variant that works without secrets so anyone can try it.

---

## 10. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Item codes and formats differ across states | Start with one state only. Normalization across states is a v2 concern |
| PDF parsing is messy and varied | Constrain v1 to text-based specs plus a structured bill of quantities. No drawing parsing |
| Scope creep | The "Out of scope" table in Section 1 is binding. Revisit it whenever tempted |
| Model barely beats baseline | That is still a finding. Report it honestly and analyze why. Interviewers respect this more than a suspiciously perfect number |
| Deployment eats a week | Dockerize early (week 6 is a checkpoint, not the first attempt). Test the deploy path with a hello-world service in week 0 |

---

## 11. How to present it

- Deploy it. A live URL or working API endpoint is the single strongest signal. A local-only repo is worth far less.
- Lead with the problem and the market, not the tech. "Estimators spend 40 to 80 hours on a single bid, and this cuts the first draft to minutes" is a better opening than "I used XGBoost."
- Put the numbers up front: your metrics against baselines, in a table, in the README.
- Show the seams: a "what I would do differently" section reads as senior, not weak.
- Practice explaining it out loud for twenty minutes. You will be asked to.

## 12. What later versions unlock

- v2: time-series price forecasting (replacing the index adjustment), the first proprietary building-trade dataset, multi-tenant accounts, and a real pilot user.
- v3: computer vision takeoff from drawings (automatic quantities), agentic review, and multi-state normalization.

Open-source strategy: the generic "documents to structured estimate" pipeline can be open-sourced to build reputation and inbound interest, while the vertical tuning and proprietary data stay private. Open core, commercial edge, is a proven model and does not conflict with using this as a portfolio piece.
