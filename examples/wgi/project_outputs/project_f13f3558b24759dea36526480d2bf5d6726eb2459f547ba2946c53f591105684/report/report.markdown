# Phase 16 WGI Governance Integration Validation

Government effectiveness, income, and life expectancy

## Metadata

| Field | Value |
| --- | --- |
| Report ID | report_ade8b830b8a164fee65642be4b924f0f05312dc8cfe27987af5e4b61146dab65 |
| Generated | 2026-08-11T14:14:41.371820+00:00 |
| Dataset ID | harmonized_country_year_42b5ab4803e5f84f |
| Source checksum | 3d7be05077afb99ea230a36bdfab395c61d0d70551d98d0d124a72f6a79ccd3a |
| Analysis procedure | ordinary_least_squares |
| Synthesis mode | deterministic |
| Ruleset | deterministic_phase9_v1 |

## Executive Summary

The coordinated assessment contains 7 referenced evidence records and 5 referenced non-causal claim candidates across governance, economics, public_health. Domain coverage is incomplete; education was not represented. Unsupported inference boundaries remain active, including causal inference. The report preserves observational and non-causal boundaries from upstream artifacts. Domain coverage is incomplete. No external literature or outside contextual evidence has been integrated.

## Research Question

| Field | Value |
| --- | --- |
| Question ID | rq_phase16_government_effectiveness_life_expectancy |
| Primary question | How is government effectiveness associated with life expectancy across countries after accounting for GDP per capita? |
| Population | Country-year observations with WDI, WHO, and WGI coverage |
| Variables | wdi_gdp_per_capita_current_usd, wgi_government_effectiveness, who_life_expectancy_at_birth_both_sexes |
| Methods | ordinary_least_squares |

## Dataset and Source

| Field | Value |
| --- | --- |
| Dataset ID | harmonized_country_year_42b5ab4803e5f84f |
| Title | Phase 12 Harmonized Country-Year Dataset |
| Provider | Polaris derived harmonization |
| Source type | local_csv |
| Checksum | 3d7be05077afb99ea230a36bdfab395c61d0d70551d98d0d124a72f6a79ccd3a |
| Accepted rows | 49 |
| Rejected rows | 0 |
| Analysis ready | true |
| Illustrative | false |
| Variables | who_life_expectancy_at_birth_both_sexes, wgi_government_effectiveness, wdi_gdp_per_capita_current_usd |

## Methodology

| Field | Value |
| --- | --- |
| Ingestion and validation | Local CSV ingestion mapped source columns to the supplied manifest, normalized supported scalar values, validated structure, and computed a SHA-256 checksum. |
| Sample construction | Phase 4 used complete-case sample construction from accepted Phase 3 records. |
| Procedure | ordinary_least_squares |
| Dependent variable | who_life_expectancy_at_birth_both_sexes |
| Predictors | wgi_government_effectiveness, wdi_gdp_per_capita_current_usd |
| Controls |  |
| Include intercept | true |
| Confidence level | 0.95 |
| Significance threshold |  |
| Diagnostics calculated | breusch_pagan, condition_number, durbin_watson, maximum_leverage, residual_normality, variance_inflation_factor, variance_inflation_factor |
| Evidence extraction | Phase 5 extracted 12 evidence records and 7 bounded non-causal claim candidates. |
| Domain agents | Phase 6 deterministic domain agents selected relevant structured evidence and claim IDs without adding outside context. |
| Coordination | Phase 7 coordinated 3 domain assessments by reference. |
| Synthesis mode | deterministic |
| Grounding and validation | Phase 8 synthesis supplied validated summaries with fabricated-reference, limitation-preservation, unsupported-inference, and overreach checks. |

## Statistical Results

| Field | Value |
| --- | --- |
| Analysis result ID | analysis_5aa4b2006b248978ba24e16f415f90dc180dee04ed5f5c4bfbdb34178a966015 |
| Method | ordinary_least_squares |
| Sample size | 49 |

| Term | Estimate | Std. Error | Statistic | p-value | CI Low | CI High |
| --- | --- | --- | --- | --- | --- | --- |
| intercept | 71.76870413324404 | 0.5768987056199891 | 124.40434245057753 | 8.320869292285549e-60 | 70.60746726767925 | 72.92994099880883 |
| wgi_government_effectiveness | 7.198102925424446 | 0.6652334852300256 | 10.820415816764656 | 3.1246374968805495e-14 | 5.859057370751095 | 8.537148480097798 |
| wdi_gdp_per_capita_current_usd | -6.058320667313104e-05 | 2.9558375935870078e-05 | -2.04961215746672 | 0.04612884791715917 | -0.00012008113150564988 | -1.085281840612203e-06 |

