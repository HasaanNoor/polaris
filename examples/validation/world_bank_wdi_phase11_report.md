# Phase 11 Real Dataset Validation Report

World Bank WDI official bulk CSV

## Metadata

| Field | Value |
| --- | --- |
| Report ID | report_072af00adec897f1b304e0264465dfcd754e2d1813bbf36020b087828243d57f |
| Generated | 2026-08-05T22:30:50.393488+00:00 |
| Dataset ID | world_bank_wdi_real_validation_00f44391cafe |
| Source checksum | 00f44391cafeb2ccfb9ec426e173c7db5bf321c0092b6663f97f59cedb35a4b8 |
| Analysis procedure | ordinary_least_squares |
| Synthesis mode | deterministic |
| Ruleset | deterministic_phase9_v1 |

## Executive Summary

The coordinated assessment contains 8 referenced evidence records and 5 referenced non-causal claim candidates across governance, economics, education, public_health. Unsupported inference boundaries remain active, including causal inference. The report preserves observational and non-causal boundaries from upstream artifacts. No external literature or outside contextual evidence has been integrated.

## Research Question

| Field | Value |
| --- | --- |
| Question ID | rq_phase11_wdi_real_validation |
| Primary question | How is secondary school enrollment associated with life expectancy at birth after accounting for GDP per capita in the official WDI validation extract? |
| Population | Country-year observations in the WDI validation extract |
| Variables | gdp_per_capita_current_usd, life_expectancy_at_birth, secondary_school_enrollment |
| Methods | ordinary_least_squares |

## Dataset and Source

| Field | Value |
| --- | --- |
| Dataset ID | world_bank_wdi_real_validation_00f44391cafe |
| Title | World Bank WDI Real Validation Extract |
| Provider | World Bank |
| Source type | local_csv |
| Checksum | 00f44391cafeb2ccfb9ec426e173c7db5bf321c0092b6663f97f59cedb35a4b8 |
| Accepted rows | 2385 |
| Rejected rows | 0 |
| Analysis ready | true |
| Illustrative | false |
| Variables | life_expectancy_at_birth, secondary_school_enrollment, gdp_per_capita_current_usd |

## Methodology

| Field | Value |
| --- | --- |
| Ingestion and validation | Local CSV ingestion mapped source columns to the supplied manifest, normalized supported scalar values, validated structure, and computed a SHA-256 checksum. |
| Sample construction | Phase 4 used complete-case sample construction from accepted Phase 3 records. |
| Procedure | ordinary_least_squares |
| Dependent variable | life_expectancy_at_birth |
| Predictors | secondary_school_enrollment |
| Controls | gdp_per_capita_current_usd |
| Include intercept | true |
| Confidence level | 0.95 |
| Significance threshold | 0.05 |
| Diagnostics calculated | breusch_pagan, condition_number, durbin_watson, maximum_leverage, residual_normality, variance_inflation_factor, variance_inflation_factor |
| Evidence extraction | Phase 5 extracted 13 evidence records and 7 bounded non-causal claim candidates. |
| Domain agents | Phase 6 deterministic domain agents selected relevant structured evidence and claim IDs without adding outside context. |
| Coordination | Phase 7 coordinated 4 domain assessments by reference. |
| Synthesis mode | deterministic |
| Grounding and validation | Phase 8 synthesis supplied validated summaries with fabricated-reference, limitation-preservation, unsupported-inference, and overreach checks. |

## Statistical Results

| Field | Value |
| --- | --- |
| Analysis result ID | analysis_8941d97c320b46d0ef37a9128be7fa4a7228906673f89a08b0408d0efb11516f |
| Method | ordinary_least_squares |
| Sample size | 1682 |

| Term | Estimate | Std. Error | Statistic | p-value | CI Low | CI High |
| --- | --- | --- | --- | --- | --- | --- |
| intercept | 57.1516469011564 | 0.36720870177681514 | 155.63805167093358 | 0.0 | 56.43141187117896 | 57.871881931133835 |
| secondary_school_enrollment | 0.1655917509364141 | 0.004486535278423235 | 36.908603334243764 | 7.444451959592596e-219 | 0.15679195982276567 | 0.17439154205006252 |
| gdp_per_capita_current_usd | 9.771485970911194e-05 | 4.762879134142232e-06 | 20.515922608376215 | 1.205376053895346e-83 | 8.837305386584302e-05 | 0.00010705666555238087 |

| Metric | Value |
| --- | --- |
| R-squared | 0.678714130272182 |
| Adjusted R-squared | 0.6783314192897784 |
| Residual degrees of freedom | 1679.0 |
| Model degrees of freedom | 2.0 |
| RSS | 27155.89416530495 |
| MSE | 16.173850009115515 |

## Evidence and Claims

