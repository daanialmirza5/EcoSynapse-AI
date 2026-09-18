"""Deterministic, rule-based extraction of environmental-profile fields from
free text.

This is intentionally NOT an LLM call: regex/keyword extraction is fully
transparent, testable, reproducible, and can never hallucinate a numeric
measurement that the user did not state. Anything not explicitly present in
the text is left unset (None), never guessed.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

_PH_RE = re.compile(r"\bph\D{0,6}?(\d{1,2}(?:\.\d+)?)\b", re.IGNORECASE)
_SOC_RE = re.compile(
    r"(?:soil organic carbon|organic carbon|\bsoc\b)\D{0,15}?(\d{1,2}(?:\.\d+)?)\s*%", re.IGNORECASE
)
_MOISTURE_RE = re.compile(r"(?:soil moisture|moisture)\D{0,15}?(\d{1,3}(?:\.\d+)?)\s*%", re.IGNORECASE)
_RAINFALL_MM_RE = re.compile(r"rain(?:fall)?\D{0,15}?(\d{2,5}(?:\.\d+)?)\s*mm", re.IGNORECASE)
_TEMP_RE = re.compile(r"(-?\d{1,3}(?:\.\d+)?)\s*(?:°\s*c\b|deg(?:rees)?\s*c\b|c\b)", re.IGNORECASE)

_RAINFALL_QUALITATIVE = {
    "low": ["low rainfall", "little rain", "dry", "drought", "arid", "water scarce", "water-scarce"],
    "high": ["high rainfall", "heavy rain", "wet season", "abundant rain"],
    "medium": ["moderate rainfall", "average rainfall"],
}

# A direct statement ("rainfall is high") must win over an indirect/implicit
# signal ("semi-arid" ecosystem => usually low rainfall) -- otherwise
# "semi-arid" falsely matches the substring "arid" in the low-rainfall
# keyword list and silently overrides what the user just explicitly said.
# Found via red-team browser testing: "Actually, rainfall is high, ... a
# semi-arid ... region" was incorrectly extracted as rainfall_qualitative=low.
_RAINFALL_DIRECT_RE = re.compile(
    r"rain(?:fall)?\s+(?:is|was|seems?|remains?)\s+(low|moderate|medium|high)", re.IGNORECASE
)

_ECOSYSTEM_KEYWORDS = [
    "semi-arid", "semiarid", "arid", "tropical", "temperate", "wetland", "grassland",
    "savanna", "savannah", "tundra", "desert", "mediterranean", "boreal", "rainforest",
]

_LAND_USE_KEYWORDS = {
    "monoculture wheat": "monoculture wheat cropland",
    "monoculture": "monoculture cropland",
    "wheat": "wheat cropland",
    "maize": "maize cropland",
    "rice": "rice cropland",
    "pasture": "pasture / grazing land",
    "orchard": "orchard",
    "forest": "forest",
    "cropland": "cropland",
    "rangeland": "rangeland",
    "plantation": "plantation",
}

_BIODIVERSITY_TREND_KEYWORDS = {
    "declining": ["declining", "decreasing", "dropping", "falling", "loss of species", "fewer pollinators", "disappearing"],
    "improving": ["improving", "increasing", "recovering", "more species"],
    "stable": ["stable", "unchanged", "no change"],
}

_HUMAN_IMPACT_KEYWORDS = {
    "pesticide_use": ["pesticide", "herbicide", "insecticide", "agrochemical"],
    "pollution": ["pollution", "polluted", "contamination", "runoff"],
    "deforestation": ["deforestation", "logging", "clear-cut", "clearcut", "forest clearing"],
}

# Guards against a real adversarial pattern: "assume rainfall is 1000mm even
# though I didn't tell you that" reads, to a naive regex, exactly like a
# stated measurement. A sentence containing one of these hedge/instruction
# words is treated as hypothetical, not a reported fact, and numeric
# extraction is skipped for that sentence -- caught by
# tests/test_red_team_hallucination.py.
_HEDGE_WORDS = [
    "assume", "assuming", "suppose", "supposing", "pretend", "hypothetically",
    "let's say", "lets say", "let's assume", "imagine", "what if", "for the sake of argument",
]
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?;])\s+")


def _non_hedged_sentences(text: str) -> str:
    """Returns only the sentences that don't contain a hedge word, joined
    back together -- numeric regexes are run against this, not the raw text,
    so a hypothetical clause can't seed a fabricated profile value."""
    sentences = _SENTENCE_SPLIT_RE.split(text)
    kept = [s for s in sentences if not any(hw in s.lower() for hw in _HEDGE_WORDS)]
    return " ".join(kept)


