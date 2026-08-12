# Phase 17 UNESCO Education Integration Validation

Education, income, and life expectancy

## Metadata

| Field | Value |
| --- | --- |
| Report ID | report_817f9012ac107c6ace968b402721170e6385ed5cacab22d09e4ae217b9f7d724 |
| Generated | 2026-08-12T20:56:07.782908+00:00 |
| Dataset ID | harmonized_country_year_ecc294e73857a6c7 |
| Source checksum | 856943986a36f32003482bd681e8108fb4d75a4a6cb94b108437c3ff8897630a |
| Analysis procedure | ordinary_least_squares |
| Synthesis mode | deterministic |
| Ruleset | deterministic_phase9_v1 |

## Executive Summary

The coordinated assessment contains 8 referenced evidence records and 5 referenced non-causal claim candidates across economics, education, public_health. Domain coverage is incomplete; governance was not represented. Unsupported inference boundaries remain active, including causal inference. The report preserves observational and non-causal boundaries from upstream artifacts. Domain coverage is incomplete. No external literature or outside contextual evidence has been integrated.

## Research Question

| Field | Value |
| --- | --- |
| Question ID | rq_phase17_education_life_expectancy |
| Primary question | How is educational attainment associated with life expectancy after accounting for GDP per capita? |
| Population | Country-year observations with WDI, WHO, and UNESCO coverage |
| Variables | uis_upper_secondary_attainment_rate_25plus, wdi_gdp_per_capita_current_usd, who_life_expectancy_at_birth_both_sexes |
| Methods | ordinary_least_squares |

## Dataset and Source

| Field | Value |
| --- | --- |
| Dataset ID | harmonized_country_year_ecc294e73857a6c7 |
| Title | Phase 12 Harmonized Country-Year Dataset |
| Provider | Polaris derived harmonization |
| Source type | local_csv |
| Checksum | 856943986a36f32003482bd681e8108fb4d75a4a6cb94b108437c3ff8897630a |
| Accepted rows | 47 |
| Rejected rows | 0 |
| Analysis ready | true |
| Illustrative | false |
| Variables | who_life_expectancy_at_birth_both_sexes, uis_upper_secondary_attainment_rate_25plus, wdi_gdp_per_capita_current_usd |

## Methodology

| Field | Value |
| --- | --- |
| Ingestion and validation | Local CSV ingestion mapped source columns to the supplied manifest, normalized supported scalar values, validated structure, and computed a SHA-256 checksum. |
| Sample construction | Phase 4 used complete-case sample construction from accepted Phase 3 records. |
| Procedure | ordinary_least_squares |
| Dependent variable | who_life_expectancy_at_birth_both_sexes |
| Predictors | uis_upper_secondary_attainment_rate_25plus, wdi_gdp_per_capita_current_usd |
| Controls |  |
| Include intercept | true |
| Confidence level | 0.95 |
| Significance threshold |  |
| Diagnostics calculated | breusch_pagan, condition_number, durbin_watson, maximum_leverage, residual_normality, variance_inflation_factor, variance_inflation_factor |
| Evidence extraction | Phase 5 extracted 13 evidence records and 7 bounded non-causal claim candidates. |
| Domain agents | Phase 6 deterministic domain agents selected relevant structured evidence and claim IDs without adding outside context. |
| Coordination | Phase 7 coordinated 3 domain assessments by reference. |
| Synthesis mode | deterministic |
| Grounding and validation | Phase 8 synthesis supplied validated summaries with fabricated-reference, limitation-preservation, unsupported-inference, and overreach checks. |

## Statistical Results

| Field | Value |
| --- | --- |
| Analysis result ID | analysis_388268c430e305262d65bc4a05245fd1cb14e3deb94bf3fdcfe2ca63e3113244 |
| Method | ordinary_least_squares |
| Sample size | 28 |

| Term | Estimate | Std. Error | Statistic | p-value | CI Low | CI High |
| --- | --- | --- | --- | --- | --- | --- |
| intercept | 55.98854627141213 | 1.284837307536134 | 43.57637028673963 | 4.199772149562e-25 | 53.34237430252572 | 58.63471824029855 |
| uis_upper_secondary_attainment_rate_25plus | 0.4723094210928428 | 0.03944665374097815 | 11.97337102899038 | 7.533216659491984e-12 | 0.3910675169361882 | 0.5535513252494974 |
| wdi_gdp_per_capita_current_usd | -0.0003226002425154611 | 4.3336228398277375e-05 | -7.44412364524746 | 8.511870007385282e-08 | -0.0004118528756326356 | -0.00023334760939828654 |

