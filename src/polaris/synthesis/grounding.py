"""Grounding payload construction for Phase 8 synthesis."""

from typing import Any

from polaris.agents.models import AgentDomain
from polaris.coordination.models import CoordinatedAssessment, CoordinationCoverageStatus
from polaris.evidence.models import EvidenceArtifact
from polaris.literature.models import LiteratureContextArtifact
from polaris.synthesis.models import GroundingPayload


def build_grounding_payload(
    coordinated: CoordinatedAssessment,
    *,
    evidence_artifact: EvidenceArtifact | None = None,
    literature_context: LiteratureContextArtifact | None = None,
) -> GroundingPayload:
    """Build deterministic JSON-compatible synthesis grounding from Phase 7 state."""

    claim_lookup = (
        {claim.claim_id: claim for claim in evidence_artifact.claim_candidates}
        if evidence_artifact
        else {}
    )
    evidence_lookup = (
        {record.evidence_id: record for record in evidence_artifact.evidence_records}
        if evidence_artifact
        else {}
    )

    payload: GroundingPayload = {
        "coordinated_assessment_id": coordinated.coordinated_assessment_id,
        "source_evidence_artifact_id": coordinated.source_evidence_artifact_id,
        "source_analysis_result_id": coordinated.source_analysis_result_id,
        "dataset_id": coordinated.dataset_id,
        "source_checksum_sha256": coordinated.source_checksum_sha256,
        "participating_domains": [domain.value for domain in coordinated.participating_domains],
        "missing_domains": [domain.value for domain in coordinated.missing_domains],
        "source_assessment_ids": list(coordinated.source_assessment_ids),
        "domain_coverage": [
            {
                "domain": record.domain.value,
                "assessment_supplied": record.assessment_supplied,
                "assessment_id": record.assessment_id,
                "coverage_status": record.coverage_status.value,
                "relevant_evidence_count": record.relevant_evidence_count,
                "relevant_claim_count": record.relevant_claim_count,
            }
            for record in coordinated.domain_coverage
        ],
        "claims": [
            _claim_payload(
                record.claim_id,
                record.selecting_domains,
                claim_lookup.get(record.claim_id),
            )
            for record in coordinated.claim_domain_map
        ],
        "evidence": [
            _evidence_payload(
                record.evidence_id,
                record.selecting_domains,
                evidence_lookup.get(record.evidence_id),
            )
            for record in coordinated.evidence_domain_map
        ],
        "agreements": [
            {
                "agreement_id": record.agreement_id,
                "agreement_type": record.agreement_type.value,
                "source_ids": list(record.source_ids),
                "limitation_codes": [code.value for code in record.limitation_codes],
                "unsupported_inference_codes": [
                    code.value for code in record.unsupported_inference_codes
                ],
                "participating_domains": [domain.value for domain in record.participating_domains],
            }
            for record in coordinated.agreements
        ],
        "divergences": [
            {
                "divergence_id": record.divergence_id,
                "divergence_type": record.divergence_type.value,
                "domains_involved": [domain.value for domain in record.domains_involved],
                "source_ids": list(record.source_ids),
                "limitation_codes": [code.value for code in record.limitation_codes],
                "unsupported_inference_codes": [
                    code.value for code in record.unsupported_inference_codes
                ],
                "factual_basis": record.factual_basis,
            }
            for record in coordinated.divergences
        ],
        "shared_limitations": [
            {
                "limitation_code": record.limitation_code.value,
                "domains": [domain.value for domain in record.domains],
                "associated_source_ids": list(record.associated_source_ids),
                "global_limitation": record.global_limitation,
            }
            for record in coordinated.shared_limitations
        ],
        "unsupported_inferences": [
            {
                "inference_code": record.inference_code.value,
                "domains": [domain.value for domain in record.domains],
                "all_participating_agents": record.all_participating_agents,
                "relevant_claim_ids": list(record.relevant_claim_ids),
            }
            for record in coordinated.shared_unsupported_inferences
        ],
        "evidence_gaps": [
            {
                "gap_id": record.gap_id,
                "gap_type": record.gap_type.value,
                "source_ids": list(record.source_ids),
                "domains": [domain.value for domain in record.domains],
            }
            for record in coordinated.evidence_gaps
        ],
        "domain_gaps": [
            {
                "gap_id": record.gap_id,
                "gap_type": record.gap_type.value,
                "domain": record.domain.value,
                "assessment_supplied": record.assessment_supplied,
                "coverage_status": record.coverage_status.value,
            }
            for record in coordinated.domain_gaps
        ],
        "coordination_findings": [
            {
                "finding_code": record.finding_code.value,
                "severity": record.severity.value,
                "source_ids": list(record.source_ids),
                "domains": [domain.value for domain in record.domains],
            }
            for record in coordinated.coordination_findings
        ],
    }
    if literature_context is not None:
        payload["literature_context"] = {
            "instruction": (
                "Literature context is separate from empirical findings and must not alter "
                "statistical results or claim IDs."
            ),
            "literature_context_id": literature_context.literature_context_id,
            "corpus_id": literature_context.corpus_id,
            "empirical_claim_ids": list(literature_context.empirical_claim_ids),
            "unmatched_claims": list(literature_context.unmatched_claims),
            "retrieval_summary": literature_context.retrieval_summary.model_dump(mode="json"),
            "records": [
                {
                    "literature_evidence_id": record.literature_evidence_id,
                    "empirical_claim_id": record.empirical_claim_id,
                    "retrieval_query": record.retrieval_query,
                    "support_classification": record.support_classification.value,
                    "chunks": [
                        {
                            "chunk_id": row.chunk.chunk_id,
                            "document_id": row.document.document_id,
                            "rank": row.rank,
                            "score": row.score,
                            "title": row.document.title,
                            "authors": list(row.document.authors),
                            "year": row.document.year,
                            "publication": row.document.publication,
                            "doi": row.document.doi,
                            "url": row.document.url,
                            "text": row.chunk.text,
                        }
                        for row in record.ranked_chunks
                    ],
                }
                for record in literature_context.literature_evidence
            ],
        }
    return payload


