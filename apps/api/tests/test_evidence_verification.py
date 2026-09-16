from app.evidence.verification import verify_claim
from app.models.evidence import ScientificClaim, ScientificSource


def _source(**kwargs):
    return ScientificSource(title="T", authors=[], doi="10.1/x", url=None, **kwargs)


def test_source_supported_claim_is_supported_when_numbers_match():
    source = _source()
    claim = ScientificClaim(claim_text="Effect increased by 36%", claim_type="source_supported", evidence_strength="moderate")
    verified = verify_claim(claim, source, excerpt="Abundance increased by 36% in the meta-analysis.")
    assert verified.evidence_status == "supported"


def test_source_supported_claim_downgraded_when_number_unverified():
    source = _source()
    claim = ScientificClaim(claim_text="Effect increased by 99%", claim_type="source_supported", evidence_strength="moderate")
    verified = verify_claim(claim, source, excerpt="Abundance increased in the meta-analysis, magnitude not restated here.")
    assert verified.evidence_status == "partially_supported"


def test_hypothesis_claim_is_always_insufficient():
    claim = ScientificClaim(claim_text="Might help", claim_type="hypothesis", evidence_strength="hypothesis")
    verified = verify_claim(claim, None, None)
    assert verified.evidence_status == "insufficient_evidence"


def test_ecosystem_mismatch_downgrades_supported_claim():
    source = _source()
    claim = ScientificClaim(claim_text="Improves habitat", claim_type="source_supported", evidence_strength="strong")
    verified = verify_claim(claim, source, "Improves habitat in the study.", ecosystem_mismatch=True)
    assert verified.evidence_status == "partially_supported"
