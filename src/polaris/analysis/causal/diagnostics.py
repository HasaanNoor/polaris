"""Causal design diagnostics and assumption records."""

from polaris.analysis.causal.models import (
    CAUSAL_RULESET_VERSION,
    DesignAssumptionCode,
    DesignAssumptionRecord,
    DesignAssumptionStatus,
    EventStudyCoefficient,
    ParallelTrendDiagnosticStatus,
    ParallelTrendsDiagnostic,
)


def parallel_trends_diagnostic(
    event_results: tuple[EventStudyCoefficient, ...],
    *,
    required_pre_periods: int,
) -> ParallelTrendsDiagnostic:
    pre = tuple(
        item
        for item in event_results
        if item.event_time < 0 and not item.reference_period and item.coefficient is not None
    )
    if len(pre) < max(1, required_pre_periods - 1):
        return ParallelTrendsDiagnostic(
            status=ParallelTrendDiagnosticStatus.INSUFFICIENT_PRE_TREATMENT_DATA,
            pre_treatment_period_count=len(pre)
            + sum(1 for item in event_results if item.reference_period),
            pre_treatment_coefficients=pre,
            trend_summary="insufficient estimable pre-treatment event coefficients",
            data_sufficiency=(
                "insufficient pre-treatment coverage for a meaningful pre-trend diagnostic"
            ),
        )
    concerning = any(
        item.confidence_interval_low is not None
        and item.confidence_interval_high is not None
        and not (item.confidence_interval_low <= 0 <= item.confidence_interval_high)
        for item in pre
    )
    if concerning:
        status = ParallelTrendDiagnosticStatus.CONCERNING_PRE_TREATMENT_EVIDENCE_DETECTED
        summary = "one or more pre-treatment event coefficients excludes zero"
    else:
        status = ParallelTrendDiagnosticStatus.NO_OBVIOUS_PRE_TREATMENT_DIVERGENCE_DETECTED
        summary = "available pre-treatment event coefficients do not show obvious divergence"
    return ParallelTrendsDiagnostic(
        status=status,
        pre_treatment_period_count=len(pre) + 1,
        pre_treatment_coefficients=pre,
        trend_summary=summary,
        joint_diagnostic=(
            "Phase 22 reports lead coefficients; it does not claim a universal "
            "mechanical pass/fail test."
        ),
        data_sufficiency="pre-treatment event coefficients were estimable",
    )


def assumption_records(
    diagnostic: ParallelTrendsDiagnostic,
    *,
    limitations: tuple[str, ...],
) -> tuple[DesignAssumptionRecord, ...]:
    if (
        diagnostic.status
        is ParallelTrendDiagnosticStatus.CONCERNING_PRE_TREATMENT_EVIDENCE_DETECTED
    ):
        parallel_status = DesignAssumptionStatus.CONCERN
    elif diagnostic.status is ParallelTrendDiagnosticStatus.INSUFFICIENT_PRE_TREATMENT_DATA:
        parallel_status = DesignAssumptionStatus.INSUFFICIENT_INFORMATION
    else:
        parallel_status = DesignAssumptionStatus.NOT_VIOLATED_BY_AVAILABLE_DIAGNOSTIC
    base = {
        "provenance": {"ruleset_version": CAUSAL_RULESET_VERSION},
    }
    return (
        DesignAssumptionRecord(
            assumption_code=DesignAssumptionCode.PARALLEL_TRENDS,
            description=(
                "Treated and comparison entities would have followed parallel outcome "
                "trends absent treatment."
            ),
            status=parallel_status,
            diagnostic_evidence=diagnostic.trend_summary,
            limitation="Statistical non-significance does not prove parallel trends.",
            empirically_testable=True,
            **base,
        ),
        DesignAssumptionRecord(
            assumption_code=DesignAssumptionCode.NO_ANTICIPATION,
            description=(
                "Entities did not change outcomes in anticipation of treatment before "
                "the start period."
            ),
            status=DesignAssumptionStatus.INSUFFICIENT_INFORMATION
            if any("anticipation" in item.lower() for item in limitations)
            else DesignAssumptionStatus.UNTESTABLE,
            limitation="No-anticipation is only partially assessable with pre-treatment data.",
            empirically_testable=False,
            **base,
        ),
        DesignAssumptionRecord(
            assumption_code=DesignAssumptionCode.STABLE_TREATMENT_DEFINITION,
            description=(
                "Treatment assignment is stable and corresponds to the supplied "
                "explicit definition."
            ),
            status=DesignAssumptionStatus.NOT_VIOLATED_BY_AVAILABLE_DIAGNOSTIC,
            diagnostic_evidence="entity-level treatment assignment passed deterministic validation",
            empirically_testable=True,
            **base,
        ),
        DesignAssumptionRecord(
            assumption_code=DesignAssumptionCode.APPROPRIATE_COMPARISON_GROUP,
            description=(
                "Never-treated controls are an appropriate comparison for treated entities."
            ),
            status=DesignAssumptionStatus.INSUFFICIENT_INFORMATION,
            limitation=(
                "Comparison-group appropriateness requires substantive design justification."
            ),
            empirically_testable=False,
            **base,
        ),
        DesignAssumptionRecord(
            assumption_code=DesignAssumptionCode.NO_TREATMENT_CONTAMINATION,
            description=(
                "Comparison entities were not exposed to the treatment or close substitutes."
            ),
            status=DesignAssumptionStatus.UNTESTABLE,
            limitation="Polaris does not discover contamination or spillovers automatically.",
            empirically_testable=False,
            **base,
        ),
        DesignAssumptionRecord(
            assumption_code=DesignAssumptionCode.CONSISTENT_OUTCOME_MEASUREMENT,
            description="Outcome measurement is comparable across groups and time.",
            status=DesignAssumptionStatus.INSUFFICIENT_INFORMATION,
            limitation=(
                "Measurement comparability comes from source documentation, not the estimator."
            ),
            empirically_testable=False,
            **base,
        ),
        DesignAssumptionRecord(
            assumption_code=DesignAssumptionCode.NO_DIFFERENTIAL_COMPOSITIONAL_CHANGE,
            description=(
                "Group composition did not change differentially in ways that drive outcomes."
            ),
            status=DesignAssumptionStatus.UNTESTABLE,
            limitation="Composition changes are not fully detected by Phase 22.",
            empirically_testable=False,
            **base,
        ),
        DesignAssumptionRecord(
            assumption_code=DesignAssumptionCode.SUTVA_SPILLOVER,
            description=(
                "Treated units' outcomes do not affect comparison units' potential outcomes."
            ),
            status=DesignAssumptionStatus.UNTESTABLE,
            limitation="Spillover concerns require external design knowledge.",
            empirically_testable=False,
            **base,
        ),
    )
