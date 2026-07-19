# Technology Decisions

## Current Status

Phase 0 makes no final implementation commitments. The project currently records architectural and methodology requirements only.

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

## Deferred Possibilities

Technologies such as pgvector, LangGraph, Redis, Celery, cloud services, and Terraform are deferred possibilities. They require a concrete engineering need, such as vector retrieval, complex orchestration persistence, background workloads, production hosting, or infrastructure management.

## Decision Rule

Future phases should adopt a technology only when:

- the problem is already demonstrated by an earlier phase;
- simpler local tooling is insufficient;
- reproducibility and auditability are preserved;
- tests can verify the behavior introduced;
- the decision is recorded in an ADR when it changes architecture.