| Metric | Value |
| --- | --- |
| R-squared | 0.9043465392570749 |
| Adjusted R-squared | 0.8966942623976408 |
| Residual degrees of freedom | 25.0 |
| Model degrees of freedom | 2.0 |
| RSS | 130.46789469297724 |
| MSE | 5.2187157877190895 |

## Evidence and Claims

| Evidence ID | Type | Variables | Direction | Limitations |
| --- | --- | --- | --- | --- |
| evidence_165e2def7695778b77e1715fdc8ec3c0be2152583560166a6f6cbdf6f35ae32d | regression_coefficient | uis_upper_secondary_attainment_rate_25plus, wdi_gdp_per_capita_current_usd, who_life_expectancy_at_birth_both_sexes | negative |  |
| evidence_42e1b91ff842d63e35d778fb839a687330e80ac85b791d5f60c1b074d62ebd3e | model_diagnostic | uis_upper_secondary_attainment_rate_25plus |  |  |
| evidence_53e58e72df1bbba803898bba137f1026df06210d4cf051ddf936832bb2df1900 | model_diagnostic |  |  |  |
| evidence_680a35fa4137cd51d7aeaa6b854fa894c3a14c51c03147f2288076203cfc58e7 | sample_quality | uis_upper_secondary_attainment_rate_25plus, wdi_gdp_per_capita_current_usd, who_life_expectancy_at_birth_both_sexes |  | MISSING_DATA_EXCLUSION |
| evidence_6839b9ef7f97da41c44328fdb2f71601448f69d4ae6aedb7be9f142d5d24bfad | model_diagnostic |  |  | HETEROSKEDASTICITY_WARNING |
| evidence_6eb2d10488d66909bc2c0dcda5a69fd879de8f0bc90348cc6506becf7131c86e | regression_coefficient | uis_upper_secondary_attainment_rate_25plus, wdi_gdp_per_capita_current_usd, who_life_expectancy_at_birth_both_sexes | positive |  |
| evidence_7f051c96a00eead56a8e088965889ed37f260396b78f93b6b63f9e94ee177dca | model_diagnostic |  |  |  |
| evidence_bdedb81bcc4c0ef72be7317aab2cf776f7da6b61a40278269ed335665afb2272 | model_diagnostic |  |  |  |
| evidence_c9eac838d8b59070d3866a9e98d6b8955af8eb38d793c42b1d206906db480dab | regression_coefficient | uis_upper_secondary_attainment_rate_25plus, wdi_gdp_per_capita_current_usd, who_life_expectancy_at_birth_both_sexes | positive |  |
| evidence_d44a62f58239a3798b8abf8c78bb0e90a49f2a7f3819706bd0b675739d47166c | model_fit | uis_upper_secondary_attainment_rate_25plus, wdi_gdp_per_capita_current_usd, who_life_expectancy_at_birth_both_sexes |  |  |
| evidence_dd48f5953b2461cdd56bdacda0d31f27ee0527a6e44857f1ce3917c20acf2447 | model_diagnostic | wdi_gdp_per_capita_current_usd |  |  |
| evidence_f1a2caefa99f731cfd8b98eb68c6da009105c630e9f044865d4f0d90ec823101 | model_diagnostic |  |  | RESIDUAL_NORMALITY_WARNING |
| evidence_fc3e262e7e92d6c717d11b9e0b82e287073beaeafb03057aa2563746e01d890d | analysis_warning | uis_upper_secondary_attainment_rate_25plus, wdi_gdp_per_capita_current_usd, who_life_expectancy_at_birth_both_sexes |  | MISSING_DATA_EXCLUSION |

| Claim ID | Type | Evidence IDs | Direction | Causal | Scope |
| --- | --- | --- | --- | --- | --- |
| claim_0d9717cff055eb0042aa768c5a5768ae41cb6ed5284a3c498476a2c520968ab5 | model_limitation | evidence_f1a2caefa99f731cfd8b98eb68c6da009105c630e9f044865d4f0d90ec823101 | not_applicable | false | analysis_sample |
| claim_148ef160195125144739cd95654889c633bb68a454d263840d0f00640cf105c7 | conditional_association | evidence_6eb2d10488d66909bc2c0dcda5a69fd879de8f0bc90348cc6506becf7131c86e | positive | false | analysis_sample |
| claim_20432d5c0befabecb9783525ea755a39d01e61fdf25be7e501cac4e43470a175 | statistical_uncertainty | evidence_c9eac838d8b59070d3866a9e98d6b8955af8eb38d793c42b1d206906db480dab | not_applicable | false | analysis_sample |
| claim_6dd235001ad7b301aacf9f1bb4653f2c4b3322c111642f4c7f8e2d4999b4c095 | conditional_association | evidence_165e2def7695778b77e1715fdc8ec3c0be2152583560166a6f6cbdf6f35ae32d | negative | false | analysis_sample |
| claim_7540edc2d83549a64f491d3e1d7f80fd63a1e3ec14bdaa3975c1b04c882959a9 | model_limitation | evidence_6839b9ef7f97da41c44328fdb2f71601448f69d4ae6aedb7be9f142d5d24bfad | not_applicable | false | analysis_sample |
| claim_7b25fdfa47e9842c97dcf1b8a05303026c2b444fcd814a4333b19e2b8602776d | statistical_uncertainty | evidence_6eb2d10488d66909bc2c0dcda5a69fd879de8f0bc90348cc6506becf7131c86e | not_applicable | false | analysis_sample |
| claim_fd58deaf7bff03ff835f4563cc1cee6ba93a0031914c69b3cbdf2b691a29c317 | statistical_uncertainty | evidence_165e2def7695778b77e1715fdc8ec3c0be2152583560166a6f6cbdf6f35ae32d | not_applicable | false | analysis_sample |

