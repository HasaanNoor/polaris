# Phase 12 Harmonized Country-Year Validation Report

Derived WDI plus WHO official local extracts

## Metadata

| Field | Value |
| --- | --- |
| Report ID | report_0aac4e2ae525701ca9de03a32e8ef6755b95590e4bf27154c5732097c5035e1b |
| Generated | 2026-08-06T21:57:23.032088+00:00 |
| Dataset ID | harmonized_country_year_77f944701e5529a1 |
| Source checksum | c92e66003705c1e05a9d188a5c392695039679270ed0c1c937500b919cf9cf19 |
| Analysis procedure | pearson_correlation |
| Synthesis mode | deterministic |
| Ruleset | deterministic_phase9_v1 |

## Executive Summary

The coordinated assessment contains 3 referenced evidence records and 1 referenced non-causal claim candidates across governance, economics, education, public_health. Unsupported inference boundaries remain active, including causal inference. The report preserves observational and non-causal boundaries from upstream artifacts. No external literature or outside contextual evidence has been integrated.

## Research Question

| Field | Value |
| --- | --- |
| Question ID | rq_phase12_harmonized_real_validation |
| Primary question | How is WDI GDP per capita associated with WHO life expectancy at birth in the Phase 12 harmonized country-year extract? |
| Population | Country-year observations in the derived WDI plus WHO harmonized extract |
| Variables | wdi_gdp_per_capita_current_usd, who_life_expectancy_at_birth_both_sexes |
| Methods | pearson_correlation |

## Dataset and Source

| Field | Value |
| --- | --- |
| Dataset ID | harmonized_country_year_77f944701e5529a1 |
| Title | Phase 12 Harmonized Country-Year Dataset |
| Provider | Polaris derived harmonization |
| Source type | local_csv |
| Checksum | c92e66003705c1e05a9d188a5c392695039679270ed0c1c937500b919cf9cf19 |
| Accepted rows | 1519 |
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
| Evidence extraction | Phase 5 extracted 3 evidence records and 1 bounded non-causal claim candidates. |
| Domain agents | Phase 6 deterministic domain agents selected relevant structured evidence and claim IDs without adding outside context. |
| Coordination | Phase 7 coordinated 4 domain assessments by reference. |
| Synthesis mode | deterministic |
| Grounding and validation | Phase 8 synthesis supplied validated summaries with fabricated-reference, limitation-preservation, unsupported-inference, and overreach checks. |

## Statistical Results

| Field | Value |
| --- | --- |
| Analysis result ID | analysis_0d25fc8bdb5904aa25dc12a632a0ab5074f067c8423a3ce26a28fa82550e8e46 |
| Method | pearson_correlation |
| Sample size | 1271 |

| Variable 1 | Variable 2 | Method | N | Coefficient | p-value | Defined |
| --- | --- | --- | --- | --- | --- | --- |
| who_life_expectancy_at_birth_both_sexes | wdi_gdp_per_capita_current_usd | pearson | 1271 | 0.6443167122946463 | 5.408672349903574e-150 | true |

## Evidence and Claims

| Evidence ID | Type | Variables | Direction | Limitations |
| --- | --- | --- | --- | --- |
| evidence_354e082449f4694ec3760b7a2574e0f010b5f4884ff7766cd3015f5783fbf268 | sample_quality | wdi_gdp_per_capita_current_usd, who_life_expectancy_at_birth_both_sexes |  | MISSING_DATA_EXCLUSION |
| evidence_3f876ff0358372f0742ffbcab038e5cf09b4c2952c343cec77b12b10d795f08f | analysis_warning | wdi_gdp_per_capita_current_usd, who_life_expectancy_at_birth_both_sexes |  | MISSING_DATA_EXCLUSION |
| evidence_b68c0a1d381e9a71582883897827551192f31c1d45dbc9e37d3a68dff06dede3 | correlation | wdi_gdp_per_capita_current_usd, who_life_expectancy_at_birth_both_sexes | positive |  |

| Claim ID | Type | Evidence IDs | Direction | Causal | Scope |
| --- | --- | --- | --- | --- | --- |
| claim_c167ca791654519914dec882b701a4c2fe84a2786a09cd059f19478df55e87f5 | association | evidence_b68c0a1d381e9a71582883897827551192f31c1d45dbc9e37d3a68dff06dede3 | positive | false | analysis_sample |

## Domain Assessments