| Metric | Value |
| --- | --- |
| R-squared | 0.8310924442831842 |
| Adjusted R-squared | 0.8237486375128878 |
| Residual degrees of freedom | 46.0 |
| Model degrees of freedom | 2.0 |
| RSS | 400.18614434459636 |
| MSE | 8.699698790099921 |

## Evidence and Claims

| Evidence ID | Type | Variables | Direction | Limitations |
| --- | --- | --- | --- | --- |
| evidence_019b5204346e69f408c708525cf7050d3445ab19c849b4fd6303b019af74f34f | regression_coefficient | wdi_gdp_per_capita_current_usd, wgi_government_effectiveness, who_life_expectancy_at_birth_both_sexes | positive |  |
| evidence_166ca5969a8cb9ce0d7bcea7daaa07c8af6b9e53f09e382dd2cba131bfa8842a | model_diagnostic |  |  | HETEROSKEDASTICITY_WARNING |
| evidence_2f7f96e6e11068cfc6fabf8d10a86c7535bcadb30cbbc8d98e691f5d577eb530 | model_diagnostic |  |  | RESIDUAL_NORMALITY_WARNING |
| evidence_3b1309e9c1cc49db59c8b83491f1914315485b3fdcd609eaba772b5651bca96e | model_diagnostic |  |  |  |
| evidence_4e70d32adb9f25cd824528d5b5281419189c171da4e83a9f8cc57446d30c48e7 | model_diagnostic | wdi_gdp_per_capita_current_usd |  |  |
| evidence_6a0eb6fcdf3493d68c5098ec6da847b5f8ffe50d10abdf2dd48ab54f9cd2f1b5 | model_diagnostic |  |  |  |
| evidence_85cf41964c544677231a67772d8eb11e2a13521413328dee1dd01e558a616aa8 | model_diagnostic | wgi_government_effectiveness |  |  |
| evidence_8804507fd3d971c4973171eb835c68926e5a17e78144af40d08c261c419fb951 | regression_coefficient | wdi_gdp_per_capita_current_usd, wgi_government_effectiveness, who_life_expectancy_at_birth_both_sexes | positive |  |
| evidence_a46999b0ca81d03e4d7f5db9da62be5590b6db79be7b13ff1ad6f7a3d17964b7 | sample_quality | wdi_gdp_per_capita_current_usd, wgi_government_effectiveness, who_life_expectancy_at_birth_both_sexes |  |  |
| evidence_abb642f960ef6cc12ab29127359e157b26b0c3479d6fabf448639b3c859f9bb3 | model_fit | wdi_gdp_per_capita_current_usd, wgi_government_effectiveness, who_life_expectancy_at_birth_both_sexes |  |  |
| evidence_b8b0b2dfa30ea4d72802fc79ef5b600e5abb50522e220d1ac4e524fcd60abc38 | model_diagnostic |  |  |  |
| evidence_d738f9de9bd25f897be3781fce993a0637c11c20bf03d34ed8b3b62e6cfa836d | regression_coefficient | wdi_gdp_per_capita_current_usd, wgi_government_effectiveness, who_life_expectancy_at_birth_both_sexes | negative |  |

| Claim ID | Type | Evidence IDs | Direction | Causal | Scope |
| --- | --- | --- | --- | --- | --- |
| claim_3b443710aa68a605c571ec069ba493b26fa789003787cba9e30af2beff807c6d | statistical_uncertainty | evidence_019b5204346e69f408c708525cf7050d3445ab19c849b4fd6303b019af74f34f | not_applicable | false | analysis_sample |
| claim_5c8a0328870dfa4b3d44665340666da1d8b6b72b764acfaaf06786bd79614cf2 | model_limitation | evidence_166ca5969a8cb9ce0d7bcea7daaa07c8af6b9e53f09e382dd2cba131bfa8842a | not_applicable | false | analysis_sample |
| claim_6e6169b9deec49d2246e3e15b8a19ea388eb474906aa866fc1fb342751fc3851 | model_limitation | evidence_2f7f96e6e11068cfc6fabf8d10a86c7535bcadb30cbbc8d98e691f5d577eb530 | not_applicable | false | analysis_sample |
| claim_6ea3035a867a5ed3f6c1337000117c49c53b86b9531fd4da5ba2e3761373f051 | statistical_uncertainty | evidence_8804507fd3d971c4973171eb835c68926e5a17e78144af40d08c261c419fb951 | not_applicable | false | analysis_sample |
| claim_aa4ee82a7423108c121a62176ba98d5bb8977b29ecf4526bab1223ba02bdfba2 | conditional_association | evidence_8804507fd3d971c4973171eb835c68926e5a17e78144af40d08c261c419fb951 | positive | false | analysis_sample |
| claim_ca248534ecf37574664bb9185e0cabf2816dd46c5c37d6e963a4e4d058cc86d3 | statistical_uncertainty | evidence_d738f9de9bd25f897be3781fce993a0637c11c20bf03d34ed8b3b62e6cfa836d | not_applicable | false | analysis_sample |
| claim_e577152ac0212314e9fe4008620261a748b1104da3cb8c9dd8e48563d3954b00 | conditional_association | evidence_d738f9de9bd25f897be3781fce993a0637c11c20bf03d34ed8b3b62e6cfa836d | negative | false | analysis_sample |

