# Technology Decisions

## Current Status

Phase 15 uses the Phase 1 Python schema foundation, the Phase 2 deterministic in-memory dataset registry, the Phase 3 local CSV ingestion layer, the Phase 4 deterministic statistical analysis package, the Phase 5 deterministic structured evidence package, the Phase 6 deterministic domain-agent package, the Phase 7 deterministic coordination package, the Phase 8 guardrailed synthesis package, the Phase 9 deterministic report-generation package, the Phase 10 provider acquisition package, the Phase 12 country-year harmonization package, the Phase 13 in-process project orchestration package, the Phase 14 local literature package, and the Phase 15 WHO panel package. Python 3.12 or a compatible modern Python version is the supported runtime target, with Pydantic v2 used for typed validation and JSON serialization. The ingestion, harmonization, and WHO exports use Python's standard `csv` module and `hashlib` for SHA-256 checksums. Literature ingestion uses standard-library file I/O, JSON parsing, normalization, SHA-256 checksums, and in-process BM25-style lexical retrieval. NumPy and SciPy are adopted for Phase 4 numerical arrays, correlations, distribution statistics, and linear-algebra-backed OLS diagnostics. Phases 5-9 and 12-15 use standard-library SHA-256 hashing for deterministic artifact IDs. Phase 15 adds no new runtime dependencies, workflow engine, database, async runtime, background job system, vector database, Elasticsearch service, online search API, or WHO-specific agent. Pytest is used for schema, registry, ingestion, analysis, evidence, agent, coordination, synthesis, reporting, provider, real-data, harmonization, project, literature, and WHO tests. Ruff is configured for linting and formatting checks only.

## Candidate Direction

The following technologies are candidates for later evaluation:

- Python;
- FastAPI;
- PostgreSQL;
- SQLAlchemy;
- Alembic;
- React;
- TypeScript;
- Plotly;
- pandas;
- statsmodels;
- scikit-learn;
- Docker;
- GitHub Actions;
- optional OpenAI integration.

These candidates fit the likely needs of typed APIs, deterministic analysis, reproducible data processing, web workflows, and documentation-driven testing. They are not approved stack decisions in Phase 0.

Only Python, Pydantic v2, NumPy, SciPy, pytest, minimal Ruff configuration, local JSON manifest files, an in-memory deterministic registry, standard-library CSV parsing, standard-library SHA-256 checksums, deterministic local statistical execution, deterministic local evidence extraction, deterministic rule-based domain assessment, deterministic structured coordination, guardrailed structured synthesis, deterministic report rendering, provider snapshot models, deterministic country-year harmonization, lightweight synchronous project orchestration, deterministic local lexical literature retrieval, and deterministic WHO GHO panel curation are adopted through Phase 15. FastAPI, PostgreSQL, SQLAlchemy, Alembic, React, TypeScript, Docker, GitHub Actions, pandas, statsmodels, scikit-learn, external orchestration frameworks, Elasticsearch, vector databases, mandatory embedding models, concrete LLM SDK dependencies, online academic search APIs, autonomous web browsing, PDF export, DOCX export, and LaTeX export remain deferred.

## Deferred Possibilities

Technologies such as pgvector, LangGraph, Redis, Celery, cloud services, and Terraform are deferred possibilities. They require a concrete engineering need, such as vector retrieval, complex orchestration persistence, background workloads, production hosting, or infrastructure management.

## Decision Rule

Future phases should adopt a technology only when:

- the problem is already demonstrated by an earlier phase;
- simpler local tooling is insufficient;
- reproducibility and auditability are preserved;
- tests can verify the behavior introduced;
- the decision is recorded in an ADR when it changes architecture.
