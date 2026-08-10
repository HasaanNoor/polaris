# Phase 15 WDI plus WHO Health Panel Example

Associational validation using local derived data

## Metadata

| Field | Value |
| --- | --- |
| Report ID | report_a7b64efce8be89a2ae7658f38df5db2864a6ed0f85659b3c3cc5a37e41b016c3 |
| Generated | 2026-08-10T22:34:05.478218+00:00 |
| Dataset ID | harmonized_country_year_9ebd53aede15593f |
| Source checksum | 5abc828b92aa6597cbe585d0de21c3a98423626fe2eb6254019f36ad6d9adfbd |
| Analysis procedure | pearson_correlation |
| Synthesis mode | deterministic |
| Ruleset | deterministic_phase9_v1 |

## Executive Summary

The coordinated assessment contains 2 referenced evidence records and 1 referenced non-causal claim candidates across economics, public_health. Domain coverage is incomplete; governance, education was not represented. Unsupported inference boundaries remain active, including causal inference. The report preserves observational and non-causal boundaries from upstream artifacts. Domain coverage is incomplete. No external literature or outside contextual evidence has been integrated.

## Research Question

| Field | Value |
| --- | --- |
| Question ID | rq_phase15_wdi_who_health_capacity |
| Primary question | How are national income and healthcare-system capacity associated with life expectancy across countries? |
| Population | Country-year observations in the Phase 15 WDI plus WHO derived sample |
| Variables | wdi_gdp_per_capita_current_usd, who_health_expenditure_pct_gdp, who_life_expectancy_birth_years |
| Methods | pearson_correlation |

## Dataset and Source

| Field | Value |
| --- | --- |
| Dataset ID | harmonized_country_year_9ebd53aede15593f |
| Title | Phase 12 Harmonized Country-Year Dataset |
| Provider | Polaris derived harmonization |
| Source type | local_csv |
| Checksum | 5abc828b92aa6597cbe585d0de21c3a98423626fe2eb6254019f36ad6d9adfbd |
| Accepted rows | 3 |
| Rejected rows | 0 |
| Analysis ready | true |
| Illustrative | false |
| Variables | who_life_expectancy_birth_years, wdi_gdp_per_capita_current_usd |

## Methodology

| Field | Value |
| --- | --- |
| Ingestion and validation | Local CSV ingestion mapped source columns to the supplied manifest, normalized supported scalar values, validated structure, and computed a SHA-256 checksum. |
| Sample construction | Phase 4 used complete-case sample construction from accepted Phase 3 records. |
| Procedure | pearson_correlation |
| Dependent variable | who_life_expectancy_birth_years |
| Predictors | wdi_gdp_per_capita_current_usd |
| Controls |  |
| Include intercept |  |
| Confidence level | 0.95 |
| Significance threshold |  |
| Diagnostics calculated |  |
| Evidence extraction | Phase 5 extracted 2 evidence records and 1 bounded non-causal claim candidates. |
| Domain agents | Phase 6 deterministic domain agents selected relevant structured evidence and claim IDs without adding outside context. |
| Coordination | Phase 7 coordinated 2 domain assessments by reference. |
| Synthesis mode | deterministic |
| Grounding and validation | Phase 8 synthesis supplied validated summaries with fabricated-reference, limitation-preservation, unsupported-inference, and overreach checks. |

## Statistical Results

| Field | Value |
| --- | --- |
| Analysis result ID | analysis_5f6a512478fca829789e00f529a7a9203f6fb6c74ddb0a0e95118fe73e1a0968 |
| Method | pearson_correlation |
| Sample size | 3 |

| Variable 1 | Variable 2 | Method | N | Coefficient | p-value | Defined |
| --- | --- | --- | --- | --- | --- | --- |
| who_life_expectancy_birth_years | wdi_gdp_per_capita_current_usd | pearson | 3 | -0.8536950386332818 | 0.34871260090946704 | true |

## Evidence and Claims