## Domain Assessments

| Domain | Supplied | Coverage | Evidence | Claims | Unsupported |
| --- | --- | --- | --- | --- | --- |
| governance | true | relevant_evidence | 6 | 5 | causality, intervention_recommendation, mechanism, policy_effectiveness, population_wide_generalization, temporal_prediction |
| economics | true | relevant_evidence | 6 | 5 | causality, intervention_recommendation, mechanism, policy_effectiveness, population_wide_generalization, temporal_prediction |
| education | false | assessment_missing | 0 | 0 |  |
| public_health | true | relevant_evidence | 5 | 5 | causality, intervention_recommendation, mechanism, medical_conclusion, policy_effectiveness, population_wide_generalization, temporal_prediction |

## Cross-Domain Synthesis

The coordinated assessment contains 7 referenced evidence records and 5 referenced non-causal claim candidates across governance, economics, public_health. Domain coverage is incomplete; education was not represented. Unsupported inference boundaries remain active, including causal inference.

| Finding ID | Domains | Claim IDs | Evidence IDs |
| --- | --- | --- | --- |
| cross_synthesis_09075d5e0e3aee7ea0c370541c394848b3c99f7f3962b54370ee8b3f01bec0cc | governance, economics, public_health |  | evidence_d738f9de9bd25f897be3781fce993a0637c11c20bf03d34ed8b3b62e6cfa836d |
| cross_synthesis_23888b65574fbaf5bd46302cedbd87d079899adfdbc78ea5147ade8e37837ec7 | governance, economics, public_health | claim_aa4ee82a7423108c121a62176ba98d5bb8977b29ecf4526bab1223ba02bdfba2 |  |
| cross_synthesis_25dcd25a6828057b89cd0cd7bf0a851f0a7c99182acb9b625dc03014d5f33ada | governance, economics, public_health | claim_ca248534ecf37574664bb9185e0cabf2816dd46c5c37d6e963a4e4d058cc86d3 |  |
| cross_synthesis_6ed21306ba7e4235986e36f822b5eb17d7ef732e4af50d032ff74f1acd6ee4de | governance, economics, public_health | claim_e577152ac0212314e9fe4008620261a748b1104da3cb8c9dd8e48563d3954b00 |  |
| cross_synthesis_a17a3c69d12463c38ccea16cfd4b38736147f220eec1247974468edc04b55833 | governance, economics, public_health |  | evidence_a46999b0ca81d03e4d7f5db9da62be5590b6db79be7b13ff1ad6f7a3d17964b7 |
| cross_synthesis_a7ac99af91db03746517cd1f3319d29bc2f5c90be0584d4d4c5c2fb713804c71 | governance, economics, public_health |  | evidence_abb642f960ef6cc12ab29127359e157b26b0c3479d6fabf448639b3c859f9bb3 |
| cross_synthesis_c77da6dd3508533939fc0cc8f64e632a15660c499dc02b8d78ececc5312d3a4e | governance, economics, public_health | claim_6ea3035a867a5ed3f6c1337000117c49c53b86b9531fd4da5ba2e3761373f051 |  |
| cross_synthesis_d68fa4151ec6c7f58301831fa221ad975ecd1f597b9aafc3479ba5e9a675cb2a | governance, economics, public_health |  | evidence_8804507fd3d971c4973171eb835c68926e5a17e78144af40d08c261c419fb951 |
| cross_synthesis_d75beb8c0c24b8c490ac3ae5663a2fdc4f32c155a12a48121faabeef98ad7ef3 | governance, economics, public_health |  | evidence_019b5204346e69f408c708525cf7050d3445ab19c849b4fd6303b019af74f34f |
| cross_synthesis_e7f9ab36eae82d8027dc5c5d5cc5425f1b0a636c7ec8a54e10d984f467cc04b7 | governance, economics, public_health | claim_3b443710aa68a605c571ec069ba493b26fa789003787cba9e30af2beff807c6d |  |

