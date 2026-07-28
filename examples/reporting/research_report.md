# Illustrative Literacy, Fertility, and GDP Report

Illustrative Polaris Phase 9 example

## Metadata

| Field | Value |
| --- | --- |
| Report ID | report_b3b4e2ad73bc66ed64736b0b0759336b28097dbe620070baee2252f81f22fe43 |
| Generated | 2026-07-28T00:00:00+00:00 |
| Dataset ID | reporting_literacy_fertility_gdp_sample |
| Source checksum | 950917ec35fc100abd811bb1a4c9eb538d9e4ea2e953444b093cd1a52aeb3c2b |
| Analysis procedure | ordinary_least_squares |
| Synthesis mode | deterministic |
| Ruleset | deterministic_phase9_v1 |

## Executive Summary

The coordinated assessment contains 8 referenced evidence records and 5 referenced non-causal claim candidates across governance, economics, education, public_health. Unsupported inference boundaries remain active, including causal inference. The report preserves observational and non-causal boundaries from upstream artifacts. No external literature or outside contextual evidence has been integrated.

## Research Question

| Field | Value |
| --- | --- |
| Question ID | rq_reporting_illustrative |
| Primary question | How is female literacy associated with fertility rate after accounting for GDP per capita in the illustrative sample? |
| Population | Illustrative country observations |
| Variables | female_literacy, fertility_rate, gdp_per_capita |
| Methods | ordinary_least_squares |

## Dataset and Source

| Field | Value |
| --- | --- |
| Dataset ID | reporting_literacy_fertility_gdp_sample |
| Title | Illustrative Literacy, Fertility, and GDP Sample |
| Provider | Polaris synthetic example |
| Source type | local_csv |
| Checksum | 950917ec35fc100abd811bb1a4c9eb538d9e4ea2e953444b093cd1a52aeb3c2b |
| Accepted rows | 7 |
| Rejected rows | 0 |
| Analysis ready | true |
| Illustrative | true |
| Variables | fertility_rate, female_literacy, gdp_per_capita |

## Methodology

| Field | Value |
| --- | --- |
| Ingestion and validation | Local CSV ingestion mapped source columns to the supplied manifest, normalized supported scalar values, validated structure, and computed a SHA-256 checksum. |
| Sample construction | Phase 4 used complete-case sample construction from accepted Phase 3 records. |
| Procedure | ordinary_least_squares |
| Dependent variable | fertility_rate |
| Predictors | female_literacy |
| Controls | gdp_per_capita |
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
| Analysis result ID | analysis_5435f04b0ccc0ffe50b40a2f8060b49bb9eb83d850138c9a1f3e3ba31de0ba8e |
| Method | ordinary_least_squares |
| Sample size | 6 |

| Term | Estimate | Std. Error | Statistic | p-value | CI Low | CI High |
| --- | --- | --- | --- | --- | --- | --- |
| intercept | 8.656456938692793 | 0.30188601164471013 | 28.674587774144978 | 9.312815013039724e-05 | 7.695720916317251 | 9.617192961068335 |
| female_literacy | -0.08570070342114552 | 0.007086138036089358 | -12.094134066352645 | 0.0012166324802283426 | -0.10825195723282845 | -0.0631494496094626 |
| gdp_per_capita | 0.00014819647634342184 | 5.584047197935565e-05 | 2.6539259266685713 | 0.07673579348940457 | -2.9512827392576962e-05 | 0.00032590578007942063 |

| Metric | Value |
| --- | --- |
| R-squared | 0.9979111300589804 |
| Adjusted R-squared | 0.9965185500983006 |
| Residual degrees of freedom | 3.0 |
| Model degrees of freedom | 2.0 |
| RSS | 0.012992771033141974 |
| MSE | 0.004330923677713991 |

## Evidence and Claims

| Evidence ID | Type | Variables | Direction | Limitations |
| --- | --- | --- | --- | --- |
| evidence_01bbaeee60d46b4369b8c5a04e4f063b0dd28e5bbb9ee48ba3468a25c707f36d | model_diagnostic | gdp_per_capita |  |  |
| evidence_3e8661fcb72dd051fe38076c5a2518b558e0283c6f4092a3dfd5428406df7d26 | model_diagnostic |  |  | UNDEFINED_DIAGNOSTIC |
| evidence_41cefd02c54b41b7e1301b01dad76013b9ba4d7e72212d0e0114bf90119b5179 | analysis_warning | female_literacy, fertility_rate, gdp_per_capita |  | MISSING_DATA_EXCLUSION |
| evidence_46cf32fa548efe4343769389a3b689c26cf82fad79668eaa3530526d61de9aff | sample_quality | female_literacy, fertility_rate, gdp_per_capita |  | MISSING_DATA_EXCLUSION |
| evidence_61dc02df5f976ad117b21412698257c13e788363ed46ad64e7ebcfd39fbaa895 | regression_coefficient | female_literacy, fertility_rate, gdp_per_capita | positive |  |
| evidence_722fcb68ccbf504807494ad563777e293a33c3e93bbe694cb016d3abf8c2b172 | regression_coefficient | female_literacy, fertility_rate, gdp_per_capita | negative |  |
| evidence_931decfcdaa6ec1f2577672079b1f140dde62822435b15d68fcad1f471d329d8 | model_fit | female_literacy, fertility_rate, gdp_per_capita |  |  |
| evidence_a74fb0faf462ca8526d44f58e9ffca09b3d263969093878439804af9c722c5d1 | regression_coefficient | female_literacy, fertility_rate, gdp_per_capita | positive |  |
| evidence_acc8821b3744480f343a24e9c30d75abcd869af879fc8d010f1cd4fd4bb1463f | model_diagnostic |  |  |  |
| evidence_b7405ec1b71828a6948bdbdabd106ed2529ab5c7931dd96a95319129989d46d5 | model_diagnostic |  |  |  |
| evidence_b97e16b92b3cfe31f37fa2ead83eec077d10bd1a733a20e5ddecb9d8faa85907 | model_diagnostic |  |  |  |
| evidence_d67711c7b6b55f032105c87233543f7174c21c8cbb93c7d70b2e36c4c10b0341 | model_diagnostic |  |  | HETEROSKEDASTICITY_WARNING |
| evidence_e19a41a0e4e8793c507b8219c6310fe01c0aac33f381f88e3334fec1aa277988 | model_diagnostic | female_literacy |  |  |

