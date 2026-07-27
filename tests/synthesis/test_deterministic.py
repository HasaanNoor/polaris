from polaris.agents.models import AgentDomain, UnsupportedInferenceCode
from polaris.synthesis import SynthesisMode, SynthesisRequest, synthesize_assessment


def test_deterministic_synthesis_surfaces_domains_and_limits(coordinated):
    artifact = synthesize_assessment(request=SynthesisRequest(coordinated_assessment=coordinated))

    assert artifact.synthesis_mode is SynthesisMode.DETERMINISTIC
    assert AgentDomain.GOVERNANCE in {summary.domain for summary in artifact.domain_summaries}
    assert "not causal proof" in " ".join(item.summary for item in artifact.cross_domain_findings)
    assert "OBSERVATIONAL_ASSOCIATION" in artifact.limitations_summary
    assert UnsupportedInferenceCode.CAUSALITY in artifact.unsupported_inferences_preserved
    assert "causes" not in artifact.model_dump_json()


def test_deterministic_synthesis_references_only_upstream_ids(coordinated):
    artifact = synthesize_assessment(request=SynthesisRequest(coordinated_assessment=coordinated))

    assert set(artifact.referenced_claim_ids) <= {
        record.claim_id for record in coordinated.claim_domain_map
    }
    assert set(artifact.referenced_evidence_ids) <= {
        record.evidence_id for record in coordinated.evidence_domain_map
    }
    assert set(artifact.referenced_assessment_ids) == set(coordinated.source_assessment_ids)
