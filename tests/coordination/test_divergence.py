from polaris.coordination import DivergenceType, coordinate_assessments


def test_different_domain_relevance_divergence(all_assessments):
    coordinated = coordinate_assessments(assessments=all_assessments)

    assert any(
        divergence.divergence_type is DivergenceType.DIFFERENT_RELEVANCE_CLASSIFICATION
        for divergence in coordinated.divergences
    )


def test_domain_specific_concern_divergence(all_assessments):
    coordinated = coordinate_assessments(assessments=all_assessments)

    assert any(
        divergence.divergence_type is DivergenceType.DOMAIN_SPECIFIC_CONCERN
        for divergence in coordinated.divergences
    )


def test_uneven_coverage_divergence(all_assessments):
    coordinated = coordinate_assessments(assessments=all_assessments)

    assert any(
        divergence.divergence_type is DivergenceType.UNEVEN_EVIDENCE_COVERAGE
        for divergence in coordinated.divergences
    )


def test_no_fabricated_contradiction_terms(all_assessments):
    coordinated = coordinate_assessments(assessments=all_assessments)
    payload = coordinated.model_dump_json()

    assert "contradiction" not in payload
    assert "conflict" not in payload


def test_divergence_ordering_is_deterministic(all_assessments):
    first = coordinate_assessments(assessments=all_assessments)
    second = coordinate_assessments(assessments=tuple(reversed(all_assessments)))

    assert tuple(item.divergence_id for item in first.divergences) == tuple(
        item.divergence_id for item in second.divergences
    )
