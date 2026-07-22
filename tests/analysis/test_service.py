from helpers import make_spec

from polaris.analysis.models import AnalysisRequest
from polaris.analysis.service import run_analysis


def test_result_serializes_without_invalid_json_numbers(analysis_ingestion):
    result = run_analysis(
        request=AnalysisRequest(
            ingestion_result=analysis_ingestion,
            statistical_specification=make_spec(
                procedure="ordinary_least_squares",
                exposures=["x", "x_duplicate"],
            ),
        )
    )

    payload = result.model_dump_json()
    assert "NaN" not in payload
    assert "Infinity" not in payload


def test_provenance_preserves_source_identity_and_rows(analysis_ingestion):
    result = run_analysis(
        request=AnalysisRequest(
            ingestion_result=analysis_ingestion,
            statistical_specification=make_spec(
                procedure="ordinary_least_squares",
                exposures=["x"],
            ),
        )
    )

    assert result.source_checksum_sha256 == analysis_ingestion.checksum_sha256
    assert result.provenance.source_checksum_sha256 == analysis_ingestion.checksum_sha256
    assert result.provenance.included_row_numbers == result.analysis_sample.included_row_numbers
    assert result.analysis_timestamp.tzinfo is not None
    assert result.provenance.library_versions
