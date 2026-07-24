import pytest
from evidence_helpers import ingest_fixture


@pytest.fixture
def evidence_ingestion(tmp_path):
    return ingest_fixture(tmp_path)
