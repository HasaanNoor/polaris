"""Robustness diagnostics derived from Phase 22 causal outputs."""

from __future__ import annotations

from polaris.analysis.causal.models import (
    CausalAnalysisResult,
    EventStudyCoefficient,
    ParallelTrendDiagnosticStatus,
)
from polaris.analysis.robustness.models import (
    EventStudyComparisonRecord,
    LeaveOneOutResult,
    ParallelTrendRobustnessStatus,
    PlaceboResult,
    PreTrendRobustnessSummary,
    RobustnessVariantResult,
    RobustnessVariantType,
)


def observation_changes(
    baseline: CausalAnalysisResult,
    variant: CausalAnalysisResult,
    excluded_entities: tuple[str, ...],
):
    from polaris.analysis.robustness.models import VariantObservationChanges

    baseline_rows = set(baseline.sample_summary.included_row_numbers)
    variant_rows = set(variant.sample_summary.included_row_numbers)
    return VariantObservationChanges(
        included_row_numbers_added=tuple(sorted(variant_rows - baseline_rows)),
        included_row_numbers_removed=tuple(sorted(baseline_rows - variant_rows)),
        excluded_entities=tuple(sorted(excluded_entities)),
    )


def interval_overlap(baseline: CausalAnalysisResult, variant: CausalAnalysisResult) -> bool | None:
    base = baseline.treatment_effect
    effect = variant.treatment_effect
    if (
        base.confidence_interval_low is None
        or base.confidence_interval_high is None
        or effect.confidence_interval_low is None
        or effect.confidence_interval_high is None
    ):
        return None
    return not (
        effect.confidence_interval_high < base.confidence_interval_low
        or effect.confidence_interval_low > base.confidence_interval_high
    )


def pretrend_summary(
    baseline: CausalAnalysisResult,
    results: tuple[RobustnessVariantResult, ...],
) -> PreTrendRobustnessSummary:
    diagnostics = (
        {
            "variant_id": "baseline",
            "status": baseline.diagnostics.parallel_trends.status.value,
            "summary": baseline.diagnostics.parallel_trends.trend_summary,
        },
        *(
            {
                "variant_id": item.variant_id,
                "status": item.analysis_result.diagnostics.parallel_trends.status.value,
                "summary": item.analysis_result.diagnostics.parallel_trends.trend_summary,
            }
            for item in results
        ),
    )
    statuses = {item["status"] for item in diagnostics}
    if not results:
        status = ParallelTrendRobustnessStatus.INSUFFICIENT_VARIANTS
        text = "no successful robustness variants were available for pre-trend comparison"
    elif statuses == {
        ParallelTrendDiagnosticStatus.CONCERNING_PRE_TREATMENT_EVIDENCE_DETECTED.value
    }:
        status = ParallelTrendRobustnessStatus.CONSISTENT_CONCERN
        text = "pre-trend concern appears consistently across reviewed specifications"
    elif ParallelTrendDiagnosticStatus.CONCERNING_PRE_TREATMENT_EVIDENCE_DETECTED.value in statuses:
        status = ParallelTrendRobustnessStatus.SOME_CONCERN
        text = "pre-trend concern appears only under some reviewed specifications"
    elif statuses == {ParallelTrendDiagnosticStatus.INSUFFICIENT_PRE_TREATMENT_DATA.value}:
        status = ParallelTrendRobustnessStatus.INSUFFICIENT_PRE_TREATMENT_DATA
        text = "pre-treatment data are insufficient across reviewed specifications"
    else:
        status = ParallelTrendRobustnessStatus.NO_OBVIOUS_DIVERGENCE_ACROSS_REVIEWED_VARIANTS
        text = "no obvious pre-treatment divergence was detected across reviewed variants"
    return PreTrendRobustnessSummary(
        status=status,
        diagnostics_by_variant=tuple(diagnostics),
        interpretation=text + "; this does not prove parallel trends.",
    )


