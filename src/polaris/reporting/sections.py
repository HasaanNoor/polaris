"""Deterministic report section assembly."""

from typing import Any

from polaris.analysis.models import (
    AnalysisResult,
    CorrelationAnalysisResult,
    DescriptiveAnalysisResult,
    OLSRegressionResult,
)
from polaris.analysis.robustness.models import RobustnessAnalysisResult, RobustnessVariantType
from polaris.coordination.models import DOMAIN_ORDER, CoordinatedAssessment
from polaris.evidence.models import (
    CausalAssumptionEvidenceRecord,
    CausalDiagnosticEvidenceRecord,
    CausalTreatmentEffectEvidenceRecord,
    EvidenceArtifact,
    LimitationCode,
)
from polaris.ingestion.models import DatasetIngestionResult
from polaris.reasoning.models import ReasoningArtifact
from polaris.reasoning.taxonomy import ReasoningCategory
from polaris.reporting.models import (
    CausalDesignSection,
    ClaimSummary,
    CrossDomainSection,
    DatasetSection,
    DomainAssessmentsSection,
    DomainAssessmentSummary,
    EvidenceAndClaimsSection,
    EvidenceGroundedInterpretationSection,
    EvidenceRecordSummary,
    GapsSection,
    LimitationsSection,
    LiteratureContextSection,
    MethodologySection,
    ProvenanceSection,
    ResearchQuestionSection,
    RobustnessSection,
    SectionStatus,
    StatisticalResultsSection,
    SynthesisSection,
    UnsupportedInferencesSection,
    VisualizationReportSection,
)
from polaris.schemas.dataset import DatasetManifest
from polaris.schemas.research_question import ResearchQuestion
from polaris.synthesis.models import SynthesisArtifact
from polaris.visualization.models import VisualizationArtifact


def research_question_section(
    research_question: ResearchQuestion | None,
) -> ResearchQuestionSection:
    if research_question is None:
        return ResearchQuestionSection(status=SectionStatus.UNAVAILABLE)
    variables = tuple(
        ref.variable_id
        for ref in (
            *research_question.outcome_variables,
            *research_question.exposure_variables,
            *research_question.covariates,
        )
    )
    constraints = tuple(
        sorted(
            [
                *research_question.assumptions,
                *research_question.exclusions,
                *research_question.required_metadata,
            ]
        )
    )
    return ResearchQuestionSection(
        status=SectionStatus.AVAILABLE,
        question_id=research_question.question_id,
        primary_question=research_question.raw_text,
        population=research_question.population,
        geographic_scope=research_question.geographic_scope.model_dump(mode="json"),
        temporal_scope=research_question.temporal_scope.model_dump(mode="json"),
        variables_or_concepts=tuple(sorted(set(variables))),
        stated_constraints=constraints,
        intended_analytical_methods=tuple(sorted(research_question.requested_analytical_methods)),
    )


def dataset_section(
    *,
    ingestion_result: DatasetIngestionResult,
    manifest: DatasetManifest | None,
    analysis_result: AnalysisResult,
) -> DatasetSection:
    active_manifest = manifest or ingestion_result.dataset_manifest
    quality_facts = tuple(
        {
            "variable_id": variable.variable_id,
            "source_column": variable.source_column,
            "data_type": variable.data_type,
            "non_null_count": variable.non_null_count,
            "null_count": variable.null_count,
            "invalid_value_count": variable.invalid_value_count,
            "unique_value_count": variable.unique_value_count,
            "minimum": variable.minimum,
            "maximum": variable.maximum,
        }
        for variable in sorted(
            ingestion_result.quality_profile.variables, key=lambda item: item.variable_id
        )
    )
    source_limitations = tuple(
        sorted(
            [
                *active_manifest.access_restrictions,
                *(warning.message for warning in active_manifest.comparability_warnings),
                *(warning.message for warning in active_manifest.licensing_warnings),
            ]
        )
    )
    return DatasetSection(
        dataset_id=ingestion_result.dataset_manifest.dataset_id,
        dataset_title=active_manifest.title,
        provider=active_manifest.provider,
        source_checksum_sha256=ingestion_result.checksum_sha256,
        source_type="local_csv",
        geographic_coverage=active_manifest.geographic_coverage.model_dump(mode="json"),
        temporal_coverage=active_manifest.temporal_coverage.model_dump(mode="json"),
        accepted_row_count=ingestion_result.validation_report.accepted_row_count,
        rejected_row_count=ingestion_result.validation_report.rejected_row_count,
        analysis_ready=ingestion_result.validation_report.analysis_ready,
        quality_profile_facts=quality_facts,
        relevant_variable_ids=analysis_result.analysis_sample.required_variable_ids,
        source_limitations=source_limitations,
        illustrative=_is_illustrative(active_manifest),
    )


