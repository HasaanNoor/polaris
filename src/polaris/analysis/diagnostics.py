"""OLS diagnostic calculations."""

import numpy as np
from scipy import stats

from polaris.analysis.models import (
    AnalysisFindingCode,
    DiagnosticResult,
    DiagnosticStatus,
    OLSRegressionResult,
)
from polaris.analysis.sample import AnalysisSample
from polaris.analysis.utils import safe_float


def ols_diagnostics(
    sample: AnalysisSample,
    regression: OLSRegressionResult,
) -> tuple[DiagnosticResult, ...]:
    y = np.asarray([row[regression.dependent_variable_id] for row in sample.rows], dtype=float)
    predictors = np.asarray(
        [
            [row[variable_id] for variable_id in regression.predictor_variable_ids]
            for row in sample.rows
        ],
        dtype=float,
    )
    x = (
        np.column_stack([np.ones(len(y)), predictors])
        if regression.include_intercept
        else predictors
    )
    beta = np.asarray([coefficient.estimate or 0.0 for coefficient in regression.coefficients])
    residuals = y - (x @ beta)
    diagnostics: list[DiagnosticResult] = [
        _condition_number(x),
        *_vif_results(predictors, regression.predictor_variable_ids),
        _residual_normality(residuals),
        _breusch_pagan(residuals, x),
        _leverage_summary(x),
        _durbin_watson(residuals),
    ]
    return tuple(diagnostics)


def _condition_number(x: np.ndarray) -> DiagnosticResult:
    value = safe_float(np.linalg.cond(x))
    status = DiagnosticStatus.CALCULATED if value is not None else DiagnosticStatus.UNDEFINED
    return DiagnosticResult(
        name="condition_number",
        status=status,
        statistic=value,
        warning_codes=() if value is not None else (AnalysisFindingCode.UNDEFINED_STATISTIC,),
        explanation="Condition number was calculated from the OLS design matrix.",
    )


def _vif_results(
    predictors: np.ndarray, variable_ids: tuple[str, ...]
) -> tuple[DiagnosticResult, ...]:
    if predictors.shape[1] < 2 or predictors.shape[0] <= predictors.shape[1]:
        return (
            DiagnosticResult(
                name="variance_inflation_factor",
                status=DiagnosticStatus.NOT_APPLICABLE,
                warning_codes=(AnalysisFindingCode.DIAGNOSTIC_NOT_APPLICABLE,),
                explanation="VIF requires at least two predictors and more rows than predictors.",
            ),
        )
    results: list[DiagnosticResult] = []
    for index, variable_id in enumerate(variable_ids):
        y = predictors[:, index]
        others = np.delete(predictors, index, axis=1)
        if len(set(y.tolist())) == 1:
            results.append(
                DiagnosticResult(
                    name="variance_inflation_factor",
                    status=DiagnosticStatus.UNDEFINED,
                    variable_id=variable_id,
                    warning_codes=(AnalysisFindingCode.CONSTANT_VARIABLE,),
                    explanation="VIF is undefined for a constant predictor.",
                )
            )
            continue
        design = np.column_stack([np.ones(others.shape[0]), others])
        fitted = design @ (np.linalg.pinv(design) @ y)
        rss = float(np.sum((y - fitted) ** 2))
        tss = float(np.sum((y - np.mean(y)) ** 2))
        if tss == 0:
            vif = None
            codes = (AnalysisFindingCode.CONSTANT_VARIABLE,)
            status = DiagnosticStatus.UNDEFINED
        else:
            r_squared = 1 - rss / tss
            if r_squared >= 1:
                vif = None
                codes = (AnalysisFindingCode.MULTICOLLINEARITY,)
                status = DiagnosticStatus.UNDEFINED
            else:
                vif = safe_float(1 / (1 - r_squared))
                codes = ()
                status = DiagnosticStatus.CALCULATED
        results.append(
            DiagnosticResult(
                name="variance_inflation_factor",
                status=status,
                statistic=vif,
                variable_id=variable_id,
                warning_codes=codes,
                explanation=(
                    "VIF was calculated by regressing this predictor on the other predictors."
                ),
            )
        )
    return tuple(results)


