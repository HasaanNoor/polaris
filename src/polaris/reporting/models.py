"""Typed contracts for Phase 9 structured research reports."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import Field, field_validator, model_validator

from polaris import __version__
from polaris.agents.models import AgentDomain, DomainConcernCode, UnsupportedInferenceCode
from polaris.analysis.models import AnalysisResult
from polaris.analysis.robustness.models import RobustnessAnalysisResult
from polaris.coordination.models import (
    CoordinatedAssessment,
    CoordinationCoverageStatus,
)
from polaris.evidence.models import EvidenceArtifact, LimitationCode
from polaris.ingestion.models import DatasetIngestionResult
from polaris.literature.models import LiteratureContextArtifact
from polaris.reasoning.models import ReasoningArtifact
from polaris.schemas.common import (
    AwareDatetime,
    DatasetId,
    FrozenPolarisBaseModel,
    NonEmptyStr,
    SchemaVersion,
    StatisticalProcedure,
    VariableId,
)
from polaris.schemas.dataset import DatasetManifest
from polaris.schemas.research_question import ResearchQuestion
from polaris.synthesis.models import SynthesisArtifact, SynthesisMode
from polaris.visualization.models import VisualizationArtifact

REPORT_SCHEMA_VERSION = "1.0.0"
REPORT_RULESET_VERSION = "deterministic_phase9_v1"


class ReportFormat(StrEnum):
    JSON = "json"
    MARKDOWN = "markdown"
    HTML = "html"


class ReportRenderingSettings(FrozenPolarisBaseModel):
    include_empty_tables: bool = True
    compact_ids: bool = False


class ReportRequest(FrozenPolarisBaseModel):
    synthesis_artifact: SynthesisArtifact
    coordinated_assessment: CoordinatedAssessment
    evidence_artifact: EvidenceArtifact
    analysis_result: AnalysisResult
    ingestion_result: DatasetIngestionResult
    research_question: ResearchQuestion | None = None
    literature_context: LiteratureContextArtifact | None = None
    reasoning_artifact: ReasoningArtifact | None = None
    robustness_result: RobustnessAnalysisResult | None = None
    visualization_artifacts: tuple[VisualizationArtifact, ...] = Field(default_factory=tuple)
    dataset_manifest: DatasetManifest | None = None
    output_format: ReportFormat = ReportFormat.JSON
    report_title: NonEmptyStr | None = None
    report_subtitle: NonEmptyStr | None = None
    author: NonEmptyStr | None = None
    organization: NonEmptyStr | None = None
    rendering_settings: ReportRenderingSettings = Field(default_factory=ReportRenderingSettings)


class GeneratedReport(FrozenPolarisBaseModel):
    report: "ResearchReport"
    rendered_content: str | None = None
    output_format: ReportFormat


class ReportMetadata(FrozenPolarisBaseModel):
    title: NonEmptyStr
    subtitle: NonEmptyStr | None = None
    generation_timestamp: AwareDatetime = Field(default_factory=lambda: datetime.now(UTC))
    polaris_software_version: NonEmptyStr = f"polaris-{__version__}"
    report_schema_version: SchemaVersion = REPORT_SCHEMA_VERSION
    dataset_id: DatasetId
    source_checksum_sha256: str
    analysis_procedure: StatisticalProcedure
    synthesis_mode: SynthesisMode
    source_artifact_ids: tuple[NonEmptyStr, ...]
    author: NonEmptyStr | None = None
    organization: NonEmptyStr | None = None
    report_format: ReportFormat
    deterministic_ruleset_version: NonEmptyStr = REPORT_RULESET_VERSION

    @field_validator("source_artifact_ids")
    @classmethod
    def sort_ids(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(sorted(set(value)))


class SectionStatus(StrEnum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    EMPTY = "empty"


class ResearchQuestionSection(FrozenPolarisBaseModel):
    status: SectionStatus
    question_id: NonEmptyStr | None = None
    primary_question: NonEmptyStr | None = None
    population: NonEmptyStr | None = None
    geographic_scope: dict[str, Any] | None = None
    temporal_scope: dict[str, Any] | None = None
    variables_or_concepts: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    stated_constraints: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    intended_analytical_methods: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)


class DatasetSection(FrozenPolarisBaseModel):
    dataset_id: DatasetId
    dataset_title: NonEmptyStr | None = None
    provider: NonEmptyStr | None = None
    source_checksum_sha256: str
    source_type: NonEmptyStr
    geographic_coverage: dict[str, Any] | None = None
    temporal_coverage: dict[str, Any] | None = None
    accepted_row_count: int = Field(ge=0)
    rejected_row_count: int = Field(ge=0)
    analysis_ready: bool
    quality_profile_facts: tuple[dict[str, Any], ...] = Field(default_factory=tuple)
    relevant_variable_ids: tuple[VariableId, ...] = Field(default_factory=tuple)
    source_limitations: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    illustrative: bool


class MethodologySection(FrozenPolarisBaseModel):
    ingestion_and_validation: NonEmptyStr
    sample_construction: NonEmptyStr
    statistical_procedure: StatisticalProcedure
    dependent_variable: VariableId | None = None
    predictors: tuple[VariableId, ...] = Field(default_factory=tuple)
    controls: tuple[VariableId, ...] = Field(default_factory=tuple)
    include_intercept: bool | None = None
    confidence_level: float | None = None
    significance_threshold: float | None = None
    diagnostics_calculated: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    evidence_extraction_process: NonEmptyStr
    domain_agent_process: NonEmptyStr
    coordination_process: NonEmptyStr
    synthesis_mode: SynthesisMode
    grounding_and_validation: NonEmptyStr


class StatisticalResultsSection(FrozenPolarisBaseModel):
    analysis_result_id: NonEmptyStr
    method: StatisticalProcedure
    sample_size: int = Field(ge=0)
    descriptive_results: tuple[dict[str, Any], ...] = Field(default_factory=tuple)
    correlation_results: tuple[dict[str, Any], ...] = Field(default_factory=tuple)
    regression_results: dict[str, Any] | None = None
    diagnostics: tuple[dict[str, Any], ...] = Field(default_factory=tuple)
    findings: tuple[dict[str, Any], ...] = Field(default_factory=tuple)


class EvidenceRecordSummary(FrozenPolarisBaseModel):
    evidence_id: NonEmptyStr
    evidence_type: NonEmptyStr
    statistical_procedure: StatisticalProcedure
    variable_ids: tuple[VariableId, ...] = Field(default_factory=tuple)
    direction: NonEmptyStr | None = None
    sample_size: int | None = Field(default=None, ge=0)
    limitation_codes: tuple[LimitationCode, ...] = Field(default_factory=tuple)
    source_analysis_result_id: NonEmptyStr

    @field_validator("limitation_codes")
    @classmethod
    def sort_limitations(cls, value: tuple[LimitationCode, ...]) -> tuple[LimitationCode, ...]:
        return tuple(sorted(set(value), key=lambda item: item.value))


class ClaimSummary(FrozenPolarisBaseModel):
    claim_id: NonEmptyStr
    claim_type: NonEmptyStr
    subject_variable: VariableId | None = None
    outcome_variable: VariableId | None = None
    related_variables: tuple[VariableId, ...] = Field(default_factory=tuple)
    direction: NonEmptyStr
    statistical_procedure: StatisticalProcedure
    supporting_evidence_ids: tuple[NonEmptyStr, ...]
    limitation_codes: tuple[LimitationCode, ...] = Field(default_factory=tuple)
    causal: bool = False
    generalization_scope: Literal["analysis_sample"] = "analysis_sample"

    @field_validator("supporting_evidence_ids", "related_variables")
    @classmethod
    def sort_strings(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(sorted(set(value)))

    @field_validator("limitation_codes")
    @classmethod
    def sort_limitations(cls, value: tuple[LimitationCode, ...]) -> tuple[LimitationCode, ...]:
        return tuple(sorted(set(value), key=lambda item: item.value))


class EvidenceAndClaimsSection(FrozenPolarisBaseModel):
    evidence_records: tuple[EvidenceRecordSummary, ...]
    claim_candidates: tuple[ClaimSummary, ...]


class CausalDesignSection(FrozenPolarisBaseModel):
    status: SectionStatus
    research_design: NonEmptyStr | None = None
    treatment: VariableId | None = None
    comparison_group: NonEmptyStr | None = None
    treatment_timing: NonEmptyStr | None = None
    outcome: VariableId | None = None
    estimand: NonEmptyStr | None = None
    model: NonEmptyStr | None = None
    treatment_effect: dict[str, Any] | None = None
    clustered_uncertainty: dict[str, Any] | None = None
    event_study_results: tuple[dict[str, Any], ...] = Field(default_factory=tuple)
    identifying_assumptions: tuple[dict[str, Any], ...] = Field(default_factory=tuple)
    diagnostics: tuple[dict[str, Any], ...] = Field(default_factory=tuple)
    registry_provenance: dict[str, str] = Field(default_factory=dict)
    limitations: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)


class RobustnessSection(FrozenPolarisBaseModel):
    status: SectionStatus
    robustness_analysis_id: NonEmptyStr
    baseline_analysis_id: NonEmptyStr
    baseline_specification: dict[str, Any]
    variants_tested: tuple[dict[str, Any], ...] = Field(default_factory=tuple)
    treatment_effect_comparison: dict[str, Any] = Field(default_factory=dict)
    time_window_sensitivity: tuple[dict[str, Any], ...] = Field(default_factory=tuple)
    control_group_sensitivity: tuple[dict[str, Any], ...] = Field(default_factory=tuple)
    covariate_sensitivity: tuple[dict[str, Any], ...] = Field(default_factory=tuple)
    leave_one_out_analysis: tuple[dict[str, Any], ...] = Field(default_factory=tuple)
    placebo_analysis: tuple[dict[str, Any], ...] = Field(default_factory=tuple)
    event_study_sensitivity: tuple[dict[str, Any], ...] = Field(default_factory=tuple)
    pre_trend_diagnostics: dict[str, Any] = Field(default_factory=dict)
    failed_variants: tuple[dict[str, Any], ...] = Field(default_factory=tuple)
    limitations: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)


class DomainAssessmentSummary(FrozenPolarisBaseModel):
    domain: AgentDomain
    assessment_supplied: bool
    assessment_id: NonEmptyStr | None = None
    relevant_evidence_count: int = Field(ge=0)
    relevant_claim_count: int = Field(ge=0)
    domain_concerns: tuple[DomainConcernCode, ...] = Field(default_factory=tuple)
    inherited_limitations: tuple[LimitationCode, ...] = Field(default_factory=tuple)
    unsupported_inferences: tuple[UnsupportedInferenceCode, ...] = Field(default_factory=tuple)
    coverage_status: CoordinationCoverageStatus
    referenced_evidence_ids: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    referenced_claim_ids: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)


class DomainAssessmentsSection(FrozenPolarisBaseModel):
    domains: tuple[DomainAssessmentSummary, ...]


class CrossDomainSection(FrozenPolarisBaseModel):
    shared_evidence: tuple[dict[str, Any], ...] = Field(default_factory=tuple)
    shared_claims: tuple[dict[str, Any], ...] = Field(default_factory=tuple)
    agreements: tuple[dict[str, Any], ...] = Field(default_factory=tuple)
    divergences: tuple[dict[str, Any], ...] = Field(default_factory=tuple)
    cross_domain_findings: tuple[dict[str, Any], ...] = Field(default_factory=tuple)
    participating_domains: tuple[AgentDomain, ...]
    missing_domains: tuple[AgentDomain, ...] = Field(default_factory=tuple)
    uneven_coverage: bool


class SynthesisSection(FrozenPolarisBaseModel):
    synthesis_id: NonEmptyStr
    overall_summary: NonEmptyStr
    domain_summaries: tuple[dict[str, Any], ...]
    cross_domain_findings: tuple[dict[str, Any], ...] = Field(default_factory=tuple)
    limitations_summary: NonEmptyStr
    evidence_gaps_summary: NonEmptyStr
    preserved_unsupported_inferences: tuple[UnsupportedInferenceCode, ...]
    grounding_findings: tuple[dict[str, Any], ...] = Field(default_factory=tuple)
    referenced_claim_ids: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    referenced_evidence_ids: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)


class EvidenceGroundedInterpretationSection(FrozenPolarisBaseModel):
    reasoning_id: NonEmptyStr
    mode: NonEmptyStr
    main_interpretations: tuple[dict[str, Any], ...] = Field(default_factory=tuple)
    cross_domain_patterns: tuple[dict[str, Any], ...] = Field(default_factory=tuple)
    plausible_mechanisms: tuple[dict[str, Any], ...] = Field(default_factory=tuple)
    alternative_explanations: tuple[dict[str, Any], ...] = Field(default_factory=tuple)
    potential_confounders: tuple[dict[str, Any], ...] = Field(default_factory=tuple)
    contradictions: tuple[dict[str, Any], ...] = Field(default_factory=tuple)
    limitations: tuple[dict[str, Any], ...] = Field(default_factory=tuple)
    follow_up_hypotheses: tuple[dict[str, Any], ...] = Field(default_factory=tuple)
    follow_up_research_questions: tuple[dict[str, Any], ...] = Field(default_factory=tuple)
    grounding_summary: dict[str, Any] = Field(default_factory=dict)


class LiteratureContextSection(FrozenPolarisBaseModel):
    status: SectionStatus
    literature_context_id: NonEmptyStr | None = None
    corpus_id: NonEmptyStr | None = None
    records: tuple[dict[str, Any], ...] = Field(default_factory=tuple)
    unmatched_claims: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    retrieval_summary: dict[str, Any] = Field(default_factory=dict)
    limitations: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)


class VisualizationReportSection(FrozenPolarisBaseModel):
    status: SectionStatus
    visualization_count: int = Field(ge=0)
    visualizations: tuple[dict[str, Any], ...] = Field(default_factory=tuple)


class LimitationsSection(FrozenPolarisBaseModel):
    limitation_codes: tuple[LimitationCode, ...]
    analysis_findings: tuple[dict[str, Any], ...] = Field(default_factory=tuple)
    coordination_findings: tuple[dict[str, Any], ...] = Field(default_factory=tuple)
    synthesis_findings: tuple[dict[str, Any], ...] = Field(default_factory=tuple)
    narrative_summary: NonEmptyStr


class GapsSection(FrozenPolarisBaseModel):
    evidence_gaps: tuple[dict[str, Any], ...] = Field(default_factory=tuple)
    domain_gaps: tuple[dict[str, Any], ...] = Field(default_factory=tuple)


class UnsupportedInferencesSection(FrozenPolarisBaseModel):
    unsupported_inferences: tuple[UnsupportedInferenceCode, ...]
    source_ids_by_code: tuple[dict[str, Any], ...] = Field(default_factory=tuple)


class ProvenanceSection(FrozenPolarisBaseModel):
    dataset_id: DatasetId
    source_checksum_sha256: str
    ingestion_timestamp: AwareDatetime
    analysis_result_id: NonEmptyStr
    evidence_artifact_id: NonEmptyStr
    claim_ids: tuple[NonEmptyStr, ...]
    agent_assessment_ids: tuple[NonEmptyStr, ...]
    coordinated_assessment_id: NonEmptyStr
    reasoning_artifact_id: NonEmptyStr | None = None
    synthesis_artifact_id: NonEmptyStr
    report_id: NonEmptyStr
    schema_versions: dict[str, str]
    software_version: NonEmptyStr
    report_ruleset_version: NonEmptyStr
    report_generation_timestamp: AwareDatetime


class ReferenceKind(StrEnum):
    EVIDENCE = "evidence"
    CLAIM = "claim"
    ASSESSMENT = "assessment"
    AGREEMENT = "agreement"
    DIVERGENCE = "divergence"
    GAP = "gap"
    SOURCE_ARTIFACT = "source_artifact"
    LITERATURE = "literature"
    REASONING_STATEMENT = "reasoning_statement"


class ReferenceIndexEntry(FrozenPolarisBaseModel):
    reference_id: NonEmptyStr
    reference_kind: ReferenceKind
    label: NonEmptyStr
    metadata: dict[str, Any] = Field(default_factory=dict)


class ResearchReport(FrozenPolarisBaseModel):
    report_id: NonEmptyStr
    title: NonEmptyStr
    subtitle: NonEmptyStr | None = None
    report_metadata: ReportMetadata
    executive_summary: NonEmptyStr
    research_question_section: ResearchQuestionSection
    dataset_section: DatasetSection
    methodology_section: MethodologySection
    statistical_results_section: StatisticalResultsSection
    causal_design_section: CausalDesignSection | None = None
    robustness_section: RobustnessSection | None = None
    evidence_section: EvidenceAndClaimsSection
    domain_assessments_section: DomainAssessmentsSection
    cross_domain_section: CrossDomainSection
    evidence_grounded_interpretation_section: EvidenceGroundedInterpretationSection | None = None
    visualization_section: VisualizationReportSection | None = None
    synthesis_section: SynthesisSection
    literature_context_section: LiteratureContextSection | None = None
    limitations_section: LimitationsSection
    gaps_section: GapsSection
    unsupported_inferences_section: UnsupportedInferencesSection
    provenance_section: ProvenanceSection
    reference_index: tuple[ReferenceIndexEntry, ...]
    source_artifact_ids: tuple[NonEmptyStr, ...]
    schema_version: SchemaVersion = REPORT_SCHEMA_VERSION

    @field_validator("source_artifact_ids")
    @classmethod
    def sort_source_artifacts(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(sorted(set(value)))

    @model_validator(mode="after")
    def require_metadata_consistency(self) -> "ResearchReport":
        if self.title != self.report_metadata.title:
            raise ValueError("report title must match metadata title")
        if self.report_id != self.provenance_section.report_id:
            raise ValueError("report ID must match provenance")
        return self