def methodology_section(
    *,
    analysis_result: AnalysisResult,
    evidence_artifact: EvidenceArtifact,
    coordinated_assessment: CoordinatedAssessment,
    synthesis_artifact: SynthesisArtifact,
) -> MethodologySection:
    spec = analysis_result.statistical_specification
    result = analysis_result.method_result
    include_intercept = (
        result.include_intercept if isinstance(result, OLSRegressionResult) else None
    )
    return MethodologySection(
        ingestion_and_validation=(
            "Local CSV ingestion mapped source columns to the supplied manifest, normalized "
            "supported scalar values, validated structure, and computed a SHA-256 checksum."
        ),
        sample_construction=(
            "Phase 4 used complete-case sample construction from accepted Phase 3 records."
        ),
        statistical_procedure=analysis_result.analysis_method,
        dependent_variable=spec.outcome_variable.variable_id,
        predictors=tuple(ref.variable_id for ref in spec.exposure_variables),
        controls=tuple(ref.variable_id for ref in spec.covariates),
        include_intercept=include_intercept,
        confidence_level=spec.confidence_level,
        significance_threshold=_significance_threshold(analysis_result),
        diagnostics_calculated=tuple(
            sorted(diagnostic.name for diagnostic in analysis_result.diagnostics)
        ),
        evidence_extraction_process=(
            f"Phase 5 extracted {len(evidence_artifact.evidence_records)} evidence records "
            f"and {len(evidence_artifact.claim_candidates)} bounded non-causal claim candidates."
        ),
        domain_agent_process=(
            "Phase 6 deterministic domain agents selected relevant structured evidence and "
            "claim IDs without adding outside context."
        ),
        coordination_process=(
            f"Phase 7 coordinated {len(coordinated_assessment.source_assessment_ids)} "
            "domain assessments by reference."
        ),
        synthesis_mode=synthesis_artifact.synthesis_mode,
        grounding_and_validation=(
            "Phase 8 synthesis supplied validated summaries with fabricated-reference, "
            "limitation-preservation, unsupported-inference, and overreach checks."
        ),
    )


def statistical_results_section(analysis_result: AnalysisResult) -> StatisticalResultsSection:
    result = analysis_result.method_result
    descriptive: tuple[dict[str, Any], ...] = ()
    correlations: tuple[dict[str, Any], ...] = ()
    regression: dict[str, Any] | None = None
    if isinstance(result, DescriptiveAnalysisResult):
        descriptive = tuple(item.model_dump(mode="json") for item in result.variables)
    elif isinstance(result, CorrelationAnalysisResult):
        correlations = tuple(item.model_dump(mode="json") for item in result.pairs)
    elif isinstance(result, OLSRegressionResult):
        regression = result.model_dump(mode="json")
    return StatisticalResultsSection(
        analysis_result_id=analysis_result.result_id,
        method=analysis_result.analysis_method,
        sample_size=analysis_result.analysis_sample.sample_size,
        descriptive_results=descriptive,
        correlation_results=correlations,
        regression_results=regression,
        diagnostics=tuple(item.model_dump(mode="json") for item in analysis_result.diagnostics),
        findings=tuple(item.model_dump(mode="json") for item in analysis_result.findings),
    )


