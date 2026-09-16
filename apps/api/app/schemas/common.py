from __future__ import annotations

from enum import StrEnum


class ClaimType(StrEnum):
    SOURCE_SUPPORTED = "source_supported"
    MODEL_DERIVED = "model_derived"
    HYPOTHESIS = "hypothesis"
    USER_OBSERVATION = "user_observation"
    UNKNOWN = "unknown"


class EvidenceStrength(StrEnum):
    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"
    HYPOTHESIS = "hypothesis"


class TimeHorizon(StrEnum):
    SHORT = "short"
    MEDIUM = "medium"
    LONG = "long"


class ConfidenceLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class MessageRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class EvidenceStatus(StrEnum):
    SUPPORTED = "supported"
    PARTIALLY_SUPPORTED = "partially_supported"
    INSUFFICIENT = "insufficient_evidence"
    UNVERIFIED = "unverified"
