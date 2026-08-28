"""Deterministic robustness comparison summaries."""

from __future__ import annotations

from statistics import median

from polaris.analysis.causal.models import CausalAnalysisResult
from polaris.analysis.robustness.models import (
    FailedRobustnessVariant,
    RobustnessComparisonSummary,
    RobustnessEvidenceStatus,
    RobustnessVariantResult,
    RobustnessVariantType,
    SignificanceStabilitySummary,
    TreatmentEffectStabilitySummary,
)


def treatment_effect_stability(
    baseline: CausalAnalysisResult,
    results: tuple[RobustnessVariantResult, ...],
) -> TreatmentEffectStabilitySummary:
    estimates = [
        item.analysis_result.treatment_effect.estimate
        for item in results
        if item.analysis_result.treatment_effect.estimate is not None
    ]
    baseline_estimate = baseline.treatment_effect.estimate
    all_estimates = ([baseline_estimate] if baseline_estimate is not None else []) + estimates
    return TreatmentEffectStabilitySummary(
        baseline_estimate=baseline_estimate,
        minimum_estimate=min(all_estimates) if all_estimates else None,
        maximum_estimate=max(all_estimates) if all_estimates else None,
        median_estimate=float(median(all_estimates)) if all_estimates else None,
        number_positive=sum(1 for value in estimates if value > 0),
        number_negative=sum(1 for value in estimates if value < 0),
        number_crossing_zero=sum(
            1
            for item in results
            if _ci_crosses_zero(
                item.analysis_result.treatment_effect.confidence_interval_low,
                item.analysis_result.treatment_effect.confidence_interval_high,
            )
        ),
        successful_variant_count=len(results),
    )


def significance_stability(
    baseline: CausalAnalysisResult,
    results: tuple[RobustnessVariantResult, ...],
    *,
    threshold: float | None,
) -> SignificanceStabilitySummary:
    baseline_sig = _significant(baseline.treatment_effect.p_value, threshold)
    values = [
        _significant(item.analysis_result.treatment_effect.p_value, threshold) for item in results
    ]
    return SignificanceStabilitySummary(
        significance_threshold=threshold,
        baseline_significant=baseline_sig,
        significant_variant_count=sum(1 for item in values if item is True),
        nonsignificant_variant_count=sum(1 for item in values if item is False),
        changed_relative_to_baseline_count=sum(
            1
            for item in values
            if item is not None and baseline_sig is not None and item != baseline_sig
        ),
    )


def comparison_summaries(
    results: tuple[RobustnessVariantResult, ...],
    failures: tuple[FailedRobustnessVariant, ...],
) -> tuple[RobustnessComparisonSummary, ...]:
    summaries = []
    for variant_type in RobustnessVariantType:
        type_results = tuple(item for item in results if item.variant_type is variant_type)
        type_failures = tuple(item for item in failures if item.variant_type is variant_type)
        if not type_results and not type_failures:
            continue
        estimates = [
            item.analysis_result.treatment_effect.estimate
            for item in type_results
            if item.analysis_result.treatment_effect.estimate is not None
        ]
        summaries.append(
            RobustnessComparisonSummary(
                variant_type=variant_type,
                successful_specifications=len(type_results),
                failed_specifications=len(type_failures),
                estimate_minimum=min(estimates) if estimates else None,
                estimate_maximum=max(estimates) if estimates else None,
                estimate_median=float(median(estimates)) if estimates else None,
            )
        )
    return tuple(summaries)


def evidence_status(
    *,
    stability: TreatmentEffectStabilitySummary,
    significance: SignificanceStabilitySummary,
    failure_count: int,
    placebo_concern_count: int,
    largest_leave_one_out_change: float | None,
) -> RobustnessEvidenceStatus:
    if stability.successful_variant_count == 0:
        return RobustnessEvidenceStatus.ROBUSTNESS_INSUFFICIENT
    if failure_count or placebo_concern_count:
        return RobustnessEvidenceStatus.ROBUSTNESS_MIXED
    if stability.number_positive and stability.number_negative:
        return RobustnessEvidenceStatus.ROBUSTNESS_SENSITIVE
    if significance.changed_relative_to_baseline_count > max(
        1, stability.successful_variant_count // 2
    ):
        return RobustnessEvidenceStatus.ROBUSTNESS_MIXED
    if largest_leave_one_out_change is not None and abs(largest_leave_one_out_change) > abs(
        stability.baseline_estimate or 0.0
    ):
        return RobustnessEvidenceStatus.ROBUSTNESS_SENSITIVE
    return RobustnessEvidenceStatus.ROBUSTNESS_CONSISTENT


def _significant(p_value: float | None, threshold: float | None) -> bool | None:
    if p_value is None or threshold is None:
        return None
    return p_value < threshold


def _ci_crosses_zero(low: float | None, high: float | None) -> bool:
    return low is not None and high is not None and low <= 0 <= high
