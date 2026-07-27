from polaris.coordination import coordinate_assessments
from polaris.evidence.models import LimitationCode


def test_global_observational_limitation(all_assessments):
    supplied = tuple(
        assessment for assessment in all_assessments if assessment.inherited_limitations
    )
    coordinated = coordinate_assessments(assessments=supplied)
    observational = next(
        record
        for record in coordinated.shared_limitations
        if record.limitation_code is LimitationCode.OBSERVATIONAL_ASSOCIATION
    )

    assert observational.domains
    assert observational.global_limitation


def test_domain_specific_limitation_not_dropped(all_assessments):
    coordinated = coordinate_assessments(assessments=all_assessments)

    assert any(
        record.limitation_code is LimitationCode.MISSING_DATA_EXCLUSION
        for record in coordinated.shared_limitations
    )


def test_model_scope_limitation_not_dropped(all_assessments):
    coordinated = coordinate_assessments(assessments=all_assessments)

    assert any(
        record.limitation_code is LimitationCode.LIMITED_MODEL_SCOPE
        for record in coordinated.shared_limitations
    )


def test_no_limitations_dropped_from_assessments(all_assessments):
    coordinated = coordinate_assessments(assessments=all_assessments)
    source_codes = {
        code for assessment in all_assessments for code in assessment.inherited_limitations
    }
    coordinated_codes = {record.limitation_code for record in coordinated.shared_limitations}

    assert source_codes <= coordinated_codes