def _residual_normality(residuals: np.ndarray) -> DiagnosticResult:
    if residuals.size < 8:
        return DiagnosticResult(
            name="residual_normality",
            status=DiagnosticStatus.NOT_APPLICABLE,
            warning_codes=(AnalysisFindingCode.DIAGNOSTIC_NOT_APPLICABLE,),
            explanation="Normality testing requires at least eight residuals.",
        )
    result = stats.normaltest(residuals)
    return DiagnosticResult(
        name="residual_normality",
        status=DiagnosticStatus.CALCULATED,
        statistic=safe_float(result.statistic),
        p_value=safe_float(result.pvalue),
        warning_codes=(AnalysisFindingCode.RESIDUAL_NORMALITY_TEST_RESULT,),
        explanation="D'Agostino and Pearson residual normality test was calculated.",
    )


def _breusch_pagan(residuals: np.ndarray, x: np.ndarray) -> DiagnosticResult:
    if residuals.size <= x.shape[1] or x.shape[1] < 2:
        return DiagnosticResult(
            name="breusch_pagan",
            status=DiagnosticStatus.NOT_APPLICABLE,
            warning_codes=(AnalysisFindingCode.DIAGNOSTIC_NOT_APPLICABLE,),
            explanation=(
                "Breusch-Pagan testing requires residual degrees of freedom and predictors."
            ),
        )
    squared = residuals**2
    fitted = x @ (np.linalg.pinv(x) @ squared)
    rss = float(np.sum((squared - fitted) ** 2))
    tss = float(np.sum((squared - np.mean(squared)) ** 2))
    if tss == 0:
        return DiagnosticResult(
            name="breusch_pagan",
            status=DiagnosticStatus.UNDEFINED,
            warning_codes=(AnalysisFindingCode.UNDEFINED_STATISTIC,),
            explanation="Breusch-Pagan statistic is undefined when squared residuals are constant.",
        )
    r_squared = 1 - rss / tss
    lm = residuals.size * r_squared
    df = x.shape[1] - 1
    return DiagnosticResult(
        name="breusch_pagan",
        status=DiagnosticStatus.CALCULATED,
        statistic=safe_float(lm),
        p_value=safe_float(stats.chi2.sf(lm, df)),
        warning_codes=(AnalysisFindingCode.HETEROSKEDASTICITY_TEST_RESULT,),
        explanation="Breusch-Pagan LM test was calculated from squared residuals and predictors.",
    )


def _leverage_summary(x: np.ndarray) -> DiagnosticResult:
    hat = x @ np.linalg.pinv(x.T @ x) @ x.T
    leverage = np.diag(hat)
    return DiagnosticResult(
        name="maximum_leverage",
        status=DiagnosticStatus.CALCULATED,
        statistic=safe_float(np.max(leverage)),
        explanation="Maximum diagonal leverage value was calculated from the OLS hat matrix.",
    )


def _durbin_watson(residuals: np.ndarray) -> DiagnosticResult:
    if residuals.size < 3:
        return DiagnosticResult(
            name="durbin_watson",
            status=DiagnosticStatus.NOT_APPLICABLE,
            warning_codes=(AnalysisFindingCode.DIAGNOSTIC_NOT_APPLICABLE,),
            explanation="Durbin-Watson requires ordered residuals and at least three observations.",
        )
    denominator = float(np.sum(residuals**2))
    statistic = (
        None if denominator == 0 else safe_float(np.sum(np.diff(residuals) ** 2) / denominator)
    )
    return DiagnosticResult(
        name="durbin_watson",
        status=DiagnosticStatus.CALCULATED if statistic is not None else DiagnosticStatus.UNDEFINED,
        statistic=statistic,
        warning_codes=() if statistic is not None else (AnalysisFindingCode.UNDEFINED_STATISTIC,),
        explanation="Durbin-Watson statistic was calculated over preserved source row order.",
    )
