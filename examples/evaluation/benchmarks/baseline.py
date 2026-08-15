"""Baseline Phase 19 benchmark fixtures."""

from datetime import UTC, datetime

from polaris import __version__
from polaris.agents.models import AgentDomain
from polaris.coordination.models import (
    ClaimDomainMapRecord,
    CoordinatedAssessment,
    CoordinationCoverageStatus,
    CoordinationProvenance,
    DomainCoverageRecord,
    DomainRelevanceReference,
    RelevanceStatus,
    SharedLimitationRecord,
)
from polaris.evaluation.models import (
    BenchmarkCase,
    BenchmarkSuite,
    BenchmarkTag,
    ExpectedLiteratureBehavior,
    ExpectedReasoningBehavior,
    deterministic_suite_id,
)
from polaris.evidence.models import (
    ClaimCandidate,
    ClaimType,
    Direction,
    EvidenceArtifact,
    EvidenceProvenance,
    LimitationCode,
    RegressionCoefficientEvidenceRecord,
)
from polaris.evidence.provenance import deterministic_id
from polaris.literature.models import (
    CitationMetadata,
    LiteratureContextArtifact,
    LiteratureEvidence,
    LiteratureSupportClassification,
    RetrievalMode,
    RetrievalQualitySummary,
)
from polaris.reasoning.taxonomy import (
    CausalStatus,
    ReasoningCategory,
    ReasoningMode,
)
from polaris.schemas.common import StatisticalProcedure

POLARIS_REASONING_BASELINE_V1 = "POLARIS_REASONING_BASELINE_V1"
_TIMESTAMP = datetime(2026, 8, 14, tzinfo=UTC)
_SOFTWARE = f"polaris-{__version__}"


