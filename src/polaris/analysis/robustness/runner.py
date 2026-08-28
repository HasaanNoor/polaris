"""Execution engine for explicit causal robustness analyses."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime

from polaris import __version__
from polaris.analysis.causal.models import CausalAnalysisRequest, CausalAnalysisResult
from polaris.analysis.causal.service import run_causal_analysis
from polaris.analysis.robustness.comparison import (
    comparison_summaries,
    evidence_status,
    significance_stability,
    treatment_effect_stability,
)
from polaris.analysis.robustness.diagnostics import (
    event_study_comparison,
    interval_overlap,
    leave_one_out_results,
    observation_changes,
    placebo_results,
    pretrend_summary,
)
from polaris.analysis.robustness.models import (
    ROBUSTNESS_RULESET_VERSION,
    ROBUSTNESS_SCHEMA_VERSION,
    BaselineSpecificationSnapshot,
    FailedRobustnessVariant,
    RobustnessAnalysisResult,
    RobustnessProvenance,
    RobustnessSpecification,
    RobustnessVariantResult,
)
from polaris.analysis.robustness.specifications import apply_variant
from polaris.ingestion.models import DatasetIngestionResult


def run_robustness_analysis(
    *,
    ingestion_result: DatasetIngestionResult,
    baseline_result: CausalAnalysisResult,
    specification: RobustnessSpecification,
    significance_threshold: float | None = None,
) -> RobustnessAnalysisResult:
    """Run explicitly configured robustness checks around one baseline causal result."""

    if specification.baseline_analysis_id != baseline_result.causal_analysis_id:
        raise ValueError("robustness baseline_analysis_id must match baseline result")
    if specification.baseline_specification != baseline_result.causal_specification:
        raise ValueError("robustness baseline specification must match baseline result")

    successes: list[RobustnessVariantResult] = []
    failures: list[FailedRobustnessVariant] = []
    for variant in specification.variants:
        try:
            variant_input = apply_variant(
                baseline=baseline_result.causal_specification,
                ingestion_result=ingestion_result,
                variant=variant,
            )
            result = run_causal_analysis(
                request=CausalAnalysisRequest(
                    ingestion_result=variant_input.ingestion_result,
                    causal_specification=variant_input.specification,
                    significance_threshold=significance_threshold,
                    confidence_level=variant.confidence_level,
                )
            )
            _validate_minimums(result, specification, variant)
            successes.append(
                RobustnessVariantResult(
                    variant_id=variant.variant_id,
                    variant_type=variant.variant_type,
                    analysis_result=result,
                    observation_changes=observation_changes(
                        baseline_result, result, variant_input.excluded_entities
                    ),
                    estimate_difference_from_baseline=_difference(
                        result.treatment_effect.estimate,
                        baseline_result.treatment_effect.estimate,
                    ),
                    confidence_interval_overlaps_baseline=interval_overlap(baseline_result, result),
                )
            )
        except Exception as exc:
            failures.append(
                FailedRobustnessVariant(
                    variant_id=variant.variant_id,
                    variant_type=variant.variant_type,
                    error_type=type(exc).__name__,
                    reason=str(exc) or type(exc).__name__,
                    methodological_implication=(
                        "The configured robustness check could not be estimated and remains "
                        "visible; it should not be dropped from interpretation."
                    ),
                )
            )

    variant_results = tuple(sorted(successes, key=lambda item: item.variant_id))
    failed = tuple(sorted(failures, key=lambda item: item.variant_id))
    loo = leave_one_out_results(baseline_result, variant_results)
    placebos = placebo_results(variant_results)
    stability = treatment_effect_stability(baseline_result, variant_results)
    significance = significance_stability(
        baseline_result, variant_results, threshold=significance_threshold
    )
    max_loo = max(
        (
            abs(item.difference_from_baseline)
            for item in loo
            if item.difference_from_baseline is not None
        ),
        default=None,
    )
    status = evidence_status(
        stability=stability,
        significance=significance,
        failure_count=len(failed),
        placebo_concern_count=sum(
            1 for item in placebos if "warning" in item.diagnostic_interpretation
        ),
        largest_leave_one_out_change=max_loo,
    )
    timestamp = datetime.now(UTC)
    provenance = RobustnessProvenance(
        dataset_id=baseline_result.dataset_id,
        source_checksum_sha256=baseline_result.source_checksum_sha256,
        baseline_analysis_id=baseline_result.causal_analysis_id,
        baseline_specification=baseline_result.causal_specification,
        variant_specifications=specification.variants,
        study_id=specification.study_id,
        intervention_id=specification.intervention_id,
        treatment_sources=specification.treatment_provenance,
        excluded_observations_by_variant=tuple(
            {
                "variant_id": item.variant_id,
                "included_row_numbers_removed": (
                    item.observation_changes.included_row_numbers_removed
                ),
                "excluded_entities": item.observation_changes.excluded_entities,
            }
            for item in variant_results
        ),
        estimator_version=baseline_result.estimator.value,
    )
    return RobustnessAnalysisResult(
        robustness_analysis_id=_robustness_id(
            baseline_result=baseline_result,
            specification=specification,
            dataset_checksum=ingestion_result.checksum_sha256,
        ),
        study_id=specification.study_id,
        baseline=_baseline_snapshot(baseline_result, specification),
        baseline_result=baseline_result,
        variants=specification.variants,
        variant_results=variant_results,
        failed_variants=failed,
        comparison_summaries=comparison_summaries(variant_results, failed),
        treatment_effect_stability=stability,
        significance_stability=significance,
        robustness_evidence_status=status,
        pre_trend_diagnostics=pretrend_summary(baseline_result, variant_results),
        leave_one_out_results=loo,
        placebo_results=placebos,
        event_study_comparison=event_study_comparison(baseline_result, variant_results),
        limitations=_limitations(baseline_result, variant_results, failed),
        plotting_artifacts=_plotting_artifacts(variant_results, loo, placebos),
        provenance=provenance,
        analysis_timestamp=timestamp,
        software_version=f"polaris-{__version__}",
    )


def _validate_minimums(result, specification, variant) -> None:
    min_obs = variant.minimum_required_observations or specification.minimum_required_observations
    min_clusters = variant.minimum_required_clusters or specification.minimum_required_clusters
    if result.sample_summary.included_rows < min_obs:
        raise ValueError("robustness variant has insufficient observations")
    if result.sample_summary.cluster_count < min_clusters:
        raise ValueError("robustness variant has insufficient clusters")


def _baseline_snapshot(
    baseline_result: CausalAnalysisResult,
    specification: RobustnessSpecification,
) -> BaselineSpecificationSnapshot:
    spec = baseline_result.causal_specification
    event = spec.event_study
    return BaselineSpecificationSnapshot(
        baseline_analysis_id=baseline_result.causal_analysis_id,
        study_id=specification.study_id,
        intervention_id=specification.intervention_id,
        treatment_provenance=specification.treatment_provenance,
        estimand=baseline_result.estimand,
        method=baseline_result.method,
        controls=tuple(
            item.strip() for item in spec.comparison_group_description.split(",") if item.strip()
        ),
        covariates=tuple(item.variable_id for item in spec.covariates),
        event_window=(event.min_event_time, event.max_event_time) if event else None,
        event_reference_period=event.reference_event_time if event else None,
        pre_treatment_window=spec.pre_treatment_window,
        post_treatment_window=spec.post_treatment_window,
        assumptions=spec.assumptions,
    )


def _limitations(
    baseline_result: CausalAnalysisResult,
    results: tuple[RobustnessVariantResult, ...],
    failures: tuple[FailedRobustnessVariant, ...],
) -> tuple[str, ...]:
    values = set(baseline_result.limitations)
    values.add("robustness diagnostics do not prove identifying assumptions")
    values.add("robustness variants were limited to explicit reviewed specifications")
    if failures:
        values.add("one or more robustness variants failed and must remain visible")
    if any(item.analysis_result.sample_summary.cluster_count < 20 for item in results):
        values.add("one or more robustness variants retains low-cluster inference warnings")
    return tuple(sorted(values))


def _plotting_artifacts(variant_results, loo, placebos):
    estimates = tuple(
        {
            "variant_id": item.variant_id,
            "variant_type": item.variant_type.value,
            "estimate": item.analysis_result.treatment_effect.estimate,
            "standard_error": item.analysis_result.treatment_effect.standard_error,
            "lower_ci": item.analysis_result.treatment_effect.confidence_interval_low,
            "upper_ci": item.analysis_result.treatment_effect.confidence_interval_high,
            "p_value": item.analysis_result.treatment_effect.p_value,
            "sample_size": item.analysis_result.sample_summary.included_rows,
            "cluster_count": item.analysis_result.sample_summary.cluster_count,
        }
        for item in variant_results
    )
    return {
        "robustness_estimates.csv": estimates,
        "leave_one_out.csv": tuple(item.model_dump(mode="json") for item in loo),
        "placebo_results.csv": tuple(item.model_dump(mode="json") for item in placebos),
    }


def _robustness_id(*, baseline_result, specification, dataset_checksum: str) -> str:
    payload = {
        "baseline_analysis_id": baseline_result.causal_analysis_id,
        "baseline_specification": baseline_result.causal_specification.model_dump(mode="json"),
        "study_id": specification.study_id,
        "intervention_id": specification.intervention_id,
        "treatment_provenance": specification.treatment_provenance,
        "variants": [item.model_dump(mode="json") for item in specification.variants],
        "dataset_checksum": dataset_checksum,
        "schema_version": ROBUSTNESS_SCHEMA_VERSION,
        "ruleset_version": ROBUSTNESS_RULESET_VERSION,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return "robustness_analysis_" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _difference(value: float | None, baseline: float | None) -> float | None:
    if value is None or baseline is None:
        return None
    return value - baseline