def causal_design_section(evidence_artifact: EvidenceArtifact) -> CausalDesignSection | None:
    effects = [
        record
        for record in evidence_artifact.evidence_records
        if isinstance(record, CausalTreatmentEffectEvidenceRecord)
    ]
    if not effects:
        return None
    effect = sorted(effects, key=lambda item: item.evidence_id)[0]
    assumptions = tuple(
        record.model_dump(mode="json")
        for record in evidence_artifact.evidence_records
        if isinstance(record, CausalAssumptionEvidenceRecord)
    )
    diagnostics = tuple(
        record.model_dump(mode="json")
        for record in evidence_artifact.evidence_records
        if isinstance(record, CausalDiagnosticEvidenceRecord)
    )
    return CausalDesignSection(
        status=SectionStatus.AVAILABLE,
        research_design=effect.causal_method,
        treatment=effect.treatment_variable_id,
        comparison_group="explicit never-treated comparison group",
        treatment_timing="explicit treatment timing supplied in CausalSpecification",
        outcome=effect.outcome_variable_id,
        estimand=effect.estimand,
        model=effect.estimator,
        treatment_effect={
            "estimate": effect.estimate,
            "p_value": effect.p_value,
            "confidence_interval_low": effect.confidence_interval_low,
            "confidence_interval_high": effect.confidence_interval_high,
        },
        clustered_uncertainty={
            "standard_error": effect.standard_error,
            "cluster_count": effect.cluster_count,
        },
        event_study_results=tuple(
            item.event_study_plot_data
            for item in evidence_artifact.evidence_records
            if isinstance(item, CausalDiagnosticEvidenceRecord)
        )[0]
        if diagnostics
        else (),
        identifying_assumptions=assumptions,
        diagnostics=diagnostics,
        registry_provenance=effect.registry_provenance,
        limitations=tuple(code.value for code in effect.limitation_codes),
    )


def robustness_section(
    robustness_result: RobustnessAnalysisResult | None,
) -> RobustnessSection | None:
    if robustness_result is None:
        return None
    variant_rows = tuple(
        {
            "variant_id": item.variant_id,
            "variant_type": item.variant_type.value,
            "estimate": item.analysis_result.treatment_effect.estimate,
            "standard_error": item.analysis_result.treatment_effect.standard_error,
            "p_value": item.analysis_result.treatment_effect.p_value,
            "sample_size": item.analysis_result.sample_summary.included_rows,
            "cluster_count": item.analysis_result.sample_summary.cluster_count,
            "difference_from_baseline": item.estimate_difference_from_baseline,
        }
        for item in robustness_result.variant_results
    )
    return RobustnessSection(
        status=SectionStatus.AVAILABLE,
        robustness_analysis_id=robustness_result.robustness_analysis_id,
        baseline_analysis_id=robustness_result.baseline.baseline_analysis_id,
        baseline_specification=robustness_result.baseline.model_dump(mode="json"),
        variants_tested=tuple(item.model_dump(mode="json") for item in robustness_result.variants),
        treatment_effect_comparison={
            "stability": robustness_result.treatment_effect_stability.model_dump(mode="json"),
            "significance": robustness_result.significance_stability.model_dump(mode="json"),
            "status": robustness_result.robustness_evidence_status.value,
            "variant_estimates": variant_rows,
        },
        time_window_sensitivity=_variant_rows(
            variant_rows, RobustnessVariantType.ALTERNATIVE_TIME_WINDOW
        ),
        control_group_sensitivity=_variant_rows(
            variant_rows, RobustnessVariantType.ALTERNATIVE_CONTROL_GROUP
        ),
        covariate_sensitivity=_variant_rows(variant_rows, RobustnessVariantType.COVARIATE_SET),
        leave_one_out_analysis=tuple(
            item.model_dump(mode="json") for item in robustness_result.leave_one_out_results
        ),
        placebo_analysis=tuple(
            item.model_dump(mode="json") for item in robustness_result.placebo_results
        ),
        event_study_sensitivity=tuple(
            item.model_dump(mode="json") for item in robustness_result.event_study_comparison
        ),
        pre_trend_diagnostics=robustness_result.pre_trend_diagnostics.model_dump(mode="json"),
        failed_variants=tuple(
            item.model_dump(mode="json") for item in robustness_result.failed_variants
        ),
        limitations=robustness_result.limitations,
    )