## Domain Assessments

| Domain | Supplied | Coverage | Evidence | Claims | Unsupported |
| --- | --- | --- | --- | --- | --- |
| governance | false | assessment_missing | 0 | 0 |  |
| economics | true | relevant_evidence | 7 | 5 | causality, intervention_recommendation, mechanism, policy_effectiveness, population_wide_generalization, temporal_prediction |
| education | true | relevant_evidence | 7 | 5 | causality, intervention_recommendation, mechanism, policy_effectiveness, population_wide_generalization, temporal_prediction |
| public_health | true | relevant_evidence | 6 | 5 | causality, intervention_recommendation, mechanism, medical_conclusion, policy_effectiveness, population_wide_generalization, temporal_prediction |

## Cross-Domain Synthesis

The coordinated assessment contains 8 referenced evidence records and 5 referenced non-causal claim candidates across economics, education, public_health. Domain coverage is incomplete; governance was not represented. Unsupported inference boundaries remain active, including causal inference.

| Finding ID | Domains | Claim IDs | Evidence IDs |
| --- | --- | --- | --- |
| cross_synthesis_21040b4598d0312bcf9ab9653f7ae7d5234edac4c226f364d7729f8529a60d17 | economics, education, public_health | claim_fd58deaf7bff03ff835f4563cc1cee6ba93a0031914c69b3cbdf2b691a29c317 |  |
| cross_synthesis_2ef73445e9747e8ed45fd2a10319a9fb10eea15964cb2eb8d286c32207d874fc | economics, education, public_health | claim_6dd235001ad7b301aacf9f1bb4653f2c4b3322c111642f4c7f8e2d4999b4c095 |  |
| cross_synthesis_6d5c212689cb3d676295e52d2977610037426081ecfd0145fdd27cb6463b7d3b | economics, education, public_health |  | evidence_680a35fa4137cd51d7aeaa6b854fa894c3a14c51c03147f2288076203cfc58e7 |
| cross_synthesis_72d7a5c1bee5a460bf32ab7619e4f9cf05ea5a449f15044db040dbfa4333333c | economics, education, public_health |  | evidence_165e2def7695778b77e1715fdc8ec3c0be2152583560166a6f6cbdf6f35ae32d |
| cross_synthesis_8924e866412367ce17c7c6f7dd5b7c9ea80c3ac781b93ef256bb13b9e9df4bb2 | economics, education, public_health | claim_20432d5c0befabecb9783525ea755a39d01e61fdf25be7e501cac4e43470a175 |  |
| cross_synthesis_8978df852bb59eec143f3ee1864142477fed1a22dcaacec69b733cdd1110fc25 | economics, education, public_health |  | evidence_6eb2d10488d66909bc2c0dcda5a69fd879de8f0bc90348cc6506becf7131c86e |
| cross_synthesis_bc949c2e301be01931a924fda56be2a8966612831ff3c37c0b836e781a0cf359 | economics, education, public_health |  | evidence_c9eac838d8b59070d3866a9e98d6b8955af8eb38d793c42b1d206906db480dab |
| cross_synthesis_c7373e0292e4402b73d1bafdff42f18a56fa327c56f7206d8b32f3959c6632bb | economics, education, public_health |  | evidence_fc3e262e7e92d6c717d11b9e0b82e287073beaeafb03057aa2563746e01d890d |
| cross_synthesis_dcd4f69e991af0a92bc1b50b861feabf6200161f09c101fa86fad6eedc8fa7ed | economics, education, public_health | claim_7b25fdfa47e9842c97dcf1b8a05303026c2b444fcd814a4333b19e2b8602776d |  |
| cross_synthesis_eba4700519b52f7604284821cd640b50ce9ce0772826e1d16246a1afb846a68c | economics, education, public_health | claim_148ef160195125144739cd95654889c633bb68a454d263840d0f00640cf105c7 |  |
| cross_synthesis_ecc114a0d47c747393b9b7b10dfe61435421a2a22157da4f6c21b5d3f1cd4eb8 | economics, education, public_health |  | evidence_d44a62f58239a3798b8abf8c78bb0e90a49f2a7f3819706bd0b675739d47166c |