def baseline_suite() -> BenchmarkSuite:
    cases = (
        _case(
            "case_a_positive_association",
            title="Positive association",
            description="Evidence clearly shows a positive non-causal association.",
            direction=Direction.POSITIVE,
            tags=(BenchmarkTag.SYNTHETIC, BenchmarkTag.BASIC_ASSOCIATION),
            expected=ExpectedReasoningBehavior(
                required_statement_categories=(
                    ReasoningCategory.EMPIRICAL_INTERPRETATION,
                    ReasoningCategory.LIMITATION,
                ),
                expected_direction=Direction.POSITIVE,
                expected_limitations=("OBSERVATIONAL_ASSOCIATION",),
            ),
        ),
        _case(
            "case_b_non_significant_result",
            title="Non-significant result",
            description="Association is weak and statistically uncertain.",
            direction=Direction.POSITIVE,
            significant=False,
            tags=(BenchmarkTag.SYNTHETIC, BenchmarkTag.NON_SIGNIFICANT_RESULT),
            expected=ExpectedReasoningBehavior(
                required_statement_categories=(ReasoningCategory.EMPIRICAL_INTERPRETATION,),
                expected_direction=Direction.POSITIVE,
                expected_limitations=("OBSERVATIONAL_ASSOCIATION",),
            ),
        ),
        _case(
            "case_c_causal_trap",
            title="Causal trap",
            description="Variable names tempt causal language, but evidence is observational.",
            exposure="education_spending",
            outcome="life_expectancy",
            direction=Direction.POSITIVE,
            tags=(BenchmarkTag.ADVERSARIAL, BenchmarkTag.CAUSAL_TRAP),
            expected=ExpectedReasoningBehavior(
                required_statement_categories=(
                    ReasoningCategory.EMPIRICAL_INTERPRETATION,
                    ReasoningCategory.PLAUSIBLE_MECHANISM,
                ),
                expected_causal_status=CausalStatus.NON_CAUSAL,
                expected_direction=Direction.POSITIVE,
            ),
        ),
        _conflicting_case(),
        _literature_case(),
        _case(
            "case_f_small_sample",
            title="Small sample",
            description="Strong coefficient but material small-sample limitation.",
            direction=Direction.POSITIVE,
            sample_size=8,
            limitations=(LimitationCode.SMALL_SAMPLE, LimitationCode.OBSERVATIONAL_ASSOCIATION),
            tags=(BenchmarkTag.ADVERSARIAL, BenchmarkTag.SMALL_SAMPLE),
            expected=ExpectedReasoningBehavior(
                required_statement_categories=(ReasoningCategory.LIMITATION,),
                expected_direction=Direction.POSITIVE,
                expected_limitations=("SMALL_SAMPLE",),
            ),
        ),
        _case(
            "case_g_candidate_confounder",
            title="Candidate confounder",
            description="Omitted domain concept should remain a potential confounder.",
            exposure="government_effectiveness",
            outcome="life_expectancy",
            covariates=("gdp_per_capita",),
            direction=Direction.POSITIVE,
            tags=(BenchmarkTag.SYNTHETIC, BenchmarkTag.POTENTIAL_CONFOUNDER),
            expected=ExpectedReasoningBehavior(
                required_statement_categories=(ReasoningCategory.POTENTIAL_CONFOUNDER,),
                expected_candidate_confounders=("education",),
                expected_direction=Direction.POSITIVE,
            ),
        ),
        _case(
            "case_h_fabricated_grounding",
            title="Fabricated grounding adversary",
            description="Evaluation fixture target for nonexistent evidence IDs.",
            direction=Direction.POSITIVE,
            tags=(BenchmarkTag.ADVERSARIAL, BenchmarkTag.FABRICATED_GROUNDING),
            expected=ExpectedReasoningBehavior(expected_direction=Direction.POSITIVE),
        ),
        _literature_case(
            case_id="case_i_fabricated_citation",
            title="Fabricated citation adversary",
            tags=(BenchmarkTag.ADVERSARIAL, BenchmarkTag.FABRICATED_CITATION),
        ),
        _case(
            "case_j_mechanism_as_fact",
            title="Mechanism presented as fact",
            description="Evaluation fixture target for mechanism labels.",
            exposure="institutional_capacity",
            outcome="healthcare_access",
            direction=Direction.POSITIVE,
            tags=(BenchmarkTag.ADVERSARIAL, BenchmarkTag.PLAUSIBLE_MECHANISM),
            expected=ExpectedReasoningBehavior(
                required_statement_categories=(ReasoningCategory.PLAUSIBLE_MECHANISM,),
                expected_direction=Direction.POSITIVE,
            ),
        ),
        _case(
            "case_real_governance_life_expectancy",
            title="Government effectiveness and life expectancy",
            description=(
                "Real-data-derived Phase 16 style case using committed Polaris variable concepts."
            ),
            exposure="government_effectiveness",
            outcome="life_expectancy",
            covariates=("gdp_per_capita",),
            direction=Direction.POSITIVE,
            tags=(
                BenchmarkTag.REAL_DATA_DERIVED,
                BenchmarkTag.CONDITIONAL_ASSOCIATION,
                BenchmarkTag.POTENTIAL_CONFOUNDER,
            ),
            expected=ExpectedReasoningBehavior(
                required_statement_categories=(
                    ReasoningCategory.EMPIRICAL_INTERPRETATION,
                    ReasoningCategory.PLAUSIBLE_MECHANISM,
                    ReasoningCategory.POTENTIAL_CONFOUNDER,
                    ReasoningCategory.LIMITATION,
                ),
                expected_direction=Direction.POSITIVE,
                expected_limitations=("OBSERVATIONAL_ASSOCIATION",),
                expected_candidate_confounders=("education",),
            ),
        ),
    )
    title = POLARIS_REASONING_BASELINE_V1
    return BenchmarkSuite(
        suite_id=deterministic_suite_id(
            title=title,
            version="1",
            case_ids=tuple(case.case_id for case in cases),
        ),
        title=title,
        description="Baseline deterministic Phase 19 reasoning evaluation suite.",
        benchmark_cases=cases,
        version="1",
        tags=tuple(
            sorted(
                {tag for case in cases for tag in case.benchmark_tags}, key=lambda item: item.value
            )
        ),
    )