def visualization_section(
    visualization_artifacts: tuple[VisualizationArtifact, ...],
) -> VisualizationReportSection | None:
    if not visualization_artifacts:
        return None
    rows = tuple(
        {
            "visualization_id": artifact.visualization_id,
            "visualization_type": artifact.visualization_type.value,
            "title": artifact.specification.title,
            "source_artifact_ids": artifact.source_artifact_ids,
            "output_references": tuple(
                item.model_dump(mode="json") for item in artifact.output_references
            ),
            "warnings": artifact.warnings,
            "limitations": artifact.limitations,
        }
        for artifact in sorted(visualization_artifacts, key=lambda item: item.visualization_id)
    )
    return VisualizationReportSection(
        status=SectionStatus.AVAILABLE,
        visualization_count=len(rows),
        visualizations=rows,
    )


def _variant_rows(rows, variant_type: RobustnessVariantType) -> tuple[dict[str, Any], ...]:
    return tuple(row for row in rows if row["variant_type"] == variant_type.value)


def evidence_section(evidence_artifact: EvidenceArtifact) -> EvidenceAndClaimsSection:
    records = tuple(
        EvidenceRecordSummary(
            evidence_id=record.evidence_id,
            evidence_type=record.evidence_type.value,
            statistical_procedure=record.statistical_procedure,
            variable_ids=_evidence_variable_ids(record),
            direction=getattr(getattr(record, "direction", None), "value", None),
            sample_size=record.sample_size,
            limitation_codes=record.limitation_codes,
            source_analysis_result_id=record.source_analysis_result_id,
        )
        for record in sorted(evidence_artifact.evidence_records, key=lambda item: item.evidence_id)
    )
    claims = tuple(
        ClaimSummary(
            claim_id=claim.claim_id,
            claim_type=claim.claim_type.value,
            subject_variable=claim.subject_variable,
            outcome_variable=claim.outcome_variable,
            related_variables=claim.related_variables,
            direction=claim.direction.value,
            statistical_procedure=claim.statistical_procedure,
            supporting_evidence_ids=claim.supporting_evidence_ids,
            limitation_codes=claim.limitation_codes,
            causal=claim.causal,
            generalization_scope=claim.generalization_scope,
        )
        for claim in sorted(evidence_artifact.claim_candidates, key=lambda item: item.claim_id)
    )
    return EvidenceAndClaimsSection(evidence_records=records, claim_candidates=claims)


def domain_assessments_section(
    coordinated_assessment: CoordinatedAssessment,
) -> DomainAssessmentsSection:
    domains = []
    for coverage in sorted(
        coordinated_assessment.domain_coverage, key=lambda item: DOMAIN_ORDER.index(item.domain)
    ):
        referenced_evidence = tuple(
            record.evidence_id
            for record in coordinated_assessment.evidence_domain_map
            if coverage.domain in record.selecting_domains
        )
        referenced_claims = tuple(
            record.claim_id
            for record in coordinated_assessment.claim_domain_map
            if coverage.domain in record.selecting_domains
        )
        domains.append(
            DomainAssessmentSummary(
                domain=coverage.domain,
                assessment_supplied=coverage.assessment_supplied,
                assessment_id=coverage.assessment_id,
                relevant_evidence_count=coverage.relevant_evidence_count,
                relevant_claim_count=coverage.relevant_claim_count,
                domain_concerns=tuple(
                    sorted(
                        {
                            concern
                            for divergence in coordinated_assessment.divergences
                            if coverage.domain in divergence.domains_involved
                            for concern in divergence.domain_concern_codes
                        },
                        key=lambda item: item.value,
                    )
                ),
                inherited_limitations=tuple(
                    sorted(
                        {
                            item.limitation_code
                            for item in coordinated_assessment.shared_limitations
                            if coverage.domain in item.domains
                        },
                        key=lambda item: item.value,
                    )
                ),
                unsupported_inferences=tuple(
                    sorted(
                        {
                            item.inference_code
                            for item in coordinated_assessment.shared_unsupported_inferences
                            if coverage.domain in item.domains
                        },
                        key=lambda item: item.value,
                    )
                ),
                coverage_status=coverage.coverage_status,
                referenced_evidence_ids=tuple(sorted(referenced_evidence)),
                referenced_claim_ids=tuple(sorted(referenced_claims)),
            )
        )
    return DomainAssessmentsSection(domains=tuple(domains))