## Phase 8 Synthesis

The coordinated assessment contains 7 referenced evidence records and 5 referenced non-causal claim candidates across governance, economics, public_health. Domain coverage is incomplete; education was not represented. Unsupported inference boundaries remain active, including causal inference.

| Domain | Summary | Claims | Evidence |
| --- | --- | --- | --- |
| governance | governance selected 6 evidence references and 5 claim references from the coordinated assessment. These references support cautious association-oriented synthesis only. | claim_3b443710aa68a605c571ec069ba493b26fa789003787cba9e30af2beff807c6d, claim_6ea3035a867a5ed3f6c1337000117c49c53b86b9531fd4da5ba2e3761373f051, claim_aa4ee82a7423108c121a62176ba98d5bb8977b29ecf4526bab1223ba02bdfba2, claim_ca248534ecf37574664bb9185e0cabf2816dd46c5c37d6e963a4e4d058cc86d3, claim_e577152ac0212314e9fe4008620261a748b1104da3cb8c9dd8e48563d3954b00 | evidence_019b5204346e69f408c708525cf7050d3445ab19c849b4fd6303b019af74f34f, evidence_85cf41964c544677231a67772d8eb11e2a13521413328dee1dd01e558a616aa8, evidence_8804507fd3d971c4973171eb835c68926e5a17e78144af40d08c261c419fb951, evidence_a46999b0ca81d03e4d7f5db9da62be5590b6db79be7b13ff1ad6f7a3d17964b7, evidence_abb642f960ef6cc12ab29127359e157b26b0c3479d6fabf448639b3c859f9bb3, evidence_d738f9de9bd25f897be3781fce993a0637c11c20bf03d34ed8b3b62e6cfa836d |
| economics | economics selected 6 evidence references and 5 claim references from the coordinated assessment. These references support cautious association-oriented synthesis only. | claim_3b443710aa68a605c571ec069ba493b26fa789003787cba9e30af2beff807c6d, claim_6ea3035a867a5ed3f6c1337000117c49c53b86b9531fd4da5ba2e3761373f051, claim_aa4ee82a7423108c121a62176ba98d5bb8977b29ecf4526bab1223ba02bdfba2, claim_ca248534ecf37574664bb9185e0cabf2816dd46c5c37d6e963a4e4d058cc86d3, claim_e577152ac0212314e9fe4008620261a748b1104da3cb8c9dd8e48563d3954b00 | evidence_019b5204346e69f408c708525cf7050d3445ab19c849b4fd6303b019af74f34f, evidence_4e70d32adb9f25cd824528d5b5281419189c171da4e83a9f8cc57446d30c48e7, evidence_8804507fd3d971c4973171eb835c68926e5a17e78144af40d08c261c419fb951, evidence_a46999b0ca81d03e4d7f5db9da62be5590b6db79be7b13ff1ad6f7a3d17964b7, evidence_abb642f960ef6cc12ab29127359e157b26b0c3479d6fabf448639b3c859f9bb3, evidence_d738f9de9bd25f897be3781fce993a0637c11c20bf03d34ed8b3b62e6cfa836d |
| education | education was not supplied and should not be described as producing substantive evidence in this synthesis. |  |  |
| public_health | public_health selected 5 evidence references and 5 claim references from the coordinated assessment. These references support cautious association-oriented synthesis only. | claim_3b443710aa68a605c571ec069ba493b26fa789003787cba9e30af2beff807c6d, claim_6ea3035a867a5ed3f6c1337000117c49c53b86b9531fd4da5ba2e3761373f051, claim_aa4ee82a7423108c121a62176ba98d5bb8977b29ecf4526bab1223ba02bdfba2, claim_ca248534ecf37574664bb9185e0cabf2816dd46c5c37d6e963a4e4d058cc86d3, claim_e577152ac0212314e9fe4008620261a748b1104da3cb8c9dd8e48563d3954b00 | evidence_019b5204346e69f408c708525cf7050d3445ab19c849b4fd6303b019af74f34f, evidence_8804507fd3d971c4973171eb835c68926e5a17e78144af40d08c261c419fb951, evidence_a46999b0ca81d03e4d7f5db9da62be5590b6db79be7b13ff1ad6f7a3d17964b7, evidence_abb642f960ef6cc12ab29127359e157b26b0c3479d6fabf448639b3c859f9bb3, evidence_d738f9de9bd25f897be3781fce993a0637c11c20bf03d34ed8b3b62e6cfa836d |

