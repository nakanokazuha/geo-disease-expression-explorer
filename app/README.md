# Application Layout

This directory contains the implementation for the Long COVID GEO Expression Explorer.

## Boundaries

- `ui/`: Streamlit entrypoint, views, components, state, formatting, and theme helpers.
- `data_pipeline/`: ingestion, Bronze, Silver, Gold, publishing, orchestration, and jobs.
- `analysis/`: reusable preprocessing, harmonization, statistics, differential expression, visualization prep, and validation logic.
- `domain/`: models, schemas, enums, contracts, filters, and provenance rules.
- `content/`: human-written copy, glossary entries, interpretation text, and dataset profiles.
- `storage/`: local Bronze, Silver, Gold, and manifest artifacts.
- `notebooks/`: exploration and validation only; notebooks are not production pipeline steps.
- `tests/`: unit, integration, contract, and snapshot tests.

## Core Rule

The Streamlit UI reads published Gold artifacts. It must not perform raw GEO ingestion, heavy harmonization, or full differential-expression computation at runtime.