def cross_domain_section(
    *,
    coordinated_assessment: CoordinatedAssessment,
    synthesis_artifact: SynthesisArtifact,
) -> CrossDomainSection:
    return CrossDomainSection(
        shared_evidence=tuple(
            record.model_dump(mode="json")
            for record in coordinated_assessment.evidence_domain_map
            if record.cross_domain
        ),
        shared_claims=tuple(
            record.model_dump(mode="json")
            for record in coordinated_assessment.claim_domain_map
            if record.cross_domain
        ),
        agreements=tuple(
            item.model_dump(mode="json") for item in coordinated_assessment.agreements
        ),
        divergences=tuple(
            item.model_dump(mode="json") for item in coordinated_assessment.divergences
        ),
        cross_domain_findings=tuple(
            item.model_dump(mode="json") for item in synthesis_artifact.cross_domain_findings
        ),
        participating_domains=coordinated_assessment.participating_domains,
        missing_domains=coordinated_assessment.missing_domains,
        uneven_coverage=bool(coordinated_assessment.domain_gaps),
    )


def synthesis_section(synthesis_artifact: SynthesisArtifact) -> SynthesisSection:
    return SynthesisSection(
        synthesis_id=synthesis_artifact.synthesis_id,
        overall_summary=synthesis_artifact.overall_summary,
        domain_summaries=tuple(
            item.model_dump(mode="json") for item in synthesis_artifact.domain_summaries
        ),
        cross_domain_findings=tuple(
            item.model_dump(mode="json") for item in synthesis_artifact.cross_domain_findings
        ),
        limitations_summary=synthesis_artifact.limitations_summary,
        evidence_gaps_summary=synthesis_artifact.evidence_gaps_summary,
        preserved_unsupported_inferences=synthesis_artifact.unsupported_inferences_preserved,
        grounding_findings=tuple(
            item.model_dump(mode="json") for item in synthesis_artifact.grounding_findings
        ),
        referenced_claim_ids=synthesis_artifact.referenced_claim_ids,
        referenced_evidence_ids=synthesis_artifact.referenced_evidence_ids,
    )


def evidence_grounded_interpretation_section(
    reasoning_artifact: ReasoningArtifact | None,
) -> EvidenceGroundedInterpretationSection | None:
    if reasoning_artifact is None:
        return None

    def select(*categories: ReasoningCategory) -> tuple[dict[str, Any], ...]:
        allowed = set(categories)
        return tuple(
            statement.model_dump(mode="json")
            for statement in reasoning_artifact.reasoning_statements
            if statement.category in allowed
        )

    return EvidenceGroundedInterpretationSection(
        reasoning_id=reasoning_artifact.reasoning_id,
        mode=reasoning_artifact.mode.value,
        main_interpretations=select(ReasoningCategory.EMPIRICAL_INTERPRETATION),
        cross_domain_patterns=select(ReasoningCategory.CROSS_DOMAIN_SYNTHESIS),
        plausible_mechanisms=select(ReasoningCategory.PLAUSIBLE_MECHANISM),
        alternative_explanations=select(ReasoningCategory.ALTERNATIVE_EXPLANATION),
        potential_confounders=tuple(
            item.model_dump(mode="json") for item in reasoning_artifact.candidate_confounders
        ),
        contradictions=tuple(
            item.model_dump(mode="json") for item in reasoning_artifact.contradictions
        ),
        limitations=select(ReasoningCategory.LIMITATION, ReasoningCategory.UNCERTAINTY),
        follow_up_hypotheses=tuple(
            item.model_dump(mode="json") for item in reasoning_artifact.follow_up_hypotheses
        ),
        follow_up_research_questions=tuple(
            item.model_dump(mode="json") for item in reasoning_artifact.follow_up_research_questions
        ),
        grounding_summary=reasoning_artifact.grounding_summary.model_dump(mode="json"),
    )