## Limitations

The report preserves upstream limitation codes and keeps interpretation bounded to structured, non-causal Polaris artifacts.

| Limitation Code |
| --- |
| HETEROSKEDASTICITY_WARNING |
| LIMITED_MODEL_SCOPE |
| OBSERVATIONAL_ASSOCIATION |
| RESIDUAL_NORMALITY_WARNING |
| UNSUPPORTED_GENERALIZATION |

## Evidence and Domain Gaps

| Gap ID | Type | Sources | Domains |
| --- | --- | --- | --- |
| coordination_evidence_gap_2069726e87a57b6c15cd554ed10de6c73da6635515341fcf832f4ccd88b53aa2 | cross_domain_claim_with_limited_domain_coverage | claim_ca248534ecf37574664bb9185e0cabf2816dd46c5c37d6e963a4e4d058cc86d3 | governance, economics, public_health |
| coordination_evidence_gap_77b609b97c78885e4a1ec83a6de2d6240267ae7374e7a9089890cec784daa444 | cross_domain_claim_with_limited_domain_coverage | claim_6ea3035a867a5ed3f6c1337000117c49c53b86b9531fd4da5ba2e3761373f051 | governance, economics, public_health |
| coordination_evidence_gap_a638e7208bff6eb8199fac328886af8b318e737094d518ba91ee75045a8ff069 | cross_domain_claim_with_limited_domain_coverage | claim_3b443710aa68a605c571ec069ba493b26fa789003787cba9e30af2beff807c6d | governance, economics, public_health |
| coordination_evidence_gap_bd71b1ea616c7f9f98e11320f02e3ddb802fe1994974236f48c09bc32dbdbbc0 | cross_domain_claim_with_limited_domain_coverage | claim_e577152ac0212314e9fe4008620261a748b1104da3cb8c9dd8e48563d3954b00 | governance, economics, public_health |
| coordination_evidence_gap_e2eb7c398297635bb4c018323ade7e138271b897361aa43514a32d9561f6adf3 | cross_domain_claim_with_limited_domain_coverage | claim_aa4ee82a7423108c121a62176ba98d5bb8977b29ecf4526bab1223ba02bdfba2 | governance, economics, public_health |
| coordination_evidence_gap_409b30d74c7f6d77bc6c3f5ad22bfa9840bbcb4ec862198080a8ec3e14a840b1 | evidence_referenced_without_cross_domain_context | evidence_4e70d32adb9f25cd824528d5b5281419189c171da4e83a9f8cc57446d30c48e7 | economics |
| coordination_evidence_gap_d46e75adca7b25602dee73a0ce8f59112f88ab78ec9e08a94a0150e1b2be707f | evidence_referenced_without_cross_domain_context | evidence_85cf41964c544677231a67772d8eb11e2a13521413328dee1dd01e558a616aa8 | governance |

| Gap ID | Type | Domain | Assessment supplied |
| --- | --- | --- | --- |
| coordination_domain_gap_6dfe7972acbb582af0493c5f46d83f4e3889a6e76542b35463ba65e833d82d51 | domain_not_represented | education | false |

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
| Source dataset | harmonized_country_year_42b5ab4803e5f84f |
| Phase 3 DatasetIngestionResult | harmonized_country_year_42b5ab4803e5f84f |
| Phase 4 AnalysisResult | analysis_5aa4b2006b248978ba24e16f415f90dc180dee04ed5f5c4bfbdb34178a966015 |
| Phase 5 EvidenceArtifact | evidence_artifact_84b6a15faa958f4edf5dbb772527ed0d0b47b14657aeb9f5ef8f9e5933928521 |
| Phase 6 AgentAssessments | agent_assessment_066cf151e525a0d642492532dedefef2908f85e14a4d8ce3eb42e872e0d343d8, agent_assessment_6026fa7b83c3dd58b3d3ed2f859e099e6359ad63a88ba33c2e7f980385788e80, agent_assessment_c1444dc3b8190b0db4af1ff80f07298b67761e710dd20208b94e4a3f2303bdf6 |
| Phase 7 CoordinatedAssessment | coordinated_assessment_fa0532643648c33d2535c1e91137a381c8bfb5a165ef17ecc54e69029b6566d1 |
| Phase 8 SynthesisArtifact | synthesis_af8303a46f05357ebd3b352d553b1bd5edb78a2167d4150933ae1d2a44ebdcd9 |
| Phase 9 ResearchReport | report_ade8b830b8a164fee65642be4b924f0f05312dc8cfe27987af5e4b61146dab65 |

