# Phase 17 UNESCO Education Integration Validation

Education, income, and life expectancy

## Metadata

| Field | Value |
| --- | --- |
| Report ID | report_38136450db7814e4f067ab49b350c9ba47bfc75093d328c777812cefa78d3423 |
| Generated | 2026-08-12T21:04:06.771503+00:00 |
| Dataset ID | harmonized_country_year_8d093613c7a39a83 |
| Source checksum | 45c28e267c7b0392afc1b49386ea2c9debdf69098b845e00d3a6d95f0390037f |
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
| Dataset ID | harmonized_country_year_8d093613c7a39a83 |
| Title | Phase 12 Harmonized Country-Year Dataset |
| Provider | Polaris derived harmonization |
| Source type | local_csv |
| Checksum | 45c28e267c7b0392afc1b49386ea2c9debdf69098b845e00d3a6d95f0390037f |
| Accepted rows | 49 |
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
| Analysis result ID | analysis_3706fb4c0e2a2e9c44b8c2f2c092f05474aa243decea5ebea6c523760803863d |
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
| evidence_0052b3869e024706bd2d2803c2b0ffeac9cecb989639f47822924625fa73ef5f | sample_quality | uis_upper_secondary_attainment_rate_25plus, wdi_gdp_per_capita_current_usd, who_life_expectancy_at_birth_both_sexes |  | MISSING_DATA_EXCLUSION |
| evidence_01e148b37d832466a1384992187ffe4e85af0329baadfa7dd392f2acf5866e5b | analysis_warning | uis_upper_secondary_attainment_rate_25plus, wdi_gdp_per_capita_current_usd, who_life_expectancy_at_birth_both_sexes |  | MISSING_DATA_EXCLUSION |
| evidence_070cc75260dfe1116b80c31f0be200bbb7686d66364d89e2b9ea13a51a9e413c | model_diagnostic |  |  | RESIDUAL_NORMALITY_WARNING |
| evidence_2927dc9785c4fcc4cdc99b073f790e9a5c5555b5fb94d7ff7453d018a47f3c16 | regression_coefficient | uis_upper_secondary_attainment_rate_25plus, wdi_gdp_per_capita_current_usd, who_life_expectancy_at_birth_both_sexes | negative |  |
| evidence_38443ada9f60c77143afb56da79f96c1369ff2ff2e73e7e9231736dcd360c4ae | model_fit | uis_upper_secondary_attainment_rate_25plus, wdi_gdp_per_capita_current_usd, who_life_expectancy_at_birth_both_sexes |  |  |
| evidence_5bc776217ab1cf9815ea237d8c2420b9d65f4b6db81b5a48c49108ff2d41a84b | regression_coefficient | uis_upper_secondary_attainment_rate_25plus, wdi_gdp_per_capita_current_usd, who_life_expectancy_at_birth_both_sexes | positive |  |
| evidence_6baa712e3f094bb1f2df27ccf771fd2e5a7768e3e7a5d20b73c9c8f875f3a7fb | model_diagnostic | wdi_gdp_per_capita_current_usd |  |  |
| evidence_7aba8c640d20987ca52d59c64b24b658e68031a2b39a7b566d4dfd22a0e8c9e2 | model_diagnostic |  |  |  |
| evidence_974a6ee26c1b9ddb56a7606bfcd6c48017f03e35533889afe0c931976673b144 | model_diagnostic |  |  |  |
| evidence_a969804844fb643ad70f2a3a8c1c0d2f7966c250734504babac1304cedd372cf | regression_coefficient | uis_upper_secondary_attainment_rate_25plus, wdi_gdp_per_capita_current_usd, who_life_expectancy_at_birth_both_sexes | positive |  |
| evidence_f51c693e72a078f6bbcd73dee8371039444735b68f4d8033e676ade07d609b54 | model_diagnostic |  |  | HETEROSKEDASTICITY_WARNING |
| evidence_fc9c80b7d0582c38c284601c65adcebc2ea70791ceb0a045f6bd2599ac759077 | model_diagnostic |  |  |  |
| evidence_fde22952d69ef4231edbfa4c8ce6ae39bd812a3b076adb99abf45b3925131aef | model_diagnostic | uis_upper_secondary_attainment_rate_25plus |  |  |

