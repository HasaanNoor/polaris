"""Typed contracts for Phase 19 reasoning evaluation and benchmarking."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import Field, field_validator, model_validator

from polaris.coordination.models import CoordinatedAssessment
from polaris.evidence.models import Direction, EvidenceArtifact
from polaris.evidence.provenance import deterministic_id
from polaris.literature.models import LiteratureContextArtifact
from polaris.reasoning.models import ReasoningArtifact
from polaris.reasoning.taxonomy import (
    CausalStatus,
    EpistemicStatus,
    ReasoningCategory,
    ReasoningMode,
)
from polaris.schemas.common import AwareDatetime, FrozenPolarisBaseModel, NonEmptyStr, SchemaVersion

EVALUATION_SCHEMA_VERSION = "1.0.0"
EVALUATOR_VERSION = "phase19_reasoning_evaluation_v1"


class BenchmarkTag(StrEnum):
    BASIC_ASSOCIATION = "basic_association"
    CONDITIONAL_ASSOCIATION = "conditional_association"
    NON_SIGNIFICANT_RESULT = "non_significant_result"
    CONFLICTING_EVIDENCE = "conflicting_evidence"
    CROSS_DOMAIN_AGREEMENT = "cross_domain_agreement"
    CROSS_DOMAIN_DIVERGENCE = "cross_domain_divergence"
    LITERATURE_ALIGNMENT = "literature_alignment"
    LITERATURE_CONTRAST = "literature_contrast"
    SMALL_SAMPLE = "small_sample"
    HIGH_MISSINGNESS = "high_missingness"
    POTENTIAL_CONFOUNDER = "potential_confounder"
    PLAUSIBLE_MECHANISM = "plausible_mechanism"
    CAUSAL_TRAP = "causal_trap"
    FABRICATED_GROUNDING = "fabricated_grounding"
    FABRICATED_CITATION = "fabricated_citation"
    PROJECTION_VS_HISTORICAL = "projection_vs_historical"
    MEASUREMENT_UNCERTAINTY = "measurement_uncertainty"
    PROVIDER_FAILURE = "provider_failure"
    DETERMINISTIC_FALLBACK = "deterministic_fallback"
    REAL_DATA_DERIVED = "real_data_derived"
    SYNTHETIC = "synthetic"
    ADVERSARIAL = "adversarial"


class ExpectedLiteratureBehavior(StrEnum):
    NONE = "none"
    ALIGNMENT = "alignment"
    CONTRAST = "contrast"
    SEPARATE_FROM_EMPIRICAL = "separate_from_empirical"


class EvaluationSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class EvaluationFindingCode(StrEnum):
    INVALID_GROUNDING = "invalid_grounding"
    ORPHAN_STATEMENT = "orphan_statement"
    EVIDENCE_DIRECTION_MISMATCH = "evidence_direction_mismatch"
    OVERSTATED_SIGNIFICANCE = "overstated_significance"
    CONDITIONALITY_LOST = "conditionality_lost"
    CAUSAL_OVERCLAIM = "causal_overclaim"
    MECHANISM_MISLABELED = "mechanism_mislabeled"
    EPISTEMIC_STATUS_MISMATCH = "epistemic_status_mismatch"
    CONTRADICTION_IGNORED = "contradiction_ignored"
    MATERIAL_LIMITATION_DROPPED = "material_limitation_dropped"
    LITERATURE_AS_EMPIRICAL_EVIDENCE = "literature_as_empirical_evidence"
    FABRICATED_CITATION = "fabricated_citation"
    STRUCTURAL_INVALIDITY = "structural_invalidity"
    NON_DETERMINISTIC_FALLBACK = "non_deterministic_fallback"
    EXPECTED_CATEGORY_MISSING = "expected_category_missing"
    PROHIBITED_CATEGORY_PRESENT = "prohibited_category_present"


class EvaluationDimension(StrEnum):
    GROUNDING = "grounding"
    EVIDENCE_FIDELITY = "evidence_fidelity"
    CAUSAL_RESTRAINT = "causal_restraint"
    EPISTEMIC_CALIBRATION = "epistemic_calibration"
    CONTRADICTION_HANDLING = "contradiction_handling"
    LIMITATION_PROPAGATION = "limitation_propagation"
    LITERATURE_SEPARATION = "literature_separation"
    STRUCTURAL_VALIDITY = "structural_validity"
    REPRODUCIBILITY = "reproducibility"
    EXPECTED_BEHAVIOR = "expected_behavior"


class ExpectedReasoningBehavior(FrozenPolarisBaseModel):
    required_statement_categories: tuple[ReasoningCategory, ...] = Field(default_factory=tuple)
    prohibited_statement_categories: tuple[ReasoningCategory, ...] = Field(default_factory=tuple)
    required_grounding_ids: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    prohibited_grounding_ids: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    expected_direction: Direction | None = None
    expected_causal_status: CausalStatus | None = CausalStatus.NON_CAUSAL
    expected_epistemic_statuses: tuple[EpistemicStatus, ...] = Field(default_factory=tuple)
    expected_limitations: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    expected_contradictions: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    expected_candidate_confounders: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    expected_literature_behavior: ExpectedLiteratureBehavior = ExpectedLiteratureBehavior.NONE
    minimum_grounded_statements: int = Field(default=1, ge=0)
    maximum_unsupported_statements: int = Field(default=0, ge=0)
    notes: NonEmptyStr | None = None

    @field_validator(
        "required_statement_categories",
        "prohibited_statement_categories",
        "expected_epistemic_statuses",
    )
    @classmethod
    def sort_enums(cls, value):
        return tuple(sorted(set(value), key=lambda item: item.value))

    @field_validator(
        "required_grounding_ids",
        "prohibited_grounding_ids",
        "expected_limitations",
        "expected_contradictions",
        "expected_candidate_confounders",
    )
    @classmethod
    def sort_strings(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(sorted(set(value)))


class BenchmarkCase(FrozenPolarisBaseModel):
    case_id: NonEmptyStr
    title: NonEmptyStr
    description: NonEmptyStr
    research_question: NonEmptyStr
    evidence_artifact: EvidenceArtifact
    coordinated_assessment: CoordinatedAssessment
    literature_context: LiteratureContextArtifact | None = None
    expected_behavior: ExpectedReasoningBehavior
    benchmark_tags: tuple[BenchmarkTag, ...]
    reasoning_modes: tuple[ReasoningMode, ...] = (ReasoningMode.DETERMINISTIC,)
    schema_version: SchemaVersion = EVALUATION_SCHEMA_VERSION

    @field_validator("benchmark_tags")
    @classmethod
    def sort_tags(cls, value: tuple[BenchmarkTag, ...]) -> tuple[BenchmarkTag, ...]:
        return tuple(sorted(set(value), key=lambda item: item.value))

    @field_validator("reasoning_modes")
    @classmethod
    def sort_modes(cls, value: tuple[ReasoningMode, ...]) -> tuple[ReasoningMode, ...]:
        return tuple(sorted(set(value), key=lambda item: item.value))

    @model_validator(mode="after")
    def validate_lineage(self) -> "BenchmarkCase":
        if (
            self.evidence_artifact.artifact_id
            != self.coordinated_assessment.source_evidence_artifact_id
        ):
            raise ValueError("benchmark case evidence and coordination lineage must match")
        if self.literature_context is not None:
            claim_ids = {claim.claim_id for claim in self.evidence_artifact.claim_candidates}
            if not set(self.literature_context.empirical_claim_ids) <= claim_ids:
                raise ValueError("benchmark literature context must reference known claim IDs")
        return self


class EvaluationFinding(FrozenPolarisBaseModel):
    code: EvaluationFindingCode
    severity: EvaluationSeverity
    dimension: EvaluationDimension
    message: NonEmptyStr
    source_ids: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    statement_ids: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)

    @field_validator("source_ids", "statement_ids")
    @classmethod
    def sort_ids(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(sorted(set(value)))


class DimensionEvaluationResult(FrozenPolarisBaseModel):
    dimension: EvaluationDimension
    passed: bool
    findings: tuple[EvaluationFinding, ...] = Field(default_factory=tuple)
    metrics: dict[str, int | float | bool] = Field(default_factory=dict)


class ReasoningEvaluationMetrics(FrozenPolarisBaseModel):
    grounding_coverage: float
    evidence_fidelity_pass_rate: float
    causal_restraint_pass: bool
    required_category_coverage: float
    contradiction_detection_rate: float
    material_limitation_coverage: float
    structural_validity_pass: bool
    deterministic_reproducibility_pass: bool | None = None


class ReasoningEvaluationResult(FrozenPolarisBaseModel):
    evaluation_id: NonEmptyStr
    benchmark_case_id: NonEmptyStr
    reasoning_artifact_id: NonEmptyStr
    reasoning_mode: ReasoningMode
    findings: tuple[EvaluationFinding, ...] = Field(default_factory=tuple)
    dimension_results: tuple[DimensionEvaluationResult, ...]
    metrics: ReasoningEvaluationMetrics
    pass_fail_criteria: tuple[NonEmptyStr, ...]
    failed_expectations: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    passed_expectations: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    evaluator_version: NonEmptyStr = EVALUATOR_VERSION
    schema_version: SchemaVersion = EVALUATION_SCHEMA_VERSION
    creation_timestamp: AwareDatetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("findings")
    @classmethod
    def sort_findings(cls, value: tuple[EvaluationFinding, ...]) -> tuple[EvaluationFinding, ...]:
        return tuple(
            sorted(value, key=lambda item: (item.severity.value, item.code.value, item.message))
        )


class BenchmarkSuite(FrozenPolarisBaseModel):
    suite_id: NonEmptyStr
    title: NonEmptyStr
    description: NonEmptyStr
    benchmark_cases: tuple[BenchmarkCase, ...]
    version: NonEmptyStr
    tags: tuple[BenchmarkTag, ...] = Field(default_factory=tuple)
    schema_version: SchemaVersion = EVALUATION_SCHEMA_VERSION

    @field_validator("benchmark_cases")
    @classmethod
    def sort_cases(cls, value: tuple[BenchmarkCase, ...]) -> tuple[BenchmarkCase, ...]:
        ids = [case.case_id for case in value]
        if len(ids) != len(set(ids)):
            raise ValueError("benchmark case IDs must be unique")
        return tuple(sorted(value, key=lambda case: case.case_id))

    @field_validator("tags")
    @classmethod
    def sort_tags(cls, value: tuple[BenchmarkTag, ...]) -> tuple[BenchmarkTag, ...]:
        return tuple(sorted(set(value), key=lambda item: item.value))


class ModeComparison(FrozenPolarisBaseModel):
    reasoning_mode: ReasoningMode
    executed_cases: int
    dimension_pass_counts: dict[str, int]
    failure_counts_by_code: dict[str, int]
    metric_means: dict[str, float]


class BenchmarkSuiteResult(FrozenPolarisBaseModel):
    suite_id: NonEmptyStr
    executed_cases: tuple[NonEmptyStr, ...]
    reasoning_modes: tuple[ReasoningMode, ...]
    case_results: tuple[ReasoningEvaluationResult, ...]
    aggregate_dimension_summaries: dict[str, dict[str, int]]
    failure_counts_by_code: dict[str, int]
    mode_comparisons: tuple[ModeComparison, ...]
    reproducibility_findings: tuple[EvaluationFinding, ...] = Field(default_factory=tuple)
    evaluator_version: NonEmptyStr = EVALUATOR_VERSION
    run_metadata: dict[str, Any] = Field(default_factory=dict)
    creation_timestamp: AwareDatetime = Field(default_factory=lambda: datetime.now(UTC))
    schema_version: SchemaVersion = EVALUATION_SCHEMA_VERSION


def deterministic_evaluation_id(
    *,
    benchmark_case_id: str,
    reasoning_artifact: ReasoningArtifact,
    dimension_results: tuple[DimensionEvaluationResult, ...],
    metrics: ReasoningEvaluationMetrics,
) -> str:
    return deterministic_id(
        "reasoning_eval_",
        {
            "benchmark_case_id": benchmark_case_id,
            "reasoning_artifact_id": reasoning_artifact.reasoning_id,
            "reasoning_mode": reasoning_artifact.mode.value,
            "dimensions": [item.model_dump(mode="json") for item in dimension_results],
            "metrics": metrics.model_dump(mode="json"),
            "evaluator_version": EVALUATOR_VERSION,
            "schema_version": EVALUATION_SCHEMA_VERSION,
        },
    )


def deterministic_suite_id(*, title: str, version: str, case_ids: tuple[str, ...]) -> str:
    return deterministic_id(
        "benchmark_suite_",
        {
            "title": title,
            "version": version,
            "case_ids": tuple(sorted(case_ids)),
            "schema_version": EVALUATION_SCHEMA_VERSION,
        },
    )