## Phase 8 Synthesis

The coordinated assessment contains 8 referenced evidence records and 5 referenced non-causal claim candidates across economics, education, public_health. Domain coverage is incomplete; governance was not represented. Unsupported inference boundaries remain active, including causal inference.

| Domain | Summary | Claims | Evidence |
| --- | --- | --- | --- |
| governance | governance was not supplied and should not be described as producing substantive evidence in this synthesis. |  |  |
| economics | economics selected 7 evidence references and 5 claim references from the coordinated assessment. These references support cautious association-oriented synthesis only. | claim_148ef160195125144739cd95654889c633bb68a454d263840d0f00640cf105c7, claim_20432d5c0befabecb9783525ea755a39d01e61fdf25be7e501cac4e43470a175, claim_6dd235001ad7b301aacf9f1bb4653f2c4b3322c111642f4c7f8e2d4999b4c095, claim_7b25fdfa47e9842c97dcf1b8a05303026c2b444fcd814a4333b19e2b8602776d, claim_fd58deaf7bff03ff835f4563cc1cee6ba93a0031914c69b3cbdf2b691a29c317 | evidence_165e2def7695778b77e1715fdc8ec3c0be2152583560166a6f6cbdf6f35ae32d, evidence_680a35fa4137cd51d7aeaa6b854fa894c3a14c51c03147f2288076203cfc58e7, evidence_6eb2d10488d66909bc2c0dcda5a69fd879de8f0bc90348cc6506becf7131c86e, evidence_c9eac838d8b59070d3866a9e98d6b8955af8eb38d793c42b1d206906db480dab, evidence_d44a62f58239a3798b8abf8c78bb0e90a49f2a7f3819706bd0b675739d47166c, evidence_dd48f5953b2461cdd56bdacda0d31f27ee0527a6e44857f1ce3917c20acf2447, evidence_fc3e262e7e92d6c717d11b9e0b82e287073beaeafb03057aa2563746e01d890d |
| education | education selected 7 evidence references and 5 claim references from the coordinated assessment. These references support cautious association-oriented synthesis only. | claim_148ef160195125144739cd95654889c633bb68a454d263840d0f00640cf105c7, claim_20432d5c0befabecb9783525ea755a39d01e61fdf25be7e501cac4e43470a175, claim_6dd235001ad7b301aacf9f1bb4653f2c4b3322c111642f4c7f8e2d4999b4c095, claim_7b25fdfa47e9842c97dcf1b8a05303026c2b444fcd814a4333b19e2b8602776d, claim_fd58deaf7bff03ff835f4563cc1cee6ba93a0031914c69b3cbdf2b691a29c317 | evidence_165e2def7695778b77e1715fdc8ec3c0be2152583560166a6f6cbdf6f35ae32d, evidence_42e1b91ff842d63e35d778fb839a687330e80ac85b791d5f60c1b074d62ebd3e, evidence_680a35fa4137cd51d7aeaa6b854fa894c3a14c51c03147f2288076203cfc58e7, evidence_6eb2d10488d66909bc2c0dcda5a69fd879de8f0bc90348cc6506becf7131c86e, evidence_c9eac838d8b59070d3866a9e98d6b8955af8eb38d793c42b1d206906db480dab, evidence_d44a62f58239a3798b8abf8c78bb0e90a49f2a7f3819706bd0b675739d47166c, evidence_fc3e262e7e92d6c717d11b9e0b82e287073beaeafb03057aa2563746e01d890d |
| public_health | public_health selected 6 evidence references and 5 claim references from the coordinated assessment. These references support cautious association-oriented synthesis only. | claim_148ef160195125144739cd95654889c633bb68a454d263840d0f00640cf105c7, claim_20432d5c0befabecb9783525ea755a39d01e61fdf25be7e501cac4e43470a175, claim_6dd235001ad7b301aacf9f1bb4653f2c4b3322c111642f4c7f8e2d4999b4c095, claim_7b25fdfa47e9842c97dcf1b8a05303026c2b444fcd814a4333b19e2b8602776d, claim_fd58deaf7bff03ff835f4563cc1cee6ba93a0031914c69b3cbdf2b691a29c317 | evidence_165e2def7695778b77e1715fdc8ec3c0be2152583560166a6f6cbdf6f35ae32d, evidence_680a35fa4137cd51d7aeaa6b854fa894c3a14c51c03147f2288076203cfc58e7, evidence_6eb2d10488d66909bc2c0dcda5a69fd879de8f0bc90348cc6506becf7131c86e, evidence_c9eac838d8b59070d3866a9e98d6b8955af8eb38d793c42b1d206906db480dab, evidence_d44a62f58239a3798b8abf8c78bb0e90a49f2a7f3819706bd0b675739d47166c, evidence_fc3e262e7e92d6c717d11b9e0b82e287073beaeafb03057aa2563746e01d890d |

