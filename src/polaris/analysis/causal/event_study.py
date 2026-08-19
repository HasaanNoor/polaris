"""Event-study construction and estimation."""

from polaris.analysis.causal.errors import InvalidReferencePeriodError
from polaris.analysis.causal.models import (
    CausalEstimator,
    CausalSpecification,
    EventStudyCoefficient,
    TreatmentEffectEstimate,
)
from polaris.analysis.causal.treatment import TreatmentPanel
from polaris.analysis.models import AnalysisSample, PanelRegressionResult, RegressionCoefficient
from polaris.analysis.panel_models import fit_panel_design_matrix
from polaris.schemas.common import StatisticalProcedure


def estimate_event_study(
    panel: TreatmentPanel,
    specification: CausalSpecification,
    *,
    confidence_level: float,
    significance_threshold: float | None,
) -> tuple[TreatmentEffectEstimate, PanelRegressionResult, tuple[EventStudyCoefficient, ...], int]:
    config = specification.event_study
    if config is None:
        raise InvalidReferencePeriodError("event-study config is required")
    if config.reference_event_time >= 0:
        raise InvalidReferencePeriodError("event-study reference period must be pre-treatment")
    entity_id = specification.entity_variable.variable_id
    time_id = specification.time_variable.variable_id
    outcome_id = specification.outcome_variable.variable_id
    treated = set(panel.treated_entities)
    event_times = tuple(
        time
        for time in range(config.min_event_time, config.max_event_time + 1)
        if time != config.reference_event_time
    )
    model_rows = []
    excluded = 0
    for row in panel.rows:
        event_time = int(float(row[time_id]) - panel.treatment_start_period)
        if not config.min_event_time <= event_time <= config.max_event_time:
            excluded += 1
            continue
        model_row = dict(row)
        is_treated = str(row[entity_id]) in treated
        for value in event_times:
            model_row[_event_term(value)] = 1.0 if is_treated and event_time == value else 0.0
        model_rows.append(model_row)
    predictor_ids = (
        *(_event_term(value) for value in event_times),
        *(item.variable_id for item in specification.covariates),
    )
    sample = AnalysisSample(
        variable_ids=(outcome_id, *predictor_ids, entity_id, time_id),
        rows=tuple(model_rows),
        included_row_numbers=tuple(int(row["_source_row_number"]) for row in model_rows),
        included_source_line_numbers=(),
        exclusions=(),
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
    coefficients = {item.term: item for item in regression.coefficients}
    event_results = [
        EventStudyCoefficient(
            event_time=config.reference_event_time,
            coefficient=None,
            standard_error=None,
            confidence_interval_low=None,
            confidence_interval_high=None,
            p_value=None,
            observation_count=sum(
                1
                for row in model_rows
                if int(float(row[time_id]) - panel.treatment_start_period)
                == config.reference_event_time
            ),
            treated_entity_count=_treated_count(
                model_rows,
                entity_id,
                time_id,
                treated,
                panel.treatment_start_period,
                config.reference_event_time,
            ),
            reference_period=True,
            pre_post_status="reference",
        )
    ]
    for value in event_times:
        coefficient = coefficients[_event_term(value)]
        event_results.append(
            EventStudyCoefficient(
                event_time=value,
                coefficient=coefficient.estimate,
                standard_error=coefficient.standard_error,
                confidence_interval_low=coefficient.confidence_interval_low,
                confidence_interval_high=coefficient.confidence_interval_high,
                p_value=coefficient.p_value,
                observation_count=sum(
                    1
                    for row in model_rows
                    if int(float(row[time_id]) - panel.treatment_start_period) == value
                ),
                treated_entity_count=_treated_count(
                    model_rows, entity_id, time_id, treated, panel.treatment_start_period, value
                ),
                reference_period=False,
                pre_post_status="pre" if value < 0 else "post",
            )
        )
    ordered = tuple(sorted(event_results, key=lambda item: item.event_time))
    first_post = next((item for item in ordered if item.event_time == 0), None)
    coefficient = _coefficient_for(coefficients.get(_event_term(0)))
    return (
        TreatmentEffectEstimate(
            estimator=CausalEstimator.TWFE_EVENT_STUDY,
            estimand=specification.estimand,
            term=_event_term(0),
            estimate=first_post.coefficient if first_post is not None else None,
            standard_error=first_post.standard_error if first_post is not None else None,
            p_value=first_post.p_value if first_post is not None else None,
            confidence_interval_low=(
                first_post.confidence_interval_low if first_post is not None else None
            ),
            confidence_interval_high=(
                first_post.confidence_interval_high if first_post is not None else None
            ),
            standard_error_type=coefficient.standard_error_type if coefficient else None,
            cluster_count=coefficient.cluster_count if coefficient else None,
            coefficient=coefficient,
        ),
        regression,
        ordered,
        excluded,
    )


def event_study_plot_data(
    results: tuple[EventStudyCoefficient, ...],
) -> tuple[dict[str, object], ...]:
    return tuple(
        {
            "event_time": item.event_time,
            "estimate": item.coefficient,
            "lower_ci": item.confidence_interval_low,
            "upper_ci": item.confidence_interval_high,
            "reference_period": item.reference_period,
            "pre_post_status": item.pre_post_status,
        }
        for item in results
    )


def _event_term(event_time: int) -> str:
    prefix = "event_lead" if event_time < 0 else "event_lag"
    return f"{prefix}_{abs(event_time)}"


def _coefficient_for(value: RegressionCoefficient | None) -> RegressionCoefficient | None:
    return value


def _treated_count(
    rows, entity_id: str, time_id: str, treated: set[str], start: float, event_time: int
) -> int:
    return len(
        {
            str(row[entity_id])
            for row in rows
            if str(row[entity_id]) in treated and int(float(row[time_id]) - start) == event_time
        }
    )