| Evidence ID | Type | Variables | Direction | Limitations |
| --- | --- | --- | --- | --- |
| evidence_063ea9d11602cc9867c3620c897722443607a33e23ae23768d0caa99595df897 | regression_coefficient | gdp_per_capita_current_usd, life_expectancy_at_birth, secondary_school_enrollment | positive |  |
| evidence_1f7899d5f4dfcfa59ebb6b19823f25421491311688424d718e1e48040d9dbbf6 | model_diagnostic | secondary_school_enrollment |  |  |
| evidence_20f0d5d5d5f63329b2bc82ee6f530b6df3071bbb7e3648dacce39cafe4529240 | regression_coefficient | gdp_per_capita_current_usd, life_expectancy_at_birth, secondary_school_enrollment | positive |  |
| evidence_38a19f90c1ce4d79762fd3e2fd7f026f3bfeb2b1f547f1a72feef113cde5bdb4 | model_fit | gdp_per_capita_current_usd, life_expectancy_at_birth, secondary_school_enrollment |  |  |
| evidence_4187048a52dfa7c69a3f6ecee0e3d7a31dbcfcd6da3308f734c878e6a3062465 | model_diagnostic |  |  |  |
| evidence_42ffe918feb8de52ff0ec2ad4022816b051c838cdc0d9ea5870879e09b14d31b | model_diagnostic | gdp_per_capita_current_usd |  |  |
| evidence_470478571848831cca35c1665cac562dd1543d2cd0778a8f1a083c5728b4f912 | regression_coefficient | gdp_per_capita_current_usd, life_expectancy_at_birth, secondary_school_enrollment | positive |  |
| evidence_65e8e691cc0566bb5a42b0a6799d113f915476b7c4df9fbe79f2b9b68a14d8dd | model_diagnostic |  |  |  |
| evidence_7675eced7b1619fa58ec34dd26d9dbdcaeae48591f1d6bbad4832c6ce9ff0067 | sample_quality | gdp_per_capita_current_usd, life_expectancy_at_birth, secondary_school_enrollment |  | MISSING_DATA_EXCLUSION |
| evidence_8f9de557412cb18444753007e0e89b1337da5ea3879dd22cd849ef7705556d8a | analysis_warning | gdp_per_capita_current_usd, life_expectancy_at_birth, secondary_school_enrollment |  | MISSING_DATA_EXCLUSION |
| evidence_909a48f1eb70c15a8224729c8a7c4697e26725077d58c5bbaac12878fd2314db | model_diagnostic |  |  |  |
| evidence_bafbd8c43e50073bf15c2204e438e602c1da0ba66b254397b4faa72b902ebec2 | model_diagnostic |  |  | RESIDUAL_NORMALITY_WARNING |
| evidence_d7edb8a78bfc39d1c3b4ead0cf048f432ed8f3659c93f4ce90627db449175dd3 | model_diagnostic |  |  | HETEROSKEDASTICITY_WARNING |

| Claim ID | Type | Evidence IDs | Direction | Causal | Scope |
| --- | --- | --- | --- | --- | --- |
| claim_14f52396489324529ec6106508a55205de81a428ff93748ad6ed8696393c31e3 | model_limitation | evidence_bafbd8c43e50073bf15c2204e438e602c1da0ba66b254397b4faa72b902ebec2 | not_applicable | false | analysis_sample |
| claim_70a2a3cbc7c021b65693294c987770d26f76bad7ceb4d879ec16c9bd9e6b7ec7 | statistical_uncertainty | evidence_063ea9d11602cc9867c3620c897722443607a33e23ae23768d0caa99595df897 | not_applicable | false | analysis_sample |
| claim_70c01379cffc9e280e5b78b8e49953893113c046ca8b46579d6bdfd9788a3285 | conditional_association | evidence_20f0d5d5d5f63329b2bc82ee6f530b6df3071bbb7e3648dacce39cafe4529240 | positive | false | analysis_sample |
| claim_8d7639b85d7ed35267215ee5efdef12ddef822bd0235d4af91341502a9a057fa | conditional_association | evidence_470478571848831cca35c1665cac562dd1543d2cd0778a8f1a083c5728b4f912 | positive | false | analysis_sample |
| claim_b6ba49773c39e13f2e3cb512b4bd9c7ee46cf95c7659df753222f752e1b5ac05 | statistical_uncertainty | evidence_20f0d5d5d5f63329b2bc82ee6f530b6df3071bbb7e3648dacce39cafe4529240 | not_applicable | false | analysis_sample |
| claim_bf5e548d3b3304b563047f53cba9e46772b1b099181fd54ad612b1896579e1e2 | model_limitation | evidence_d7edb8a78bfc39d1c3b4ead0cf048f432ed8f3659c93f4ce90627db449175dd3 | not_applicable | false | analysis_sample |
| claim_d4296edb211368b0d83e941dceafd394c105abb1af5a70def453cd575faf7988 | statistical_uncertainty | evidence_470478571848831cca35c1665cac562dd1543d2cd0778a8f1a083c5728b4f912 | not_applicable | false | analysis_sample |

## Domain Assessments

| Domain | Supplied | Coverage | Evidence | Claims | Unsupported |
| --- | --- | --- | --- | --- | --- |
| governance | true | no_relevant_evidence | 0 | 0 | causality, intervention_recommendation, mechanism, policy_effectiveness, temporal_prediction |
| economics | true | relevant_evidence | 7 | 5 | causality, intervention_recommendation, mechanism, policy_effectiveness, population_wide_generalization, temporal_prediction |
| education | true | relevant_evidence | 7 | 5 | causality, intervention_recommendation, mechanism, policy_effectiveness, population_wide_generalization, temporal_prediction |
| public_health | true | relevant_evidence | 6 | 5 | causality, intervention_recommendation, mechanism, medical_conclusion, policy_effectiveness, population_wide_generalization, temporal_prediction |

## Cross-Domain Synthesis

The coordinated assessment contains 8 referenced evidence records and 5 referenced non-causal claim candidates across governance, economics, education, public_health. Unsupported inference boundaries remain active, including causal inference.