| Claim ID | Type | Evidence IDs | Direction | Causal | Scope |
| --- | --- | --- | --- | --- | --- |
| claim_0d8e477d7698dd47897ef4f4ad43a2f42750763e5f04137e7a8eb0bb2febfa86 | conditional_association | evidence_722fcb68ccbf504807494ad563777e293a33c3e93bbe694cb016d3abf8c2b172 | negative | false | analysis_sample |
| claim_54f6deed014d5a5c012a024bf94daac479e28151ce420698f6abd23b7c79a907 | model_limitation | evidence_3e8661fcb72dd051fe38076c5a2518b558e0283c6f4092a3dfd5428406df7d26 | not_applicable | false | analysis_sample |
| claim_5bde0a88a7f3f87f5e99959114e5d09aaedd2cc465554fcf1159e144d95bd5d8 | statistical_uncertainty | evidence_61dc02df5f976ad117b21412698257c13e788363ed46ad64e7ebcfd39fbaa895 | not_applicable | false | analysis_sample |
| claim_8c85d2d9e124c16e007a573220afa8b763e401ad2188b94bd3326c34238400a0 | statistical_uncertainty | evidence_722fcb68ccbf504807494ad563777e293a33c3e93bbe694cb016d3abf8c2b172 | not_applicable | false | analysis_sample |
| claim_a6082af5be042bc66b0886cba000846711c211e4b101eb464e8ad01bb39f2f32 | model_limitation | evidence_d67711c7b6b55f032105c87233543f7174c21c8cbb93c7d70b2e36c4c10b0341 | not_applicable | false | analysis_sample |
| claim_e8c10cabcef573ebd74615b6710a91caf95546400711bf460ca21c09d0f97c4f | statistical_uncertainty | evidence_a74fb0faf462ca8526d44f58e9ffca09b3d263969093878439804af9c722c5d1 | not_applicable | false | analysis_sample |
| claim_efa01972ca8eeaf95b985204913340d645113a7f80d9456f01f72b000658fd91 | conditional_association | evidence_61dc02df5f976ad117b21412698257c13e788363ed46ad64e7ebcfd39fbaa895 | positive | false | analysis_sample |

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
| cross_synthesis_01d282f57556bbb90b8387f5d5f103e9b9ae0be5f4c072ff1b407b59b6c5cd5d | economics, education, public_health | claim_e8c10cabcef573ebd74615b6710a91caf95546400711bf460ca21c09d0f97c4f |  |
| cross_synthesis_0b13c7a5337344067f22a3cafebf5cd56fbf25aeb3583711ad6f05920826b197 | economics, education, public_health | claim_efa01972ca8eeaf95b985204913340d645113a7f80d9456f01f72b000658fd91 |  |
| cross_synthesis_160ba1f5311f2017f859c144086f77df356698e2c22986a7a030b430d0753085 | economics, education, public_health |  | evidence_722fcb68ccbf504807494ad563777e293a33c3e93bbe694cb016d3abf8c2b172 |
| cross_synthesis_331594ca2393cbc0e639afe0b4dc9c83b582dc33c6bc02811855c930b043e202 | economics, education, public_health | claim_0d8e477d7698dd47897ef4f4ad43a2f42750763e5f04137e7a8eb0bb2febfa86 |  |
| cross_synthesis_6f8ec78a416870626431fdae796d8cbc1623c9ad978c77977889aad93929b2e7 | economics, education, public_health |  | evidence_61dc02df5f976ad117b21412698257c13e788363ed46ad64e7ebcfd39fbaa895 |
| cross_synthesis_72b7bfabea3a56eaccfb7adcbde9665eefe24526669d7c4b86215310bdea85b1 | economics, education, public_health |  | evidence_a74fb0faf462ca8526d44f58e9ffca09b3d263969093878439804af9c722c5d1 |
| cross_synthesis_7714440f6989437ceb0afd4353ea1f75885fc70971e5b497b1ca6d4f5b946481 | economics, education, public_health |  | evidence_931decfcdaa6ec1f2577672079b1f140dde62822435b15d68fcad1f471d329d8 |
| cross_synthesis_82d13378e48b5f5ff7b95f50267bbfff3551a023668720ed75139fb1464c7a2b | economics, education, public_health |  | evidence_46cf32fa548efe4343769389a3b689c26cf82fad79668eaa3530526d61de9aff |
| cross_synthesis_c98d370deda9161e5633f466c46d25f546397f6db51b9f9bda0cd9a7fb241e8a | economics, education, public_health | claim_8c85d2d9e124c16e007a573220afa8b763e401ad2188b94bd3326c34238400a0 |  |
| cross_synthesis_e107eb8568676ef4fd16f9cc57ea878ed166b155baee68c8074a7b69175ba4ab | economics, education, public_health |  | evidence_41cefd02c54b41b7e1301b01dad76013b9ba4d7e72212d0e0114bf90119b5179 |
| cross_synthesis_ff46f7b590656a88e3131e1422a06708d744ce83ec60431912c945cd0e5b6a69 | economics, education, public_health | claim_5bde0a88a7f3f87f5e99959114e5d09aaedd2cc465554fcf1159e144d95bd5d8 |  |