| Evidence ID | Type | Variables | Direction | Limitations |
| --- | --- | --- | --- | --- |
| evidence_36506b76936454fd47e1bc5d58f4bf1935e6f9057c3a5b69aee990a918120ed5 | correlation | wdi_gdp_per_capita_current_usd, who_life_expectancy_birth_years | negative |  |
| evidence_ca47f0e58ab381c6f2f455a34bdfb5c18655ce733354c4a8e51e8de98fdd112c | sample_quality | wdi_gdp_per_capita_current_usd, who_life_expectancy_birth_years |  |  |

| Claim ID | Type | Evidence IDs | Direction | Causal | Scope |
| --- | --- | --- | --- | --- | --- |
| claim_4d576a32dcb64cfe49e46ca874cc540751fa1785a84ec5bfb7b5320b76c514a1 | association | evidence_36506b76936454fd47e1bc5d58f4bf1935e6f9057c3a5b69aee990a918120ed5 | negative | false | analysis_sample |

## Domain Assessments

| Domain | Supplied | Coverage | Evidence | Claims | Unsupported |
| --- | --- | --- | --- | --- | --- |
| governance | false | assessment_missing | 0 | 0 |  |
| economics | true | relevant_evidence | 2 | 1 | causality, intervention_recommendation, mechanism, policy_effectiveness, population_wide_generalization, temporal_prediction |
| education | false | assessment_missing | 0 | 0 |  |
| public_health | true | relevant_evidence | 2 | 1 | causality, intervention_recommendation, mechanism, medical_conclusion, policy_effectiveness, population_wide_generalization, temporal_prediction |

## Cross-Domain Synthesis

The coordinated assessment contains 2 referenced evidence records and 1 referenced non-causal claim candidates across economics, public_health. Domain coverage is incomplete; governance, education was not represented. Unsupported inference boundaries remain active, including causal inference.

| Finding ID | Domains | Claim IDs | Evidence IDs |
| --- | --- | --- | --- |
| cross_synthesis_2fcd22fa378060c69b54f6aaf36d90903492c4c306009b744c40b5bf3e93ee2c | economics, public_health |  | evidence_ca47f0e58ab381c6f2f455a34bdfb5c18655ce733354c4a8e51e8de98fdd112c |
| cross_synthesis_51213d2860fd7981fcab647f81999fdf54d93889b128dd1e44952253b1eb1ca0 | economics, public_health |  | evidence_36506b76936454fd47e1bc5d58f4bf1935e6f9057c3a5b69aee990a918120ed5 |
| cross_synthesis_9dca6075f2f93b6010964aecaa7b64d24a3d8b8bdcd0d547d12e36b9c94aeaae | economics, public_health | claim_4d576a32dcb64cfe49e46ca874cc540751fa1785a84ec5bfb7b5320b76c514a1 |  |

## Phase 8 Synthesis

The coordinated assessment contains 2 referenced evidence records and 1 referenced non-causal claim candidates across economics, public_health. Domain coverage is incomplete; governance, education was not represented. Unsupported inference boundaries remain active, including causal inference.

| Domain | Summary | Claims | Evidence |
| --- | --- | --- | --- |
| governance | governance was not supplied and should not be described as producing substantive evidence in this synthesis. |  |  |
| economics | economics selected 2 evidence references and 1 claim references from the coordinated assessment. These references support cautious association-oriented synthesis only. | claim_4d576a32dcb64cfe49e46ca874cc540751fa1785a84ec5bfb7b5320b76c514a1 | evidence_36506b76936454fd47e1bc5d58f4bf1935e6f9057c3a5b69aee990a918120ed5, evidence_ca47f0e58ab381c6f2f455a34bdfb5c18655ce733354c4a8e51e8de98fdd112c |
| education | education was not supplied and should not be described as producing substantive evidence in this synthesis. |  |  |
| public_health | public_health selected 2 evidence references and 1 claim references from the coordinated assessment. These references support cautious association-oriented synthesis only. | claim_4d576a32dcb64cfe49e46ca874cc540751fa1785a84ec5bfb7b5320b76c514a1 | evidence_36506b76936454fd47e1bc5d58f4bf1935e6f9057c3a5b69aee990a918120ed5, evidence_ca47f0e58ab381c6f2f455a34bdfb5c18655ce733354c4a8e51e8de98fdd112c |

