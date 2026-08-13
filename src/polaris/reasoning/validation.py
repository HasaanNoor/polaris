"""Structured validation and guardrails for Phase 18 reasoning."""

import re

from pydantic import ValidationError

from polaris.reasoning.errors import GroundingValidationError, ReasoningValidationError
from polaris.reasoning.grounding import ReasoningGroundingIndex
from polaris.reasoning.models import (
    ReasoningRequest,
    ReasoningStatement,
    ReasoningValidationFinding,
    StructuredReasoningResponse,
)
from polaris.reasoning.taxonomy import CausalStatus, ReasoningCategory
from polaris.schemas.common import WarningSeverity

_BLOCKED_CAUSAL_PATTERNS = (
    re.compile(r"\bcauses?\b", re.IGNORECASE),
    re.compile(r"\bcaused\s+by\b", re.IGNORECASE),
    re.compile(r"\bleads?\s+to\b", re.IGNORECASE),
    re.compile(r"\bresults?\s+in\b", re.IGNORECASE),
    re.compile(r"\bdrives?\b", re.IGNORECASE),
    re.compile(r"\bimproves?\b", re.IGNORECASE),
    re.compile(r"\bworsens?\b", re.IGNORECASE),
    re.compile(r"\bimpact\s+of\b", re.IGNORECASE),
    re.compile(r"\beffect\s+of\b", re.IGNORECASE),
)
_ALLOWED_CAUSAL_CONTEXTS = (
    "causal effect is not established",
    "causal effect cannot be inferred",
    "causality is not established",
    "causality was not established",
    "causal inference is unsupported",
    "does not establish causation",
    "not causal proof",
    "causal_status = not_established",
)
_POLICY_PATTERNS = (
    re.compile(r"\bpolicy should\b", re.IGNORECASE),
    re.compile(r"\bpolicies should\b", re.IGNORECASE),
    re.compile(r"\bgovernments? should\b", re.IGNORECASE),
    re.compile(r"\bgovernments? must\b", re.IGNORECASE),
    re.compile(r"\brecommend(?:s|ed|ation)?\b", re.IGNORECASE),
)
_MEDICAL_PATTERNS = (
    re.compile(r"\bmedical advice\b", re.IGNORECASE),
    re.compile(r"\bclinicians? should\b", re.IGNORECASE),
    re.compile(r"\bpatients? should\b", re.IGNORECASE),
    re.compile(r"\btreatment should\b", re.IGNORECASE),
    re.compile(r"\bdiagnos(?:e|is)\b", re.IGNORECASE),
)


def parse_provider_response(
    response: StructuredReasoningResponse | dict,
) -> StructuredReasoningResponse:
    if isinstance(response, StructuredReasoningResponse):
        return response
    try:
        return StructuredReasoningResponse.model_validate(response)
    except ValidationError as exc:
        raise ReasoningValidationError("provider returned malformed structured reasoning") from exc


def validate_reasoning_response(
    response: StructuredReasoningResponse,
    request: ReasoningRequest,
) -> tuple[ReasoningValidationFinding, ...]:
    findings: list[ReasoningValidationFinding] = []
    index = ReasoningGroundingIndex(
        evidence_artifact=request.evidence_artifact,
        coordinated_assessment=request.coordinated_assessment,
        literature_context=request.literature_context,
    )
    if not response.reasoning_statements:
        findings.append(
            _finding(
                "EMPTY_REASONING_RESPONSE",
                "Provider reasoning response did not include substantive statements.",
            )
        )
    ids = [statement.statement_id for statement in response.reasoning_statements]
    if len(ids) != len(set(ids)):
        findings.append(_finding("DUPLICATED_STATEMENT_ID", "Statement IDs must be unique."))
    for statement in response.reasoning_statements:
        findings.extend(validate_statement(statement, request, index))
    _validate_contradictions(response, index, findings)
    _validate_confounders(response, index, findings)
    if any(finding.severity is WarningSeverity.HIGH for finding in findings):
        raise GroundingValidationError("reasoning failed grounding or guardrail validation")
    return tuple(findings)


