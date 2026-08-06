"""Compatibility validation for reviewed harmonization variable mappings."""

from __future__ import annotations

from polaris.harmonization.models import (
    CompatibilityStatus,
    HarmonizationFinding,
    HarmonizationFindingCode,
    HarmonizationRequest,
    HarmonizationSeverity,
    TransformationRule,
)


def validate_variable_compatibility(
    request: HarmonizationRequest,
) -> tuple[HarmonizationFinding, ...]:
    """Validate requested mappings without guessing equivalence."""

    findings: list[HarmonizationFinding] = []
    manifests = {
        result.dataset_manifest.dataset_id: result.dataset_manifest
        for result in request.ingestion_results
    }
    seen: set[tuple[str, str]] = set()
    precedence_variables = {rule.canonical_variable_id for rule in request.provider_precedence}
    canonical_sources: dict[str, set[str]] = {}

    for mapping in request.variable_mappings:
        manifest = manifests[mapping.source_dataset_id]
        declared = {variable.variable_id: variable for variable in manifest.variables}
        source_columns = {
            variable.source_field_name or variable.variable_id for variable in manifest.variables
        }
        if (
            mapping.source_variable_id not in declared
            and mapping.source_field_name not in source_columns
        ):
            findings.append(
                HarmonizationFinding(
                    severity=HarmonizationSeverity.FATAL,
                    code=HarmonizationFindingCode.VARIABLE_NOT_FOUND,
                    message=(
                        f"source variable {mapping.source_variable_id} is not declared by "
                        f"{mapping.source_dataset_id}"
                    ),
                    dataset_id=mapping.source_dataset_id,
                    provider=mapping.source_provider,
                    canonical_variable_id=mapping.canonical_variable_id,
                )
            )
        if mapping.compatibility_status is not CompatibilityStatus.COMPATIBLE:
            findings.append(
                HarmonizationFinding(
                    severity=HarmonizationSeverity.FATAL,
                    code=HarmonizationFindingCode.NO_COMPATIBLE_VARIABLES,
                    message=f"mapping {mapping.canonical_variable_id} is not marked compatible",
                    dataset_id=mapping.source_dataset_id,
                    provider=mapping.source_provider,
                    canonical_variable_id=mapping.canonical_variable_id,
                )
            )
        if request.strictness.require_unit_match and mapping.source_unit != mapping.canonical_unit:
            findings.append(
                HarmonizationFinding(
                    severity=HarmonizationSeverity.FATAL,
                    code=HarmonizationFindingCode.UNIT_MISMATCH,
                    message=f"unit mismatch for {mapping.canonical_variable_id}",
                    dataset_id=mapping.source_dataset_id,
                    provider=mapping.source_provider,
                    canonical_variable_id=mapping.canonical_variable_id,
                )
            )
        if request.strictness.require_definition and not mapping.conceptual_definition.strip():
            findings.append(
                HarmonizationFinding(
                    severity=HarmonizationSeverity.FATAL,
                    code=HarmonizationFindingCode.DEFINITION_MISMATCH,
                    message=f"definition is required for {mapping.canonical_variable_id}",
                    dataset_id=mapping.source_dataset_id,
                    provider=mapping.source_provider,
                    canonical_variable_id=mapping.canonical_variable_id,
                )
            )
        if mapping.transformation_rule not in {
            TransformationRule.NONE,
            TransformationRule.RENAME_ONLY,
            TransformationRule.PERCENT_TO_PROPORTION,
            TransformationRule.PROPORTION_TO_PERCENT,
        }:
            findings.append(
                HarmonizationFinding(
                    severity=HarmonizationSeverity.FATAL,
                    code=HarmonizationFindingCode.DEFINITION_MISMATCH,
                    message=f"unsupported transformation for {mapping.canonical_variable_id}",
                    dataset_id=mapping.source_dataset_id,
                    provider=mapping.source_provider,
                    canonical_variable_id=mapping.canonical_variable_id,
                )
            )
        duplicate_key = (mapping.source_dataset_id, mapping.canonical_variable_id)
        if duplicate_key in seen:
            findings.append(
                HarmonizationFinding(
                    severity=HarmonizationSeverity.FATAL,
                    code=HarmonizationFindingCode.DUPLICATE_COUNTRY_YEAR,
                    message=f"duplicate mapping for {mapping.canonical_variable_id}",
                    dataset_id=mapping.source_dataset_id,
                    provider=mapping.source_provider,
                    canonical_variable_id=mapping.canonical_variable_id,
                )
            )
        seen.add(duplicate_key)
        canonical_sources.setdefault(mapping.canonical_variable_id, set()).add(
            mapping.source_provider
        )

    for canonical_variable_id, providers in sorted(canonical_sources.items()):
        if len(providers) > 1 and canonical_variable_id not in precedence_variables:
            findings.append(
                HarmonizationFinding(
                    severity=HarmonizationSeverity.FATAL,
                    code=HarmonizationFindingCode.CONFLICTING_SOURCE_VALUES,
                    message=(
                        f"{canonical_variable_id} maps multiple providers "
                        "without explicit precedence"
                    ),
                    canonical_variable_id=canonical_variable_id,
                )
            )
    return tuple(findings)