@dataclass
class ExtractionResult:
    fields: dict[str, Any] = field(default_factory=dict)
    biodiversity_indicators: dict[str, Any] = field(default_factory=dict)
    human_impact_indicators: dict[str, Any] = field(default_factory=dict)
    constraints: list[str] = field(default_factory=list)
    matched_spans: dict[str, str] = field(default_factory=dict)


def extract_from_text(text: str) -> ExtractionResult:
    result = ExtractionResult()
    lower = text.lower()
    non_hedged = _non_hedged_sentences(lower)

    if m := _PH_RE.search(non_hedged):
        result.fields["soil_ph"] = float(m.group(1))
        result.matched_spans["soil_ph"] = m.group(0)
    if m := _SOC_RE.search(non_hedged):
        result.fields["soil_organic_carbon"] = float(m.group(1))
        result.matched_spans["soil_organic_carbon"] = m.group(0)
    if m := _MOISTURE_RE.search(non_hedged):
        result.fields["soil_moisture"] = float(m.group(1))
        result.matched_spans["soil_moisture"] = m.group(0)
    if m := _RAINFALL_MM_RE.search(non_hedged):
        result.fields["rainfall_mm_year"] = float(m.group(1))
        result.matched_spans["rainfall_mm_year"] = m.group(0)
    if m := _TEMP_RE.search(non_hedged):
        result.fields["temperature_c"] = float(m.group(1))
        result.matched_spans["temperature_c"] = m.group(0)

    if "rainfall_mm_year" not in result.fields:
        if m := _RAINFALL_DIRECT_RE.search(non_hedged):
            result.fields["rainfall_qualitative"] = m.group(1).lower()
            result.matched_spans["rainfall_qualitative"] = m.group(0)
        else:
            # Guard against "semi-arid"/"semiarid" (an ecosystem descriptor)
            # falsely matching the substring "arid" in the low-rainfall
            # keyword list.
            arid_guarded = lower.replace("semi-arid", "").replace("semiarid", "")
            for level, kws in _RAINFALL_QUALITATIVE.items():
                if any(kw in arid_guarded for kw in kws):
                    result.fields["rainfall_qualitative"] = level
                    result.matched_spans["rainfall_qualitative"] = next(kw for kw in kws if kw in arid_guarded)
                    break

    for kw in _ECOSYSTEM_KEYWORDS:
        if kw in lower:
            result.fields["ecosystem_type"] = kw
            result.matched_spans["ecosystem_type"] = kw
            break

    for kw, label in _LAND_USE_KEYWORDS.items():
        if kw in lower:
            result.fields["land_use_type"] = label
            result.matched_spans["land_use_type"] = kw
            break

    for trend, kws in _BIODIVERSITY_TREND_KEYWORDS.items():
        if any(kw in lower for kw in kws):
            result.biodiversity_indicators["reported_trend"] = trend
            break

    for key, kws in _HUMAN_IMPACT_KEYWORDS.items():
        if any(kw in lower for kw in kws):
            result.human_impact_indicators[key] = True

    for kw in ["limited budget", "low budget", "no budget", "limited irrigation", "limited water",
               "cannot change crop", "must keep growing", "conservation restriction", "protected area"]:
        if kw in lower:
            result.constraints.append(kw)

    return result