| Domain | Supplied | Coverage | Evidence | Claims | Unsupported |
| --- | --- | --- | --- | --- | --- |
| governance | true | no_relevant_evidence | 0 | 0 | causality, intervention_recommendation, mechanism, policy_effectiveness, temporal_prediction |
| economics | true | relevant_evidence | 3 | 1 | causality, intervention_recommendation, mechanism, policy_effectiveness, population_wide_generalization, temporal_prediction |
| education | true | no_relevant_evidence | 0 | 0 | causality, intervention_recommendation, mechanism, policy_effectiveness, temporal_prediction |
| public_health | true | relevant_evidence | 3 | 1 | causality, intervention_recommendation, mechanism, medical_conclusion, policy_effectiveness, population_wide_generalization, temporal_prediction |

## Cross-Domain Synthesis

The coordinated assessment contains 3 referenced evidence records and 1 referenced non-causal claim candidates across governance, economics, education, public_health. Unsupported inference boundaries remain active, including causal inference.

| Finding ID | Domains | Claim IDs | Evidence IDs |
| --- | --- | --- | --- |
| cross_synthesis_3f4719a3ef88d20589e4f3e52a3f8ac257a01f15b9c113d4d000ea28cb5a0691 | economics, public_health |  | evidence_3f876ff0358372f0742ffbcab038e5cf09b4c2952c343cec77b12b10d795f08f |
| cross_synthesis_80df693623793ae3ad8383032ce1758ba834bc9e98cb40a26a1980d2b1dba021 | economics, public_health | claim_c167ca791654519914dec882b701a4c2fe84a2786a09cd059f19478df55e87f5 |  |
| cross_synthesis_85fefda5e2c0039b5f490c3e5620d3b119e4ffd3db2cb0d50e175fc7463fbe28 | economics, public_health |  | evidence_354e082449f4694ec3760b7a2574e0f010b5f4884ff7766cd3015f5783fbf268 |
| cross_synthesis_a1385a289a9932564053a2d56d8d0e18d1453bc8b2ea6d493b2c6508209bce69 | economics, public_health |  | evidence_b68c0a1d381e9a71582883897827551192f31c1d45dbc9e37d3a68dff06dede3 |

## Phase 8 Synthesis

The coordinated assessment contains 3 referenced evidence records and 1 referenced non-causal claim candidates across governance, economics, education, public_health. Unsupported inference boundaries remain active, including causal inference.

| Domain | Summary | Claims | Evidence |
| --- | --- | --- | --- |
| governance | governance was supplied with no relevant evidence and should not be described as producing substantive evidence in this synthesis. |  |  |
| economics | economics selected 3 evidence references and 1 claim references from the coordinated assessment. These references support cautious association-oriented synthesis only. | claim_c167ca791654519914dec882b701a4c2fe84a2786a09cd059f19478df55e87f5 | evidence_354e082449f4694ec3760b7a2574e0f010b5f4884ff7766cd3015f5783fbf268, evidence_3f876ff0358372f0742ffbcab038e5cf09b4c2952c343cec77b12b10d795f08f, evidence_b68c0a1d381e9a71582883897827551192f31c1d45dbc9e37d3a68dff06dede3 |
| education | education was supplied with no relevant evidence and should not be described as producing substantive evidence in this synthesis. |  |  |
| public_health | public_health selected 3 evidence references and 1 claim references from the coordinated assessment. These references support cautious association-oriented synthesis only. | claim_c167ca791654519914dec882b701a4c2fe84a2786a09cd059f19478df55e87f5 | evidence_354e082449f4694ec3760b7a2574e0f010b5f4884ff7766cd3015f5783fbf268, evidence_3f876ff0358372f0742ffbcab038e5cf09b4c2952c343cec77b12b10d795f08f, evidence_b68c0a1d381e9a71582883897827551192f31c1d45dbc9e37d3a68dff06dede3 |

## Limitations

The report preserves upstream limitation codes and keeps interpretation bounded to structured, non-causal Polaris artifacts.

| Limitation Code |
| --- |
| MISSING_DATA_EXCLUSION |
| OBSERVATIONAL_ASSOCIATION |
| UNSUPPORTED_GENERALIZATION |

## Evidence and Domain Gaps

| Gap ID | Type | Sources | Domains |
| --- | --- | --- | --- |
| coordination_evidence_gap_dbf6a23f1d65a9d3724160ba4e5a32f6f5507dbe2a898dca5651eb648d7e1461 | cross_domain_claim_with_limited_domain_coverage | claim_c167ca791654519914dec882b701a4c2fe84a2786a09cd059f19478df55e87f5 | economics, public_health |