| Finding ID | Domains | Claim IDs | Evidence IDs |
| --- | --- | --- | --- |
| cross_synthesis_388cf343351aa21499c1d490f0cc4a226fd3541af0799a8e75787d3291c441cc | economics, education, public_health | claim_d4296edb211368b0d83e941dceafd394c105abb1af5a70def453cd575faf7988 |  |
| cross_synthesis_4691935cda654d3deaef4da1f789475025766b8cb84398a0526f873af42c104c | economics, education, public_health |  | evidence_7675eced7b1619fa58ec34dd26d9dbdcaeae48591f1d6bbad4832c6ce9ff0067 |
| cross_synthesis_4edb4e1aae030dc62f5ff89c6d492ce02a14085ff2c13acb67fc07e9749909e6 | economics, education, public_health |  | evidence_8f9de557412cb18444753007e0e89b1337da5ea3879dd22cd849ef7705556d8a |
| cross_synthesis_67e3f491b0376daeb8946e4073f579c7c40a531cd9d9ad0c8e9c30727f99c08f | economics, education, public_health | claim_70c01379cffc9e280e5b78b8e49953893113c046ca8b46579d6bdfd9788a3285 |  |
| cross_synthesis_6db8f2faccd2dffa16a95a06c41624f4737407f8aeffbbf188de6d619cdcf12e | economics, education, public_health |  | evidence_38a19f90c1ce4d79762fd3e2fd7f026f3bfeb2b1f547f1a72feef113cde5bdb4 |
| cross_synthesis_730c6b43a6fd4f35d59c2f950bb568c0d318f7b935a61ede34bf8c88d4c4f225 | economics, education, public_health |  | evidence_470478571848831cca35c1665cac562dd1543d2cd0778a8f1a083c5728b4f912 |
| cross_synthesis_88859336c8471d6dbbfa407b0fc5139ff5dcd44b66a7f2b1e957a9ac839d1f9b | economics, education, public_health | claim_70a2a3cbc7c021b65693294c987770d26f76bad7ceb4d879ec16c9bd9e6b7ec7 |  |
| cross_synthesis_8c5a173912ad1a1c99e1c56f53947314a1fbb949050fcdd4d01872f934d00d1d | economics, education, public_health | claim_b6ba49773c39e13f2e3cb512b4bd9c7ee46cf95c7659df753222f752e1b5ac05 |  |
| cross_synthesis_9c28471b6cf187f6f79e38a723972c5647740aadd7fad065f7fe373babf9ac58 | economics, education, public_health | claim_8d7639b85d7ed35267215ee5efdef12ddef822bd0235d4af91341502a9a057fa |  |
| cross_synthesis_d6240ba1df917642c72878c2330e88274513c16ecc05d94635ee5cf598f72e98 | economics, education, public_health |  | evidence_063ea9d11602cc9867c3620c897722443607a33e23ae23768d0caa99595df897 |
| cross_synthesis_ed8a5bc1575a84c67e42d662e75596352bfd6f0130961f5c85d1b1c373c547e6 | economics, education, public_health |  | evidence_20f0d5d5d5f63329b2bc82ee6f530b6df3071bbb7e3648dacce39cafe4529240 |

## Phase 8 Synthesis

The coordinated assessment contains 8 referenced evidence records and 5 referenced non-causal claim candidates across governance, economics, education, public_health. Unsupported inference boundaries remain active, including causal inference.

