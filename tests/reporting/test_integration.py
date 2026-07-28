import copy
import json

from polaris.reporting.models import ReportFormat
from polaris.reporting.service import generate_report


def test_phase3_to_phase9_integration(report_request):
    before = copy.deepcopy(report_request.model_dump(mode="json"))
    generated = generate_report(request=report_request)
    report = generated.report
    assert (
        report.dataset_section.source_checksum_sha256
        == report_request.ingestion_result.checksum_sha256
    )
    assert report.provenance_section.analysis_result_id == report_request.analysis_result.result_id
    assert set(report.provenance_section.claim_ids) == {
        claim.claim_id for claim in report_request.evidence_artifact.claim_candidates
    }
    assert report.provenance_section.coordinated_assessment_id == (
        report_request.coordinated_assessment.coordinated_assessment_id
    )
    assert (
        report.provenance_section.synthesis_artifact_id
        == report_request.synthesis_artifact.synthesis_id
    )
    assert report.limitations_section.limitation_codes
    assert report.unsupported_inferences_section.unsupported_inferences
    assert json.loads(report.model_dump_json())["report_id"] == report.report_id
    assert report_request.model_dump(mode="json") == before


def test_no_credentials_or_network_required(report_request):
    generated = generate_report(
        request=report_request.model_copy(update={"output_format": ReportFormat.HTML})
    )
    assert generated.rendered_content
