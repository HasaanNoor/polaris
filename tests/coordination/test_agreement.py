from polaris.coordination import AgreementType, coordinate_assessments


def test_shared_evidence_agreement(all_assessments):
    coordinated = coordinate_assessments(assessments=all_assessments)

    assert any(
        agreement.agreement_type is AgreementType.SHARED_EVIDENCE
        for agreement in coordinated.agreements
    )


def test_shared_claim_agreement(all_assessments):
    coordinated = coordinate_assessments(assessments=all_assessments)

    assert any(
        agreement.agreement_type is AgreementType.SHARED_CLAIM
        for agreement in coordinated.agreements
    )


def test_shared_limitation_and_unsupported_agreement(all_assessments):
    coordinated = coordinate_assessments(assessments=all_assessments)
    types = {agreement.agreement_type for agreement in coordinated.agreements}

    assert AgreementType.SHARED_LIMITATION in types
    assert AgreementType.SHARED_UNSUPPORTED_INFERENCE in types


def test_agreement_id_is_deterministic(all_assessments):
    first = coordinate_assessments(assessments=all_assessments)
    second = coordinate_assessments(assessments=tuple(reversed(all_assessments)))

    assert tuple(item.agreement_id for item in first.agreements) == tuple(
        item.agreement_id for item in second.agreements
    )


def test_no_false_cross_domain_agreement_for_one_agent(all_assessments):
    coordinated = coordinate_assessments(assessments=(all_assessments[0],))

    assert not [
        agreement
        for agreement in coordinated.agreements
        if agreement.agreement_type in {AgreementType.SHARED_EVIDENCE, AgreementType.SHARED_CLAIM}
    ]
