"""Deterministic file-backed causal-study registry."""

from __future__ import annotations

import json
from collections import OrderedDict
from collections.abc import Iterable
from pathlib import Path

from polaris.causal_studies.errors import CausalStudyError, CausalStudyNotFoundError
from polaris.causal_studies.models import (
    CausalStudyDefinition,
    CausalStudyFinding,
    CausalStudySearchQuery,
    FindingCode,
    FindingSeverity,
)
from polaris.causal_studies.validation import validate_study

DEFAULT_REGISTRY_DIR = Path("data/causal_studies")


class CausalStudyRegistry:
    """Ordered in-memory registry of reviewed treatment metadata definitions."""

    def __init__(self, studies: Iterable[CausalStudyDefinition] = ()) -> None:
        self._studies: OrderedDict[str, CausalStudyDefinition] = OrderedDict()
        self._registry_findings: tuple[CausalStudyFinding, ...] = ()
        self.register_many(studies)

    @property
    def count(self) -> int:
        return len(self._studies)

    def register_many(self, studies: Iterable[CausalStudyDefinition]) -> None:
        findings: list[CausalStudyFinding] = list(self._registry_findings)
        for study in sorted(studies, key=lambda item: item.study_id):
            if study.study_id in self._studies:
                findings.append(
                    CausalStudyFinding(
                        code=FindingCode.DUPLICATE_STUDY_ID,
                        severity=FindingSeverity.BLOCKING,
                        message=f"duplicate study ID: {study.study_id}",
                    )
                )
                continue
            if any(
                existing.intervention.intervention_id == study.intervention.intervention_id
                for existing in self._studies.values()
            ):
                findings.append(
                    CausalStudyFinding(
                        code=FindingCode.DUPLICATE_INTERVENTION_ID,
                        severity=FindingSeverity.BLOCKING,
                        message=f"duplicate intervention ID: {study.intervention.intervention_id}",
                    )
                )
                continue
            self._studies[study.study_id] = study
        self._registry_findings = tuple(findings)

    def list_studies(self) -> tuple[CausalStudyDefinition, ...]:
        return tuple(self._studies.values())

    def get_study(self, study_id: str) -> CausalStudyDefinition:
        try:
            return self._studies[study_id]
        except KeyError as exc:
            raise CausalStudyNotFoundError(f"unknown causal study: {study_id}") from exc

    def search(
        self, query: CausalStudySearchQuery | None = None
    ) -> tuple[CausalStudyDefinition, ...]:
        active = query or CausalStudySearchQuery()
        results = [study for study in self._studies.values() if _matches(study, active)]
        return tuple(sorted(results, key=lambda item: item.study_id))

    def validate_study(self, study_id: str) -> tuple[CausalStudyFinding, ...]:
        return validate_study(self.get_study(study_id))

    def registry_findings(self) -> tuple[CausalStudyFinding, ...]:
        return self._registry_findings


def load_causal_study_registry(path: Path | str = DEFAULT_REGISTRY_DIR) -> CausalStudyRegistry:
    root = Path(path)
    if not root.exists():
        return CausalStudyRegistry()
    studies: list[CausalStudyDefinition] = []
    for file_path in sorted(root.glob("*.json")):
        try:
            payload = json.loads(file_path.read_text(encoding="utf-8"))
            items = payload if isinstance(payload, list) else [payload]
            studies.extend(CausalStudyDefinition.model_validate(item) for item in items)
        except Exception as exc:
            raise CausalStudyError(f"failed to load causal-study file {file_path}") from exc
    return CausalStudyRegistry(studies)


def _matches(study: CausalStudyDefinition, query: CausalStudySearchQuery) -> bool:
    if (
        query.intervention_types
        and study.intervention.intervention_type not in query.intervention_types
    ):
        return False
    if query.geography:
        geography = " ".join(
            item
            for item in (
                study.intervention.geographic_scope,
                *study.intervention.treated_entities,
                *study.explicit_comparison_entities,
            )
            if item
        ).casefold()
        if not all(item.casefold() in geography for item in query.geography):
            return False
    if query.treated_entities:
        treated = {
            item.entity_id
            for item in study.treatment_assignments
            if item.treatment_status.value == "treated"
        }
        if not set(query.treated_entities) <= treated:
            return False
    if query.treatment_years:
        starts = {
            int(item.treatment_start)
            for item in study.treatment_assignments
            if item.treatment_start is not None
        }
        if not set(query.treatment_years) & starts:
            return False
    if query.outcome_domains:
        text = " ".join(
            item.label or item.variable_id for item in study.proposed_outcomes
        ).casefold()
        if not any(domain.casefold() in text for domain in query.outcome_domains):
            return False
    if query.providers:
        providers = {
            item.provider.casefold()
            for item in (*study.proposed_outcomes, *study.proposed_covariates)
            if item.provider
        }
        if not {item.casefold() for item in query.providers} & providers:
            return False
    if query.review_statuses and study.review_status not in query.review_statuses:
        return False
    if query.readiness_statuses:
        return False
    return True
