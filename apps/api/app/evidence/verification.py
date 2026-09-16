"""Claim-level evidence verification.

For every claim attached to a recommendation, decides an ``evidence_status``
(supported / partially_supported / insufficient_evidence / unverified) based
on: the claim's declared type, whether a real source/excerpt backs it, and
whether any numeric figure in the claim text actually appears in the
retrieved excerpt (a lightweight but real check against invented numbers).
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from app.models.evidence import ScientificClaim, ScientificSource

_NUMBER_RE = re.compile(r"\d+(?:\.\d+)?")


@dataclass
class VerifiedClaim:
    claim_text: str
    claim_type: str
    source_id: str | None
    source_title: str | None
    citation: str | None
    excerpt: str | None
    limitations: str | None
    evidence_status: str
    applicability_note: str


def _citation_for(source: ScientificSource | None) -> str | None:
    if source is None:
        return None
    return source.doi and f"https://doi.org/{source.doi}" or source.url


def verify_claim(
    claim: ScientificClaim,
    source: ScientificSource | None,
    excerpt: str | None,
    ecosystem_mismatch: bool = False,
) -> VerifiedClaim:
    applicability = "General applicability; see conditions/limitations."
    if claim.conditions:
        applicability = "Applies under: " + "; ".join(claim.conditions)

    if claim.claim_type == "source_supported" and source is not None:
        status = "partially_supported" if ecosystem_mismatch else "supported"
        if excerpt:
            claim_numbers = set(_NUMBER_RE.findall(claim.claim_text))
            excerpt_numbers = set(_NUMBER_RE.findall(excerpt))
            unverified_numbers = claim_numbers - excerpt_numbers
            if unverified_numbers:
                status = "partially_supported"
                applicability += (
                    f" Note: figure(s) {', '.join(sorted(unverified_numbers))} in the claim could not be "
                    "automatically matched against the retrieved excerpt text."
                )
    elif claim.claim_type == "model_derived":
        status = "partially_supported"
    elif claim.claim_type in ("hypothesis", "unknown"):
        status = "insufficient_evidence"
    else:
        status = "unverified"

    return VerifiedClaim(
        claim_text=claim.claim_text,
        claim_type=claim.claim_type,
        source_id=source.id if source else None,
        source_title=source.title if source else None,
        citation=_citation_for(source),
        excerpt=excerpt,
        limitations=claim.limitations,
        evidence_status=status,
        applicability_note=applicability,
    )
