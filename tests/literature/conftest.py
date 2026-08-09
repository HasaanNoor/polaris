from datetime import UTC, datetime
from pathlib import Path

import pytest

from polaris.evidence.service import extract_evidence
from polaris.literature import ingest_literature_corpus
from tests.evidence.evidence_helpers import ingest_fixture, run_fixture_analysis
from tests.reporting.conftest import report_request as report_request
from tests.reporting.conftest import reporting_pipeline as reporting_pipeline


@pytest.fixture
def literature_dir(tmp_path: Path) -> Path:
    root = tmp_path / "corpus"
    root.mkdir()
    (root / "income_health.md").write_text(
        "\n".join(
            [
                "# Income and Health",
                "",
                "Higher GDP per capita is often discussed alongside life expectancy in",
                "cross-country association research. This illustrative source is local.",
                "",
                "## Limits",
                "",
                "A lexical match does not establish causality or scientific agreement.",
            ]
        ),
        encoding="utf-8",
    )
    (root / "education.txt").write_text(
        "Education and health literacy may contextualize public health outcomes.",
        encoding="utf-8",
    )
    (root / "structured.json").write_text(
        """
{
  "document_id": "structured_income_health",
  "title": "Structured Income Health Note",
  "authors": ["Test Author"],
  "year": 2024,
  "publication": "Local Test Corpus",
  "doi": "10.0000/test",
  "url": "https://example.test/literature",
  "citation_text": "Test Author. 2024. Structured Income Health Note.",
  "full_text": "GDP per capita and life expectancy are variables in health research."
}
""".strip(),
        encoding="utf-8",
    )
    (root / "manifest.json").write_text(
        """
{
  "documents": {
    "income_health.md": {
      "document_id": "income_health_note",
      "title": "Income and Health",
      "authors": ["Repository Author"],
      "year": 2026,
      "publication": "Local Test Corpus",
      "citation_text": "Repository Author. 2026. Income and Health."
    },
    "education.txt": {
      "document_id": "education_health_note",
      "title": "Education and Health",
      "authors": ["Repository Author"],
      "year": 2025,
      "publication": "Local Test Corpus",
      "citation_text": "Repository Author. 2025. Education and Health."
    }
  }
}
""".strip(),
        encoding="utf-8",
    )
    return root


@pytest.fixture
def literature_corpus(literature_dir):
    return ingest_literature_corpus(
        literature_dir,
        manifest_path=literature_dir / "manifest.json",
        ingestion_timestamp=datetime(2026, 8, 8, tzinfo=UTC),
    )


@pytest.fixture
def regression_evidence(tmp_path):
    ingestion = ingest_fixture(tmp_path)
    analysis = run_fixture_analysis(
        ingestion,
        procedure="ordinary_least_squares",
        analysis_type="regression",
        model_family="linear",
        outcome="y",
        exposures=["x"],
        covariates=["z"],
        significance_threshold=0.05,
    )
    return extract_evidence(analysis_result=analysis)
