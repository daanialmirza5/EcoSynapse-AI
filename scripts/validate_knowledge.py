#!/usr/bin/env python3
"""Validates the seed knowledge corpus (data/seed/*.json) for internal
consistency. Run before committing changes to the corpus:

    python scripts/validate_knowledge.py

Exits non-zero if any check fails. This is a static, offline validator --
it does not re-verify sources against the internet (that verification step
is manual and documented in docs/scientific-grounding.md); it only catches
structural/internal-consistency mistakes: duplicate sources, malformed
URLs, orphaned references, and relation entries pointing at a source id
that doesn't exist.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SEED_DIR = REPO_ROOT / "data" / "seed"

_URL_RE = re.compile(r"^https?://[^\s]+$")
VALID_CLAIM_TYPES = {"source_supported", "model_derived", "hypothesis", "user_observation", "unknown"}
VALID_EVIDENCE_STRENGTHS = {"strong", "moderate", "weak", "hypothesis"}


def load(name: str) -> list[dict]:
    with (SEED_DIR / name).open("r", encoding="utf-8") as f:
        return json.load(f)


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    sources = load("sources.json")
    relationships = load("relationships.json")
    interventions = load("interventions.json")

    # --- Sources ---
    source_ids = set()
    seen_titles: dict[str, str] = {}
    seen_dois: dict[str, str] = {}
    for s in sources:
        sid = s.get("id")
        if not sid:
            errors.append(f"Source missing 'id': {s.get('title')!r}")
            continue
        if sid in source_ids:
            errors.append(f"Duplicate source id: {sid}")
        source_ids.add(sid)

        if not s.get("title"):
            errors.append(f"Source {sid} missing title")
        title_key = (s.get("title") or "").strip().lower()
        if title_key and title_key in seen_titles:
            errors.append(f"Duplicate source title between {seen_titles[title_key]} and {sid}: {s['title']!r}")
        elif title_key:
            seen_titles[title_key] = sid

        doi = s.get("doi")
        if doi:
            if doi in seen_dois:
                errors.append(f"Duplicate DOI {doi} between {seen_dois[doi]} and {sid}")
            seen_dois[doi] = sid

        url = s.get("url")
        if url and not _URL_RE.match(url):
            errors.append(f"Source {sid} has a malformed URL: {url!r}")

        if not doi and not url:
            errors.append(f"Source {sid} has neither a DOI nor a URL -- not traceable/verifiable")

        if not s.get("limitations"):
            warnings.append(f"Source {sid} has no 'limitations' field -- every source should state one")

        if s.get("is_verified") and s.get("source_type") not in (
            "peer_reviewed_article", "institutional_report", "systematic_review",
        ):
            warnings.append(f"Source {sid} is marked verified with unusual source_type={s.get('source_type')!r}")

    # --- Relationships / claims ---
    edge_ids = set()
    node_types: dict[str, str] = {}
    for rel in relationships:
        rid = rel.get("id")
        if not rid:
            errors.append(f"Relationship missing 'id': {rel}")
            continue
        if rid in edge_ids:
            errors.append(f"Duplicate relationship id: {rid}")
        edge_ids.add(rid)

        claim_type = rel.get("claim_type")
        if claim_type not in VALID_CLAIM_TYPES:
            errors.append(f"Relationship {rid} has invalid claim_type: {claim_type!r}")

        strength = rel.get("evidence_strength")
        if strength not in VALID_EVIDENCE_STRENGTHS:
            errors.append(f"Relationship {rid} has invalid evidence_strength: {strength!r}")

        src_id = rel.get("source_id")
        if src_id is not None and src_id not in source_ids:
            errors.append(f"Relationship {rid} references unknown source_id: {src_id!r}")

        if claim_type == "source_supported" and src_id is None:
            errors.append(f"Relationship {rid} is claim_type=source_supported but has no source_id")
        if claim_type in ("hypothesis", "unknown") and src_id is not None:
            warnings.append(
                f"Relationship {rid} is claim_type={claim_type!r} but still cites source_id={src_id!r} "
                "-- double check this is intentional (e.g. a partially-related source)"
            )

        if not rel.get("limitations"):
            warnings.append(f"Relationship {rid} has no 'limitations' field")

        for role in ("from", "to"):
            name = rel.get(f"{role}_node")
            ntype = rel.get(f"{role}_type")
            if not name or not ntype:
                errors.append(f"Relationship {rid} missing {role}_node/{role}_type")
                continue
            if name in node_types and node_types[name] != ntype:
                errors.append(
                    f"Node {name!r} used with inconsistent types: {node_types[name]!r} vs {ntype!r} (in {rid})"
                )
            node_types[name] = ntype

    # --- Interventions ---
    intervention_ids = set()
    for interv in interventions:
        iid = interv.get("id")
        if not iid:
            errors.append(f"Intervention missing 'id': {interv}")
            continue
        if iid in intervention_ids:
            errors.append(f"Duplicate intervention id: {iid}")
        intervention_ids.add(iid)

        if not interv.get("target_metrics"):
            warnings.append(f"Intervention {iid} has no target_metrics")

        for claim_ref in interv.get("source_claim_ids", []):
            if claim_ref not in edge_ids:
                errors.append(f"Intervention {iid} references unknown relationship id: {claim_ref!r}")

        if iid not in node_types:
            warnings.append(f"Intervention {iid} has no corresponding edge in relationships.json (orphan catalog entry)")

    # --- Report ---
    print(f"Checked {len(sources)} sources, {len(relationships)} relationships, {len(interventions)} interventions.")
    if warnings:
        print(f"\n{len(warnings)} warning(s):")
        for w in warnings:
            print(f"  WARN  {w}")
    if errors:
        print(f"\n{len(errors)} error(s):")
        for e in errors:
            print(f"  ERROR {e}")
        print("\nFAILED")
        return 1

    print("\nOK -- no structural errors found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
