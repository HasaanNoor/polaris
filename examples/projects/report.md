# How is x associated with y?

## Metadata

| Field | Value |
| --- | --- |
| Report ID | report_79e6384869daa38aec4660a3e7fd020267c872f039f344ad47b3786d84fb15f8 |
| Generated | 2026-08-07T21:09:43.275722+00:00 |
| Dataset ID | harmonized_country_year_67e9b4ea18e4343d |
| Source checksum | 1495324ac7bf0315af5b83d94ac4f1309cd5b53788c8829554d39e7de06d1a09 |
| Analysis procedure | pearson_correlation |
| Synthesis mode | deterministic |
| Ruleset | deterministic_phase9_v1 |

## Executive Summary

The coordinated assessment contains 2 referenced evidence records and 1 referenced non-causal claim candidates across economics, public_health. Domain coverage is incomplete; governance, education was not represented. Unsupported inference boundaries remain active, including causal inference. The report preserves observational and non-causal boundaries from upstream artifacts. Domain coverage is incomplete. No external literature or outside contextual evidence has been integrated.

## Research Question

| Field | Value |
| --- | --- |
| Question ID | rq_project_test |
| Primary question | How is x associated with y? |
| Population | Test country-year rows |
| Variables | x, y |
| Methods | pearson_correlation |

## Dataset and Source

| Field | Value |
| --- | --- |
| Dataset ID | harmonized_country_year_67e9b4ea18e4343d |
| Title | Phase 12 Harmonized Country-Year Dataset |
| Provider | Polaris derived harmonization |
| Source type | local_csv |
| Checksum | 1495324ac7bf0315af5b83d94ac4f1309cd5b53788c8829554d39e7de06d1a09 |
| Accepted rows | 2 |
| Rejected rows | 0 |
| Analysis ready | true |
| Illustrative | false |
| Variables | who_life_expectancy_at_birth_both_sexes, wdi_gdp_per_capita_current_usd |

## Methodology

| Field | Value |
| --- | --- |
| Ingestion and validation | Local CSV ingestion mapped source columns to the supplied manifest, normalized supported scalar values, validated structure, and computed a SHA-256 checksum. |
| Sample construction | Phase 4 used complete-case sample construction from accepted Phase 3 records. |
| Procedure | pearson_correlation |
| Dependent variable | who_life_expectancy_at_birth_both_sexes |
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
| Analysis result ID | analysis_3128626ba1296f90a8723f47962ff9d98b7b84ea90fd557c426c0faac61e5cd6 |
| Method | pearson_correlation |
| Sample size | 2 |

| Variable 1 | Variable 2 | Method | N | Coefficient | p-value | Defined |
| --- | --- | --- | --- | --- | --- | --- |
| who_life_expectancy_at_birth_both_sexes | wdi_gdp_per_capita_current_usd | pearson | 2 | 1.0 | 1.0 | true |

## Evidence and Claims

| Evidence ID | Type | Variables | Direction | Limitations |
| --- | --- | --- | --- | --- |
| evidence_01c0f95f1303a4bde3c2a95dc11d2f238979d9c5afe3e6d4353bfc0cb452e383 | sample_quality | wdi_gdp_per_capita_current_usd, who_life_expectancy_at_birth_both_sexes |  |  |
| evidence_d9446cf83d41c05fe13a0b6ade2a5c515ae7bd14958444324814ecfe403aa84e | correlation | wdi_gdp_per_capita_current_usd, who_life_expectancy_at_birth_both_sexes | positive | PERFECT_CORRELATION |

| Claim ID | Type | Evidence IDs | Direction | Causal | Scope |
| --- | --- | --- | --- | --- | --- |
| claim_3d2cd9445fa7b7a1734e51b118afb5367b094f43e804af08c67e13af5215170e | association | evidence_d9446cf83d41c05fe13a0b6ade2a5c515ae7bd14958444324814ecfe403aa84e | positive | false | analysis_sample |

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
| cross_synthesis_98af1ba09efd603560da548c2f922150790c827b682c5b3b51f97b1638041dff | economics, public_health |  | evidence_d9446cf83d41c05fe13a0b6ade2a5c515ae7bd14958444324814ecfe403aa84e |
| cross_synthesis_e71d49e63673d1637c09ac981bda0421ffaee90577edab4843b653b26cbb6407 | economics, public_health | claim_3d2cd9445fa7b7a1734e51b118afb5367b094f43e804af08c67e13af5215170e |  |
| cross_synthesis_f6a89a37609db8a243026125ff2fc85fc6fcc6d3e2aa58e5040b3a301b8a1e63 | economics, public_health |  | evidence_01c0f95f1303a4bde3c2a95dc11d2f238979d9c5afe3e6d4353bfc0cb452e383 |

## Phase 8 Synthesis

