# BidForge v1 Architecture

BidForge is an AI preconstruction estimating engine designed to transform a bid package (a scope/spec PDF and a bill of quantities in CSV/Excel) into a structured, defensible draft estimate.

## System Flow Diagram

```
+-------------------------------------------------------------------------+
|                              USER INGESTION                             |
|  1. Project Scope & Specification (PDF)                                 |
|  2. Bill of Quantities (CSV / Excel)                                    |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
|                            INGESTION SERVICE                            |
|  - Parse text chunks from spec PDF (pdfplumber)                         |
|  - Parse tabular line items from BOQ (pandas/openpyxl)                  |
|  - Canonical schema validation (Pydantic / Postgres)                    |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
|                             ML COST ENGINE                              |
|  - Market adjustment via FRED Construction Price Index (WPUSI012011)    |
|  - Feature extraction: categorical, log-quantity, embeddings            |
|  - Quantile gradient boosting (XGBoost / LightGBM at 10%, 50%, 90%)     |
|  - Baseline benchmark comparison (Historical Mean & Median)             |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
|                        RETRIEVAL (RAG & GROUNDING)                      |
|  - Spec chunk semantic matching (sentence-transformers + pgvector)      |
|  - Historical comparable bid lookup (ODOT state letting dataset)        |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
|                            ESTIMATE ASSEMBLER                           |
|  - Compute extended costs (Unit Price x Quantity)                       |
|  - Assemble low/avg/high range bounds                                   |
|  - Attach comparable bids & spec citation for full traceability        |
|  - Optional LLM narrative summary generation                            |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
|                        REVIEW WORKSPACE & EXPORT                        |
|  - Human-in-the-loop inspection & manual unit price override            |
|  - Approval workflow                                                    |
|  - Export to structured Excel & CSV format                              |
+-------------------------------------------------------------------------+
```

## Cross-Cutting Services
- **FastAPI Backend**: Async processing, schema validation, persistence.
- **PostgreSQL + pgvector**: Unified database for structured estimates, historical bid tabs, and vector embeddings.
- **MLflow**: Experiment tracking, metrics logging, artifact storage, and model registry.
- **Input-Drift Logging**: Real-time statistical distance comparison between incoming requests and training distributions.
