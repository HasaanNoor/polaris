"""Public Phase 5 evidence extraction service."""

from datetime import UTC, datetime

from polaris import __version__
from polaris.analysis.causal.models import CausalAnalysisResult
from polaris.analysis.models import (
    AnalysisResult,
    CorrelationAnalysisResult,
    DescriptiveAnalysisResult,
    OLSRegressionResult,
    PanelRegressionResult,
)
from polaris.analysis.robustness.models import RobustnessAnalysisResult
from polaris.evidence.claims import generate_claim_candidates
from polaris.evidence.extractors import extract_evidence_records
from polaris.evidence.models import (
    EVIDENCE_SCHEMA_VERSION,
    EvidenceArtifact,
    ExtractionFinding,
    ExtractionFindingCode,
)
from polaris.evidence.provenance import artifact_id, evidence_provenance


def extract_evidence(
    *,
    analysis_result: AnalysisResult | CausalAnalysisResult,
    robustness_result: RobustnessAnalysisResult | None = None,
) -> EvidenceArtifact:
    """Convert a supported Phase 4 analysis result into evidence and claims."""

    _validate_supported_result(analysis_result)
    timestamp = datetime.now(UTC)
    provenance = evidence_provenance(analysis_result, extraction_timestamp=timestamp)
    evidence_records = extract_evidence_records(
        analysis_result,
        robustness_result=robustness_result,
        extraction_timestamp=timestamp,
    )
    claim_candidates = generate_claim_candidates(
        analysis_result,
        evidence_records,
        extraction_timestamp=timestamp,
    )
    findings = (
        ExtractionFinding(
            code=ExtractionFindingCode.EVIDENCE_EXTRACTED,
            message="structured evidence records were extracted deterministically",
            evidence_ids=tuple(record.evidence_id for record in evidence_records),
        ),
        ExtractionFinding(
            code=ExtractionFindingCode.CLAIM_GENERATED,
            message="bounded claim candidates were generated deterministically",
            claim_ids=tuple(claim.claim_id for claim in claim_candidates),
        ),
    )
    return EvidenceArtifact(
        artifact_id=artifact_id(_source_result_id(analysis_result)),
        source_analysis_result_id=_source_result_id(analysis_result),
        dataset_id=analysis_result.dataset_id,
        source_checksum_sha256=analysis_result.source_checksum_sha256,
        evidence_records=evidence_records,
        claim_candidates=claim_candidates,
        extraction_findings=findings,
        provenance=provenance,
        extraction_timestamp=timestamp,
        software_version=f"polaris-{__version__}",
        schema_version=EVIDENCE_SCHEMA_VERSION,
    )


def _validate_supported_result(analysis_result: AnalysisResult) -> None:
    if isinstance(analysis_result, CausalAnalysisResult):
        return
    if not isinstance(
        analysis_result.method_result,
        DescriptiveAnalysisResult
        | CorrelationAnalysisResult
        | OLSRegressionResult
        | PanelRegressionResult,
    ):
        # The current AnalysisResult union should make this unreachable. The branch is
        # deliberately explicit so future Phase 4 result types cannot be ignored.
        from polaris.evidence.errors import UnsupportedEvidenceSourceError

        raise UnsupportedEvidenceSourceError(
            "Phase 5 does not support this Phase 4 result type",
            analysis_result_id=_source_result_id(analysis_result),
        )


def _source_result_id(analysis_result: AnalysisResult | CausalAnalysisResult) -> str:
    return (
        analysis_result.result_id
        if isinstance(analysis_result, AnalysisResult)
        else analysis_result.causal_analysis_id
    )
