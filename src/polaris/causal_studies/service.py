"""Public service API for Phase 23 causal-study metadata."""

from __future__ import annotations

from pathlib import Path

from polaris.causal_studies.models import CausalStudySearchQuery, DesignReadinessAssessment
from polaris.causal_studies.readiness import assess_design_readiness
from polaris.causal_studies.registry import (
    CausalStudyRegistry,
    load_causal_study_registry,
)
from polaris.ingestion.models import DatasetIngestionResult
from polaris.registry import DatasetRegistry


def list_causal_studies(
    *,
    registry: CausalStudyRegistry | None = None,
    query: CausalStudySearchQuery | None = None,
) -> tuple[dict[str, object], ...]:
    active = registry or load_causal_study_registry()
    return tuple(
        {
            "study_id": study.study_id,
            "title": study.title,
            "intervention_id": study.intervention.intervention_id,
            "intervention_type": study.intervention.intervention_type.value,
            "review_status": study.review_status.value,
            "treated_entities": tuple(
                item.entity_id
                for item in study.treatment_assignments
                if item.treatment_status.value == "treated"
            ),
            "treatment_year": study.treatment_timing_rule.analysis_treatment_year,
        }
        for study in active.search(query)
    )


def inspect_causal_study(
    study_id: str,
    *,
    registry: CausalStudyRegistry | None = None,
) -> dict[str, object]:
    active = registry or load_causal_study_registry()
    study = active.get_study(study_id)
    return study.model_dump(mode="json")


def assess_causal_study_readiness(
    study_id: str,
    *,
    registry: CausalStudyRegistry | None = None,
    dataset_registry: DatasetRegistry | None = None,
    ingestion_results: tuple[DatasetIngestionResult, ...] = (),
    dataset_id: str | None = None,
) -> DesignReadinessAssessment:
    active = registry or load_causal_study_registry()
    return assess_design_readiness(
        active.get_study(study_id),
        registry=dataset_registry,
        ingestion_results=ingestion_results,
        dataset_id=dataset_id,
    )


def load_registry_from(path: Path | str) -> CausalStudyRegistry:
    return load_causal_study_registry(path)
