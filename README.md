# Long COVID GEO Expression Explorer

A study-aware, dashboard-first explorer for curated public Long COVID GEO expression data.

This project is being built as a structured data product, not a notebook-only analysis. The intended architecture separates:

- automated Bronze / Silver / Gold data pipeline
- reusable analysis and domain logic
- explicit app-facing data contracts
- thin Streamlit UI
- safe export behavior with provenance

## Current Status

Milestone 0: repository foundation.

The repository currently contains project scaffolding, Python tooling, and test infrastructure. Real GEO ingestion, harmonization, differential expression, Gold artifact publication, and dashboard views come after the data contract is written.

## Setup

This project uses `uv` and Python 3.11.

```bash
uv sync
```

## Test

```bash
uv run pytest
```

## Run UI

```bash
uv run streamlit run app/ui/app.py
```