| Domain | Summary | Claims | Evidence |
| --- | --- | --- | --- |
| governance | governance was supplied with no relevant evidence and should not be described as producing substantive evidence in this synthesis. |  |  |
| economics | economics selected 7 evidence references and 5 claim references from the coordinated assessment. These references support cautious association-oriented synthesis only. | claim_70a2a3cbc7c021b65693294c987770d26f76bad7ceb4d879ec16c9bd9e6b7ec7, claim_70c01379cffc9e280e5b78b8e49953893113c046ca8b46579d6bdfd9788a3285, claim_8d7639b85d7ed35267215ee5efdef12ddef822bd0235d4af91341502a9a057fa, claim_b6ba49773c39e13f2e3cb512b4bd9c7ee46cf95c7659df753222f752e1b5ac05, claim_d4296edb211368b0d83e941dceafd394c105abb1af5a70def453cd575faf7988 | evidence_063ea9d11602cc9867c3620c897722443607a33e23ae23768d0caa99595df897, evidence_20f0d5d5d5f63329b2bc82ee6f530b6df3071bbb7e3648dacce39cafe4529240, evidence_38a19f90c1ce4d79762fd3e2fd7f026f3bfeb2b1f547f1a72feef113cde5bdb4, evidence_42ffe918feb8de52ff0ec2ad4022816b051c838cdc0d9ea5870879e09b14d31b, evidence_470478571848831cca35c1665cac562dd1543d2cd0778a8f1a083c5728b4f912, evidence_7675eced7b1619fa58ec34dd26d9dbdcaeae48591f1d6bbad4832c6ce9ff0067, evidence_8f9de557412cb18444753007e0e89b1337da5ea3879dd22cd849ef7705556d8a |
| education | education selected 7 evidence references and 5 claim references from the coordinated assessment. These references support cautious association-oriented synthesis only. | claim_70a2a3cbc7c021b65693294c987770d26f76bad7ceb4d879ec16c9bd9e6b7ec7, claim_70c01379cffc9e280e5b78b8e49953893113c046ca8b46579d6bdfd9788a3285, claim_8d7639b85d7ed35267215ee5efdef12ddef822bd0235d4af91341502a9a057fa, claim_b6ba49773c39e13f2e3cb512b4bd9c7ee46cf95c7659df753222f752e1b5ac05, claim_d4296edb211368b0d83e941dceafd394c105abb1af5a70def453cd575faf7988 | evidence_063ea9d11602cc9867c3620c897722443607a33e23ae23768d0caa99595df897, evidence_1f7899d5f4dfcfa59ebb6b19823f25421491311688424d718e1e48040d9dbbf6, evidence_20f0d5d5d5f63329b2bc82ee6f530b6df3071bbb7e3648dacce39cafe4529240, evidence_38a19f90c1ce4d79762fd3e2fd7f026f3bfeb2b1f547f1a72feef113cde5bdb4, evidence_470478571848831cca35c1665cac562dd1543d2cd0778a8f1a083c5728b4f912, evidence_7675eced7b1619fa58ec34dd26d9dbdcaeae48591f1d6bbad4832c6ce9ff0067, evidence_8f9de557412cb18444753007e0e89b1337da5ea3879dd22cd849ef7705556d8a |
| public_health | public_health selected 6 evidence references and 5 claim references from the coordinated assessment. These references support cautious association-oriented synthesis only. | claim_70a2a3cbc7c021b65693294c987770d26f76bad7ceb4d879ec16c9bd9e6b7ec7, claim_70c01379cffc9e280e5b78b8e49953893113c046ca8b46579d6bdfd9788a3285, claim_8d7639b85d7ed35267215ee5efdef12ddef822bd0235d4af91341502a9a057fa, claim_b6ba49773c39e13f2e3cb512b4bd9c7ee46cf95c7659df753222f752e1b5ac05, claim_d4296edb211368b0d83e941dceafd394c105abb1af5a70def453cd575faf7988 | evidence_063ea9d11602cc9867c3620c897722443607a33e23ae23768d0caa99595df897, evidence_20f0d5d5d5f63329b2bc82ee6f530b6df3071bbb7e3648dacce39cafe4529240, evidence_38a19f90c1ce4d79762fd3e2fd7f026f3bfeb2b1f547f1a72feef113cde5bdb4, evidence_470478571848831cca35c1665cac562dd1543d2cd0778a8f1a083c5728b4f912, evidence_7675eced7b1619fa58ec34dd26d9dbdcaeae48591f1d6bbad4832c6ce9ff0067, evidence_8f9de557412cb18444753007e0e89b1337da5ea3879dd22cd849ef7705556d8a |

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
| coordination_evidence_gap_0a0c38bc8066e1b216f60065b9a64b528a96d09445e67b64b4adafea3a797eca | cross_domain_claim_with_limited_domain_coverage | claim_70a2a3cbc7c021b65693294c987770d26f76bad7ceb4d879ec16c9bd9e6b7ec7 | economics, education, public_health |
| coordination_evidence_gap_7459eea00e9537f72175e04cdf297529b51f89a9756c4116d6b815bcb5ed6d2f | cross_domain_claim_with_limited_domain_coverage | claim_b6ba49773c39e13f2e3cb512b4bd9c7ee46cf95c7659df753222f752e1b5ac05 | economics, education, public_health |
| coordination_evidence_gap_b21766ad7c2fabb04ded719b32e401a8102e07a22a7707b9e38747a90b59ab6d | cross_domain_claim_with_limited_domain_coverage | claim_8d7639b85d7ed35267215ee5efdef12ddef822bd0235d4af91341502a9a057fa | economics, education, public_health |
| coordination_evidence_gap_bcf062a743e4f0832ac87d50cdb7b5832bfd3b4a66108a58ff725c02e8786e12 | cross_domain_claim_with_limited_domain_coverage | claim_d4296edb211368b0d83e941dceafd394c105abb1af5a70def453cd575faf7988 | economics, education, public_health |
| coordination_evidence_gap_c989a98422208462d2def61fa192e0c62c4e97644cd8ba93ec84264d6a1219b3 | cross_domain_claim_with_limited_domain_coverage | claim_70c01379cffc9e280e5b78b8e49953893113c046ca8b46579d6bdfd9788a3285 | economics, education, public_health |
| coordination_evidence_gap_08fbeb99f4382398c257a78166e8c0b185c96b28bb06ad7996970090edc55181 | evidence_referenced_without_cross_domain_context | evidence_42ffe918feb8de52ff0ec2ad4022816b051c838cdc0d9ea5870879e09b14d31b | economics |
| coordination_evidence_gap_8edb52a86f3e63ccace2d10961ce6b192c892f84648e07f4d3aa1ac599f8c141 | evidence_referenced_without_cross_domain_context | evidence_1f7899d5f4dfcfa59ebb6b19823f25421491311688424d718e1e48040d9dbbf6 | education |

| Gap ID | Type | Domain | Assessment supplied |
| --- | --- | --- | --- |
| coordination_domain_gap_c9e63a4ccc57d28d9be7245855b73d2c9a9ad4e641dd42e4aca177f658bd8758 | domain_has_no_relevant_evidence | governance | true |

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
| Source dataset | world_bank_wdi_real_validation_00f44391cafe |
| Phase 3 DatasetIngestionResult | world_bank_wdi_real_validation_00f44391cafe |
| Phase 4 AnalysisResult | analysis_8941d97c320b46d0ef37a9128be7fa4a7228906673f89a08b0408d0efb11516f |
| Phase 5 EvidenceArtifact | evidence_artifact_c8f460e6bcd957bbe38aed15b02a8912f88da16c168305161e9affe1fe7a4892 |
| Phase 6 AgentAssessments | agent_assessment_7d537324c35569dae9785f5331f300da931568ef6b5f5337253737db9213b547, agent_assessment_b6fe41e601ecfac5b043f0c11f8bece28415f0f6fb90c89614988079762c9cf8, agent_assessment_d061f76efdbc6974fff26e95ec5fc5d4a9296e85877f78611fd730fd8b9688a2, agent_assessment_dd949259dacc461d2ce48f5161ab4c8cf32e130a7c5f8bf8f5bf8cc095ce39ca |
| Phase 7 CoordinatedAssessment | coordinated_assessment_434794799b37d91232a038e7c2647c1892395e5ed946cb448baa02d0e87043e8 |
| Phase 8 SynthesisArtifact | synthesis_e9ba8a29952686c80e230273ab4b59b0b1f701830ddd2f4d2b853b0afc7c547c |
| Phase 9 ResearchReport | report_072af00adec897f1b304e0264465dfcd754e2d1813bbf36020b087828243d57f |

