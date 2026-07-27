from datetime import UTC, datetime

from polaris.coordination import (
    CoordinationFindingCode,
    CoordinationRequest,
    coordinate_assessments,
)


def test_coordinate_assessments_accepts_request(all_assessments):
    coordinated = coordinate_assessments(request=CoordinationRequest(assessments=all_assessments))

    assert coordinated.source_assessment_ids == tuple(
        sorted(assessment.assessment_id for assessment in all_assessments)
    )


def test_provenance_timestamp_override(all_assessments):
    timestamp = datetime(2026, 7, 26, tzinfo=UTC)
    coordinated = coordinate_assessments(
        assessments=all_assessments,
        coordination_timestamp=timestamp,
    )

    assert coordinated.provenance.coordination_timestamp == timestamp


def test_coordination_findings_include_causality_warning(all_assessments):
    coordinated = coordinate_assessments(assessments=all_assessments)

    assert any(
        finding.finding_code is CoordinationFindingCode.BROAD_UNSUPPORTED_CAUSALITY_WARNING
        for finding in coordinated.coordination_findings
    )


def test_source_objects_are_not_mutated(all_assessments):
    before = tuple(assessment.model_copy(deep=True) for assessment in all_assessments)

    coordinate_assessments(assessments=all_assessments)

    assert all_assessments == before