def validate_statement(
    statement: ReasoningStatement,
    request: ReasoningRequest,
    index: ReasoningGroundingIndex,
) -> tuple[ReasoningValidationFinding, ...]:
    findings: list[ReasoningValidationFinding] = []
    if statement.category not in set(request.requested_categories):
        findings.append(
            _finding(
                "UNREQUESTED_CATEGORY",
                "Reasoning statement used a category not requested by configuration.",
                (statement.statement_id,),
            )
        )
    missing = index.unsupported_ids(statement)
    if missing:
        findings.append(
            _finding(
                "UNSUPPORTED_GROUNDING",
                "Reasoning statement referenced unknown grounding IDs.",
                missing,
            )
        )
    if request.strictness.reject_unsupported_causal_language:
        causal_message = causal_language_violation(statement)
        if causal_message is not None:
            findings.append(
                _finding(
                    "CAUSAL_GUARD_VIOLATION",
                    causal_message,
                    (statement.statement_id,),
                )
            )
    if request.strictness.reject_policy_recommendations and any(
        pattern.search(statement.text) for pattern in _POLICY_PATTERNS
    ):
        findings.append(
            _finding(
                "POLICY_RECOMMENDATION_VIOLATION",
                "Reasoning introduced a prohibited policy recommendation.",
                (statement.statement_id,),
            )
        )
    if request.strictness.reject_medical_recommendations and any(
        pattern.search(statement.text) for pattern in _MEDICAL_PATTERNS
    ):
        findings.append(
            _finding(
                "MEDICAL_RECOMMENDATION_VIOLATION",
                "Reasoning introduced a prohibited medical recommendation.",
                (statement.statement_id,),
            )
        )
    return tuple(findings)


def causal_language_violation(statement: ReasoningStatement) -> str | None:
    scrubbed = statement.text.lower()
    for allowed in _ALLOWED_CAUSAL_CONTEXTS:
        scrubbed = scrubbed.replace(allowed, "")
    if (
        statement.category is ReasoningCategory.PLAUSIBLE_MECHANISM
        and statement.causal_status is CausalStatus.NOT_ESTABLISHED
        and "may plausibly contribute to" in scrubbed
    ):
        scrubbed = scrubbed.replace("may plausibly contribute to", "")
    if any(pattern.search(scrubbed) for pattern in _BLOCKED_CAUSAL_PATTERNS):
        return "Reasoning introduced unsupported causal language."
    if statement.causal_status is CausalStatus.CAUSAL_CLAIM_REJECTED:
        return "Accepted artifacts must not retain causal claims."
    return None


def _validate_contradictions(
    response: StructuredReasoningResponse,
    index: ReasoningGroundingIndex,
    findings: list[ReasoningValidationFinding],
) -> None:
    for item in response.contradictions:
        referenced = tuple(
            source
            for source in (
                item.evidence_id_a,
                item.evidence_id_b,
                item.claim_id_a,
                item.claim_id_b,
                item.literature_evidence_id,
                *item.agent_assessment_ids,
            )
            if source is not None
        )
        missing = [
            source
            for source in referenced
            if source
            not in index.evidence_ids
            | index.claim_ids
            | index.literature_evidence_ids
            | index.agent_assessment_ids
        ]
        if missing:
            findings.append(
                _finding("UNSUPPORTED_GROUNDING", "Contradiction referenced unknown IDs.", missing)
            )


def _validate_confounders(
    response: StructuredReasoningResponse,
    index: ReasoningGroundingIndex,
    findings: list[ReasoningValidationFinding],
) -> None:
    allowed = (
        index.evidence_ids
        | index.claim_ids
        | index.literature_evidence_ids
        | index.agent_assessment_ids
    )
    for item in response.candidate_confounders:
        missing = tuple(sorted(set(item.supporting_source_ids) - allowed))
        if missing:
            findings.append(
                _finding(
                    "UNSUPPORTED_GROUNDING",
                    "Candidate confounder referenced unknown IDs.",
                    missing,
                )
            )


def _finding(
    code: str,
    message: str,
    source_ids: tuple[str, ...] = (),
) -> ReasoningValidationFinding:
    return ReasoningValidationFinding(
        finding_code=code,
        severity=WarningSeverity.HIGH,
        message=message,
        source_ids=source_ids,
    )