## Phase 8 Synthesis

The coordinated assessment contains 8 referenced evidence records and 5 referenced non-causal claim candidates across governance, economics, education, public_health. Unsupported inference boundaries remain active, including causal inference.

| Domain | Summary | Claims | Evidence |
| --- | --- | --- | --- |
| governance | governance was supplied with no relevant evidence and should not be described as producing substantive evidence in this synthesis. |  |  |
| economics | economics selected 7 evidence references and 5 claim references from the coordinated assessment. These references support cautious association-oriented synthesis only. | claim_0d8e477d7698dd47897ef4f4ad43a2f42750763e5f04137e7a8eb0bb2febfa86, claim_5bde0a88a7f3f87f5e99959114e5d09aaedd2cc465554fcf1159e144d95bd5d8, claim_8c85d2d9e124c16e007a573220afa8b763e401ad2188b94bd3326c34238400a0, claim_e8c10cabcef573ebd74615b6710a91caf95546400711bf460ca21c09d0f97c4f, claim_efa01972ca8eeaf95b985204913340d645113a7f80d9456f01f72b000658fd91 | evidence_01bbaeee60d46b4369b8c5a04e4f063b0dd28e5bbb9ee48ba3468a25c707f36d, evidence_41cefd02c54b41b7e1301b01dad76013b9ba4d7e72212d0e0114bf90119b5179, evidence_46cf32fa548efe4343769389a3b689c26cf82fad79668eaa3530526d61de9aff, evidence_61dc02df5f976ad117b21412698257c13e788363ed46ad64e7ebcfd39fbaa895, evidence_722fcb68ccbf504807494ad563777e293a33c3e93bbe694cb016d3abf8c2b172, evidence_931decfcdaa6ec1f2577672079b1f140dde62822435b15d68fcad1f471d329d8, evidence_a74fb0faf462ca8526d44f58e9ffca09b3d263969093878439804af9c722c5d1 |
| education | education selected 7 evidence references and 5 claim references from the coordinated assessment. These references support cautious association-oriented synthesis only. | claim_0d8e477d7698dd47897ef4f4ad43a2f42750763e5f04137e7a8eb0bb2febfa86, claim_5bde0a88a7f3f87f5e99959114e5d09aaedd2cc465554fcf1159e144d95bd5d8, claim_8c85d2d9e124c16e007a573220afa8b763e401ad2188b94bd3326c34238400a0, claim_e8c10cabcef573ebd74615b6710a91caf95546400711bf460ca21c09d0f97c4f, claim_efa01972ca8eeaf95b985204913340d645113a7f80d9456f01f72b000658fd91 | evidence_41cefd02c54b41b7e1301b01dad76013b9ba4d7e72212d0e0114bf90119b5179, evidence_46cf32fa548efe4343769389a3b689c26cf82fad79668eaa3530526d61de9aff, evidence_61dc02df5f976ad117b21412698257c13e788363ed46ad64e7ebcfd39fbaa895, evidence_722fcb68ccbf504807494ad563777e293a33c3e93bbe694cb016d3abf8c2b172, evidence_931decfcdaa6ec1f2577672079b1f140dde62822435b15d68fcad1f471d329d8, evidence_a74fb0faf462ca8526d44f58e9ffca09b3d263969093878439804af9c722c5d1, evidence_e19a41a0e4e8793c507b8219c6310fe01c0aac33f381f88e3334fec1aa277988 |
| public_health | public_health selected 6 evidence references and 5 claim references from the coordinated assessment. These references support cautious association-oriented synthesis only. | claim_0d8e477d7698dd47897ef4f4ad43a2f42750763e5f04137e7a8eb0bb2febfa86, claim_5bde0a88a7f3f87f5e99959114e5d09aaedd2cc465554fcf1159e144d95bd5d8, claim_8c85d2d9e124c16e007a573220afa8b763e401ad2188b94bd3326c34238400a0, claim_e8c10cabcef573ebd74615b6710a91caf95546400711bf460ca21c09d0f97c4f, claim_efa01972ca8eeaf95b985204913340d645113a7f80d9456f01f72b000658fd91 | evidence_41cefd02c54b41b7e1301b01dad76013b9ba4d7e72212d0e0114bf90119b5179, evidence_46cf32fa548efe4343769389a3b689c26cf82fad79668eaa3530526d61de9aff, evidence_61dc02df5f976ad117b21412698257c13e788363ed46ad64e7ebcfd39fbaa895, evidence_722fcb68ccbf504807494ad563777e293a33c3e93bbe694cb016d3abf8c2b172, evidence_931decfcdaa6ec1f2577672079b1f140dde62822435b15d68fcad1f471d329d8, evidence_a74fb0faf462ca8526d44f58e9ffca09b3d263969093878439804af9c722c5d1 |