def source_reference_sets(
    coordinated: CoordinatedAssessment,
) -> tuple[set[str], set[str], set[str], set[str], set[str], set[AgentDomain], set[AgentDomain]]:
    claim_ids = {record.claim_id for record in coordinated.claim_domain_map}
    evidence_ids = {record.evidence_id for record in coordinated.evidence_domain_map}
    assessment_ids = set(coordinated.source_assessment_ids)
    agreement_ids = {record.agreement_id for record in coordinated.agreements}
    divergence_ids = {record.divergence_id for record in coordinated.divergences}
    participating_domains = set(coordinated.participating_domains)
    missing_domains = set(coordinated.missing_domains)
    return (
        claim_ids,
        evidence_ids,
        assessment_ids,
        agreement_ids,
        divergence_ids,
        participating_domains,
        missing_domains,
    )


def _claim_payload(
    claim_id: str,
    domains: tuple[AgentDomain, ...],
    claim: Any | None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "claim_id": claim_id,
        "selecting_domains": [domain.value for domain in domains],
    }
    if claim is not None:
        payload.update(
            {
                "claim_type": claim.claim_type.value,
                "subject_variable": claim.subject_variable,
                "outcome_variable": claim.outcome_variable,
                "related_variables": list(claim.related_variables),
                "direction": claim.direction.value,
                "statistical_procedure": claim.statistical_procedure.value,
                "supporting_evidence_ids": list(claim.supporting_evidence_ids),
                "limitation_codes": [code.value for code in claim.limitation_codes],
                "causal": claim.causal,
                "generalization_scope": claim.generalization_scope,
                "p_value_below_threshold": claim.p_value_below_threshold,
                "confidence_interval_crosses_zero": claim.confidence_interval_crosses_zero,
            }
        )
    return payload


def _evidence_payload(
    evidence_id: str,
    domains: tuple[AgentDomain, ...],
    evidence: Any | None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "evidence_id": evidence_id,
        "selecting_domains": [domain.value for domain in domains],
    }
    if evidence is not None:
        payload.update(
            {
                "evidence_type": evidence.evidence_type.value,
                "statistical_procedure": evidence.statistical_procedure.value,
                "sample_size": evidence.sample_size,
                "limitation_codes": [code.value for code in evidence.limitation_codes],
            }
        )
        for key in (
            "variable_id",
            "variable_id_1",
            "variable_id_2",
            "dependent_variable_id",
            "predictor_variable_ids",
            "term",
            "estimate",
            "standard_error",
            "p_value",
            "confidence_interval_low",
            "confidence_interval_high",
            "direction",
            "r_squared",
            "adjusted_r_squared",
            "diagnostic_type",
            "status",
            "finding_code",
        ):
            if hasattr(evidence, key):
                value = getattr(evidence, key)
                payload[key] = value.value if hasattr(value, "value") else value
        if payload.get("predictor_variable_ids") is not None:
            payload["predictor_variable_ids"] = list(payload["predictor_variable_ids"])
    return payload


def missing_domain_status(coordinated: CoordinatedAssessment, domain: AgentDomain) -> str:
    for record in coordinated.domain_coverage:
        if record.domain is domain:
            if record.coverage_status is CoordinationCoverageStatus.NO_RELEVANT_EVIDENCE:
                return "supplied with no relevant evidence"
            if record.coverage_status is CoordinationCoverageStatus.ASSESSMENT_MISSING:
                return "not supplied"
    return "not supplied"