## Limitations

The report preserves upstream limitation codes and keeps interpretation bounded to structured, non-causal Polaris artifacts.

| Limitation Code |
| --- |
| HETEROSKEDASTICITY_WARNING |
| LIMITED_MODEL_SCOPE |
| MISSING_DATA_EXCLUSION |
| OBSERVATIONAL_ASSOCIATION |
| RESIDUAL_NORMALITY_WARNING |
| UNSUPPORTED_GENERALIZATION |

## Evidence and Domain Gaps

| Gap ID | Type | Sources | Domains |
| --- | --- | --- | --- |
| coordination_evidence_gap_4b18886ee661cd185773f1cf7b575f9e6ac1c89f5d789f7f8cf745a0e9839cf5 | cross_domain_claim_with_limited_domain_coverage | claim_20432d5c0befabecb9783525ea755a39d01e61fdf25be7e501cac4e43470a175 | economics, education, public_health |
| coordination_evidence_gap_b2753f8d62c13f2c80c84e56739a91f0186ad2c6c84a9bed11a039d483661fcd | cross_domain_claim_with_limited_domain_coverage | claim_148ef160195125144739cd95654889c633bb68a454d263840d0f00640cf105c7 | economics, education, public_health |
| coordination_evidence_gap_bd2c86d306f7d7dcc748d580dffd00f5da88f61086b2f682df396a46b97bef99 | cross_domain_claim_with_limited_domain_coverage | claim_7b25fdfa47e9842c97dcf1b8a05303026c2b444fcd814a4333b19e2b8602776d | economics, education, public_health |
| coordination_evidence_gap_c02f297430ec936a318a2f5be723abff5865b117046c3eb9db08f8232b41de34 | cross_domain_claim_with_limited_domain_coverage | claim_fd58deaf7bff03ff835f4563cc1cee6ba93a0031914c69b3cbdf2b691a29c317 | economics, education, public_health |
| coordination_evidence_gap_e39c91a474a96acc68488eefb01920ab95b5c169e7855a67e2cb5d034bcdf8b4 | cross_domain_claim_with_limited_domain_coverage | claim_6dd235001ad7b301aacf9f1bb4653f2c4b3322c111642f4c7f8e2d4999b4c095 | economics, education, public_health |
| coordination_evidence_gap_19a9d0b97152ccd5dd5df303fc2d4fe3aa797548345d8ce68c2cea8a39a97497 | evidence_referenced_without_cross_domain_context | evidence_42e1b91ff842d63e35d778fb839a687330e80ac85b791d5f60c1b074d62ebd3e | education |
| coordination_evidence_gap_abff83d41382477943f0f220924f58fdaf6b32a6f3a56359f567e6d458d2452b | evidence_referenced_without_cross_domain_context | evidence_dd48f5953b2461cdd56bdacda0d31f27ee0527a6e44857f1ce3917c20acf2447 | economics |

| Gap ID | Type | Domain | Assessment supplied |
| --- | --- | --- | --- |
| coordination_domain_gap_2cda4ca8f7436f9f2c37185bda78a91223f6045f01a8d2a1090a39c37ae6b12f | domain_not_represented | governance | false |

## Unsupported Inferences

| Boundary |
| --- |
| causality |
| intervention_recommendation |
| mechanism |
| medical_conclusion |
| policy_effectiveness |
| population_wide_generalization |
| temporal_prediction |

## Provenance

| Stage | Identifier |
| --- | --- |
| Source dataset | harmonized_country_year_ecc294e73857a6c7 |
| Phase 3 DatasetIngestionResult | harmonized_country_year_ecc294e73857a6c7 |
| Phase 4 AnalysisResult | analysis_388268c430e305262d65bc4a05245fd1cb14e3deb94bf3fdcfe2ca63e3113244 |
| Phase 5 EvidenceArtifact | evidence_artifact_d4eb237f7dfb3aa0cd82c000487a444351b0f8891e22f612cdc4f2e9f4797b5b |
| Phase 6 AgentAssessments | agent_assessment_897a055e2611441fa6c9a63e223f0c29082b9a29986d83b29ca3fc5f239bc9ea, agent_assessment_d953dffc299e6ba200b86ee5d7c40459cdf96d7c6444c2a9d2501abfe19af061, agent_assessment_ff0851e918fcee335c80afa4ce235efae87ce21488f113c3986f7881def94908 |
| Phase 7 CoordinatedAssessment | coordinated_assessment_6b59e9b13423866d62bd88c26c0d2253028d256bc1b37bff4c3eebf92b4eb9c1 |
| Phase 8 SynthesisArtifact | synthesis_dfc3ba73ac340cc4e9c6faf63c345380d26f0e3e508a559ff0e363d7274dc41e |
| Phase 9 ResearchReport | report_817f9012ac107c6ace968b402721170e6385ed5cacab22d09e4ae217b9f7d724 |

