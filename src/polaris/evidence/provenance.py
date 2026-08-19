"""Evidence provenance and deterministic identity helpers."""

import hashlib
import json
import math
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from polaris import __version__
from polaris.analysis.causal.models import CausalAnalysisResult
from polaris.analysis.models import AnalysisResult
from polaris.evidence.models import EVIDENCE_SCHEMA_VERSION, EvidenceProvenance
from polaris.schemas.common import StatisticalProcedure


def evidence_provenance(
    analysis_result: AnalysisResult | CausalAnalysisResult,
    *,
    extraction_timestamp: datetime | None = None,
) -> EvidenceProvenance:
    timestamp = extraction_timestamp or datetime.now(UTC)
    return EvidenceProvenance(
        dataset_id=analysis_result.dataset_id,
        source_checksum_sha256=analysis_result.source_checksum_sha256,
        source_analysis_result_id=_source_result_id(analysis_result),
        statistical_procedure=_procedure(analysis_result),
        phase4_schema_version=analysis_result.schema_version,
        extraction_timestamp=timestamp,
        software_version=f"polaris-{__version__}",
    )


def _source_result_id(analysis_result: AnalysisResult | CausalAnalysisResult) -> str:
    return (
        analysis_result.result_id
        if isinstance(analysis_result, AnalysisResult)
        else analysis_result.causal_analysis_id
    )


def _procedure(analysis_result: AnalysisResult | CausalAnalysisResult) -> StatisticalProcedure:
    if isinstance(analysis_result, AnalysisResult):
        return analysis_result.analysis_method
    if analysis_result.method.value == "event_study":
        return StatisticalProcedure.EVENT_STUDY
    return StatisticalProcedure.DIFFERENCE_IN_DIFFERENCES


def deterministic_id(prefix: str, payload: dict[str, Any]) -> str:
    canonical = json.dumps(
        _canonicalize(payload),
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return prefix + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def evidence_id(payload: dict[str, Any]) -> str:
    return deterministic_id("evidence_", {**payload, "schema_version": EVIDENCE_SCHEMA_VERSION})


def claim_id(payload: dict[str, Any]) -> str:
    return deterministic_id("claim_", {**payload, "schema_version": EVIDENCE_SCHEMA_VERSION})


def artifact_id(source_analysis_result_id: str) -> str:
    return deterministic_id(
        "evidence_artifact_",
        {
            "source_analysis_result_id": source_analysis_result_id,
            "schema_version": EVIDENCE_SCHEMA_VERSION,
        },
    )


def _canonicalize(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(key): _canonicalize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_canonicalize(item) for item in value]
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("deterministic IDs cannot include non-finite floats")
        return value
    return value