## Limitations

The report preserves upstream limitation codes and keeps interpretation bounded to structured, non-causal Polaris artifacts.

| Limitation Code |
| --- |
| OBSERVATIONAL_ASSOCIATION |
| UNSUPPORTED_GENERALIZATION |

## Evidence and Domain Gaps

| Gap ID | Type | Sources | Domains |
| --- | --- | --- | --- |
| coordination_evidence_gap_41df6e2d195109fce69cafa1bcb8013f192babfb5c27e00c73a733edc02c22e9 | cross_domain_claim_with_limited_domain_coverage | claim_4d576a32dcb64cfe49e46ca874cc540751fa1785a84ec5bfb7b5320b76c514a1 | economics, public_health |

| Gap ID | Type | Domain | Assessment supplied |
| --- | --- | --- | --- |
| coordination_domain_gap_2cda4ca8f7436f9f2c37185bda78a91223f6045f01a8d2a1090a39c37ae6b12f | domain_not_represented | governance | false |
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
| Source dataset | harmonized_country_year_9ebd53aede15593f |
| Phase 3 DatasetIngestionResult | harmonized_country_year_9ebd53aede15593f |
| Phase 4 AnalysisResult | analysis_5f6a512478fca829789e00f529a7a9203f6fb6c74ddb0a0e95118fe73e1a0968 |
| Phase 5 EvidenceArtifact | evidence_artifact_deeedfabe4bf507dba0b2b2e48ef35d38598c2effe09802b1fd75e7c996b0b51 |
| Phase 6 AgentAssessments | agent_assessment_73d00fcc12005ea49afd901bf69366bf5d49ea659792b7c743bb4c7af931101e, agent_assessment_b686b28ff371f019d675304273aeb0b93314f38a1bb876544400072a1a39028c |
| Phase 7 CoordinatedAssessment | coordinated_assessment_dc60394a5728d19a55a7bc41a8999e02cbb7ea1fb3a134cc9b073c16162de8ef |
| Phase 8 SynthesisArtifact | synthesis_e8677dd554f5995bbe865a29f383449ec4a9a9446c803a88e1def7fddafb6826 |
| Phase 9 ResearchReport | report_a7b64efce8be89a2ae7658f38df5db2864a6ed0f85659b3c3cc5a37e41b016c3 |

## Reference Index

