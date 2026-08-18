# Phase 21 Panel Analysis Example

Question: Within countries over time, how is government effectiveness associated with life expectancy after accounting for GDP per capita and common year effects?

Data: committed derived WDI + WHO + WGI country-year example artifact `harmonized_country_year_610b7b1c05b09044`. Raw provider datasets are not included.

Two-way fixed-effects result: 49 observations across 7 countries and 7 years. The government-effectiveness coefficient is 3.500042, clustered SE 1.067082, p-value 0.0023537201792779407, and confidence interval [1.333750, 5.666334]. Within R-squared is 0.3137303645133567.

Interpretation: higher government effectiveness is associated with higher life expectancy within countries over time under the specified two-way fixed-effects model, conditional on GDP per capita and common year effects. Causality is not established by this fixed-effects result.

Comparison: `pooled_vs_panel_comparison.json` includes pooled OLS, entity fixed effects, and two-way fixed effects. These specifications answer different associational questions and are not ranked as automatically correct.

Education example: {"analysis_result_id": "analysis_9ee9ec704cfe8a5b752d7dc1050966c17a15578e706ec12e2bc40a2b7f0d24d3", "coefficient": {"below_significance_threshold": null, "cluster_count": 7, "confidence_interval_high": 0.3417516825152435, "confidence_interval_low": -0.2516362452204803, "estimate": 0.04505771864738162, "p_value": 0.7546882281712334, "standard_error": 0.14223353925820115, "standard_error_type": "cluster_robust_entity", "term": "uis_upper_secondary_attainment_rate_25plus", "test_statistic": 0.31678687658602717, "variable_id": "uis_upper_secondary_attainment_rate_25plus"}, "implemented": true, "sample": {"balanced": false, "cluster_count": 7, "effective_model_sample": 28, "entity_count": 7, "excluded_rows": 21, "included_rows": 28, "input_rows": 49, "lag_induced_exclusions": 0, "max_observations_per_entity": 7, "min_observations_per_entity": 1, "missing_data_exclusions": 21, "singleton_entity_exclusions": 1, "time_period_count": 7, "year_range": [2015.0, 2021.0]}}