The coordinated assessment contains 2 referenced evidence records and 1 referenced non-causal claim candidates across economics, public_health. Domain coverage is incomplete; governance, education was not represented. Unsupported inference boundaries remain active, including causal inference.

| Domain | Summary | Claims | Evidence |
| --- | --- | --- | --- |
| governance | governance was not supplied and should not be described as producing substantive evidence in this synthesis. |  |  |
| economics | economics selected 2 evidence references and 1 claim references from the coordinated assessment. These references support cautious association-oriented synthesis only. | claim_3d2cd9445fa7b7a1734e51b118afb5367b094f43e804af08c67e13af5215170e | evidence_01c0f95f1303a4bde3c2a95dc11d2f238979d9c5afe3e6d4353bfc0cb452e383, evidence_d9446cf83d41c05fe13a0b6ade2a5c515ae7bd14958444324814ecfe403aa84e |
| education | education was not supplied and should not be described as producing substantive evidence in this synthesis. |  |  |
| public_health | public_health selected 2 evidence references and 1 claim references from the coordinated assessment. These references support cautious association-oriented synthesis only. | claim_3d2cd9445fa7b7a1734e51b118afb5367b094f43e804af08c67e13af5215170e | evidence_01c0f95f1303a4bde3c2a95dc11d2f238979d9c5afe3e6d4353bfc0cb452e383, evidence_d9446cf83d41c05fe13a0b6ade2a5c515ae7bd14958444324814ecfe403aa84e |

## Limitations

The report preserves upstream limitation codes and keeps interpretation bounded to structured, non-causal Polaris artifacts.

| Limitation Code |
| --- |
| OBSERVATIONAL_ASSOCIATION |
| PERFECT_CORRELATION |
| UNSUPPORTED_GENERALIZATION |

## Evidence and Domain Gaps

| Gap ID | Type | Sources | Domains |
| --- | --- | --- | --- |
| coordination_evidence_gap_8d87c53abec37cde420c8bdd5f01d9b30a16275eee04603098ff8042884f8235 | cross_domain_claim_with_limited_domain_coverage | claim_3d2cd9445fa7b7a1734e51b118afb5367b094f43e804af08c67e13af5215170e | economics, public_health |

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
| Source dataset | harmonized_country_year_67e9b4ea18e4343d |
| Phase 3 DatasetIngestionResult | harmonized_country_year_67e9b4ea18e4343d |
| Phase 4 AnalysisResult | analysis_3128626ba1296f90a8723f47962ff9d98b7b84ea90fd557c426c0faac61e5cd6 |
| Phase 5 EvidenceArtifact | evidence_artifact_69dc0b8f21ef91f524390748921d52cfc502e86f8c8f34d617d33867728d352a |
| Phase 6 AgentAssessments | agent_assessment_5f4bc87dca0e63f2892036cd450146c582a293b78a0e8abcdcf9aa4e9c35a508, agent_assessment_bf665d663ac3f529cd7ab272d47be81dcce8e15e1b1fde47289fae9fc02fb189 |
| Phase 7 CoordinatedAssessment | coordinated_assessment_09913d7db5079c98669528b74823cf9a23fe49897a88bdd403f030eed2ce6424 |
| Phase 8 SynthesisArtifact | synthesis_9cfaf18bb17dd97ea5c52e6481bf66ee9056697695202f96ee7ab16980328eb7 |
| Phase 9 ResearchReport | report_79e6384869daa38aec4660a3e7fd020267c872f039f344ad47b3786d84fb15f8 |

## Reference Index