| Claim ID | Type | Evidence IDs | Direction | Causal | Scope |
| --- | --- | --- | --- | --- | --- |
| claim_1ac86d7cd3d7af3049342d72fc4f4a81716b39a4f91543dc1579e32ee9e8d1c3 | model_limitation | evidence_070cc75260dfe1116b80c31f0be200bbb7686d66364d89e2b9ea13a51a9e413c | not_applicable | false | analysis_sample |
| claim_313622942cb4e9faa9634cf0c5387bf65589796b6f9cfd0292c7a472c0e81612 | conditional_association | evidence_5bc776217ab1cf9815ea237d8c2420b9d65f4b6db81b5a48c49108ff2d41a84b | positive | false | analysis_sample |
| claim_3ce7764384d14f1623e445a2f1b0620f7d0bdd199f59b8f58c4f6783b9a1f8be | statistical_uncertainty | evidence_5bc776217ab1cf9815ea237d8c2420b9d65f4b6db81b5a48c49108ff2d41a84b | not_applicable | false | analysis_sample |
| claim_7bc791cadae609738519d8071a279228ca23ab732e9d2242e86ddf628dead8ec | conditional_association | evidence_2927dc9785c4fcc4cdc99b073f790e9a5c5555b5fb94d7ff7453d018a47f3c16 | negative | false | analysis_sample |
| claim_abbb743e7385d0e70c225ef0e1eb95f94ef18bf40fad5d75e3f40988cc185ab6 | model_limitation | evidence_f51c693e72a078f6bbcd73dee8371039444735b68f4d8033e676ade07d609b54 | not_applicable | false | analysis_sample |
| claim_bcba3a3d9660c0f941d3af94084ff957f46b9dacadbf4e0528ab7c307eb20515 | statistical_uncertainty | evidence_a969804844fb643ad70f2a3a8c1c0d2f7966c250734504babac1304cedd372cf | not_applicable | false | analysis_sample |
| claim_d03ba0e9975703d28b5e3fde24d2945e3fd9f57b4e3e31a04f1cc3e231ee284e | statistical_uncertainty | evidence_2927dc9785c4fcc4cdc99b073f790e9a5c5555b5fb94d7ff7453d018a47f3c16 | not_applicable | false | analysis_sample |

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
| cross_synthesis_02d621c84f99fb21ea04aa2ad64836df41db55ff3d43d626b4404fb985cf1b9d | economics, education, public_health |  | evidence_0052b3869e024706bd2d2803c2b0ffeac9cecb989639f47822924625fa73ef5f |
| cross_synthesis_09026b903f932d2a68d13465b89ea779b12027118f56c1d0e2ce7ab77c9a7bd3 | economics, education, public_health | claim_d03ba0e9975703d28b5e3fde24d2945e3fd9f57b4e3e31a04f1cc3e231ee284e |  |
| cross_synthesis_41b66e78a0253040d4a935fd47df0c36390edf6083614d6bd2c154d6354cb1ee | economics, education, public_health | claim_bcba3a3d9660c0f941d3af94084ff957f46b9dacadbf4e0528ab7c307eb20515 |  |
| cross_synthesis_42c25c989e0cd0c56a073e3e108b3103fdafacc7215717a75f2174ea54d38cec | economics, education, public_health |  | evidence_2927dc9785c4fcc4cdc99b073f790e9a5c5555b5fb94d7ff7453d018a47f3c16 |
| cross_synthesis_5f4e16fc72fd944007fe50084a7545c38a5668d2dbdb181f34cd02cbd89f5584 | economics, education, public_health |  | evidence_5bc776217ab1cf9815ea237d8c2420b9d65f4b6db81b5a48c49108ff2d41a84b |
| cross_synthesis_91be8790be62eb4453463619489174e324124319b301b235f99c65e0410baec8 | economics, education, public_health |  | evidence_38443ada9f60c77143afb56da79f96c1369ff2ff2e73e7e9231736dcd360c4ae |
| cross_synthesis_9284d2ee59a7b54fd2b866fa0afb32ed26d532e4bb431348edfeba8e3ef68835 | economics, education, public_health |  | evidence_a969804844fb643ad70f2a3a8c1c0d2f7966c250734504babac1304cedd372cf |
| cross_synthesis_9fb1f3d402a204a2350f962f7a6b478fe3849a7523be02b7a215ef177f1f02ae | economics, education, public_health |  | evidence_01e148b37d832466a1384992187ffe4e85af0329baadfa7dd392f2acf5866e5b |
| cross_synthesis_a89f24fb951071e280e23c87b0a1c97169bf0838e7b15b48fcb5414ce160ac6d | economics, education, public_health | claim_7bc791cadae609738519d8071a279228ca23ab732e9d2242e86ddf628dead8ec |  |
| cross_synthesis_b3658977c6992cc222ab070275cba6a060ca214e5f23a6997583e0bd4974f16c | economics, education, public_health | claim_313622942cb4e9faa9634cf0c5387bf65589796b6f9cfd0292c7a472c0e81612 |  |
| cross_synthesis_dc5ce515912b324338623c1666e66e3607ad3d71cc70a4939fb8396b75c26805 | economics, education, public_health | claim_3ce7764384d14f1623e445a2f1b0620f7d0bdd199f59b8f58c4f6783b9a1f8be |  |

