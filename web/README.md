# BidForge Web Review Workspace

This directory contains the user interface for inspecting, adjusting, approving, and exporting draft estimates.

## Running the Streamlit App
```bash
streamlit run web/app.py --server.port 8501
```

## Features
- **Instant Demo Package Generator**: Generates and parses synthetic DOT bid packages in seconds.
- **Quantile Price Bands Visualization**: Displays 10th (Low), 50th (Expected), and 90th (High) percentile prices per line item.
- **RAG Spec & Comparable Bids Grounding**: Displays matching spec clauses and historical comparable letting rows for defense and auditability.
- **Human-in-the-loop Overrides**: Allows estimators to adjust unit prices, automatically updating extended totals.
- **Client Exports**: Direct download of CSV and formatted Excel workbooks.