def leave_one_out_results(
    baseline: CausalAnalysisResult,
    results: tuple[RobustnessVariantResult, ...],
) -> tuple[LeaveOneOutResult, ...]:
    values = []
    for item in results:
        if item.variant_type not in {
            RobustnessVariantType.LEAVE_ONE_TREATED_ENTITY_OUT,
            RobustnessVariantType.LEAVE_ONE_CONTROL_ENTITY_OUT,
        }:
            continue
        entity = item.observation_changes.excluded_entities[0]
        effect = item.analysis_result.treatment_effect
        values.append(
            LeaveOneOutResult(
                variant_id=item.variant_id,
                omitted_entity=entity,
                omitted_role=(
                    "treated"
                    if item.variant_type is RobustnessVariantType.LEAVE_ONE_TREATED_ENTITY_OUT
                    else "control"
                ),
                treatment_estimate=effect.estimate,
                standard_error=effect.standard_error,
                confidence_interval_low=effect.confidence_interval_low,
                confidence_interval_high=effect.confidence_interval_high,
                p_value=effect.p_value,
                sample_size=item.analysis_result.sample_summary.included_rows,
                cluster_count=item.analysis_result.sample_summary.cluster_count,
                difference_from_baseline=_difference(
                    effect.estimate,
                    baseline.treatment_effect.estimate,
                ),
                low_cluster_warning=item.analysis_result.sample_summary.cluster_count < 20,
            )
        )
    return tuple(sorted(values, key=lambda item: item.variant_id))


def placebo_results(results: tuple[RobustnessVariantResult, ...]) -> tuple[PlaceboResult, ...]:
    values = []
    for item in results:
        if item.variant_type not in {
            RobustnessVariantType.PLACEBO_TIMING,
            RobustnessVariantType.PLACEBO_ASSIGNMENT,
        }:
            continue
        effect = item.analysis_result.treatment_effect
        significant = effect.p_value is not None and effect.p_value < 0.05
        values.append(
            PlaceboResult(
                variant_id=item.variant_id,
                placebo_year=item.analysis_result.causal_specification.treatment.treatment_start_period,
                placebo_treated_entities=tuple(
                    sorted(item.analysis_result.sample_summary.model_dump().keys())
                )
                if item.variant_type is RobustnessVariantType.PLACEBO_ASSIGNMENT
                else (),
                estimate=effect.estimate,
                standard_error=effect.standard_error,
                confidence_interval_low=effect.confidence_interval_low,
                confidence_interval_high=effect.confidence_interval_high,
                p_value=effect.p_value,
                sample_size=item.analysis_result.sample_summary.included_rows,
                cluster_count=item.analysis_result.sample_summary.cluster_count,
                diagnostic_interpretation=(
                    "placebo estimate is statistically distinguishable from zero; "
                    "this is a warning, not automatic invalidation"
                    if significant
                    else "placebo estimate was not statistically distinguishable from zero "
                    "under the configured threshold"
                ),
            )
        )
    return tuple(sorted(values, key=lambda item: item.variant_id))


def event_study_comparison(
    baseline: CausalAnalysisResult,
    results: tuple[RobustnessVariantResult, ...],
) -> tuple[EventStudyComparisonRecord, ...]:
    baseline_records = (
        _event_records("baseline", baseline.event_study_results)
        if baseline.event_study_results
        else ()
    )
    records = [
        *baseline_records,
        *[
            record
            for item in results
            if item.analysis_result.event_study_results
            for record in _event_records(item.variant_id, item.analysis_result.event_study_results)
        ],
    ]
    return tuple(sorted(records, key=lambda item: (item.variant_id, item.event_time)))


def _event_records(
    variant_id: str, coefficients: tuple[EventStudyCoefficient, ...]
) -> tuple[EventStudyComparisonRecord, ...]:
    if not coefficients:
        return ()
    reference = next(item.event_time for item in coefficients if item.reference_period)
    return tuple(
        EventStudyComparisonRecord(
            variant_id=variant_id,
            event_time=item.event_time,
            estimate=item.coefficient,
            standard_error=item.standard_error,
            confidence_interval_low=item.confidence_interval_low,
            confidence_interval_high=item.confidence_interval_high,
            p_value=item.p_value,
            pre_post_status=item.pre_post_status,
            omitted_reference_period=reference,
        )
        for item in coefficients
    )


def _difference(value: float | None, baseline: float | None) -> float | None:
    if value is None or baseline is None:
        return None
    return value - baseline