| Reference ID | Kind | Label |
| --- | --- | --- |
| coordination_agreement_0951ddfd6f2180b5f8b7ef9cda7ccd755b3f250d972d70a374c49ebcef936b3c | agreement | Coordination agreement: shared_domain_concern |
| coordination_agreement_19bac76da4d19a4bb4ea96a0d41ed1aebdf26ba8515f1a9589fa2a03a0cdff3c | agreement | Coordination agreement: shared_unsupported_inference |
| coordination_agreement_1eac77ce34e30ac24b9082a5e55daf6da5c22c2acaeb515db354c0f689dc7c21 | agreement | Coordination agreement: shared_claim |
| coordination_agreement_2177966a2f8b828b7a1f8f2c33f9694161ab030a75d073ca48a171cbbca649fa | agreement | Coordination agreement: shared_unsupported_inference |
| coordination_agreement_27b0ddfbd6f50248977e16582897732360e92e7f1ea3452fe5cec6f72da1bb66 | agreement | Coordination agreement: shared_limitation |
| coordination_agreement_3de64027318551ed57db77b82377f7b6325781959589002ed13eedaa5fb9840c | agreement | Coordination agreement: shared_domain_concern |
| coordination_agreement_4489fbc07832c6a6819c36e1d6d522f3bff7abeeb5ad59864d50780c507cc1ac | agreement | Coordination agreement: shared_domain_concern |
| coordination_agreement_61a5b926b2e6b07f3dd33a96f85fbfff328496c19a7b47d7b972ac42463a4302 | agreement | Coordination agreement: shared_domain_concern |
| coordination_agreement_79032f40c3bc03717ea6c93c3f1e6f61c92cbd83026f83463b44f557f5207d36 | agreement | Coordination agreement: shared_unsupported_inference |
| coordination_agreement_7eb1ed2b3a25663ea9107b0ac1077120945a8d9d93b506b795695f7707c14383 | agreement | Coordination agreement: shared_unsupported_inference |
| coordination_agreement_7fd5e3c1426011283a34ab2fa7e1cbc822ff25878236f5d20e4e7d9b992cb5ff | agreement | Coordination agreement: shared_evidence |
| coordination_agreement_954742801130a28ce5353ce1223fc8d24b732ad177ed0c55c28664639950f85f | agreement | Coordination agreement: shared_limitation |
| coordination_agreement_a280d727bb57dc763c23eefb79233b57c99c7a701d0f3149bf458504571b69c9 | agreement | Coordination agreement: shared_limitation |
| coordination_agreement_a766dcd4f0676e47771bd57fc9106aaa6b7d3c992ab13ce91950612c93554d33 | agreement | Coordination agreement: shared_unsupported_inference |
| coordination_agreement_ae2dc1491f99c147b5eeac9db293f3d31c3366243b0587a461feaa69f0a02f76 | agreement | Coordination agreement: shared_unsupported_inference |
| coordination_agreement_c6e89227e6c26cbd12bdbb9af00c227612e22187f5ccfea37fe2e7cd6c911cab | agreement | Coordination agreement: shared_evidence |
| coordination_agreement_d10c6caced030cd394cb4ea94b4c774ac7a226c67085bae15f7b53b3bc7d71f3 | agreement | Coordination agreement: shared_domain_concern |
| coordination_agreement_d7aa6b9fa324041eb9b4a2811ffe206552ba4d35b293f4b9ff3702f041c1d845 | agreement | Coordination agreement: shared_domain_concern |
| coordination_agreement_f9ec1c513583650235014e6424d08463e0cfd99164541faff3cf2422ebbd2adc | agreement | Coordination agreement: shared_domain_concern |
| agent_assessment_5f4bc87dca0e63f2892036cd450146c582a293b78a0e8abcdcf9aa4e9c35a508 | assessment | Domain assessment: economics |
| agent_assessment_bf665d663ac3f529cd7ab272d47be81dcce8e15e1b1fde47289fae9fc02fb189 | assessment | Domain assessment: public_health |
| claim_3d2cd9445fa7b7a1734e51b118afb5367b094f43e804af08c67e13af5215170e | claim | Claim candidate: association |
| coordination_divergence_5f3b8f69c2465b9497e517801aab17fe9d5736953c5082aadb23018dafdf8a6f | divergence | Coordination divergence: domain_specific_unsupported_inference |
| evidence_01c0f95f1303a4bde3c2a95dc11d2f238979d9c5afe3e6d4353bfc0cb452e383 | evidence | Evidence record: sample_quality |
| evidence_d9446cf83d41c05fe13a0b6ade2a5c515ae7bd14958444324814ecfe403aa84e | evidence | Evidence record: correlation |
| coordination_domain_gap_2cda4ca8f7436f9f2c37185bda78a91223f6045f01a8d2a1090a39c37ae6b12f | gap | Domain gap: governance |
| coordination_domain_gap_6dfe7972acbb582af0493c5f46d83f4e3889a6e76542b35463ba65e833d82d51 | gap | Domain gap: education |
| coordination_evidence_gap_8d87c53abec37cde420c8bdd5f01d9b30a16275eee04603098ff8042884f8235 | gap | Evidence gap: cross_domain_claim_with_limited_domain_coverage |
| analysis_3128626ba1296f90a8723f47962ff9d98b7b84ea90fd557c426c0faac61e5cd6 | source_artifact | Source Polaris artifact |
| coordinated_assessment_09913d7db5079c98669528b74823cf9a23fe49897a88bdd403f030eed2ce6424 | source_artifact | Source Polaris artifact |
| evidence_artifact_69dc0b8f21ef91f524390748921d52cfc502e86f8c8f34d617d33867728d352a | source_artifact | Source Polaris artifact |
| harmonized_country_year_67e9b4ea18e4343d | source_artifact | Source Polaris artifact |
| synthesis_9cfaf18bb17dd97ea5c52e6481bf66ee9056697695202f96ee7ab16980328eb7 | source_artifact | Source Polaris artifact |
