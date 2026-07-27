"""Guardrailed LLM-assisted interdisciplinary synthesis for Polaris Phase 8."""

from polaris.synthesis.errors import (
    GroundingValidationError,
    SynthesisError,
    SynthesisProviderError,
    SynthesisValidationError,
    UnsupportedSynthesisModeError,
)
from polaris.synthesis.models import (
    CrossDomainSynthesis,
    DomainSynthesis,
    SynthesisArtifact,
    SynthesisFinding,
    SynthesisFindingCode,
    SynthesisMode,
    SynthesisProvenance,
    SynthesisProviderConfig,
    SynthesisRequest,
    UncertaintyCode,
)
from polaris.synthesis.provider import SynthesisProvider
from polaris.synthesis.service import synthesize_assessment

__all__ = [
    "CrossDomainSynthesis",
    "DomainSynthesis",
    "GroundingValidationError",
    "SynthesisArtifact",
    "SynthesisError",
    "SynthesisFinding",
    "SynthesisFindingCode",
    "SynthesisMode",
    "SynthesisProvider",
    "SynthesisProviderConfig",
    "SynthesisProviderError",
    "SynthesisProvenance",
    "SynthesisRequest",
    "SynthesisValidationError",
    "UncertaintyCode",
    "UnsupportedSynthesisModeError",
    "synthesize_assessment",
]