def _case(
    case_id: str,
    *,
    title: str,
    description: str,
    direction: Direction,
    expected: ExpectedReasoningBehavior,
    tags: tuple[BenchmarkTag, ...],
    exposure: str = "x",
    outcome: str = "y",
    covariates: tuple[str, ...] = (),
    significant: bool = True,
    sample_size: int = 42,
    limitations: tuple[LimitationCode, ...] = (LimitationCode.OBSERVATIONAL_ASSOCIATION,),
) -> BenchmarkCase:
    evidence, coordination = _artifacts(
        case_id=case_id,
        exposure=exposure,
        outcome=outcome,
        direction=direction,
        covariates=covariates,
        significant=significant,
        sample_size=sample_size,
        limitations=limitations,
    )
    return BenchmarkCase(
        case_id=case_id,
        title=title,
        description=description,
        research_question=f"How is {exposure} associated with {outcome}?",
        evidence_artifact=evidence,
        coordinated_assessment=coordination,
        expected_behavior=expected,
        benchmark_tags=tags,
        reasoning_modes=(ReasoningMode.DETERMINISTIC, ReasoningMode.PROVIDER_BACKED),
    )


def _conflicting_case() -> BenchmarkCase:
    case_id = "case_d_conflicting_domain_evidence"
    evidence, coordination = _artifacts(
        case_id=case_id,
        exposure="x",
        outcome="y",
        direction=Direction.POSITIVE,
        second_direction=Direction.NEGATIVE,
        covariates=("gdp_per_capita",),
    )
    return BenchmarkCase(
        case_id=case_id,
        title="Conflicting domain evidence",
        description="Two claim candidates point in opposing directions.",
        research_question="How is x associated with y across specifications?",
        evidence_artifact=evidence,
        coordinated_assessment=coordination,
        expected_behavior=ExpectedReasoningBehavior(
            required_statement_categories=(ReasoningCategory.EMPIRICAL_INTERPRETATION,),
            expected_contradictions=tuple(claim.claim_id for claim in evidence.claim_candidates),
            expected_limitations=("OBSERVATIONAL_ASSOCIATION",),
        ),
        benchmark_tags=(BenchmarkTag.ADVERSARIAL, BenchmarkTag.CONFLICTING_EVIDENCE),
        reasoning_modes=(ReasoningMode.DETERMINISTIC, ReasoningMode.PROVIDER_BACKED),
    )


def _literature_case(
    case_id: str = "case_e_literature_disagreement",
    title: str = "Literature disagreement",
    tags: tuple[BenchmarkTag, ...] = (
        BenchmarkTag.ADVERSARIAL,
        BenchmarkTag.LITERATURE_CONTRAST,
    ),
) -> BenchmarkCase:
    evidence, coordination = _artifacts(
        case_id=case_id,
        exposure="x",
        outcome="y",
        direction=Direction.POSITIVE,
    )
    claim = evidence.claim_candidates[0]
    literature_id = f"{case_id}_literature_1"
    literature = LiteratureContextArtifact(
        literature_context_id=f"{case_id}_literature_context",
        corpus_id=f"{case_id}_corpus",
        research_question="How is x associated with y?",
        empirical_claim_ids=(claim.claim_id,),
        literature_evidence=(
            LiteratureEvidence(
                literature_evidence_id=literature_id,
                empirical_claim_id=claim.claim_id,
                retrieval_query="x y association",
                ranked_chunks=(),
                citations=(CitationMetadata(citation_text="Synthetic benchmark citation"),),
                relevance_scores=(1.0,),
                support_classification=LiteratureSupportClassification.CONTRASTING,
                limitations=("synthetic benchmark literature context",),
            ),
        ),
        retrieval_summary=RetrievalQualitySummary(
            corpus_document_count=1,
            chunk_count=1,
            query_count=1,
            retrieved_chunk_count=1,
            unique_cited_documents=1,
            retrieval_mode=RetrievalMode.BM25,
        ),
    )
    return BenchmarkCase(
        case_id=case_id,
        title=title,
        description="Empirical evidence and literature context contrast.",
        research_question="How is x associated with y?",
        evidence_artifact=evidence,
        coordinated_assessment=coordination,
        literature_context=literature,
        expected_behavior=ExpectedReasoningBehavior(
            required_statement_categories=(ReasoningCategory.LITERATURE_CONTRAST,),
            expected_direction=Direction.POSITIVE,
            expected_literature_behavior=ExpectedLiteratureBehavior.CONTRAST,
        ),
        benchmark_tags=tags,
        reasoning_modes=(ReasoningMode.DETERMINISTIC, ReasoningMode.PROVIDER_BACKED),
    )