## Limitations

The report preserves upstream limitation codes and keeps interpretation bounded to structured, non-causal Polaris artifacts.

| Limitation Code |
| --- |
| HETEROSKEDASTICITY_WARNING |
| LIMITED_MODEL_SCOPE |
| MISSING_DATA_EXCLUSION |
| OBSERVATIONAL_ASSOCIATION |
| UNDEFINED_DIAGNOSTIC |
| UNSUPPORTED_GENERALIZATION |

## Evidence and Domain Gaps

| Gap ID | Type | Sources | Domains |
| --- | --- | --- | --- |
| coordination_evidence_gap_064150e4fa7eef182434adca63d4ffa9c5d98442b11390eb589b86ad2946be4e | cross_domain_claim_with_limited_domain_coverage | claim_e8c10cabcef573ebd74615b6710a91caf95546400711bf460ca21c09d0f97c4f | economics, education, public_health |
| coordination_evidence_gap_1460eb94af7ab5531385c71ad916551c6b30296a8207f32632719141b9069767 | cross_domain_claim_with_limited_domain_coverage | claim_0d8e477d7698dd47897ef4f4ad43a2f42750763e5f04137e7a8eb0bb2febfa86 | economics, education, public_health |
| coordination_evidence_gap_487532fac4b0caf246fbb4672e0be291262010290700be9926bb463043ccb2a9 | cross_domain_claim_with_limited_domain_coverage | claim_8c85d2d9e124c16e007a573220afa8b763e401ad2188b94bd3326c34238400a0 | economics, education, public_health |
| coordination_evidence_gap_a0cb7a15dd55b01dc3312c1683165102e947892d9af17ddc591a5187b2c33d3e | cross_domain_claim_with_limited_domain_coverage | claim_5bde0a88a7f3f87f5e99959114e5d09aaedd2cc465554fcf1159e144d95bd5d8 | economics, education, public_health |
| coordination_evidence_gap_d1f390114b79a70275b2066004f8a1ad537411509f89a928c8df4b72364b132e | cross_domain_claim_with_limited_domain_coverage | claim_efa01972ca8eeaf95b985204913340d645113a7f80d9456f01f72b000658fd91 | economics, education, public_health |
| coordination_evidence_gap_4e1f189047dd58677563dd9b59e3b83d1d943bb4361af5edfc87c01b2bd5346b | evidence_referenced_without_cross_domain_context | evidence_e19a41a0e4e8793c507b8219c6310fe01c0aac33f381f88e3334fec1aa277988 | education |
| coordination_evidence_gap_beb8acb07230631b45cdfb1eada61b51f6f30f3525c776f1af2174b777a69bd3 | evidence_referenced_without_cross_domain_context | evidence_01bbaeee60d46b4369b8c5a04e4f063b0dd28e5bbb9ee48ba3468a25c707f36d | economics |

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
| Source dataset | reporting_literacy_fertility_gdp_sample |
| Phase 3 DatasetIngestionResult | reporting_literacy_fertility_gdp_sample |
| Phase 4 AnalysisResult | analysis_5435f04b0ccc0ffe50b40a2f8060b49bb9eb83d850138c9a1f3e3ba31de0ba8e |
| Phase 5 EvidenceArtifact | evidence_artifact_8253963504702ba862b13ba4e20311c8a4123c0d36401743bb621a217776c190 |
| Phase 6 AgentAssessments | agent_assessment_15a05139ecdedb8c3c41de35c651b44ca1a9c553b1eb5d809642f60d248017df, agent_assessment_3017a729e13421e692471012d451153c4ef1264a13f506b07cae336625746e58, agent_assessment_4e8d30b61f7f0b1738adbba3015577cdeeaef13d1e05cd4347c87919ae7afa57, agent_assessment_e53e77cf82f9ac082d7d9f27266a1fe613de107af2333446464a4d9aba32fe4e |
| Phase 7 CoordinatedAssessment | coordinated_assessment_003cbf6edba757bd7662e6254502613e4a96ca6ad234b0616f5183b5dfd78462 |
| Phase 8 SynthesisArtifact | synthesis_85581f85f9d64c87966803e509b56746f1aaad80e1944e62704171855176a137 |
| Phase 9 ResearchReport | report_b3b4e2ad73bc66ed64736b0b0759336b28097dbe620070baee2252f81f22fe43 |

## Reference Index