## Phase 8 Synthesis

The coordinated assessment contains 8 referenced evidence records and 5 referenced non-causal claim candidates across economics, education, public_health. Domain coverage is incomplete; governance was not represented. Unsupported inference boundaries remain active, including causal inference.

| Domain | Summary | Claims | Evidence |
| --- | --- | --- | --- |
| governance | governance was not supplied and should not be described as producing substantive evidence in this synthesis. |  |  |
| economics | economics selected 7 evidence references and 5 claim references from the coordinated assessment. These references support cautious association-oriented synthesis only. | claim_313622942cb4e9faa9634cf0c5387bf65589796b6f9cfd0292c7a472c0e81612, claim_3ce7764384d14f1623e445a2f1b0620f7d0bdd199f59b8f58c4f6783b9a1f8be, claim_7bc791cadae609738519d8071a279228ca23ab732e9d2242e86ddf628dead8ec, claim_bcba3a3d9660c0f941d3af94084ff957f46b9dacadbf4e0528ab7c307eb20515, claim_d03ba0e9975703d28b5e3fde24d2945e3fd9f57b4e3e31a04f1cc3e231ee284e | evidence_0052b3869e024706bd2d2803c2b0ffeac9cecb989639f47822924625fa73ef5f, evidence_01e148b37d832466a1384992187ffe4e85af0329baadfa7dd392f2acf5866e5b, evidence_2927dc9785c4fcc4cdc99b073f790e9a5c5555b5fb94d7ff7453d018a47f3c16, evidence_38443ada9f60c77143afb56da79f96c1369ff2ff2e73e7e9231736dcd360c4ae, evidence_5bc776217ab1cf9815ea237d8c2420b9d65f4b6db81b5a48c49108ff2d41a84b, evidence_6baa712e3f094bb1f2df27ccf771fd2e5a7768e3e7a5d20b73c9c8f875f3a7fb, evidence_a969804844fb643ad70f2a3a8c1c0d2f7966c250734504babac1304cedd372cf |
| education | education selected 7 evidence references and 5 claim references from the coordinated assessment. These references support cautious association-oriented synthesis only. | claim_313622942cb4e9faa9634cf0c5387bf65589796b6f9cfd0292c7a472c0e81612, claim_3ce7764384d14f1623e445a2f1b0620f7d0bdd199f59b8f58c4f6783b9a1f8be, claim_7bc791cadae609738519d8071a279228ca23ab732e9d2242e86ddf628dead8ec, claim_bcba3a3d9660c0f941d3af94084ff957f46b9dacadbf4e0528ab7c307eb20515, claim_d03ba0e9975703d28b5e3fde24d2945e3fd9f57b4e3e31a04f1cc3e231ee284e | evidence_0052b3869e024706bd2d2803c2b0ffeac9cecb989639f47822924625fa73ef5f, evidence_01e148b37d832466a1384992187ffe4e85af0329baadfa7dd392f2acf5866e5b, evidence_2927dc9785c4fcc4cdc99b073f790e9a5c5555b5fb94d7ff7453d018a47f3c16, evidence_38443ada9f60c77143afb56da79f96c1369ff2ff2e73e7e9231736dcd360c4ae, evidence_5bc776217ab1cf9815ea237d8c2420b9d65f4b6db81b5a48c49108ff2d41a84b, evidence_a969804844fb643ad70f2a3a8c1c0d2f7966c250734504babac1304cedd372cf, evidence_fde22952d69ef4231edbfa4c8ce6ae39bd812a3b076adb99abf45b3925131aef |
| public_health | public_health selected 6 evidence references and 5 claim references from the coordinated assessment. These references support cautious association-oriented synthesis only. | claim_313622942cb4e9faa9634cf0c5387bf65589796b6f9cfd0292c7a472c0e81612, claim_3ce7764384d14f1623e445a2f1b0620f7d0bdd199f59b8f58c4f6783b9a1f8be, claim_7bc791cadae609738519d8071a279228ca23ab732e9d2242e86ddf628dead8ec, claim_bcba3a3d9660c0f941d3af94084ff957f46b9dacadbf4e0528ab7c307eb20515, claim_d03ba0e9975703d28b5e3fde24d2945e3fd9f57b4e3e31a04f1cc3e231ee284e | evidence_0052b3869e024706bd2d2803c2b0ffeac9cecb989639f47822924625fa73ef5f, evidence_01e148b37d832466a1384992187ffe4e85af0329baadfa7dd392f2acf5866e5b, evidence_2927dc9785c4fcc4cdc99b073f790e9a5c5555b5fb94d7ff7453d018a47f3c16, evidence_38443ada9f60c77143afb56da79f96c1369ff2ff2e73e7e9231736dcd360c4ae, evidence_5bc776217ab1cf9815ea237d8c2420b9d65f4b6db81b5a48c49108ff2d41a84b, evidence_a969804844fb643ad70f2a3a8c1c0d2f7966c250734504babac1304cedd372cf |

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
| coordination_evidence_gap_4c40388fe8551624305bea257dd3caa6235fe8562a490ab03e6ac2162bb43c7d | cross_domain_claim_with_limited_domain_coverage | claim_7bc791cadae609738519d8071a279228ca23ab732e9d2242e86ddf628dead8ec | economics, education, public_health |
| coordination_evidence_gap_5f857d355a7e3e3280a3cccbe3a0fccf48e92163c8e3acff14840b34e4b45f6b | cross_domain_claim_with_limited_domain_coverage | claim_d03ba0e9975703d28b5e3fde24d2945e3fd9f57b4e3e31a04f1cc3e231ee284e | economics, education, public_health |
| coordination_evidence_gap_897fd77ed77bf1e9147375873c9d325b6773ea4635b9d64a928bdf66885d06b7 | cross_domain_claim_with_limited_domain_coverage | claim_3ce7764384d14f1623e445a2f1b0620f7d0bdd199f59b8f58c4f6783b9a1f8be | economics, education, public_health |
| coordination_evidence_gap_c642b29f9308bf1c617a4b90645d86353c1484d45aa2441a4aaab5fd80ba899b | cross_domain_claim_with_limited_domain_coverage | claim_313622942cb4e9faa9634cf0c5387bf65589796b6f9cfd0292c7a472c0e81612 | economics, education, public_health |
| coordination_evidence_gap_fb1eee390910e3e544d8313a5c78d0b8df0eb38861d9c36754b0ae7c1da88592 | cross_domain_claim_with_limited_domain_coverage | claim_bcba3a3d9660c0f941d3af94084ff957f46b9dacadbf4e0528ab7c307eb20515 | economics, education, public_health |
| coordination_evidence_gap_50eae6ba0ce4c0d34b9dbcd3ed219a9bfe7ed8f4f982af8b714e1ec5ff7208fb | evidence_referenced_without_cross_domain_context | evidence_6baa712e3f094bb1f2df27ccf771fd2e5a7768e3e7a5d20b73c9c8f875f3a7fb | economics |
| coordination_evidence_gap_63c15ad858f1efc09053e266edfcca38437fa0619697a1f34d14e5a55174e01d | evidence_referenced_without_cross_domain_context | evidence_fde22952d69ef4231edbfa4c8ce6ae39bd812a3b076adb99abf45b3925131aef | education |

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
| Source dataset | harmonized_country_year_8d093613c7a39a83 |
| Phase 3 DatasetIngestionResult | harmonized_country_year_8d093613c7a39a83 |
| Phase 4 AnalysisResult | analysis_3706fb4c0e2a2e9c44b8c2f2c092f05474aa243decea5ebea6c523760803863d |
| Phase 5 EvidenceArtifact | evidence_artifact_a62e6e07e229af51bfb879e4d1e2d6e35ab0438fa9c52551676a8f53c0676d5f |
| Phase 6 AgentAssessments | agent_assessment_484e5c61b94a59e3c87029bc5c997c9e7f340153b1ac57a5468091bf922b3ad0, agent_assessment_a78dda5f786dd8fd1b1e909fcea9ffb3aa29103c1028c7e07ece729e11e48b98, agent_assessment_d4edb44e063092a79c53ad0f12efcbcfd8174f4f99097aa55df8d367fbb2733c |
| Phase 7 CoordinatedAssessment | coordinated_assessment_1516d5fe93ffaad941b0148f4f8078b3b66b0cbc417486b4f8eaaa6e725587e2 |
| Phase 8 SynthesisArtifact | synthesis_105857adcd8e4e5572e0531f7508b261083bcae3738b54eb0735ce817c4f79bb |
| Phase 9 ResearchReport | report_38136450db7814e4f067ab49b350c9ba47bfc75093d328c777812cefa78d3423 |