| Gap ID | Type | Domain | Assessment supplied |
| --- | --- | --- | --- |
| coordination_domain_gap_c9e63a4ccc57d28d9be7245855b73d2c9a9ad4e641dd42e4aca177f658bd8758 | domain_has_no_relevant_evidence | governance | true |
| coordination_domain_gap_9153f81ad9c644b0c94eef230c25cc7c33cac16a0526c344d14d784cc29b3506 | domain_has_no_relevant_evidence | education | true |

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
| Source dataset | harmonized_country_year_77f944701e5529a1 |
| Phase 3 DatasetIngestionResult | harmonized_country_year_77f944701e5529a1 |
| Phase 4 AnalysisResult | analysis_0d25fc8bdb5904aa25dc12a632a0ab5074f067c8423a3ce26a28fa82550e8e46 |
| Phase 5 EvidenceArtifact | evidence_artifact_b89c287ce0dd3a117c59a98e66b35a2136ddcd910fa34eec9e90ef517e23211f |
| Phase 6 AgentAssessments | agent_assessment_28336f5c46d94734fc1e0d02b896ba5aff110e05631d6883b000e967a6c3ae30, agent_assessment_59b330c0c13be472dbde6bb3277ca976e3e24e958ed8a1ba4f84c5a66d630cff, agent_assessment_76e6d1c0794ca9c9560317e8901da29de3f608c0b7756ecf3ef8eaafb5e23a7d, agent_assessment_d34bf8e213c3f2569581690540a2e2e1e33dfe7cd489868c396e54aac22ba936 |
| Phase 7 CoordinatedAssessment | coordinated_assessment_400880bd684c6828eb00de529e73534ddc54b921f85f4344b52fb461918b1a1d |
| Phase 8 SynthesisArtifact | synthesis_2a451d859a263e2d344c6d099e6a4ca474930f0f325fdb14ef3164ac757b225e |
| Phase 9 ResearchReport | report_0aac4e2ae525701ca9de03a32e8ef6755b95590e4bf27154c5732097c5035e1b |

## Reference Index

