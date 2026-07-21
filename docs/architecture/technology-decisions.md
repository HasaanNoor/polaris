# Technology Decisions

## Current Status

Phase 3 uses the Phase 1 Python schema foundation, the Phase 2 deterministic in-memory dataset registry, and a local CSV ingestion layer. Python 3.12 or a compatible modern Python version is the supported runtime target, with Pydantic v2 used for typed validation and JSON serialization. The ingestion loader uses Python's standard `csv` module and `hashlib` for SHA-256 checksums. Pytest is used for schema, registry, and ingestion tests. Ruff is configured for linting and formatting checks only.

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
- NumPy;
- SciPy;
- statsmodels;
- scikit-learn;
- Docker;
- GitHub Actions;
- optional OpenAI integration.

These candidates fit the likely needs of typed APIs, deterministic analysis, reproducible data processing, web workflows, and documentation-driven testing. They are not approved stack decisions in Phase 0.

Only Python, Pydantic v2, pytest, minimal Ruff configuration, local JSON manifest files, an in-memory deterministic registry, standard-library CSV parsing, and standard-library SHA-256 checksums are adopted through Phase 3. FastAPI, PostgreSQL, SQLAlchemy, Alembic, React, TypeScript, Docker, GitHub Actions, pandas, NumPy, SciPy, statsmodels, scikit-learn, orchestration frameworks, Elasticsearch, vector databases, embedding models, and LLM libraries remain deferred.

## Deferred Possibilities

Technologies such as pgvector, LangGraph, Redis, Celery, cloud services, and Terraform are deferred possibilities. They require a concrete engineering need, such as vector retrieval, complex orchestration persistence, background workloads, production hosting, or infrastructure management.

## Decision Rule

Future phases should adopt a technology only when:

- the problem is already demonstrated by an earlier phase;
- simpler local tooling is insufficient;
- reproducibility and auditability are preserved;
- tests can verify the behavior introduced;
- the decision is recorded in an ADR when it changes architecture.
