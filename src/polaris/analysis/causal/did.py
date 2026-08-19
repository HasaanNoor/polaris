"""Difference-in-Differences estimators for simple explicit designs."""

import numpy as np

from polaris.analysis.causal.models import (
    CausalEstimator,
    CausalSpecification,
    DIDComponentMeans,
    TreatmentEffectEstimate,
)
from polaris.analysis.causal.treatment import TreatmentPanel
from polaris.analysis.models import AnalysisSample, PanelRegressionResult
from polaris.analysis.panel_models import fit_panel_design_matrix
from polaris.analysis.utils import safe_float
from polaris.schemas.common import StatisticalProcedure

DID_TERM = "treated_post"


def simple_did(
    panel: TreatmentPanel,
    specification: CausalSpecification,
) -> TreatmentEffectEstimate:
    entity_id = specification.entity_variable.variable_id
    time_id = specification.time_variable.variable_id
    outcome_id = specification.outcome_variable.variable_id
    treated = set(panel.treated_entities)
    pre_start, pre_end = (float(value) for value in specification.pre_treatment_window)
    post_start, post_end = (float(value) for value in specification.post_treatment_window)

    treated_pre = _values(panel.rows, entity_id, time_id, outcome_id, treated, pre_start, pre_end)
    treated_post = _values(
        panel.rows, entity_id, time_id, outcome_id, treated, post_start, post_end
    )
    control_pre = _values(
        panel.rows, entity_id, time_id, outcome_id, set(panel.control_entities), pre_start, pre_end
    )
    control_post = _values(
        panel.rows,
        entity_id,
        time_id,
        outcome_id,
        set(panel.control_entities),
        post_start,
        post_end,
    )
    component = DIDComponentMeans(
        treated_pre_mean=float(np.mean(treated_pre)),
        treated_post_mean=float(np.mean(treated_post)),
        control_pre_mean=float(np.mean(control_pre)),
        control_post_mean=float(np.mean(control_post)),
        treated_difference=float(np.mean(treated_post) - np.mean(treated_pre)),
        control_difference=float(np.mean(control_post) - np.mean(control_pre)),
    )
    return TreatmentEffectEstimate(
        estimator=CausalEstimator.SIMPLE_DID,
        estimand=specification.estimand,
        term="simple_difference_in_differences",
        estimate=safe_float(component.treated_difference - component.control_difference),
        component_means=component,
    )


def regression_did(
    panel: TreatmentPanel,
    specification: CausalSpecification,
    *,
    confidence_level: float,
    significance_threshold: float | None,
) -> tuple[TreatmentEffectEstimate, PanelRegressionResult]:
    entity_id = specification.entity_variable.variable_id
    time_id = specification.time_variable.variable_id
    outcome_id = specification.outcome_variable.variable_id
    treated = set(panel.treated_entities)
    model_rows = []
    for row in panel.rows:
        model_row = dict(row)
        is_treated = str(row[entity_id]) in treated
        post = float(row[time_id]) >= panel.treatment_start_period
        model_row[DID_TERM] = 1.0 if is_treated and post else 0.0
        model_rows.append(model_row)
    predictor_ids = (DID_TERM, *(item.variable_id for item in specification.covariates))
    sample = AnalysisSample(
        variable_ids=(outcome_id, *predictor_ids, entity_id, time_id),
        rows=tuple(model_rows),
        included_row_numbers=panel.sample.included_row_numbers,
        included_source_line_numbers=panel.sample.included_source_line_numbers,
        exclusions=panel.sample.exclusions,
    )
    regression = fit_panel_design_matrix(
        sample,
        dependent_variable_id=outcome_id,
        predictor_variable_ids=predictor_ids,
        entity_variable_id=entity_id,
        time_variable_id=time_id,
        entity_fixed_effects=specification.fixed_effects.entity_fixed_effects,
        time_fixed_effects=specification.fixed_effects.time_fixed_effects,
        standard_error_strategy=specification.standard_error_strategy,
        confidence_level=confidence_level,
        significance_threshold=significance_threshold,
        procedure=StatisticalProcedure.PANEL_TWO_WAY_FE,
    )
    coefficient = next(item for item in regression.coefficients if item.term == DID_TERM)
    return (
        TreatmentEffectEstimate(
            estimator=CausalEstimator.TWFE_DID,
            estimand=specification.estimand,
            term=DID_TERM,
            estimate=coefficient.estimate,
            standard_error=coefficient.standard_error,
            test_statistic=coefficient.test_statistic,
            p_value=coefficient.p_value,
            confidence_interval_low=coefficient.confidence_interval_low,
            confidence_interval_high=coefficient.confidence_interval_high,
            standard_error_type=coefficient.standard_error_type,
            cluster_count=coefficient.cluster_count,
            component_means=simple_did(panel, specification).component_means,
            coefficient=coefficient,
        ),
        regression,
    )


def _values(
    rows,
    entity_id: str,
    time_id: str,
    outcome_id: str,
    entities: set[str],
    start: float,
    end: float,
) -> list[float]:
    return [
        float(row[outcome_id])
        for row in rows
        if str(row[entity_id]) in entities and start <= float(row[time_id]) <= end
    ]
