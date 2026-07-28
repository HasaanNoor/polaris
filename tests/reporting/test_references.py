import pytest

from polaris.reporting.errors import ReportReferenceError
from polaris.reporting.models import ReferenceIndexEntry, ReferenceKind
from polaris.reporting.service import build_research_report
from polaris.reporting.validation import validate_report


def test_reference_index_contains_source_ids(report_request):
    report = build_research_report(request=report_request)
    reference_ids = {entry.reference_id for entry in report.reference_index}
    assert {
        record.evidence_id for record in report_request.evidence_artifact.evidence_records
    } <= reference_ids
    assert {
        claim.claim_id for claim in report_request.evidence_artifact.claim_candidates
    } <= reference_ids
    assert set(report_request.coordinated_assessment.source_assessment_ids) <= reference_ids


def test_fabricated_reference_rejected(report_request):
    report = build_research_report(request=report_request)
    bad = report.model_copy(
        update={
            "reference_index": (
                *report.reference_index,
                ReferenceIndexEntry(
                    reference_id="evidence_fabricated",
                    reference_kind=ReferenceKind.EVIDENCE,
                    label="Fabricated",
                ),
            )
        }
    )
    with pytest.raises(ReportReferenceError):
        validate_report(bad, report_request)


def test_reference_ordering_is_deterministic(report_request):
    report_a = build_research_report(request=report_request)
    report_b = build_research_report(request=report_request)
    assert report_a.reference_index == report_b.reference_index