## Reference Index

| Reference ID | Kind | Label |
| --- | --- | --- |
| coordination_agreement_02785ee8f225ec8de1931cdd5edaffce056f25f29ebb9217825e19bdfb086d1d | agreement | Coordination agreement: shared_domain_concern |
| coordination_agreement_0785a9da7f590a0cb86ff3cda0f2aabf08d0ed58509f32595f38d076ecc70aa6 | agreement | Coordination agreement: shared_domain_concern |
| coordination_agreement_0d5c20c6a2eb647677bff281af55401291b4352a2d1e74f54003feff9008ab4d | agreement | Coordination agreement: shared_unsupported_inference |
| coordination_agreement_0e6158669c3a5e2f495bd5e11c32ad03810ec1d7416eb442e811e15c4dcd143c | agreement | Coordination agreement: shared_unsupported_inference |
| coordination_agreement_158aa496e2dd6c5ade1202e6173f8b40f80ab6d33722611e0f599a7fc81cf5b3 | agreement | Coordination agreement: shared_evidence |
| coordination_agreement_16c70088ff6c3c3b839dbf967eddc79a72949c8977307b756f4bb1e2a4c3a958 | agreement | Coordination agreement: shared_domain_concern |
| coordination_agreement_1c8f76de93d4c166a9f7c017c71ccc73fb9fb84e8821d4b544a5bd07589d6ab3 | agreement | Coordination agreement: shared_evidence |
| coordination_agreement_2793a57d85d1b5ec775e38f45de8785433d1f1e5f8199a3aedd511a9d1489af2 | agreement | Coordination agreement: shared_unsupported_inference |
| coordination_agreement_317ccbf082badbab4c7343679ce3f4043fb757b6b3ab39a953357117b1d5117d | agreement | Coordination agreement: shared_unsupported_inference |
| coordination_agreement_31ee2b1ad702b23f635d06641a8c5a36c71a2ae23836068808811c50e0b7759b | agreement | Coordination agreement: shared_unsupported_inference |
| coordination_agreement_46c38435a04df7e74167712302e02e19bd0f50cdfda6910bf63d2aba765cdcd2 | agreement | Coordination agreement: shared_claim |
| coordination_agreement_4d53c2aca9dcc68240ac51bc8743e2ad1eecb5f7f15ec7478ac5c62ef0ca3df7 | agreement | Coordination agreement: shared_evidence |
| coordination_agreement_53af29fe6454d0a88f8e51d541915d007a0abe12b57aeca8101aa53f577a1afa | agreement | Coordination agreement: shared_limitation |
| coordination_agreement_556ff2f55d96b6082ef2db3225e78838314472c3a32ecabd2ebcf015ac00645a | agreement | Coordination agreement: shared_domain_concern |
| coordination_agreement_59a0010622d478a874d7f8503066153e84cbb9b54573ea5f0b14746f06c2e745 | agreement | Coordination agreement: shared_domain_concern |
| coordination_agreement_60ef4cf61bbb29945865da4454834de6a58702b656a4afc0745074311ffe9452 | agreement | Coordination agreement: shared_domain_concern |
| coordination_agreement_6ab1ea4e257e86c72d44288b6814a7abc72f05297b740a247784f848b6b7ce2d | agreement | Coordination agreement: shared_domain_concern |
| coordination_agreement_6af40b1f1e0a7842e31fd7b49cd3267800fab1afc2152a684a8a9a5c16f77f42 | agreement | Coordination agreement: shared_evidence |
| coordination_agreement_75b019702e00e1d111b4f9cfcffa2142308c7f5dda7f181c1b209cdc241facd3 | agreement | Coordination agreement: shared_claim |
| coordination_agreement_790f5a12043ef2ffb2e7b549390e57679e90ad29ac60d227c88d63c4c0ca1ad4 | agreement | Coordination agreement: shared_domain_concern |
| coordination_agreement_7b74ed99c9d49794fd083e3ba9d6f03c98a5b34f56185c35e46cf5d135586af9 | agreement | Coordination agreement: shared_limitation |
| coordination_agreement_8f81e2855a3ab110059911fe530d80b4aa711ba5f10d8be0a722e112b3d4e628 | agreement | Coordination agreement: shared_domain_concern |
| coordination_agreement_92dbc1753ba2228e1b02e2d3201f671de8dda07f0e30112f23e2388d5657e91f | agreement | Coordination agreement: shared_claim |
| coordination_agreement_9bef5c426f7b40d6565aced8f60d1bccc247d61189a50057f3b39d5a52ec2326 | agreement | Coordination agreement: shared_limitation |
| coordination_agreement_aa90c940e479aa222e5c6072100f148f5bc303820338d3b8598985af64314cfc | agreement | Coordination agreement: shared_evidence |
| coordination_agreement_aaeb5839d3f196f528aea51833dbdb51718492377b5d08c48ebe7055cacc66e2 | agreement | Coordination agreement: shared_limitation |
| coordination_agreement_aefc9822a00d44a2cbdd9852e561fd2a33180436357b97617c8c4174bbd124b1 | agreement | Coordination agreement: shared_unsupported_inference |
| coordination_agreement_b53d18adf0905707f546a980c2e350778f3dd3d9b3125a87dba9d718efb8293c | agreement | Coordination agreement: shared_claim |
| coordination_agreement_c0311635e0ed6b098bdc7443d27d934ac9d85a2a52577032e1263929b7f1bf0c | agreement | Coordination agreement: shared_limitation |
| coordination_agreement_e43130726f00e83bff182618642e064ab722b19c98d421a171cabe732f29b593 | agreement | Coordination agreement: shared_limitation |
| coordination_agreement_ef11473b4949b8cce545743039fb925d2db239e98337bb5341e68eaaf3818d0b | agreement | Coordination agreement: shared_evidence |
| coordination_agreement_f34133ef6363aa72a0aa53da6b73a84e6dd621bc99a074b915cac8415ec4ca1f | agreement | Coordination agreement: shared_claim |
| coordination_agreement_fd3cf8887ff29b4b991344879c2c275d97f06664887844b85c58ff6f81326e17 | agreement | Coordination agreement: shared_domain_concern |
| agent_assessment_7d537324c35569dae9785f5331f300da931568ef6b5f5337253737db9213b547 | assessment | Domain assessment: governance |
| agent_assessment_b6fe41e601ecfac5b043f0c11f8bece28415f0f6fb90c89614988079762c9cf8 | assessment | Domain assessment: public_health |
| agent_assessment_d061f76efdbc6974fff26e95ec5fc5d4a9296e85877f78611fd730fd8b9688a2 | assessment | Domain assessment: economics |
| agent_assessment_dd949259dacc461d2ce48f5161ab4c8cf32e130a7c5f8bf8f5bf8cc095ce39ca | assessment | Domain assessment: education |
| claim_14f52396489324529ec6106508a55205de81a428ff93748ad6ed8696393c31e3 | claim | Claim candidate: model_limitation |
| claim_70a2a3cbc7c021b65693294c987770d26f76bad7ceb4d879ec16c9bd9e6b7ec7 | claim | Claim candidate: statistical_uncertainty |
| claim_70c01379cffc9e280e5b78b8e49953893113c046ca8b46579d6bdfd9788a3285 | claim | Claim candidate: conditional_association |
| claim_8d7639b85d7ed35267215ee5efdef12ddef822bd0235d4af91341502a9a057fa | claim | Claim candidate: conditional_association |
| claim_b6ba49773c39e13f2e3cb512b4bd9c7ee46cf95c7659df753222f752e1b5ac05 | claim | Claim candidate: statistical_uncertainty |
| claim_bf5e548d3b3304b563047f53cba9e46772b1b099181fd54ad612b1896579e1e2 | claim | Claim candidate: model_limitation |
| claim_d4296edb211368b0d83e941dceafd394c105abb1af5a70def453cd575faf7988 | claim | Claim candidate: statistical_uncertainty |
| coordination_divergence_06bc3927bd437c4e80c48c884884500efb9cef168613c6f43a6434237ba38904 | divergence | Coordination divergence: different_relevance_classification |
| coordination_divergence_083941fddd7551a2333f2c9513b80346596e5751493463e1ec34349990014442 | divergence | Coordination divergence: domain_specific_concern |
| coordination_divergence_08b3c6e01d19f8147b3344b0be9e61d2cfa91db3a0ecc4b9f87bef34029498eb | divergence | Coordination divergence: uneven_evidence_coverage |
| coordination_divergence_0ad191a5cb623d0e6f0e3f86cf814466d6a66b3cee08b3b9d5984e133198be4f | divergence | Coordination divergence: uneven_evidence_coverage |
| coordination_divergence_1714f98c5c21613bd0acaae9815909a36ae48257e5b6a64da7cfae09f9a7ba2f | divergence | Coordination divergence: domain_specific_concern |
| coordination_divergence_1721974c1d96782bba0a40e646cb55d1072dbda4de7257663209f3a847468d33 | divergence | Coordination divergence: domain_specific_concern |
| coordination_divergence_18a213866a5da6161eae45da6eeb8966cba33b9e2f21b5c8fd5657e6d34e5c50 | divergence | Coordination divergence: uneven_evidence_coverage |
| coordination_divergence_1c278c146080b6f10001e48570c620cee46c45f2a97e8e12eb2db1ddbeea02b7 | divergence | Coordination divergence: domain_specific_concern |
| coordination_divergence_1d574feaf862ee69adcab1384588fe2d5282d8620bdad4de94e3b220fc607824 | divergence | Coordination divergence: uneven_evidence_coverage |
| coordination_divergence_24209fb13c75224ae30dfacd0d4575d715b623a82d761423556c94329639672f | divergence | Coordination divergence: different_relevance_classification |
| coordination_divergence_2e2254bbc5b2dd5e1551d5f98e44b2eee6d704f8373c04230c44634825852e51 | divergence | Coordination divergence: uneven_evidence_coverage |
| coordination_divergence_3cd1948088bc482aa65a9455491ca807ecd5e40b3494fadd19488d7213a27871 | divergence | Coordination divergence: domain_specific_limitation |
| coordination_divergence_497fddf6d6ac0fa589b0bcf1a7ebe17c5c55fdea7e5eaed3da40cb36f9239c01 | divergence | Coordination divergence: different_relevance_classification |
| coordination_divergence_56fcc214f0f90b7980170c19c960d652a416976feaee8c61a726a15c4b7df5f8 | divergence | Coordination divergence: domain_specific_unsupported_inference |
| coordination_divergence_5b179f3b74b89138f161253591649ffd62761f39c970f2a4d6ef39b099b077d2 | divergence | Coordination divergence: uneven_evidence_coverage |
| coordination_divergence_5d01a16ebb90b928532bb2e613ada447b46e0850222663bb729406d3d642cdaa | divergence | Coordination divergence: domain_specific_limitation |
| coordination_divergence_5f3b8f69c2465b9497e517801aab17fe9d5736953c5082aadb23018dafdf8a6f | divergence | Coordination divergence: domain_specific_unsupported_inference |
| coordination_divergence_609dedd3e8e81c6db9e467ecb054b983dda80530cef240214c7e846f93d0b21c | divergence | Coordination divergence: different_relevance_classification |
| coordination_divergence_6845d66c11d0e26dd68c598a5336ee9eaeecc52a5996b2669b1d5f180f371ac8 | divergence | Coordination divergence: different_relevance_classification |
| coordination_divergence_6868002ac9fcfcb4bda0d47a20f6a15df4dd16e9bd43f71edde08cb91c664dc6 | divergence | Coordination divergence: uneven_evidence_coverage |
| coordination_divergence_68fc234e1502df267c2b9096a346bc9e7b9f1459bed8360c36499695d8599543 | divergence | Coordination divergence: domain_specific_concern |
| coordination_divergence_78171e07806ef8ad7c61921452ac6c4119cb3e24e2d2e5113162b55293145083 | divergence | Coordination divergence: different_relevance_classification |
| coordination_divergence_7b977d28b8482c323a86f990880272f407ac5d74e305389c7a4b4b8ee5a2fcc7 | divergence | Coordination divergence: uneven_evidence_coverage |
| coordination_divergence_7e47e1fa4b88d53714fedaace54b2d756470c1600871662252d115d3db269106 | divergence | Coordination divergence: domain_specific_limitation |
| coordination_divergence_84cfadd722d968888121201c6871d55b9bff2691124d6ef84ecc469ff95f3cac | divergence | Coordination divergence: uneven_evidence_coverage |
| coordination_divergence_968717e9480da01b935011880d310c75d2ff859adb93fb2a60d22b1639ee5b0d | divergence | Coordination divergence: domain_specific_limitation |
| coordination_divergence_9af5b6926acea8df2b9b2fdb59e1b08431e01b21de466172102349b042a45b62 | divergence | Coordination divergence: uneven_evidence_coverage |
| coordination_divergence_9c13bc8711b8293e3f7e8c1909d3931f9e8969125c991afd440ec9268c11f319 | divergence | Coordination divergence: domain_specific_concern |
| coordination_divergence_a1ebba174ad0964b939520454b6eee6be610d13dfe6caf3d439200bf3424f07d | divergence | Coordination divergence: different_relevance_classification |
| coordination_divergence_a31e7eb629425f069b3ee0984f51252781a8bbc9482f9b939c050df19b9cab38 | divergence | Coordination divergence: domain_specific_concern |
| coordination_divergence_a380ceb298ae9d9786ecf6a9b97d825832adc535896bb8894e8a7a32db2e53fe | divergence | Coordination divergence: different_relevance_classification |
| coordination_divergence_a705deb9a32326023d98f87420de5b9a77a19f13681db412ed5cc698835d44bc | divergence | Coordination divergence: uneven_evidence_coverage |
| coordination_divergence_acb3141870f3656d18096b04af90221a09cb840a0572e6708bc685af7a5e9eee | divergence | Coordination divergence: domain_specific_concern |
| coordination_divergence_aed35ddb77e47006b51b3cbe8167216a51e40ae2d08337182c072e2603b0717d | divergence | Coordination divergence: different_relevance_classification |
| coordination_divergence_b1a71e79fdcbd3b959d9719ed15b366b508112dd9494c42588c70fefee5f5ea7 | divergence | Coordination divergence: domain_specific_concern |
| coordination_divergence_c423bb27a98ec6d0e51ec3e8eb1e603f1a652956e08cccb8dbfc9ebc1a31b134 | divergence | Coordination divergence: domain_specific_concern |
| coordination_divergence_c6a2b6756da845b850a4cc49a3d9b6d9c381d4ae46dfb7255c64fff755bfd1eb | divergence | Coordination divergence: domain_specific_limitation |
| coordination_divergence_c713adc72be431bf0938b1f017187e695bc63331c3da4dcd6d8a794c81c6ce02 | divergence | Coordination divergence: different_relevance_classification |
| coordination_divergence_d1fdf17e74d13e40c901ed253b57294ceb8ce0a610bb8d4f8e9cbecbd7100ed2 | divergence | Coordination divergence: uneven_evidence_coverage |
| coordination_divergence_dfd513e7181cfcdc18bd9d8d657c0c3c124563f85cdbb2fd7e47251aa9a2cc41 | divergence | Coordination divergence: uneven_evidence_coverage |
| coordination_divergence_e98c7fdf4bfc20b6355055ea00ba2982556c44d4806ddc1b08b82ff4bb9dff32 | divergence | Coordination divergence: different_relevance_classification |
| coordination_divergence_e99cb6130f41eab72d8002970ef80da8d582084ba6c247c1c1ef3fc7412da660 | divergence | Coordination divergence: different_relevance_classification |
| coordination_divergence_ee5d4a11595dae9ab8dfafe247586b1d728ed4311511c9e52c53c95cfa3e423a | divergence | Coordination divergence: domain_specific_concern |
| coordination_divergence_f7c2e8f34622efe71a93b86f52fddb5ec7589cf9d6ca2fe78237964f63d4ffd3 | divergence | Coordination divergence: different_relevance_classification |
| coordination_divergence_f82ed5e670d3e834dee8fb002d622ad5d11aa4834de7dcf86dd6b835fcbbdc50 | divergence | Coordination divergence: domain_specific_limitation |
| evidence_063ea9d11602cc9867c3620c897722443607a33e23ae23768d0caa99595df897 | evidence | Evidence record: regression_coefficient |
| evidence_1f7899d5f4dfcfa59ebb6b19823f25421491311688424d718e1e48040d9dbbf6 | evidence | Evidence record: model_diagnostic |
| evidence_20f0d5d5d5f63329b2bc82ee6f530b6df3071bbb7e3648dacce39cafe4529240 | evidence | Evidence record: regression_coefficient |
| evidence_38a19f90c1ce4d79762fd3e2fd7f026f3bfeb2b1f547f1a72feef113cde5bdb4 | evidence | Evidence record: model_fit |
| evidence_4187048a52dfa7c69a3f6ecee0e3d7a31dbcfcd6da3308f734c878e6a3062465 | evidence | Evidence record: model_diagnostic |
| evidence_42ffe918feb8de52ff0ec2ad4022816b051c838cdc0d9ea5870879e09b14d31b | evidence | Evidence record: model_diagnostic |
| evidence_470478571848831cca35c1665cac562dd1543d2cd0778a8f1a083c5728b4f912 | evidence | Evidence record: regression_coefficient |
| evidence_65e8e691cc0566bb5a42b0a6799d113f915476b7c4df9fbe79f2b9b68a14d8dd | evidence | Evidence record: model_diagnostic |
| evidence_7675eced7b1619fa58ec34dd26d9dbdcaeae48591f1d6bbad4832c6ce9ff0067 | evidence | Evidence record: sample_quality |
| evidence_8f9de557412cb18444753007e0e89b1337da5ea3879dd22cd849ef7705556d8a | evidence | Evidence record: analysis_warning |
| evidence_909a48f1eb70c15a8224729c8a7c4697e26725077d58c5bbaac12878fd2314db | evidence | Evidence record: model_diagnostic |
| evidence_bafbd8c43e50073bf15c2204e438e602c1da0ba66b254397b4faa72b902ebec2 | evidence | Evidence record: model_diagnostic |
| evidence_d7edb8a78bfc39d1c3b4ead0cf048f432ed8f3659c93f4ce90627db449175dd3 | evidence | Evidence record: model_diagnostic |
| coordination_domain_gap_c9e63a4ccc57d28d9be7245855b73d2c9a9ad4e641dd42e4aca177f658bd8758 | gap | Domain gap: governance |
| coordination_evidence_gap_08fbeb99f4382398c257a78166e8c0b185c96b28bb06ad7996970090edc55181 | gap | Evidence gap: evidence_referenced_without_cross_domain_context |
| coordination_evidence_gap_0a0c38bc8066e1b216f60065b9a64b528a96d09445e67b64b4adafea3a797eca | gap | Evidence gap: cross_domain_claim_with_limited_domain_coverage |
| coordination_evidence_gap_7459eea00e9537f72175e04cdf297529b51f89a9756c4116d6b815bcb5ed6d2f | gap | Evidence gap: cross_domain_claim_with_limited_domain_coverage |
| coordination_evidence_gap_8edb52a86f3e63ccace2d10961ce6b192c892f84648e07f4d3aa1ac599f8c141 | gap | Evidence gap: evidence_referenced_without_cross_domain_context |
| coordination_evidence_gap_b21766ad7c2fabb04ded719b32e401a8102e07a22a7707b9e38747a90b59ab6d | gap | Evidence gap: cross_domain_claim_with_limited_domain_coverage |
| coordination_evidence_gap_bcf062a743e4f0832ac87d50cdb7b5832bfd3b4a66108a58ff725c02e8786e12 | gap | Evidence gap: cross_domain_claim_with_limited_domain_coverage |
| coordination_evidence_gap_c989a98422208462d2def61fa192e0c62c4e97644cd8ba93ec84264d6a1219b3 | gap | Evidence gap: cross_domain_claim_with_limited_domain_coverage |
| analysis_8941d97c320b46d0ef37a9128be7fa4a7228906673f89a08b0408d0efb11516f | source_artifact | Source Polaris artifact |
| coordinated_assessment_434794799b37d91232a038e7c2647c1892395e5ed946cb448baa02d0e87043e8 | source_artifact | Source Polaris artifact |
| evidence_artifact_c8f460e6bcd957bbe38aed15b02a8912f88da16c168305161e9affe1fe7a4892 | source_artifact | Source Polaris artifact |
| synthesis_e9ba8a29952686c80e230273ab4b59b0b1f701830ddd2f4d2b853b0afc7c547c | source_artifact | Source Polaris artifact |
| world_bank_wdi_real_validation_00f44391cafe | source_artifact | Source Polaris artifact |