## Reference Index

| Reference ID | Kind | Label |
| --- | --- | --- |
| coordination_agreement_018593e787c8c4bdfe2dd6416a3532cf965b40d1db6e817531663437136ee767 | agreement | Coordination agreement: shared_evidence |
| coordination_agreement_05c364c2c9cf66ee2920ddabee28303e8c061ae3972524cda172adc13765c6f6 | agreement | Coordination agreement: shared_domain_concern |
| coordination_agreement_0d5c20c6a2eb647677bff281af55401291b4352a2d1e74f54003feff9008ab4d | agreement | Coordination agreement: shared_unsupported_inference |
| coordination_agreement_22dc7d566e8d11a73d0fce14bc1228a2a88370d49098dcc57923d8cfff98f89a | agreement | Coordination agreement: shared_evidence |
| coordination_agreement_359c6727206115977f1279b72b464be28a77b96717dd7d84886e98f6aeff448c | agreement | Coordination agreement: shared_unsupported_inference |
| coordination_agreement_35cd623384250d1403210fc1b7b26d751c46c00fc809420d8e4ff3fb8d982139 | agreement | Coordination agreement: shared_unsupported_inference |
| coordination_agreement_3e8e75a904e5768d2aca517d87d40574c018aa1736329742e1d05a27c0afae29 | agreement | Coordination agreement: shared_domain_concern |
| coordination_agreement_53af29fe6454d0a88f8e51d541915d007a0abe12b57aeca8101aa53f577a1afa | agreement | Coordination agreement: shared_limitation |
| coordination_agreement_59a0010622d478a874d7f8503066153e84cbb9b54573ea5f0b14746f06c2e745 | agreement | Coordination agreement: shared_domain_concern |
| coordination_agreement_6b90f2364e2d3d47936aac5f536d9c2ee9254f2dd1707ddc6395c4c33f5db7e4 | agreement | Coordination agreement: shared_evidence |
| coordination_agreement_6e79d70adcdf8277865c1ec36b41f59435b17110c81f5176bb9829db34b96591 | agreement | Coordination agreement: shared_domain_concern |
| coordination_agreement_7407c0283310965caa9ee65375e053537bf449647b1a72c5e0d544f9457cd53d | agreement | Coordination agreement: shared_claim |
| coordination_agreement_790f5a12043ef2ffb2e7b549390e57679e90ad29ac60d227c88d63c4c0ca1ad4 | agreement | Coordination agreement: shared_domain_concern |
| coordination_agreement_7b74ed99c9d49794fd083e3ba9d6f03c98a5b34f56185c35e46cf5d135586af9 | agreement | Coordination agreement: shared_limitation |
| coordination_agreement_839e36dbd031b826ca00add9e392d21354875b462af14a8218506705d382a4bf | agreement | Coordination agreement: shared_unsupported_inference |
| coordination_agreement_8c336b92839ad9197f1273439f2b541a9e97e961b3c90ab31b78de44b2e5507b | agreement | Coordination agreement: shared_claim |
| coordination_agreement_8f81e2855a3ab110059911fe530d80b4aa711ba5f10d8be0a722e112b3d4e628 | agreement | Coordination agreement: shared_domain_concern |
| coordination_agreement_96a905ff61ca5303fdb1daf0f09b35a278228554d71e998b067461eef48394f2 | agreement | Coordination agreement: shared_evidence |
| coordination_agreement_9bef5c426f7b40d6565aced8f60d1bccc247d61189a50057f3b39d5a52ec2326 | agreement | Coordination agreement: shared_limitation |
| coordination_agreement_aaeb5839d3f196f528aea51833dbdb51718492377b5d08c48ebe7055cacc66e2 | agreement | Coordination agreement: shared_limitation |
| coordination_agreement_ab181f563aadd6e36e8559b4d4af0fc94ab35c4283a3ba1477f1af33f216d3d9 | agreement | Coordination agreement: shared_unsupported_inference |
| coordination_agreement_b9a933fbf97f6a42295ba409709c925f9c5cc99ff4294500b6f46edb10f4e702 | agreement | Coordination agreement: shared_evidence |
| coordination_agreement_c0311635e0ed6b098bdc7443d27d934ac9d85a2a52577032e1263929b7f1bf0c | agreement | Coordination agreement: shared_limitation |
| coordination_agreement_c04c2421e3ab85bb9d676df878b322d20929e2fcefb3c3bd28323ab4d59b033f | agreement | Coordination agreement: shared_unsupported_inference |
| coordination_agreement_c2c57cd813d5ce38678bca06f7083ebee3d5bda2c16fdce239b7bc849111a6e8 | agreement | Coordination agreement: shared_domain_concern |
| coordination_agreement_c5e451d3eda45f7a4ba870d6d52661ec5712602b53c713c8e56497a79aee8ada | agreement | Coordination agreement: shared_domain_concern |
| coordination_agreement_d0cb68ebbad88ba4ad0edae27b27af4eb49b547c63a21521a3775dd0730ef582 | agreement | Coordination agreement: shared_evidence |
| coordination_agreement_da543afec5dc25bd2ba8da6ce015a08615ee080b34805ef630ce44f669d95043 | agreement | Coordination agreement: shared_claim |
| coordination_agreement_dbf4deb7287b20554ee0d2bbf3e1c722a5a0b11c71a258a999edded4758bb925 | agreement | Coordination agreement: shared_domain_concern |
| coordination_agreement_dd19a9e85fa37361ea26ce0c8f3b2d7d92e762a411951751dc56272effeaa100 | agreement | Coordination agreement: shared_claim |
| coordination_agreement_de25ab5e0606c4a3005b19a01e53e0e7a4836705bffa27494b408cded997789d | agreement | Coordination agreement: shared_claim |
| coordination_agreement_e43130726f00e83bff182618642e064ab722b19c98d421a171cabe732f29b593 | agreement | Coordination agreement: shared_limitation |
| coordination_agreement_fd3cf8887ff29b4b991344879c2c275d97f06664887844b85c58ff6f81326e17 | agreement | Coordination agreement: shared_domain_concern |
| agent_assessment_897a055e2611441fa6c9a63e223f0c29082b9a29986d83b29ca3fc5f239bc9ea | assessment | Domain assessment: economics |
| agent_assessment_d953dffc299e6ba200b86ee5d7c40459cdf96d7c6444c2a9d2501abfe19af061 | assessment | Domain assessment: education |
| agent_assessment_ff0851e918fcee335c80afa4ce235efae87ce21488f113c3986f7881def94908 | assessment | Domain assessment: public_health |
| claim_0d9717cff055eb0042aa768c5a5768ae41cb6ed5284a3c498476a2c520968ab5 | claim | Claim candidate: model_limitation |
| claim_148ef160195125144739cd95654889c633bb68a454d263840d0f00640cf105c7 | claim | Claim candidate: conditional_association |
| claim_20432d5c0befabecb9783525ea755a39d01e61fdf25be7e501cac4e43470a175 | claim | Claim candidate: statistical_uncertainty |
| claim_6dd235001ad7b301aacf9f1bb4653f2c4b3322c111642f4c7f8e2d4999b4c095 | claim | Claim candidate: conditional_association |
| claim_7540edc2d83549a64f491d3e1d7f80fd63a1e3ec14bdaa3975c1b04c882959a9 | claim | Claim candidate: model_limitation |
| claim_7b25fdfa47e9842c97dcf1b8a05303026c2b444fcd814a4333b19e2b8602776d | claim | Claim candidate: statistical_uncertainty |
| claim_fd58deaf7bff03ff835f4563cc1cee6ba93a0031914c69b3cbdf2b691a29c317 | claim | Claim candidate: statistical_uncertainty |
| coordination_divergence_448da3df20443bcaba1cd60dd1dd5213a4b522b49cf24533b6db690349d14bcd | divergence | Coordination divergence: uneven_evidence_coverage |
| coordination_divergence_5f3b8f69c2465b9497e517801aab17fe9d5736953c5082aadb23018dafdf8a6f | divergence | Coordination divergence: domain_specific_unsupported_inference |
| coordination_divergence_aed6d53e89a4128e32316f7ed0b4acc179929a8cbf9500ad3a6695f92ea49ac6 | divergence | Coordination divergence: uneven_evidence_coverage |
| coordination_divergence_e60fd597b396df074e81a292803393b81b29c12a98c2de0e507b044e49889b6c | divergence | Coordination divergence: different_relevance_classification |
| coordination_divergence_ecb46b8c4c62e83746489af4e7ce2b613fcabf568daf103e053cf42319b1932e | divergence | Coordination divergence: different_relevance_classification |
| evidence_165e2def7695778b77e1715fdc8ec3c0be2152583560166a6f6cbdf6f35ae32d | evidence | Evidence record: regression_coefficient |
| evidence_42e1b91ff842d63e35d778fb839a687330e80ac85b791d5f60c1b074d62ebd3e | evidence | Evidence record: model_diagnostic |
| evidence_53e58e72df1bbba803898bba137f1026df06210d4cf051ddf936832bb2df1900 | evidence | Evidence record: model_diagnostic |
| evidence_680a35fa4137cd51d7aeaa6b854fa894c3a14c51c03147f2288076203cfc58e7 | evidence | Evidence record: sample_quality |
| evidence_6839b9ef7f97da41c44328fdb2f71601448f69d4ae6aedb7be9f142d5d24bfad | evidence | Evidence record: model_diagnostic |
| evidence_6eb2d10488d66909bc2c0dcda5a69fd879de8f0bc90348cc6506becf7131c86e | evidence | Evidence record: regression_coefficient |
| evidence_7f051c96a00eead56a8e088965889ed37f260396b78f93b6b63f9e94ee177dca | evidence | Evidence record: model_diagnostic |
| evidence_bdedb81bcc4c0ef72be7317aab2cf776f7da6b61a40278269ed335665afb2272 | evidence | Evidence record: model_diagnostic |
| evidence_c9eac838d8b59070d3866a9e98d6b8955af8eb38d793c42b1d206906db480dab | evidence | Evidence record: regression_coefficient |
| evidence_d44a62f58239a3798b8abf8c78bb0e90a49f2a7f3819706bd0b675739d47166c | evidence | Evidence record: model_fit |
| evidence_dd48f5953b2461cdd56bdacda0d31f27ee0527a6e44857f1ce3917c20acf2447 | evidence | Evidence record: model_diagnostic |
| evidence_f1a2caefa99f731cfd8b98eb68c6da009105c630e9f044865d4f0d90ec823101 | evidence | Evidence record: model_diagnostic |
| evidence_fc3e262e7e92d6c717d11b9e0b82e287073beaeafb03057aa2563746e01d890d | evidence | Evidence record: analysis_warning |
| coordination_domain_gap_2cda4ca8f7436f9f2c37185bda78a91223f6045f01a8d2a1090a39c37ae6b12f | gap | Domain gap: governance |
| coordination_evidence_gap_19a9d0b97152ccd5dd5df303fc2d4fe3aa797548345d8ce68c2cea8a39a97497 | gap | Evidence gap: evidence_referenced_without_cross_domain_context |
| coordination_evidence_gap_4b18886ee661cd185773f1cf7b575f9e6ac1c89f5d789f7f8cf745a0e9839cf5 | gap | Evidence gap: cross_domain_claim_with_limited_domain_coverage |
| coordination_evidence_gap_abff83d41382477943f0f220924f58fdaf6b32a6f3a56359f567e6d458d2452b | gap | Evidence gap: evidence_referenced_without_cross_domain_context |
| coordination_evidence_gap_b2753f8d62c13f2c80c84e56739a91f0186ad2c6c84a9bed11a039d483661fcd | gap | Evidence gap: cross_domain_claim_with_limited_domain_coverage |
| coordination_evidence_gap_bd2c86d306f7d7dcc748d580dffd00f5da88f61086b2f682df396a46b97bef99 | gap | Evidence gap: cross_domain_claim_with_limited_domain_coverage |
| coordination_evidence_gap_c02f297430ec936a318a2f5be723abff5865b117046c3eb9db08f8232b41de34 | gap | Evidence gap: cross_domain_claim_with_limited_domain_coverage |
| coordination_evidence_gap_e39c91a474a96acc68488eefb01920ab95b5c169e7855a67e2cb5d034bcdf8b4 | gap | Evidence gap: cross_domain_claim_with_limited_domain_coverage |
| analysis_388268c430e305262d65bc4a05245fd1cb14e3deb94bf3fdcfe2ca63e3113244 | source_artifact | Source Polaris artifact |
| coordinated_assessment_6b59e9b13423866d62bd88c26c0d2253028d256bc1b37bff4c3eebf92b4eb9c1 | source_artifact | Source Polaris artifact |
| evidence_artifact_d4eb237f7dfb3aa0cd82c000487a444351b0f8891e22f612cdc4f2e9f4797b5b | source_artifact | Source Polaris artifact |
| harmonized_country_year_ecc294e73857a6c7 | source_artifact | Source Polaris artifact |
| synthesis_dfc3ba73ac340cc4e9c6faf63c345380d26f0e3e508a559ff0e363d7274dc41e | source_artifact | Source Polaris artifact |