| Reference ID | Kind | Label |
| --- | --- | --- |
| coordination_agreement_19bac76da4d19a4bb4ea96a0d41ed1aebdf26ba8515f1a9589fa2a03a0cdff3c | agreement | Coordination agreement: shared_unsupported_inference |
| coordination_agreement_2177966a2f8b828b7a1f8f2c33f9694161ab030a75d073ca48a171cbbca649fa | agreement | Coordination agreement: shared_unsupported_inference |
| coordination_agreement_27b0ddfbd6f50248977e16582897732360e92e7f1ea3452fe5cec6f72da1bb66 | agreement | Coordination agreement: shared_limitation |
| coordination_agreement_296f91d6a9d51eb1926a4c5dcdea4aaf05e6089e623595e15586155220b27b64 | agreement | Coordination agreement: shared_domain_concern |
| coordination_agreement_4489fbc07832c6a6819c36e1d6d522f3bff7abeeb5ad59864d50780c507cc1ac | agreement | Coordination agreement: shared_domain_concern |
| coordination_agreement_57837afaaaac25be4ba1802a18e6631da33f1c4229b62ef95a549924186ff805 | agreement | Coordination agreement: shared_domain_concern |
| coordination_agreement_6709034aa3635455a4775f0a2dd9a84600bd2de0e1ab44eafde53df0f6632583 | agreement | Coordination agreement: shared_domain_concern |
| coordination_agreement_6c81486ddb5c2b5d142cae02d62a16c1c13e9bcf4eafe9e66ba00f372db29c9c | agreement | Coordination agreement: shared_domain_concern |
| coordination_agreement_78a248346e028471ddd1e36473b16612509af5cc08cbf5449848ec10db73fa0d | agreement | Coordination agreement: shared_claim |
| coordination_agreement_79032f40c3bc03717ea6c93c3f1e6f61c92cbd83026f83463b44f557f5207d36 | agreement | Coordination agreement: shared_unsupported_inference |
| coordination_agreement_7eb1ed2b3a25663ea9107b0ac1077120945a8d9d93b506b795695f7707c14383 | agreement | Coordination agreement: shared_unsupported_inference |
| coordination_agreement_8dc57d02c4352a550dcc92cf91ddc34c421fff95d45618adeb817edd8140ec8e | agreement | Coordination agreement: shared_domain_concern |
| coordination_agreement_a280d727bb57dc763c23eefb79233b57c99c7a701d0f3149bf458504571b69c9 | agreement | Coordination agreement: shared_limitation |
| coordination_agreement_a766dcd4f0676e47771bd57fc9106aaa6b7d3c992ab13ce91950612c93554d33 | agreement | Coordination agreement: shared_unsupported_inference |
| coordination_agreement_ae2dc1491f99c147b5eeac9db293f3d31c3366243b0587a461feaa69f0a02f76 | agreement | Coordination agreement: shared_unsupported_inference |
| coordination_agreement_b3634bc2e3b6126743fea57d43e69e776d5c07be3e88ba40306f2a4aacb942d1 | agreement | Coordination agreement: shared_domain_concern |
| coordination_agreement_bb10a3a808fff07151585a085cf5a002c67d8ec16ebcff632c9fbbc8149c23d0 | agreement | Coordination agreement: shared_evidence |
| coordination_agreement_e652e40b839d3ef1c8050d2f8fc67579553bd7b231d585396a431c7289683537 | agreement | Coordination agreement: shared_evidence |
| agent_assessment_73d00fcc12005ea49afd901bf69366bf5d49ea659792b7c743bb4c7af931101e | assessment | Domain assessment: economics |
| agent_assessment_b686b28ff371f019d675304273aeb0b93314f38a1bb876544400072a1a39028c | assessment | Domain assessment: public_health |
| claim_4d576a32dcb64cfe49e46ca874cc540751fa1785a84ec5bfb7b5320b76c514a1 | claim | Claim candidate: association |
| coordination_divergence_5f3b8f69c2465b9497e517801aab17fe9d5736953c5082aadb23018dafdf8a6f | divergence | Coordination divergence: domain_specific_unsupported_inference |
| evidence_36506b76936454fd47e1bc5d58f4bf1935e6f9057c3a5b69aee990a918120ed5 | evidence | Evidence record: correlation |
| evidence_ca47f0e58ab381c6f2f455a34bdfb5c18655ce733354c4a8e51e8de98fdd112c | evidence | Evidence record: sample_quality |
| coordination_domain_gap_2cda4ca8f7436f9f2c37185bda78a91223f6045f01a8d2a1090a39c37ae6b12f | gap | Domain gap: governance |
| coordination_domain_gap_6dfe7972acbb582af0493c5f46d83f4e3889a6e76542b35463ba65e833d82d51 | gap | Domain gap: education |
| coordination_evidence_gap_41df6e2d195109fce69cafa1bcb8013f192babfb5c27e00c73a733edc02c22e9 | gap | Evidence gap: cross_domain_claim_with_limited_domain_coverage |
| analysis_5f6a512478fca829789e00f529a7a9203f6fb6c74ddb0a0e95118fe73e1a0968 | source_artifact | Source Polaris artifact |
| coordinated_assessment_dc60394a5728d19a55a7bc41a8999e02cbb7ea1fb3a134cc9b073c16162de8ef | source_artifact | Source Polaris artifact |
| evidence_artifact_deeedfabe4bf507dba0b2b2e48ef35d38598c2effe09802b1fd75e7c996b0b51 | source_artifact | Source Polaris artifact |
| harmonized_country_year_9ebd53aede15593f | source_artifact | Source Polaris artifact |
| synthesis_e8677dd554f5995bbe865a29f383449ec4a9a9446c803a88e1def7fddafb6826 | source_artifact | Source Polaris artifact |