def literature_context_section(literature_context) -> LiteratureContextSection:
    if literature_context is None:
        return LiteratureContextSection(
            status=SectionStatus.UNAVAILABLE,
            limitations=("No literature context artifact was supplied.",),
        )
    return LiteratureContextSection(
        status=SectionStatus.AVAILABLE,
        literature_context_id=literature_context.literature_context_id,
        corpus_id=literature_context.corpus_id,
        records=tuple(
            {
                "literature_evidence_id": record.literature_evidence_id,
                "empirical_claim_id": record.empirical_claim_id,
                "retrieval_query": record.retrieval_query,
                "support_classification": record.support_classification.value,
                "chunks": [
                    {
                        "rank": row.rank,
                        "chunk_id": row.chunk.chunk_id,
                        "document_id": row.document.document_id,
                        "score": row.score,
                        "title": row.document.title,
                        "authors": list(row.document.authors),
                        "year": row.document.year,
                        "publication": row.document.publication,
                        "doi": row.document.doi,
                        "url": row.document.url,
                    }
                    for row in record.ranked_chunks
                ],
            }
            for record in literature_context.literature_evidence
        ),
        unmatched_claims=literature_context.unmatched_claims,
        retrieval_summary=literature_context.retrieval_summary.model_dump(mode="json"),
        limitations=(
            "Literature retrieval is corpus-grounded and lexical.",
            "Retrieved literature does not replace empirical evidence or validate causality.",
        ),
    )


def limitations_section(
    *,
    evidence_artifact: EvidenceArtifact,
    analysis_result: AnalysisResult,
    coordinated_assessment: CoordinatedAssessment,
    synthesis_artifact: SynthesisArtifact,
) -> LimitationsSection:
    limitations = _all_limitations(evidence_artifact, coordinated_assessment)
    if limitations:
        summary = (
            "The report preserves upstream limitation codes and keeps interpretation bounded "
            "to structured, non-causal Polaris artifacts."
        )
    else:
        summary = (
            "No upstream limitation codes were recorded; evidence strength remains unassessed."
        )
    return LimitationsSection(
        limitation_codes=limitations,
        analysis_findings=tuple(item.model_dump(mode="json") for item in analysis_result.findings),
        coordination_findings=tuple(
            item.model_dump(mode="json") for item in coordinated_assessment.coordination_findings
        ),
        synthesis_findings=tuple(
            item.model_dump(mode="json") for item in synthesis_artifact.grounding_findings
        ),
        narrative_summary=summary,
    )


def gaps_section(coordinated_assessment: CoordinatedAssessment) -> GapsSection:
    return GapsSection(
        evidence_gaps=tuple(
            item.model_dump(mode="json") for item in coordinated_assessment.evidence_gaps
        ),
        domain_gaps=tuple(
            item.model_dump(mode="json") for item in coordinated_assessment.domain_gaps
        ),
    )


def unsupported_inferences_section(
    coordinated_assessment: CoordinatedAssessment, synthesis_artifact: SynthesisArtifact
) -> UnsupportedInferencesSection:
    codes = tuple(
        sorted(
            {
                *(
                    item.inference_code
                    for item in coordinated_assessment.shared_unsupported_inferences
                ),
                *synthesis_artifact.unsupported_inferences_preserved,
            },
            key=lambda item: item.value,
        )
    )
    sources = tuple(
        {
            "inference_code": item.inference_code.value,
            "domains": [domain.value for domain in item.domains],
            "relevant_claim_ids": list(item.relevant_claim_ids),
        }
        for item in coordinated_assessment.shared_unsupported_inferences
    )
    return UnsupportedInferencesSection(unsupported_inferences=codes, source_ids_by_code=sources)