def _artifacts(
    *,
    case_id: str,
    exposure: str,
    outcome: str,
    direction: Direction,
    covariates: tuple[str, ...] = (),
    second_direction: Direction | None = None,
    significant: bool = True,
    sample_size: int = 42,
    limitations: tuple[LimitationCode, ...] = (LimitationCode.OBSERVATIONAL_ASSOCIATION,),
) -> tuple[EvidenceArtifact, CoordinatedAssessment]:
    evidence_records = []
    claims = []
    for index, item_direction in enumerate((direction, second_direction), start=1):
        if item_direction is None:
            continue
        suffix = f"{case_id}_{index}"
        provenance = _evidence_provenance(suffix)
        evidence_id = f"{suffix}_evidence"
        estimate = 1.2 if item_direction is Direction.POSITIVE else -1.2
        if not significant:
            estimate = 0.08
        evidence_records.append(
            RegressionCoefficientEvidenceRecord(
                evidence_id=evidence_id,
                source_analysis_result_id=f"{suffix}_analysis",
                dataset_id=f"{case_id}_dataset",
                source_checksum_sha256=f"{case_id}_checksum",
                statistical_procedure=StatisticalProcedure.ORDINARY_LEAST_SQUARES,
                sample_size=sample_size,
                limitation_codes=limitations,
                provenance=provenance,
                dependent_variable_id=outcome,
                term=exposure,
                variable_id=exposure,
                estimate=estimate,
                standard_error=0.2 if significant else 0.5,
                test_statistic=6.0 if significant else 0.16,
                p_value=0.01 if significant else 0.88,
                confidence_interval_low=0.7
                if significant and item_direction is Direction.POSITIVE
                else -0.4,
                confidence_interval_high=1.7 if significant else 0.5,
                below_significance_threshold=significant,
                direction=item_direction,
                is_intercept=False,
                model_result_id=f"{suffix}_model",
                predictor_variable_ids=(exposure, *covariates),
            )
        )
        claims.append(
            ClaimCandidate(
                claim_id=f"{suffix}_claim",
                claim_type=(
                    ClaimType.CONDITIONAL_ASSOCIATION if covariates else ClaimType.ASSOCIATION
                ),
                subject_variable=exposure,
                outcome_variable=outcome,
                related_variables=covariates,
                direction=item_direction,
                statistical_procedure=StatisticalProcedure.ORDINARY_LEAST_SQUARES,
                supporting_evidence_ids=(evidence_id,),
                limitation_codes=limitations,
                source_analysis_result_id=f"{suffix}_analysis",
                dataset_id=f"{case_id}_dataset",
                provenance=provenance,
                p_value_below_threshold=significant,
                confidence_interval_crosses_zero=not significant,
            )
        )
    artifact = EvidenceArtifact(
        artifact_id=f"{case_id}_evidence_artifact",
        source_analysis_result_id=f"{case_id}_analysis",
        dataset_id=f"{case_id}_dataset",
        source_checksum_sha256=f"{case_id}_checksum",
        evidence_records=tuple(evidence_records),
        claim_candidates=tuple(claims),
        provenance=_evidence_provenance(case_id),
        extraction_timestamp=_TIMESTAMP,
        software_version=_SOFTWARE,
    )
    coordination = _coordination(case_id=case_id, artifact=artifact, limitations=limitations)
    return artifact, coordination