## Reference Index

| Reference ID | Kind | Label |
| --- | --- | --- |
| coordination_agreement_0c396c621199b5d17074356ce25c44344aee1601e8b5b77379ee0f102b0fbe06 | agreement | Coordination agreement: shared_evidence |
| coordination_agreement_1a7142e4c06aefd7bf6c89a5c64200d163f42062fe9c4ff7b2329ceb3a79aae5 | agreement | Coordination agreement: shared_evidence |
| coordination_agreement_1b3d648530993f59186b5926addd90e0ba81f41ac85e48b60c3d9c739c0d78ae | agreement | Coordination agreement: shared_evidence |
| coordination_agreement_1b925dcf99fc9032e84af68eca3f20fc6853bf04e67c544ffd8c9c170a2bd8e6 | agreement | Coordination agreement: shared_domain_concern |
| coordination_agreement_1c5389abc356f4e9d4943e3bacc1e0a35a79a9b6aed788a28c97009667cb6941 | agreement | Coordination agreement: shared_unsupported_inference |
| coordination_agreement_238a13e40ea3a552028b96f2580b11792fb11ef67a34d8e2395e25d16936416a | agreement | Coordination agreement: shared_domain_concern |
| coordination_agreement_29423e40dec65d4625022db9fdd9d99679d61db15b6f1d77abc6fa4a7750f14b | agreement | Coordination agreement: shared_limitation |
| coordination_agreement_30eaabbda92ce5d8f3adf39daf8b59db5f10e308f9c0793711bd590a4b65ca72 | agreement | Coordination agreement: shared_limitation |
| coordination_agreement_40a8d32d26c809e8a52cc05f1ed7891dfb6b7c29ac8685a124dabcf0a9fc1abb | agreement | Coordination agreement: shared_evidence |
| coordination_agreement_47469bdd71b7841ed49156843ecc76ab5a35f4fcdc173a4624eb5057be5702a1 | agreement | Coordination agreement: shared_unsupported_inference |
| coordination_agreement_5ff04325572f03343c7ae948c4f66a3cb0a03769013234cabb91f5cac45bd4e1 | agreement | Coordination agreement: shared_domain_concern |
| coordination_agreement_61fa78d80bfe601ed889ffc61410028e27f9bf4723636dd6b71cd5f1f440f730 | agreement | Coordination agreement: shared_limitation |
| coordination_agreement_6e3cf305eb12e1834262dd72a44bdb3ca0c7434e22bb122e85b64502ee55b332 | agreement | Coordination agreement: shared_claim |
| coordination_agreement_70e2006a9e8ab83120231bdca8e26a3e52dd918a2db1fa8bf347aa37f75f5408 | agreement | Coordination agreement: shared_domain_concern |
| coordination_agreement_74ef00dd2cb0eff12d857adf102cfab63fbcbaff30e62dda484f5f3a14a8cccc | agreement | Coordination agreement: shared_domain_concern |
| coordination_agreement_7f8c331c6be9430afaf26b7f9401e6b25442f490cc22e33650dc08fc7a8ccd91 | agreement | Coordination agreement: shared_domain_concern |
| coordination_agreement_7fd41ec7287ba0916a3a5319aae9267befcb28df518c59aa8ae8ac9122662979 | agreement | Coordination agreement: shared_domain_concern |
| coordination_agreement_90764887582d8f3359f28f5b4ce3f9fb09952dd2015e062ff40d565c8bb5558e | agreement | Coordination agreement: shared_limitation |
| coordination_agreement_9c9c34e5078920bdb5cd7f68ca511f09920849100d5d934e2fa83f07592c3322 | agreement | Coordination agreement: shared_limitation |
| coordination_agreement_9cd9e15a6df7f0aba82ac48eee5632f0fba566aafc033a3e154fcae28b739983 | agreement | Coordination agreement: shared_unsupported_inference |
| coordination_agreement_aec87b0910f92c875bc9ea3b7c52c260416a291ebe6d5de91d2c312c81146561 | agreement | Coordination agreement: shared_unsupported_inference |
| coordination_agreement_b4a923eca2a05f3ab80ee3df51dee1a3ae2f4a13288d307c62ae13f1f143e367 | agreement | Coordination agreement: shared_claim |
| coordination_agreement_b982b4cac5a7bf421bd6f8d921aebbb57e40e0083f88dd2f07d6636711379c7d | agreement | Coordination agreement: shared_unsupported_inference |
| coordination_agreement_bdfe7049924860f7cc30b99609c2c543a9cf3af7ca9ab8316992225dc7e72a8b | agreement | Coordination agreement: shared_unsupported_inference |
| coordination_agreement_c76147ffe3adff9def72e7a2f9a6e0b61b07df8fd140f9abb5c3046ffbf55a63 | agreement | Coordination agreement: shared_domain_concern |
| coordination_agreement_cb8c310ccd919ebe81d1273a009402c9c6ab64ffbe527f5f6703fbe75be0ef27 | agreement | Coordination agreement: shared_evidence |
| coordination_agreement_ddd290fa5672d797873a090f66312678bdb7a87dd83af26eeec9558947b09d99 | agreement | Coordination agreement: shared_claim |
| coordination_agreement_e1ae649ff98a5e83c99849e88d29a298492fe34cfd1fd6146ae75f08daf6e130 | agreement | Coordination agreement: shared_claim |
| coordination_agreement_e2c9ddeeafb21386a10b3da6e39eaec9aaec8559de794f1fd19a49ae090f440c | agreement | Coordination agreement: shared_claim |
| coordination_agreement_eb4ffb22c78650df82c3de15db1ec96dea7b68bb6a7cf45ae6d690355f1ead25 | agreement | Coordination agreement: shared_domain_concern |
| agent_assessment_066cf151e525a0d642492532dedefef2908f85e14a4d8ce3eb42e872e0d343d8 | assessment | Domain assessment: public_health |
| agent_assessment_6026fa7b83c3dd58b3d3ed2f859e099e6359ad63a88ba33c2e7f980385788e80 | assessment | Domain assessment: economics |
| agent_assessment_c1444dc3b8190b0db4af1ff80f07298b67761e710dd20208b94e4a3f2303bdf6 | assessment | Domain assessment: governance |
| claim_3b443710aa68a605c571ec069ba493b26fa789003787cba9e30af2beff807c6d | claim | Claim candidate: statistical_uncertainty |
| claim_5c8a0328870dfa4b3d44665340666da1d8b6b72b764acfaaf06786bd79614cf2 | claim | Claim candidate: model_limitation |
| claim_6e6169b9deec49d2246e3e15b8a19ea388eb474906aa866fc1fb342751fc3851 | claim | Claim candidate: model_limitation |
| claim_6ea3035a867a5ed3f6c1337000117c49c53b86b9531fd4da5ba2e3761373f051 | claim | Claim candidate: statistical_uncertainty |
| claim_aa4ee82a7423108c121a62176ba98d5bb8977b29ecf4526bab1223ba02bdfba2 | claim | Claim candidate: conditional_association |
| claim_ca248534ecf37574664bb9185e0cabf2816dd46c5c37d6e963a4e4d058cc86d3 | claim | Claim candidate: statistical_uncertainty |
| claim_e577152ac0212314e9fe4008620261a748b1104da3cb8c9dd8e48563d3954b00 | claim | Claim candidate: conditional_association |
| coordination_divergence_01de599f68d27faedcc9ec44e548479e28b5647b0ef11b2940ebf7f357819945 | divergence | Coordination divergence: different_relevance_classification |
| coordination_divergence_176ca9fb7138b954d973be37b24c64f8b7392ea981d1b8b449a6e02c914c100a | divergence | Coordination divergence: uneven_evidence_coverage |
| coordination_divergence_5f3b8f69c2465b9497e517801aab17fe9d5736953c5082aadb23018dafdf8a6f | divergence | Coordination divergence: domain_specific_unsupported_inference |
| coordination_divergence_92128342ae459a950581e8babe7a987f1d852f6f933608edefc7828f09d5533e | divergence | Coordination divergence: uneven_evidence_coverage |
| coordination_divergence_c7327318460548e8393a0b4d24bb6b21bada4ea6ec93edd66e0cc2beb61155b2 | divergence | Coordination divergence: different_relevance_classification |
| evidence_019b5204346e69f408c708525cf7050d3445ab19c849b4fd6303b019af74f34f | evidence | Evidence record: regression_coefficient |
| evidence_166ca5969a8cb9ce0d7bcea7daaa07c8af6b9e53f09e382dd2cba131bfa8842a | evidence | Evidence record: model_diagnostic |
| evidence_2f7f96e6e11068cfc6fabf8d10a86c7535bcadb30cbbc8d98e691f5d577eb530 | evidence | Evidence record: model_diagnostic |
| evidence_3b1309e9c1cc49db59c8b83491f1914315485b3fdcd609eaba772b5651bca96e | evidence | Evidence record: model_diagnostic |
| evidence_4e70d32adb9f25cd824528d5b5281419189c171da4e83a9f8cc57446d30c48e7 | evidence | Evidence record: model_diagnostic |
| evidence_6a0eb6fcdf3493d68c5098ec6da847b5f8ffe50d10abdf2dd48ab54f9cd2f1b5 | evidence | Evidence record: model_diagnostic |
| evidence_85cf41964c544677231a67772d8eb11e2a13521413328dee1dd01e558a616aa8 | evidence | Evidence record: model_diagnostic |
| evidence_8804507fd3d971c4973171eb835c68926e5a17e78144af40d08c261c419fb951 | evidence | Evidence record: regression_coefficient |
| evidence_a46999b0ca81d03e4d7f5db9da62be5590b6db79be7b13ff1ad6f7a3d17964b7 | evidence | Evidence record: sample_quality |
| evidence_abb642f960ef6cc12ab29127359e157b26b0c3479d6fabf448639b3c859f9bb3 | evidence | Evidence record: model_fit |
| evidence_b8b0b2dfa30ea4d72802fc79ef5b600e5abb50522e220d1ac4e524fcd60abc38 | evidence | Evidence record: model_diagnostic |
| evidence_d738f9de9bd25f897be3781fce993a0637c11c20bf03d34ed8b3b62e6cfa836d | evidence | Evidence record: regression_coefficient |
| coordination_domain_gap_6dfe7972acbb582af0493c5f46d83f4e3889a6e76542b35463ba65e833d82d51 | gap | Domain gap: education |
| coordination_evidence_gap_2069726e87a57b6c15cd554ed10de6c73da6635515341fcf832f4ccd88b53aa2 | gap | Evidence gap: cross_domain_claim_with_limited_domain_coverage |
| coordination_evidence_gap_409b30d74c7f6d77bc6c3f5ad22bfa9840bbcb4ec862198080a8ec3e14a840b1 | gap | Evidence gap: evidence_referenced_without_cross_domain_context |
| coordination_evidence_gap_77b609b97c78885e4a1ec83a6de2d6240267ae7374e7a9089890cec784daa444 | gap | Evidence gap: cross_domain_claim_with_limited_domain_coverage |
| coordination_evidence_gap_a638e7208bff6eb8199fac328886af8b318e737094d518ba91ee75045a8ff069 | gap | Evidence gap: cross_domain_claim_with_limited_domain_coverage |
| coordination_evidence_gap_bd71b1ea616c7f9f98e11320f02e3ddb802fe1994974236f48c09bc32dbdbbc0 | gap | Evidence gap: cross_domain_claim_with_limited_domain_coverage |
| coordination_evidence_gap_d46e75adca7b25602dee73a0ce8f59112f88ab78ec9e08a94a0150e1b2be707f | gap | Evidence gap: evidence_referenced_without_cross_domain_context |
| coordination_evidence_gap_e2eb7c398297635bb4c018323ade7e138271b897361aa43514a32d9561f6adf3 | gap | Evidence gap: cross_domain_claim_with_limited_domain_coverage |
| analysis_5aa4b2006b248978ba24e16f415f90dc180dee04ed5f5c4bfbdb34178a966015 | source_artifact | Source Polaris artifact |
| coordinated_assessment_fa0532643648c33d2535c1e91137a381c8bfb5a165ef17ecc54e69029b6566d1 | source_artifact | Source Polaris artifact |
| evidence_artifact_84b6a15faa958f4edf5dbb772527ed0d0b47b14657aeb9f5ef8f9e5933928521 | source_artifact | Source Polaris artifact |
| harmonized_country_year_42b5ab4803e5f84f | source_artifact | Source Polaris artifact |
| synthesis_af8303a46f05357ebd3b352d553b1bd5edb78a2167d4150933ae1d2a44ebdcd9 | source_artifact | Source Polaris artifact |