def provenance_section(
    *,
    ingestion_result: DatasetIngestionResult,
    analysis_result: AnalysisResult,
    evidence_artifact: EvidenceArtifact,
    coordinated_assessment: CoordinatedAssessment,
    reasoning_artifact: ReasoningArtifact | None = None,
    synthesis_artifact: SynthesisArtifact,
    report_id: str,
    generation_timestamp,
    report_ruleset_version: str,
) -> ProvenanceSection:
    return ProvenanceSection(
        dataset_id=ingestion_result.dataset_manifest.dataset_id,
        source_checksum_sha256=ingestion_result.checksum_sha256,
        ingestion_timestamp=ingestion_result.ingestion_timestamp,
        analysis_result_id=analysis_result.result_id,
        evidence_artifact_id=evidence_artifact.artifact_id,
        claim_ids=tuple(sorted(claim.claim_id for claim in evidence_artifact.claim_candidates)),
        agent_assessment_ids=coordinated_assessment.source_assessment_ids,
        coordinated_assessment_id=coordinated_assessment.coordinated_assessment_id,
        reasoning_artifact_id=(
            reasoning_artifact.reasoning_id if reasoning_artifact is not None else None
        ),
        synthesis_artifact_id=synthesis_artifact.synthesis_id,
        report_id=report_id,
        schema_versions={
            "phase3": ingestion_result.schema_version,
            "phase4": analysis_result.schema_version,
            "phase5": evidence_artifact.schema_version,
            "phase7": coordinated_assessment.schema_version,
            **(
                {"phase18": reasoning_artifact.schema_version}
                if reasoning_artifact is not None
                else {}
            ),
            "phase8": synthesis_artifact.schema_version,
        },
        software_version=synthesis_artifact.provenance.software_version,
        report_ruleset_version=report_ruleset_version,
        report_generation_timestamp=generation_timestamp,
    )


def executive_summary(
    synthesis_artifact: SynthesisArtifact,
    coordinated: CoordinatedAssessment,
    reasoning_artifact: ReasoningArtifact | None = None,
) -> str:
    parts = [synthesis_artifact.overall_summary]
    parts.append(
        "The report preserves observational and non-causal boundaries from upstream artifacts."
    )
    if coordinated.missing_domains:
        parts.append("Domain coverage is incomplete.")
    if reasoning_artifact is not None:
        parts.append(
            "Evidence-grounded interpretation is supplied as a separate reasoning artifact."
        )
    parts.append("No external literature or outside contextual evidence has been integrated.")
    if any(
        item.finding_code.value == "FALLBACK_USED" for item in synthesis_artifact.grounding_findings
    ):
        parts.append("Deterministic fallback synthesis was used.")
    return " ".join(parts)


def _all_limitations(
    evidence_artifact: EvidenceArtifact, coordinated_assessment: CoordinatedAssessment
) -> tuple[LimitationCode, ...]:
    limitations = {
        limitation
        for record in evidence_artifact.evidence_records
        for limitation in record.limitation_codes
    }
    limitations.update(
        limitation
        for claim in evidence_artifact.claim_candidates
        for limitation in claim.limitation_codes
    )
    limitations.update(item.limitation_code for item in coordinated_assessment.shared_limitations)
    return tuple(sorted(limitations, key=lambda item: item.value))


def _evidence_variable_ids(record) -> tuple[str, ...]:
    values = []
    for field_name in (
        "variable_id",
        "variable_id_1",
        "variable_id_2",
        "dependent_variable_id",
        "predictor_variable_ids",
        "required_variable_ids",
        "variable_ids",
    ):
        value = getattr(record, field_name, None)
        if value is None:
            continue
        if isinstance(value, tuple):
            values.extend(value)
        else:
            values.append(value)
    return tuple(sorted(set(values)))


def _significance_threshold(analysis_result: AnalysisResult) -> float | None:
    for coefficient in getattr(analysis_result.method_result, "coefficients", ()):
        if coefficient.below_significance_threshold is not None:
            return 0.05
    return None


def _is_illustrative(manifest: DatasetManifest) -> bool:
    text = " ".join(
        item
        for item in (
            manifest.dataset_id,
            manifest.title,
            manifest.provider,
            manifest.description or "",
            manifest.source_url,
        )
        if item
    ).lower()
    return any(marker in text for marker in ("sample", "synthetic", "illustrative", "test"))
