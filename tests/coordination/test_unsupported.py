from polaris.agents.models import AgentDomain, UnsupportedInferenceCode
from polaris.coordination import coordinate_assessments


def test_causal_inference_shared(all_assessments):
    coordinated = coordinate_assessments(assessments=all_assessments)
    causal = next(
        record
        for record in coordinated.shared_unsupported_inferences
        if record.inference_code is UnsupportedInferenceCode.CAUSALITY
    )

    assert causal.all_participating_agents


def test_policy_inference_aggregation(all_assessments):
    coordinated = coordinate_assessments(assessments=all_assessments)

    assert any(
        record.inference_code is UnsupportedInferenceCode.POLICY_EFFECTIVENESS
        for record in coordinated.shared_unsupported_inferences
    )


def test_medical_conclusion_public_health_specific(all_assessments):
    coordinated = coordinate_assessments(assessments=all_assessments)
    medical = next(
        record
        for record in coordinated.shared_unsupported_inferences
        if record.inference_code is UnsupportedInferenceCode.MEDICAL_CONCLUSION
    )

    assert medical.domains == (AgentDomain.PUBLIC_HEALTH,)
    assert not medical.all_participating_agents


def test_generalization_warning_aggregation(all_assessments):
    coordinated = coordinate_assessments(assessments=all_assessments)

    assert any(
        record.inference_code is UnsupportedInferenceCode.POPULATION_WIDE_GENERALIZATION
        for record in coordinated.shared_unsupported_inferences
    )