| Reference ID | Kind | Label |
| --- | --- | --- |
| coordination_agreement_00b400f5624d99d337174e23ff6b5c3269d79865b38ffe829ea2c3191a3e7bc9 | agreement | Coordination agreement: shared_evidence |
| coordination_agreement_0d5c20c6a2eb647677bff281af55401291b4352a2d1e74f54003feff9008ab4d | agreement | Coordination agreement: shared_unsupported_inference |
| coordination_agreement_0ddbe89893bc6dbf748c9ea9b8fe8089941193949f19958be12f8cddb5bae457 | agreement | Coordination agreement: shared_limitation |
| coordination_agreement_0e6158669c3a5e2f495bd5e11c32ad03810ec1d7416eb442e811e15c4dcd143c | agreement | Coordination agreement: shared_unsupported_inference |
| coordination_agreement_0fd280eb8f8770f2a3042e0d322bf5f63116f83794f670a313437eb8e38ae48b | agreement | Coordination agreement: shared_evidence |
| coordination_agreement_22f8b7503b44b7b9a9c3854547d255eaf03b70b2b86d6c0b9ccc2ba174a45bf9 | agreement | Coordination agreement: shared_domain_concern |
| coordination_agreement_23a80585aad44d7b155fffe41f2599d07781dd8b775f911ada1760f8d3b6c5cf | agreement | Coordination agreement: shared_evidence |
| coordination_agreement_2493c94fb4443b6864a0e006f0da9197c56b5738135feea3890df3db25aa063e | agreement | Coordination agreement: shared_domain_concern |
| coordination_agreement_2793a57d85d1b5ec775e38f45de8785433d1f1e5f8199a3aedd511a9d1489af2 | agreement | Coordination agreement: shared_unsupported_inference |
| coordination_agreement_2cf5cc9245deb60d6f7e4dac422f12e02d75c063bc25ace7fb638dd9fe32917d | agreement | Coordination agreement: shared_claim |
| coordination_agreement_317ccbf082badbab4c7343679ce3f4043fb757b6b3ab39a953357117b1d5117d | agreement | Coordination agreement: shared_unsupported_inference |
| coordination_agreement_31ee2b1ad702b23f635d06641a8c5a36c71a2ae23836068808811c50e0b7759b | agreement | Coordination agreement: shared_unsupported_inference |
| coordination_agreement_3e29f08a15b36590c247c95533b3ac64c2fd9915e3a26678c85580eeecdea25f | agreement | Coordination agreement: shared_evidence |
| coordination_agreement_402415d3e391b03114cc267bd885c604c09b22eaafe36b72dfb9acc1527a80e4 | agreement | Coordination agreement: shared_domain_concern |
| coordination_agreement_53af29fe6454d0a88f8e51d541915d007a0abe12b57aeca8101aa53f577a1afa | agreement | Coordination agreement: shared_limitation |
| coordination_agreement_59a0010622d478a874d7f8503066153e84cbb9b54573ea5f0b14746f06c2e745 | agreement | Coordination agreement: shared_domain_concern |
| coordination_agreement_763c47e5bab98dfe0bf237359298ba3990ec23f662870869d2921bb3a02f5efb | agreement | Coordination agreement: shared_claim |
| coordination_agreement_790f5a12043ef2ffb2e7b549390e57679e90ad29ac60d227c88d63c4c0ca1ad4 | agreement | Coordination agreement: shared_domain_concern |
| coordination_agreement_7b74ed99c9d49794fd083e3ba9d6f03c98a5b34f56185c35e46cf5d135586af9 | agreement | Coordination agreement: shared_limitation |
| coordination_agreement_88e011ad86beb8003f86ec58cdef98127bb958e7a808d5724c1f0c6baf25d4ab | agreement | Coordination agreement: shared_domain_concern |
| coordination_agreement_8f81e2855a3ab110059911fe530d80b4aa711ba5f10d8be0a722e112b3d4e628 | agreement | Coordination agreement: shared_domain_concern |
| coordination_agreement_93b2d9734df56482d307414f8d438e4acf9cf9743c31eda172dc8571cca2a624 | agreement | Coordination agreement: shared_evidence |
| coordination_agreement_9799a4519b35bf0cd06641325de5a0c6d19bfc56c75778f6635c76dd0404582f | agreement | Coordination agreement: shared_claim |
| coordination_agreement_9bef5c426f7b40d6565aced8f60d1bccc247d61189a50057f3b39d5a52ec2326 | agreement | Coordination agreement: shared_limitation |
| coordination_agreement_aaeb5839d3f196f528aea51833dbdb51718492377b5d08c48ebe7055cacc66e2 | agreement | Coordination agreement: shared_limitation |
| coordination_agreement_aefc9822a00d44a2cbdd9852e561fd2a33180436357b97617c8c4174bbd124b1 | agreement | Coordination agreement: shared_unsupported_inference |
| coordination_agreement_bf456ff94d5b0b9bb8980b5e8d7d8c6dbfcde2eebaec02fca17654520b722524 | agreement | Coordination agreement: shared_claim |
| coordination_agreement_c46ca723a50f6b40bfe8b735f35bbabed2ceac6386de8232294d22a53e1d4083 | agreement | Coordination agreement: shared_evidence |
| coordination_agreement_c51aed08dcdcbb9794fe01969578d06e6154812508b18496b14709906c4e5a41 | agreement | Coordination agreement: shared_domain_concern |
| coordination_agreement_d27aa000ed644ff1525ae1662a3ebbabb4371b2145d814cb791ce5d58578867d | agreement | Coordination agreement: shared_domain_concern |
| coordination_agreement_daa339600ecd99f7d51a8da7ce724809c2111f8a3119e92109fffb72230b72d4 | agreement | Coordination agreement: shared_claim |
| coordination_agreement_e43130726f00e83bff182618642e064ab722b19c98d421a171cabe732f29b593 | agreement | Coordination agreement: shared_limitation |
| coordination_agreement_fd3cf8887ff29b4b991344879c2c275d97f06664887844b85c58ff6f81326e17 | agreement | Coordination agreement: shared_domain_concern |
| agent_assessment_15a05139ecdedb8c3c41de35c651b44ca1a9c553b1eb5d809642f60d248017df | assessment | Domain assessment: governance |
| agent_assessment_3017a729e13421e692471012d451153c4ef1264a13f506b07cae336625746e58 | assessment | Domain assessment: public_health |
| agent_assessment_4e8d30b61f7f0b1738adbba3015577cdeeaef13d1e05cd4347c87919ae7afa57 | assessment | Domain assessment: economics |
| agent_assessment_e53e77cf82f9ac082d7d9f27266a1fe613de107af2333446464a4d9aba32fe4e | assessment | Domain assessment: education |
| claim_0d8e477d7698dd47897ef4f4ad43a2f42750763e5f04137e7a8eb0bb2febfa86 | claim | Claim candidate: conditional_association |
| claim_54f6deed014d5a5c012a024bf94daac479e28151ce420698f6abd23b7c79a907 | claim | Claim candidate: model_limitation |
| claim_5bde0a88a7f3f87f5e99959114e5d09aaedd2cc465554fcf1159e144d95bd5d8 | claim | Claim candidate: statistical_uncertainty |
| claim_8c85d2d9e124c16e007a573220afa8b763e401ad2188b94bd3326c34238400a0 | claim | Claim candidate: statistical_uncertainty |
| claim_a6082af5be042bc66b0886cba000846711c211e4b101eb464e8ad01bb39f2f32 | claim | Claim candidate: model_limitation |
| claim_e8c10cabcef573ebd74615b6710a91caf95546400711bf460ca21c09d0f97c4f | claim | Claim candidate: statistical_uncertainty |
| claim_efa01972ca8eeaf95b985204913340d645113a7f80d9456f01f72b000658fd91 | claim | Claim candidate: conditional_association |
| coordination_divergence_083941fddd7551a2333f2c9513b80346596e5751493463e1ec34349990014442 | divergence | Coordination divergence: domain_specific_concern |
| coordination_divergence_0bb0d73a41848cf02271b435dccca38ba2b371204d751a33a3180bf123d8be2f | divergence | Coordination divergence: domain_specific_concern |
| coordination_divergence_14797eba421049fe64e500aa9a4f5b2aedd504498aa38462a21803908e287f3b | divergence | Coordination divergence: domain_specific_concern |
| coordination_divergence_1714f98c5c21613bd0acaae9815909a36ae48257e5b6a64da7cfae09f9a7ba2f | divergence | Coordination divergence: domain_specific_concern |
| coordination_divergence_1721974c1d96782bba0a40e646cb55d1072dbda4de7257663209f3a847468d33 | divergence | Coordination divergence: domain_specific_concern |
| coordination_divergence_1c278c146080b6f10001e48570c620cee46c45f2a97e8e12eb2db1ddbeea02b7 | divergence | Coordination divergence: domain_specific_concern |
| coordination_divergence_1c58583782a1bd76bc9dc0f4ffc488ab998174c40d9ff36d35b5d902698c087b | divergence | Coordination divergence: uneven_evidence_coverage |
| coordination_divergence_21586c2cc8e51c44d7f83f52b0808f7f7f569d3ccc164712ebee18d65b959034 | divergence | Coordination divergence: domain_specific_concern |
| coordination_divergence_2bb12b46456481c8c9566b427141a320bae1902a78cdb126353e1300d6507fc4 | divergence | Coordination divergence: different_relevance_classification |
| coordination_divergence_34e2575aa9e1e886a2b8e0a2549dca8486d971774425ab55f76d0909925c54d2 | divergence | Coordination divergence: different_relevance_classification |
| coordination_divergence_35aba9f57b7e42101d1291413dfa8fc224195ad7863e6a9ac316dee6d0b076d8 | divergence | Coordination divergence: domain_specific_concern |
| coordination_divergence_3ac2d411754d3b1bb17c790f3cbe24532d30489246b296ad9cfb63cadf21b842 | divergence | Coordination divergence: uneven_evidence_coverage |
| coordination_divergence_40403d8c745713e46f91c91e3ff851acc69eecb8183aaddaddaba5a01ea3402e | divergence | Coordination divergence: different_relevance_classification |
| coordination_divergence_429dde9a71247bd88cdbbe6b1ed1a29ad6f94414347acc462da4485f50c3016a | divergence | Coordination divergence: uneven_evidence_coverage |
| coordination_divergence_50fffccfec9c3bf4b88b8daa90aecd8ff4801b5645eca96233b10745d489ada9 | divergence | Coordination divergence: different_relevance_classification |
| coordination_divergence_5193fbfa3ac09efbf089506a8e66cd65767b411ee4005c1cb832f7262b057b8e | divergence | Coordination divergence: uneven_evidence_coverage |
| coordination_divergence_54f3788c3e114c5b6f6feab3f052d2f1d9d1d27dc864e3a2a92c4e4509b727ae | divergence | Coordination divergence: different_relevance_classification |
| coordination_divergence_56fcc214f0f90b7980170c19c960d652a416976feaee8c61a726a15c4b7df5f8 | divergence | Coordination divergence: domain_specific_unsupported_inference |
| coordination_divergence_57e3d17f04a632c28354820869b0a9a58eb70fa78c47ecac18b133d51f51b9a1 | divergence | Coordination divergence: uneven_evidence_coverage |
| coordination_divergence_582a239488b27cfc9f42654981dead6c303246cbedbf4b159700be5ada32588d | divergence | Coordination divergence: uneven_evidence_coverage |
| coordination_divergence_588b68deefd88feed70ef7408760c0f6e954891d9a6d2dd77007978a80493147 | divergence | Coordination divergence: different_relevance_classification |
| coordination_divergence_5d01a16ebb90b928532bb2e613ada447b46e0850222663bb729406d3d642cdaa | divergence | Coordination divergence: domain_specific_limitation |
| coordination_divergence_5d9c23527cf90d6255b983d0e658acd0e4f20eca3721e83a02959eee63bda546 | divergence | Coordination divergence: different_relevance_classification |
| coordination_divergence_5f3b8f69c2465b9497e517801aab17fe9d5736953c5082aadb23018dafdf8a6f | divergence | Coordination divergence: domain_specific_unsupported_inference |
| coordination_divergence_6667d9260c0c4bb19eda10585c3165a39d271714aa3f1c16c14322ae0bb92199 | divergence | Coordination divergence: uneven_evidence_coverage |
| coordination_divergence_666ecd23fb2707c600be5fffcf56ef63a668411b82385745d6c839ec6afdeec5 | divergence | Coordination divergence: different_relevance_classification |
| coordination_divergence_670eebc39901094abfeec3815d3c7f3779625c14c6d47e461e8a46ad70d8305e | divergence | Coordination divergence: domain_specific_concern |
| coordination_divergence_6827acf80b5632fb71840707c32c3903260dde3cb3621c927397f00694cb1fcf | divergence | Coordination divergence: uneven_evidence_coverage |
| coordination_divergence_68fc234e1502df267c2b9096a346bc9e7b9f1459bed8360c36499695d8599543 | divergence | Coordination divergence: domain_specific_concern |
| coordination_divergence_69abacdb401e8bed9d891f052870fdaa3ad2c16b917f242dd81dc21b9d8b7737 | divergence | Coordination divergence: different_relevance_classification |
| coordination_divergence_6b77a24489a0b92e03c8de1baf7eacb41100ea41e098cbcdaf13c0ac0b85b360 | divergence | Coordination divergence: domain_specific_concern |
| coordination_divergence_7e47e1fa4b88d53714fedaace54b2d756470c1600871662252d115d3db269106 | divergence | Coordination divergence: domain_specific_limitation |
| coordination_divergence_80f1b10081fed50092a4ca73fe6d65e3d02c7cd2fa65df6e11b06102c194aa39 | divergence | Coordination divergence: different_relevance_classification |
| coordination_divergence_841acdb7416dc8df5a1d0d5abba9dfb29981431f85cbc611ef79fb5578904c42 | divergence | Coordination divergence: different_relevance_classification |
| coordination_divergence_95c719b766102b039cceb056dad8e2b49db52dcf3b6656194a7f41ea16adc107 | divergence | Coordination divergence: uneven_evidence_coverage |
| coordination_divergence_968717e9480da01b935011880d310c75d2ff859adb93fb2a60d22b1639ee5b0d | divergence | Coordination divergence: domain_specific_limitation |
| coordination_divergence_9ac725d0c875cf349be31b30efc55987bac59d4171ffbeb53108242d64115952 | divergence | Coordination divergence: uneven_evidence_coverage |
| coordination_divergence_9decd4edfcd89a8970ed969e1f89d23c3747008646ab28fe598f61851a9f190a | divergence | Coordination divergence: uneven_evidence_coverage |
| coordination_divergence_9f2092a0f4ea376bd2d942a85281391dac963bf1cea43c53f73d455975bc9aa9 | divergence | Coordination divergence: domain_specific_limitation |
| coordination_divergence_9f4612eceb39c925baff993233b0f78994d45338001d0ee00c7519cc2af525a0 | divergence | Coordination divergence: different_relevance_classification |
| coordination_divergence_c1e4afd7d344005941ad65a2a3b4f995261d7eb54d34a8f308d112c25df33ea8 | divergence | Coordination divergence: different_relevance_classification |
| coordination_divergence_c6a2b6756da845b850a4cc49a3d9b6d9c381d4ae46dfb7255c64fff755bfd1eb | divergence | Coordination divergence: domain_specific_limitation |
| coordination_divergence_df79bd1345863856313b6ecd000d9b448f52d66327af0dd19aeb1b1da5d46de9 | divergence | Coordination divergence: uneven_evidence_coverage |
| coordination_divergence_e5e4dd8b3c4e8e7e133a7a8c37a1de12545c50b697051589596687eb706e14d0 | divergence | Coordination divergence: uneven_evidence_coverage |
| coordination_divergence_f82ed5e670d3e834dee8fb002d622ad5d11aa4834de7dcf86dd6b835fcbbdc50 | divergence | Coordination divergence: domain_specific_limitation |
| evidence_01bbaeee60d46b4369b8c5a04e4f063b0dd28e5bbb9ee48ba3468a25c707f36d | evidence | Evidence record: model_diagnostic |
| evidence_3e8661fcb72dd051fe38076c5a2518b558e0283c6f4092a3dfd5428406df7d26 | evidence | Evidence record: model_diagnostic |
| evidence_41cefd02c54b41b7e1301b01dad76013b9ba4d7e72212d0e0114bf90119b5179 | evidence | Evidence record: analysis_warning |
| evidence_46cf32fa548efe4343769389a3b689c26cf82fad79668eaa3530526d61de9aff | evidence | Evidence record: sample_quality |
| evidence_61dc02df5f976ad117b21412698257c13e788363ed46ad64e7ebcfd39fbaa895 | evidence | Evidence record: regression_coefficient |
| evidence_722fcb68ccbf504807494ad563777e293a33c3e93bbe694cb016d3abf8c2b172 | evidence | Evidence record: regression_coefficient |
| evidence_931decfcdaa6ec1f2577672079b1f140dde62822435b15d68fcad1f471d329d8 | evidence | Evidence record: model_fit |
| evidence_a74fb0faf462ca8526d44f58e9ffca09b3d263969093878439804af9c722c5d1 | evidence | Evidence record: regression_coefficient |
| evidence_acc8821b3744480f343a24e9c30d75abcd869af879fc8d010f1cd4fd4bb1463f | evidence | Evidence record: model_diagnostic |
| evidence_b7405ec1b71828a6948bdbdabd106ed2529ab5c7931dd96a95319129989d46d5 | evidence | Evidence record: model_diagnostic |
| evidence_b97e16b92b3cfe31f37fa2ead83eec077d10bd1a733a20e5ddecb9d8faa85907 | evidence | Evidence record: model_diagnostic |
| evidence_d67711c7b6b55f032105c87233543f7174c21c8cbb93c7d70b2e36c4c10b0341 | evidence | Evidence record: model_diagnostic |
| evidence_e19a41a0e4e8793c507b8219c6310fe01c0aac33f381f88e3334fec1aa277988 | evidence | Evidence record: model_diagnostic |
| coordination_domain_gap_c9e63a4ccc57d28d9be7245855b73d2c9a9ad4e641dd42e4aca177f658bd8758 | gap | Domain gap: governance |
| coordination_evidence_gap_064150e4fa7eef182434adca63d4ffa9c5d98442b11390eb589b86ad2946be4e | gap | Evidence gap: cross_domain_claim_with_limited_domain_coverage |
| coordination_evidence_gap_1460eb94af7ab5531385c71ad916551c6b30296a8207f32632719141b9069767 | gap | Evidence gap: cross_domain_claim_with_limited_domain_coverage |
| coordination_evidence_gap_487532fac4b0caf246fbb4672e0be291262010290700be9926bb463043ccb2a9 | gap | Evidence gap: cross_domain_claim_with_limited_domain_coverage |
| coordination_evidence_gap_4e1f189047dd58677563dd9b59e3b83d1d943bb4361af5edfc87c01b2bd5346b | gap | Evidence gap: evidence_referenced_without_cross_domain_context |
| coordination_evidence_gap_a0cb7a15dd55b01dc3312c1683165102e947892d9af17ddc591a5187b2c33d3e | gap | Evidence gap: cross_domain_claim_with_limited_domain_coverage |
| coordination_evidence_gap_beb8acb07230631b45cdfb1eada61b51f6f30f3525c776f1af2174b777a69bd3 | gap | Evidence gap: evidence_referenced_without_cross_domain_context |
| coordination_evidence_gap_d1f390114b79a70275b2066004f8a1ad537411509f89a928c8df4b72364b132e | gap | Evidence gap: cross_domain_claim_with_limited_domain_coverage |
| analysis_5435f04b0ccc0ffe50b40a2f8060b49bb9eb83d850138c9a1f3e3ba31de0ba8e | source_artifact | Source Polaris artifact |
| coordinated_assessment_003cbf6edba757bd7662e6254502613e4a96ca6ad234b0616f5183b5dfd78462 | source_artifact | Source Polaris artifact |
| evidence_artifact_8253963504702ba862b13ba4e20311c8a4123c0d36401743bb621a217776c190 | source_artifact | Source Polaris artifact |
| reporting_literacy_fertility_gdp_sample | source_artifact | Source Polaris artifact |
| synthesis_85581f85f9d64c87966803e509b56746f1aaad80e1944e62704171855176a137 | source_artifact | Source Polaris artifact |