def _evidence_provenance(identifier: str) -> EvidenceProvenance:
    return EvidenceProvenance(
        dataset_id=f"{identifier}_dataset",
        source_checksum_sha256=f"{identifier}_checksum",
        source_analysis_result_id=f"{identifier}_analysis",
        statistical_procedure=StatisticalProcedure.ORDINARY_LEAST_SQUARES,
        phase4_schema_version="1.0.0",
        extraction_timestamp=_TIMESTAMP,
        software_version=_SOFTWARE,
    )


def _coordination(
    *,
    case_id: str,
    artifact: EvidenceArtifact,
    limitations: tuple[LimitationCode, ...],
) -> CoordinatedAssessment:
    domains = (AgentDomain.GOVERNANCE, AgentDomain.ECONOMICS, AgentDomain.PUBLIC_HEALTH)
    assessment_ids = tuple(f"{case_id}_{domain.value}_assessment" for domain in domains)
    claim_maps = tuple(
        ClaimDomainMapRecord(
            claim_id=claim.claim_id,
            selecting_domains=domains,
            relevance_by_domain=tuple(
                DomainRelevanceReference(
                    domain=domain,
                    relevance_status=RelevanceStatus.RELEVANT,
                    matched_variable_ids=(
                        tuple(
                            item
                            for item in (claim.subject_variable, claim.outcome_variable)
                            if item
                        )
                    ),
                )
                for domain in domains
            ),
            shared_limitations=limitations,
            selection_count=len(domains),
            cross_domain=True,
        )
        for claim in artifact.claim_candidates
    )
    provenance = CoordinationProvenance(
        source_evidence_artifact_id=artifact.artifact_id,
        source_assessment_ids=assessment_ids,
        source_analysis_result_id=artifact.source_analysis_result_id,
        dataset_id=artifact.dataset_id,
        source_checksum_sha256=artifact.source_checksum_sha256,
        participating_domains=domains,
        missing_domains=(AgentDomain.EDUCATION,),
        coordination_timestamp=_TIMESTAMP,
        software_version=_SOFTWARE,
        phase5_schema_version=artifact.schema_version,
    )
    return CoordinatedAssessment(
        coordinated_assessment_id=deterministic_id(
            "coordination_",
            {"case_id": case_id, "artifact_id": artifact.artifact_id},
        ),
        source_evidence_artifact_id=artifact.artifact_id,
        source_analysis_result_id=artifact.source_analysis_result_id,
        dataset_id=artifact.dataset_id,
        source_checksum_sha256=artifact.source_checksum_sha256,
        participating_domains=domains,
        missing_domains=(AgentDomain.EDUCATION,),
        source_assessment_ids=assessment_ids,
        domain_coverage=tuple(
            DomainCoverageRecord(
                domain=domain,
                assessment_supplied=True,
                assessment_id=f"{case_id}_{domain.value}_assessment",
                relevant_evidence_count=len(artifact.evidence_records),
                relevant_claim_count=len(artifact.claim_candidates),
                direct_domain_variable_count=1,
                cross_domain_claim_count=len(artifact.claim_candidates),
                inherited_limitation_count=len(limitations),
                coverage_status=CoordinationCoverageStatus.RELEVANT_EVIDENCE,
            )
            for domain in domains
        ),
        claim_domain_map=claim_maps,
        shared_limitations=tuple(
            SharedLimitationRecord(
                limitation_code=limitation,
                domains=domains,
                associated_source_ids=tuple(claim.claim_id for claim in artifact.claim_candidates),
                global_limitation=True,
            )
            for limitation in limitations
        ),
        provenance=provenance,
    )