## Reference Index

| Reference ID | Kind | Label |
| --- | --- | --- |
| coordination_agreement_0d5c20c6a2eb647677bff281af55401291b4352a2d1e74f54003feff9008ab4d | agreement | Coordination agreement: shared_unsupported_inference |
| coordination_agreement_1b73b02c415100dd37449be9b4f2129c54729ab520c854957aef1048d2d7fa41 | agreement | Coordination agreement: shared_claim |
| coordination_agreement_1dbb5cc0bbe065dff447eaaca4be48d2579bf60153798477d02670a68e1b65b9 | agreement | Coordination agreement: shared_domain_concern |
| coordination_agreement_2089b58aab4329c761130143ea3c623e499a590ab76ca786e92314301490495d | agreement | Coordination agreement: shared_claim |
| coordination_agreement_325c2ff9bf54195e4fa19a2876e64870459aa87d2a7b84be43b98feadee1129d | agreement | Coordination agreement: shared_claim |
| coordination_agreement_359c6727206115977f1279b72b464be28a77b96717dd7d84886e98f6aeff448c | agreement | Coordination agreement: shared_unsupported_inference |
| coordination_agreement_35cd623384250d1403210fc1b7b26d751c46c00fc809420d8e4ff3fb8d982139 | agreement | Coordination agreement: shared_unsupported_inference |
| coordination_agreement_3ed9e7d365949b4bd58ac9cc735bf76ab38d614849e362901a8dcc7503ea11b6 | agreement | Coordination agreement: shared_domain_concern |
| coordination_agreement_4a2fd99115353993cb46c08db1db334478cfc773cfd3f2d2844d14aebdd567b3 | agreement | Coordination agreement: shared_evidence |
| coordination_agreement_53af29fe6454d0a88f8e51d541915d007a0abe12b57aeca8101aa53f577a1afa | agreement | Coordination agreement: shared_limitation |
| coordination_agreement_56133235bf8ac2fc82d5b586f422558e715e43ce10ffb899f1875574e61d5f3f | agreement | Coordination agreement: shared_claim |
| coordination_agreement_59a0010622d478a874d7f8503066153e84cbb9b54573ea5f0b14746f06c2e745 | agreement | Coordination agreement: shared_domain_concern |
| coordination_agreement_74820eb0c953a33e1592fd0ebb2fb6f5c59e12143aaf1812d848fa6dad3ef5fe | agreement | Coordination agreement: shared_evidence |
| coordination_agreement_790f5a12043ef2ffb2e7b549390e57679e90ad29ac60d227c88d63c4c0ca1ad4 | agreement | Coordination agreement: shared_domain_concern |
| coordination_agreement_7b74ed99c9d49794fd083e3ba9d6f03c98a5b34f56185c35e46cf5d135586af9 | agreement | Coordination agreement: shared_limitation |
| coordination_agreement_80bd2c10788c672c3035dbf17dc919b125248364f988471e7af0c67c8fef23b9 | agreement | Coordination agreement: shared_evidence |
| coordination_agreement_82959a00fa6412057bf3552a0e7e475efb86f5ba90eb645440e96f33852f0fce | agreement | Coordination agreement: shared_evidence |
| coordination_agreement_839e36dbd031b826ca00add9e392d21354875b462af14a8218506705d382a4bf | agreement | Coordination agreement: shared_unsupported_inference |
| coordination_agreement_8f81e2855a3ab110059911fe530d80b4aa711ba5f10d8be0a722e112b3d4e628 | agreement | Coordination agreement: shared_domain_concern |
| coordination_agreement_98db62bd7bdcb87c6b42cec626f37a3ba50b9d84f56ca0cac1f59363dfda7446 | agreement | Coordination agreement: shared_evidence |
| coordination_agreement_9bef5c426f7b40d6565aced8f60d1bccc247d61189a50057f3b39d5a52ec2326 | agreement | Coordination agreement: shared_limitation |
| coordination_agreement_a84a14057193859b289d2812fa58c5dd3200c9f792a9f5f97599395718ed0d72 | agreement | Coordination agreement: shared_domain_concern |
| coordination_agreement_a926f4a013b280033638a941c8905d4ca5a2438d1394886210e58ddf0ace6f6a | agreement | Coordination agreement: shared_domain_concern |
| coordination_agreement_aaeb5839d3f196f528aea51833dbdb51718492377b5d08c48ebe7055cacc66e2 | agreement | Coordination agreement: shared_limitation |
| coordination_agreement_ab181f563aadd6e36e8559b4d4af0fc94ab35c4283a3ba1477f1af33f216d3d9 | agreement | Coordination agreement: shared_unsupported_inference |
| coordination_agreement_acc19537beefde53587f6c38afa1a2b687cd5a949d0663195d4e0285c97504c8 | agreement | Coordination agreement: shared_domain_concern |
| coordination_agreement_aee3f61b34a91d2cfbf98fb6259f2b5fa17185ee19d2de24a3e1e4a4bfe37d8f | agreement | Coordination agreement: shared_evidence |
| coordination_agreement_c0311635e0ed6b098bdc7443d27d934ac9d85a2a52577032e1263929b7f1bf0c | agreement | Coordination agreement: shared_limitation |
| coordination_agreement_c04c2421e3ab85bb9d676df878b322d20929e2fcefb3c3bd28323ab4d59b033f | agreement | Coordination agreement: shared_unsupported_inference |
| coordination_agreement_c2e925dc27e0785c7ab921b4a23a483f28f0fb6ba51d59d59aa82f6f0a38e6d8 | agreement | Coordination agreement: shared_claim |
| coordination_agreement_e43130726f00e83bff182618642e064ab722b19c98d421a171cabe732f29b593 | agreement | Coordination agreement: shared_limitation |
| coordination_agreement_f7ec5c6261c965776adccc790cdf828a52bfa0a410704666fb84c094566ccd0c | agreement | Coordination agreement: shared_domain_concern |
| coordination_agreement_fd3cf8887ff29b4b991344879c2c275d97f06664887844b85c58ff6f81326e17 | agreement | Coordination agreement: shared_domain_concern |
| agent_assessment_484e5c61b94a59e3c87029bc5c997c9e7f340153b1ac57a5468091bf922b3ad0 | assessment | Domain assessment: public_health |
| agent_assessment_a78dda5f786dd8fd1b1e909fcea9ffb3aa29103c1028c7e07ece729e11e48b98 | assessment | Domain assessment: education |
| agent_assessment_d4edb44e063092a79c53ad0f12efcbcfd8174f4f99097aa55df8d367fbb2733c | assessment | Domain assessment: economics |
| claim_1ac86d7cd3d7af3049342d72fc4f4a81716b39a4f91543dc1579e32ee9e8d1c3 | claim | Claim candidate: model_limitation |
| claim_313622942cb4e9faa9634cf0c5387bf65589796b6f9cfd0292c7a472c0e81612 | claim | Claim candidate: conditional_association |
| claim_3ce7764384d14f1623e445a2f1b0620f7d0bdd199f59b8f58c4f6783b9a1f8be | claim | Claim candidate: statistical_uncertainty |
| claim_7bc791cadae609738519d8071a279228ca23ab732e9d2242e86ddf628dead8ec | claim | Claim candidate: conditional_association |
| claim_abbb743e7385d0e70c225ef0e1eb95f94ef18bf40fad5d75e3f40988cc185ab6 | claim | Claim candidate: model_limitation |
| claim_bcba3a3d9660c0f941d3af94084ff957f46b9dacadbf4e0528ab7c307eb20515 | claim | Claim candidate: statistical_uncertainty |
| claim_d03ba0e9975703d28b5e3fde24d2945e3fd9f57b4e3e31a04f1cc3e231ee284e | claim | Claim candidate: statistical_uncertainty |
| coordination_divergence_0abc5eb0cf837d972112c2559ba0beedb411132fa20fa8ff847cf5453e97161f | divergence | Coordination divergence: uneven_evidence_coverage |
| coordination_divergence_1824dbc7e6c75198982874386c7d0f51daea653ccbed028e64bd64453439639f | divergence | Coordination divergence: different_relevance_classification |
| coordination_divergence_1fc13724b6bdc13e86e7364a4ea243d589fae0871e8578e7098740df46c48660 | divergence | Coordination divergence: different_relevance_classification |
| coordination_divergence_5f3b8f69c2465b9497e517801aab17fe9d5736953c5082aadb23018dafdf8a6f | divergence | Coordination divergence: domain_specific_unsupported_inference |
| coordination_divergence_ee27c517ad102ccd6b5737641a81882ba1be9fdb4e1ec1d994e388516ad8c216 | divergence | Coordination divergence: uneven_evidence_coverage |
| evidence_0052b3869e024706bd2d2803c2b0ffeac9cecb989639f47822924625fa73ef5f | evidence | Evidence record: sample_quality |
| evidence_01e148b37d832466a1384992187ffe4e85af0329baadfa7dd392f2acf5866e5b | evidence | Evidence record: analysis_warning |
| evidence_070cc75260dfe1116b80c31f0be200bbb7686d66364d89e2b9ea13a51a9e413c | evidence | Evidence record: model_diagnostic |
| evidence_2927dc9785c4fcc4cdc99b073f790e9a5c5555b5fb94d7ff7453d018a47f3c16 | evidence | Evidence record: regression_coefficient |
| evidence_38443ada9f60c77143afb56da79f96c1369ff2ff2e73e7e9231736dcd360c4ae | evidence | Evidence record: model_fit |
| evidence_5bc776217ab1cf9815ea237d8c2420b9d65f4b6db81b5a48c49108ff2d41a84b | evidence | Evidence record: regression_coefficient |
| evidence_6baa712e3f094bb1f2df27ccf771fd2e5a7768e3e7a5d20b73c9c8f875f3a7fb | evidence | Evidence record: model_diagnostic |
| evidence_7aba8c640d20987ca52d59c64b24b658e68031a2b39a7b566d4dfd22a0e8c9e2 | evidence | Evidence record: model_diagnostic |
| evidence_974a6ee26c1b9ddb56a7606bfcd6c48017f03e35533889afe0c931976673b144 | evidence | Evidence record: model_diagnostic |
| evidence_a969804844fb643ad70f2a3a8c1c0d2f7966c250734504babac1304cedd372cf | evidence | Evidence record: regression_coefficient |
| evidence_f51c693e72a078f6bbcd73dee8371039444735b68f4d8033e676ade07d609b54 | evidence | Evidence record: model_diagnostic |
| evidence_fc9c80b7d0582c38c284601c65adcebc2ea70791ceb0a045f6bd2599ac759077 | evidence | Evidence record: model_diagnostic |
| evidence_fde22952d69ef4231edbfa4c8ce6ae39bd812a3b076adb99abf45b3925131aef | evidence | Evidence record: model_diagnostic |
| coordination_domain_gap_2cda4ca8f7436f9f2c37185bda78a91223f6045f01a8d2a1090a39c37ae6b12f | gap | Domain gap: governance |
| coordination_evidence_gap_4c40388fe8551624305bea257dd3caa6235fe8562a490ab03e6ac2162bb43c7d | gap | Evidence gap: cross_domain_claim_with_limited_domain_coverage |
| coordination_evidence_gap_50eae6ba0ce4c0d34b9dbcd3ed219a9bfe7ed8f4f982af8b714e1ec5ff7208fb | gap | Evidence gap: evidence_referenced_without_cross_domain_context |
| coordination_evidence_gap_5f857d355a7e3e3280a3cccbe3a0fccf48e92163c8e3acff14840b34e4b45f6b | gap | Evidence gap: cross_domain_claim_with_limited_domain_coverage |
| coordination_evidence_gap_63c15ad858f1efc09053e266edfcca38437fa0619697a1f34d14e5a55174e01d | gap | Evidence gap: evidence_referenced_without_cross_domain_context |
| coordination_evidence_gap_897fd77ed77bf1e9147375873c9d325b6773ea4635b9d64a928bdf66885d06b7 | gap | Evidence gap: cross_domain_claim_with_limited_domain_coverage |
| coordination_evidence_gap_c642b29f9308bf1c617a4b90645d86353c1484d45aa2441a4aaab5fd80ba899b | gap | Evidence gap: cross_domain_claim_with_limited_domain_coverage |
| coordination_evidence_gap_fb1eee390910e3e544d8313a5c78d0b8df0eb38861d9c36754b0ae7c1da88592 | gap | Evidence gap: cross_domain_claim_with_limited_domain_coverage |
| analysis_3706fb4c0e2a2e9c44b8c2f2c092f05474aa243decea5ebea6c523760803863d | source_artifact | Source Polaris artifact |
| coordinated_assessment_1516d5fe93ffaad941b0148f4f8078b3b66b0cbc417486b4f8eaaa6e725587e2 | source_artifact | Source Polaris artifact |
| evidence_artifact_a62e6e07e229af51bfb879e4d1e2d6e35ab0438fa9c52551676a8f53c0676d5f | source_artifact | Source Polaris artifact |
| harmonized_country_year_8d093613c7a39a83 | source_artifact | Source Polaris artifact |
| synthesis_105857adcd8e4e5572e0531f7508b261083bcae3738b54eb0735ce817c4f79bb | source_artifact | Source Polaris artifact |