| Reference ID | Kind | Label |
| --- | --- | --- |
| coordination_agreement_0e6158669c3a5e2f495bd5e11c32ad03810ec1d7416eb442e811e15c4dcd143c | agreement | Coordination agreement: shared_unsupported_inference |
| coordination_agreement_1d6f707861657f9e985cdd39570263ee9e4a673dda39ff826978cdc2aabf3672 | agreement | Coordination agreement: shared_domain_concern |
| coordination_agreement_2726b47de5442a9ede1c743ba4b3b6526d9bee10fd8c54d3c56c6531f2f52a65 | agreement | Coordination agreement: shared_limitation |
| coordination_agreement_2793a57d85d1b5ec775e38f45de8785433d1f1e5f8199a3aedd511a9d1489af2 | agreement | Coordination agreement: shared_unsupported_inference |
| coordination_agreement_27b0ddfbd6f50248977e16582897732360e92e7f1ea3452fe5cec6f72da1bb66 | agreement | Coordination agreement: shared_limitation |
| coordination_agreement_29af860ebc588fb0edf6671ef9aec91e711ce0107d363ce310e35056a1527e0c | agreement | Coordination agreement: shared_domain_concern |
| coordination_agreement_317ccbf082badbab4c7343679ce3f4043fb757b6b3ab39a953357117b1d5117d | agreement | Coordination agreement: shared_unsupported_inference |
| coordination_agreement_31ee2b1ad702b23f635d06641a8c5a36c71a2ae23836068808811c50e0b7759b | agreement | Coordination agreement: shared_unsupported_inference |
| coordination_agreement_4489fbc07832c6a6819c36e1d6d522f3bff7abeeb5ad59864d50780c507cc1ac | agreement | Coordination agreement: shared_domain_concern |
| coordination_agreement_5b270d4d4f26fefa5dfe43dbab16cb1b19e58fd835505bc91b308d4f77c61064 | agreement | Coordination agreement: shared_evidence |
| coordination_agreement_71962ca5fe761b0df1de25830c03db3dde4252b3748f16a43adc8060d7d3d4ac | agreement | Coordination agreement: shared_evidence |
| coordination_agreement_88bdc270f290326218b7dd8b2763a97669c349726210e0af02521702d3052c4c | agreement | Coordination agreement: shared_evidence |
| coordination_agreement_8f5cd6761e6f7607603d0522de3d5da8c55f99a988d79eadf18194fcde16495e | agreement | Coordination agreement: shared_domain_concern |
| coordination_agreement_96914ab44f34084b49ba57b4d6adbd7760c66cf3c47a626d06d21fa6de1dd02f | agreement | Coordination agreement: shared_domain_concern |
| coordination_agreement_a280d727bb57dc763c23eefb79233b57c99c7a701d0f3149bf458504571b69c9 | agreement | Coordination agreement: shared_limitation |
| coordination_agreement_a766dcd4f0676e47771bd57fc9106aaa6b7d3c992ab13ce91950612c93554d33 | agreement | Coordination agreement: shared_unsupported_inference |
| coordination_agreement_aefc9822a00d44a2cbdd9852e561fd2a33180436357b97617c8c4174bbd124b1 | agreement | Coordination agreement: shared_unsupported_inference |
| coordination_agreement_b42fc55004ef73949421e68c7978a41dc21b6e3ccc1e73b97df071b94521aa52 | agreement | Coordination agreement: shared_domain_concern |
| coordination_agreement_bdd6de57ca9be1f67d05b7564eabd3551260516f5227d2282100284c3e8063d5 | agreement | Coordination agreement: shared_domain_concern |
| coordination_agreement_c7ce4874bdfe238dde1a0577846b52b1bbb89dceeae732023614f02bb86bafa9 | agreement | Coordination agreement: shared_domain_concern |
| coordination_agreement_cadca660fa8b3467748dd2f117287e228b5834ae28bbec0943dce027f280595d | agreement | Coordination agreement: shared_claim |
| coordination_agreement_eb2861402bad88c2a104219a1a8417199690610988656a08c32167c809d492f8 | agreement | Coordination agreement: shared_domain_concern |
| agent_assessment_28336f5c46d94734fc1e0d02b896ba5aff110e05631d6883b000e967a6c3ae30 | assessment | Domain assessment: public_health |
| agent_assessment_59b330c0c13be472dbde6bb3277ca976e3e24e958ed8a1ba4f84c5a66d630cff | assessment | Domain assessment: education |
| agent_assessment_76e6d1c0794ca9c9560317e8901da29de3f608c0b7756ecf3ef8eaafb5e23a7d | assessment | Domain assessment: governance |
| agent_assessment_d34bf8e213c3f2569581690540a2e2e1e33dfe7cd489868c396e54aac22ba936 | assessment | Domain assessment: economics |
| claim_c167ca791654519914dec882b701a4c2fe84a2786a09cd059f19478df55e87f5 | claim | Claim candidate: association |
| coordination_divergence_0594f8fd291cefc7891992366defbbb357bdf19c49f69cfe59c17474364a9ead | divergence | Coordination divergence: domain_specific_concern |
| coordination_divergence_09ec89aee87d416ee18c184107ef17bbac4b430fd48802d01d4270ab00a1a01e | divergence | Coordination divergence: different_relevance_classification |
| coordination_divergence_1072a384a19cd6b91fdd828a4fe4880cabf755cce0abe47784b368379fc5d97f | divergence | Coordination divergence: domain_specific_unsupported_inference |
| coordination_divergence_1909980aca4b1b57323f0b57c8896844f28aa16492c9c448c340d2b7a22ced96 | divergence | Coordination divergence: uneven_evidence_coverage |
| coordination_divergence_1c2b02164b5bc4c4b65691f496f12f43536926e0b4cd15d46acf547a5b0b0286 | divergence | Coordination divergence: domain_specific_concern |
| coordination_divergence_52eff198e441bf7692ee49f2e14447bc79a2dde5b9656a0101aedd1007d639ad | divergence | Coordination divergence: domain_specific_concern |
| coordination_divergence_5f3b8f69c2465b9497e517801aab17fe9d5736953c5082aadb23018dafdf8a6f | divergence | Coordination divergence: domain_specific_unsupported_inference |
| coordination_divergence_621a4c7e4c5043aeeb19df6b5da76b3f6aba02b2077c1d63629bb542bc274582 | divergence | Coordination divergence: domain_specific_limitation |
| coordination_divergence_62d77f1afb2cfecaa1381f57e0bd5a10b505e433a711f756fb81fe46dfdf9f25 | divergence | Coordination divergence: domain_specific_concern |
| coordination_divergence_6c3a509eee99e26960dfb63ce8a2f9d804dca2a75712e040ec6d17c99fa9e2a9 | divergence | Coordination divergence: domain_specific_limitation |
| coordination_divergence_7a084523278be9595f99fad8d096585da8b67892da6f3fd9884564eae6f38beb | divergence | Coordination divergence: domain_specific_concern |
| coordination_divergence_8746d45bf0e7e10e4da5322dd3c56837484fc0da69326209f07f38a6b5ec9814 | divergence | Coordination divergence: domain_specific_concern |
| coordination_divergence_9db2221f7f7a73bcf0d902b54e5eb41744375d7c0515de46f54da1478f98c78e | divergence | Coordination divergence: domain_specific_concern |
| coordination_divergence_ade9af2d4782c32d37ea722327e07ebc3e72a8da073eb51e6bddb82bf7942c44 | divergence | Coordination divergence: different_relevance_classification |
| coordination_divergence_c69deff858ea7df9ea8364be2c5971225b2e0a52f0d7455c768628887e0db237 | divergence | Coordination divergence: domain_specific_concern |
| coordination_divergence_caeb37655b06958c0172ec5885a1c6c374d3195fddaa6a8e340566219688fc6e | divergence | Coordination divergence: uneven_evidence_coverage |
| coordination_divergence_dbd94f746de1c8a563c7c15bec1b2913236980c36a748a8150ae593295ae9198 | divergence | Coordination divergence: domain_specific_concern |
| coordination_divergence_e34cdcd72ab888fe7a1b087a649fd4b18c940dd9fa774f597377474a9d96316d | divergence | Coordination divergence: different_relevance_classification |
| coordination_divergence_e68e3aec23a2e7f419d8ee0d0ea628fa5d4248d1a208660a8a87098d0641c53d | divergence | Coordination divergence: domain_specific_limitation |
| coordination_divergence_ee355bcdeeb003ef6c6e9964a32df3ed6aa1cd38ca3c76d4a3201b5d44c88e58 | divergence | Coordination divergence: different_relevance_classification |
| coordination_divergence_fd39a4591e2ac22ea042620e5c1c1bd85cde2687070823da773d08ff1778e561 | divergence | Coordination divergence: uneven_evidence_coverage |
| coordination_divergence_feb52650ef7d11bceb99cbe80beed14d4e64bb235b8ca7c355dbabdbbce858a4 | divergence | Coordination divergence: uneven_evidence_coverage |
| evidence_354e082449f4694ec3760b7a2574e0f010b5f4884ff7766cd3015f5783fbf268 | evidence | Evidence record: sample_quality |
| evidence_3f876ff0358372f0742ffbcab038e5cf09b4c2952c343cec77b12b10d795f08f | evidence | Evidence record: analysis_warning |
| evidence_b68c0a1d381e9a71582883897827551192f31c1d45dbc9e37d3a68dff06dede3 | evidence | Evidence record: correlation |
| coordination_domain_gap_9153f81ad9c644b0c94eef230c25cc7c33cac16a0526c344d14d784cc29b3506 | gap | Domain gap: education |
| coordination_domain_gap_c9e63a4ccc57d28d9be7245855b73d2c9a9ad4e641dd42e4aca177f658bd8758 | gap | Domain gap: governance |
| coordination_evidence_gap_dbf6a23f1d65a9d3724160ba4e5a32f6f5507dbe2a898dca5651eb648d7e1461 | gap | Evidence gap: cross_domain_claim_with_limited_domain_coverage |
| analysis_0d25fc8bdb5904aa25dc12a632a0ab5074f067c8423a3ce26a28fa82550e8e46 | source_artifact | Source Polaris artifact |
| coordinated_assessment_400880bd684c6828eb00de529e73534ddc54b921f85f4344b52fb461918b1a1d | source_artifact | Source Polaris artifact |
| evidence_artifact_b89c287ce0dd3a117c59a98e66b35a2136ddcd910fa34eec9e90ef517e23211f | source_artifact | Source Polaris artifact |
| harmonized_country_year_77f944701e5529a1 | source_artifact | Source Polaris artifact |
| synthesis_2a451d859a263e2d344c6d099e6a4ca474930f0f325fdb14ef3164ac757b225e | source_artifact | Source Polaris artifact |
