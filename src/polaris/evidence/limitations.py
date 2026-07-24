"""Deterministic limitation-code propagation from Phase 4 results."""

from collections.abc import Iterable

from polaris.analysis.models import (
    AnalysisFinding,
    AnalysisFindingCode,
    DiagnosticResult,
    DiagnosticStatus,
)
from polaris.evidence.models import LimitationCode

_FINDING_LIMITATIONS: dict[AnalysisFindingCode, LimitationCode] = {
    AnalysisFindingCode.EXCLUDED_MISSING_ROWS: LimitationCode.MISSING_DATA_EXCLUSION,
    AnalysisFindingCode.CONSTANT_VARIABLE: LimitationCode.CONSTANT_VARIABLE,
    AnalysisFindingCode.ALL_NULL_VARIABLE: LimitationCode.CONSTANT_VARIABLE,
    AnalysisFindingCode.SINGULAR_DESIGN_MATRIX: LimitationCode.SINGULAR_DESIGN_MATRIX,
    AnalysisFindingCode.MULTICOLLINEARITY: LimitationCode.MULTICOLLINEARITY,
    AnalysisFindingCode.HETEROSKEDASTICITY_TEST_RESULT: (LimitationCode.HETEROSKEDASTICITY_WARNING),
    AnalysisFindingCode.RESIDUAL_NORMALITY_TEST_RESULT: (LimitationCode.RESIDUAL_NORMALITY_WARNING),
    AnalysisFindingCode.UNDEFINED_STATISTIC: LimitationCode.UNDEFINED_DIAGNOSTIC,
    AnalysisFindingCode.DIAGNOSTIC_NOT_APPLICABLE: LimitationCode.UNDEFINED_DIAGNOSTIC,
    AnalysisFindingCode.PERFECT_CORRELATION: LimitationCode.PERFECT_CORRELATION,
}


def limitations_from_findings(
    findings: Iterable[AnalysisFinding],
) -> tuple[LimitationCode, ...]:
    values = [
        limitation
        for finding in findings
        if (limitation := _FINDING_LIMITATIONS.get(finding.code)) is not None
    ]
    return ordered_limitations(values)


def limitations_from_diagnostic(diagnostic: DiagnosticResult) -> tuple[LimitationCode, ...]:
    values: list[LimitationCode] = []
    if diagnostic.status is not DiagnosticStatus.CALCULATED:
        values.append(LimitationCode.UNDEFINED_DIAGNOSTIC)
    for code in diagnostic.warning_codes:
        if limitation := _FINDING_LIMITATIONS.get(code):
            values.append(limitation)
    return ordered_limitations(values)


def ordered_limitations(values: Iterable[LimitationCode]) -> tuple[LimitationCode, ...]:
    return tuple(sorted(set(values), key=lambda item: item.value))
