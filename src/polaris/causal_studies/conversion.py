"""Conversion from reviewed study metadata to explicit Phase 22 specifications."""

from __future__ import annotations

from polaris.analysis.causal.models import (
    CausalFixedEffectsConfig,
    CausalMethod,
    CausalSpecification,
    EventStudyConfig,
)
from polaris.analysis.causal.models import (
    TreatmentAssignment as Phase22TreatmentAssignment,
)
from polaris.causal_studies.errors import StudyConversionError
from polaris.causal_studies.models import (
    CausalStudyDefinition,
    ComparisonGroupPolicy,
    ReviewStatus,
    TreatmentStatus,
)
from polaris.causal_studies.provenance import registry_provenance
from polaris.schemas.common import NonEmptyStr, SpecificationId, VariableReference
from polaris.schemas.statistics import StandardErrorSpec


def build_causal_specification(
    *,
    study: CausalStudyDefinition,
    specification_id: SpecificationId,
    investigation_id: NonEmptyStr,
    outcome: VariableReference,
    controls: tuple[str, ...],
    covariates: tuple[VariableReference, ...] = (),
    treatment_variable: VariableReference,
    treatment_timing_variable: VariableReference | None = None,
    method: CausalMethod,
    pre_treatment_window: tuple[int | float, int | float],
    post_treatment_window: tuple[int | float, int | float],
    event_study: EventStudyConfig | None = None,
    fixed_effects: CausalFixedEffectsConfig | None = None,
    standard_error_strategy: StandardErrorSpec | None = None,
    treatment_timing_rule_confirmed: bool = False,
) -> CausalSpecification:
    """Build Phase 22 config only from explicit caller-approved methodological choices."""

    if study.review_status is not ReviewStatus.DESIGN_READY:
        raise StudyConversionError("study must be DESIGN_READY before conversion")
    if method not in study.supported_methods:
        raise StudyConversionError("requested method is not supported by the study definition")
    if outcome.variable_id not in {item.variable_id for item in study.proposed_outcomes}:
        raise StudyConversionError("outcome must be an explicitly reviewed study outcome")
    reviewed_covariates = {item.variable_id for item in study.proposed_covariates}
    missing_covariates = [
        item.variable_id for item in covariates if item.variable_id not in reviewed_covariates
    ]
    if missing_covariates:
        raise StudyConversionError("covariates must be explicitly reviewed by the study definition")
    if not controls:
        raise StudyConversionError("controls must be explicitly selected by the caller")
    if not treatment_timing_rule_confirmed:
        raise StudyConversionError("caller must explicitly confirm the treatment timing rule")
    if method is CausalMethod.EVENT_STUDY and event_study is None:
        raise StudyConversionError("event-study conversion requires an explicit event window")
    if method is CausalMethod.DIFFERENCE_IN_DIFFERENCES and event_study is not None:
        raise StudyConversionError("DiD conversion must not include an event-study window")
    explicit_controls = set(study.explicit_comparison_entities) | {
        item.entity_id
        for item in study.treatment_assignments
        if item.treatment_status is TreatmentStatus.NEVER_TREATED
    }
    if (
        study.comparison_group_policy is ComparisonGroupPolicy.EXPLICIT_ONLY
        and not set(controls) <= explicit_controls
    ):
        raise StudyConversionError("EXPLICIT_ONLY studies require controls declared in metadata")
    treatment_start = study.treatment_timing_rule.analysis_treatment_year
    return CausalSpecification(
        specification_id=specification_id,
        investigation_id=investigation_id,
        method=method,
        entity_variable=study.entity_variable,
        time_variable=study.time_variable,
        outcome_variable=outcome,
        treatment=Phase22TreatmentAssignment(
            treatment_variable=treatment_variable,
            treatment_start_period=treatment_start,
            treatment_timing_variable=treatment_timing_variable,
            absorbing=study.intervention.treatment_persistence.value == "absorbing",
            treatment_source=(
                f"causal_study_registry:{study.study_id}:{study.intervention.intervention_id}"
            ),
        ),
        treated_group_description=", ".join(
            item.entity_id
            for item in study.treatment_assignments
            if item.treatment_status is TreatmentStatus.TREATED
        ),
        comparison_group_description=", ".join(sorted(controls)),
        pre_treatment_window=pre_treatment_window,
        post_treatment_window=post_treatment_window,
        covariates=covariates,
        fixed_effects=fixed_effects or CausalFixedEffectsConfig(),
        standard_error_strategy=standard_error_strategy
        or StandardErrorSpec(
            strategy="cluster_robust",
            cluster_variables=[study.entity_variable],
        ),
        estimand=study.estimand,
        event_study=event_study,
        assumptions=study.identifying_assumptions,
        registry_provenance={key: str(value) for key, value in registry_provenance(study).items()},
    )
