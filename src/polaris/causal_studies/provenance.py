"""Deterministic provenance helpers for causal-study metadata."""

from __future__ import annotations

from typing import Any

from polaris.causal_studies.models import (
    CAUSAL_STUDY_RULESET_VERSION,
    CAUSAL_STUDY_SCHEMA_VERSION,
    CausalStudyDefinition,
    DesignReadinessAssessment,
    deterministic_id,
)


def deterministic_intervention_id_payload(study: CausalStudyDefinition) -> dict[str, Any]:
    intervention = study.intervention
    return intervention.model_dump(mode="json", exclude={"intervention_id"})


def deterministic_study_id_payload(study: CausalStudyDefinition) -> dict[str, Any]:
    payload = study.model_dump(mode="json")
    payload.pop("study_id", None)
    if isinstance(payload.get("intervention"), dict):
        payload["intervention"].pop("intervention_id", None)
    return payload


def deterministic_assessment_id_payload(assessment: DesignReadinessAssessment) -> dict[str, Any]:
    return assessment.model_dump(mode="json", exclude={"assessment_id"})


def intervention_id_for(study: CausalStudyDefinition) -> str:
    return deterministic_id("intervention", deterministic_intervention_id_payload(study))


def study_id_for(study: CausalStudyDefinition) -> str:
    return deterministic_id("study", deterministic_study_id_payload(study))


def assessment_id_for_payload(payload: dict[str, Any]) -> str:
    return deterministic_id("readiness", payload)


def registry_provenance(study: CausalStudyDefinition) -> dict[str, Any]:
    source_ids = tuple(
        sorted(
            {
                *study.source_ids,
                *study.intervention.source_ids,
                *[source.source_id for source in study.sources],
                *[
                    source_id
                    for assignment in study.treatment_assignments
                    for source_id in assignment.assignment_source_ids
                ],
            }
        )
    )
    return {
        "study_id": study.study_id,
        "intervention_id": study.intervention.intervention_id,
        "treatment_source_ids": source_ids,
        "assignment_source_ids": tuple(
            sorted(
                {
                    source_id
                    for assignment in study.treatment_assignments
                    for source_id in assignment.assignment_source_ids
                }
            )
        ),
        "review_status": study.review_status.value,
        "registry_schema_version": CAUSAL_STUDY_SCHEMA_VERSION,
        "registry_ruleset_version": CAUSAL_STUDY_RULESET_VERSION,
    }
