# Hackathon requirement audit

Every requirement from the challenge brief, mapped to its exact
implementation location, how to see it demonstrated, and the test that
validates it. Limitations are stated honestly rather than omitted.

## 1. Core system capabilities

| Requirement | Implementation | Demonstration | Test | Limitation |
|---|---|---|---|---|
| Structured, retrievable biodiversity/environmental knowledge base | `app/models/evidence.py`, `app/models/knowledge.py`; seeded by `app/knowledge/seed.py` from `data/seed/*.json` | `GET /api/v1/knowledge/sources`, Evidence Explorer page | `tests/test_retrieval.py::test_sources_endpoint_lists_verified_sources` | 12-source demo corpus, not comprehensive |
| Understands ecosystem/land/climate queries | `app/conversations/extraction.py` (regex NLU), `app/retrieval/hybrid.py` (query parsing) | Send free text in Workspace chat | `tests/test_extraction.py` | Rule-based; misses phrasing outside its patterns by design (see scientific-grounding.md) |
| Actionable, non-obvious recommendations | `app/reasoning/engine.py` | Run assessment on demo scenario | `tests/test_assessments.py::test_demo_scenario_produces_grounded_recommendations` | Candidate set limited to 6-intervention seed catalog |
| Scientific reasoning + evidence support | `app/evidence/verification.py`, evidence table in `RecommendationOut` | Expand any recommendation's evidence table in UI | `tests/test_evidence_verification.py` | — |

## 2. Mandatory knowledge areas

| Area | Where covered |
|---|---|
| Soil health (pH, organic carbon, moisture) | `EnvironmentalProfile.soil_ph/soil_organic_carbon/soil_moisture`; graph nodes `soil_ph`, `soil_organic_carbon`, `soil_moisture`, `soil_biological_activity`; sources `s1`, `s2`, `s9` |
| Land use / land cover | `EnvironmentalProfile.land_use_type`; nodes `land_use_monoculture`, `habitat_fragmentation`; sources `s3`, `s4` |
| Biodiversity indicators (species richness, habitat diversity) | Nodes `species_richness`, `habitat_diversity`; sources `s3`, `s4`, `s11` |
| Climate factors (temperature, rainfall) | `EnvironmentalProfile.temperature_c/rainfall_*`; nodes `rainfall`, `temperature`, `species_range_shift`; sources `s8`, `s9` |
| Human impact (pollution, deforestation) | `EnvironmentalProfile.human_impact_indicators`; nodes `pesticide_use`, `deforestation`; sources `s7`, `s10` |

Test: `tests/test_evaluation_benchmark.py::test_evaluation_case[deforestation_pressure]`
exercises the human-impact + climate + land-use combination end to end.

## 3. Knowledge-system expectations

| Requirement | Implementation | Demonstration |
|---|---|---|
| RAG / embeddings / vector search | `app/ai/embeddings.py` (pluggable: hashing default, OpenAI-compatible optional), `app/retrieval/hybrid.py` | `POST /api/v1/retrieval/inspect`, Evidence Explorer |
| Indexed research papers/reports | `data/seed/sources.json` (12 verified sources) loaded into `EvidenceChunk` with embeddings | `GET /api/v1/knowledge/sources` |
| Retrieval is demonstrably shown | Full trace returned by `/retrieval/inspect`: expanded terms, graph concepts, semantic/lexical candidate counts, per-result match reasons | Evidence Explorer page |

**Limitation:** the default embedding provider is a deterministic hashing
scheme, not a trained neural embedding model (see architecture.md). pgvector
is not yet wired into queries (see database-schema.md).

## 4. Conversational capabilities

| Requirement | Implementation | Test |
|---|---|---|
| Ask clarifying questions when incomplete | `app/conversations/clarify.py::generate_clarifying_questions` (max 3, priority-ordered) | `tests/test_conversations.py::test_ambiguous_message_triggers_clarifying_questions` |
| Multi-turn conversation with memory | `Conversation`/`Message` models; profile persists across turns via `conversation_id` | `tests/test_conversations.py::test_structured_facts_extracted_and_marked_ready` |
| Adapt answers based on context | Reassessment diff (`Assessment.diff_from_previous`) | `tests/test_assessments.py::test_reassess_reflects_profile_change` |
| Structured JSON + natural-language input both accepted | `MessageCreate.structured_input` field; `POST /profiles` direct JSON | `tests/test_conversations.py::test_structured_input_merges_into_profile` |
| Distinguishes user-reported vs. inferred vs. unknown vs. conflicting | `EnvironmentalProfile.uncertainty_metadata["recent_conflicts"]`; `missing_fields` list; `claim_type=user_observation` | `tests/test_conversations.py::test_conflicting_value_is_flagged` |

## 5. Recommendation fields (challenge section 14 contract)

`RecommendationOut` (`app/schemas/assessment.py`) includes: `what_to_do`,
`why_it_may_work`, `impacted_metrics`, `time_horizon`, `confidence`
(level + reason), `evidence[]` (claim, type, source, citation, excerpt,
limitations, status), `monitoring_plan[]`, `heuristic_score`. Verified by
`tests/test_evaluation_benchmark.py::test_evaluation_case` (schema-validity
assertions) on every parametrized case.

## 6. Multi-metric reasoning

| Required pairing | Graph edges | Test |
|---|---|---|
| Soil health ↔ biodiversity | `e1` (SOC→microbial activity), `e2` (microbial activity→habitat diversity, hypothesis) | `test_assessments.py::test_demo_scenario_produces_grounded_recommendations` |
| Water availability ↔ species survival | `e3` (rainfall→soil moisture), `e4` (soil moisture→vegetation establishment), `e5` (→species survival, hypothesis) | same |
| Land use ↔ habitat fragmentation | `e6` (monoculture→fragmentation), `e7` (fragmentation→habitat diversity), `e8` (→species richness) | same |

The engine requires **≥3 known variables** before generating any
recommendation (`reasoning/engine.py::run_assessment`, gate at the top),
directly implementing "must handle at least three environmental variables
together" and "must not force three variables... should ask for missing
information" as a hard code path, not a suggestion.
Test: `tests/test_assessments.py::test_insufficient_variables_returns_explicit_limitation`.

## 7. Input formats

- Natural language: chat `content` field.
- Structured JSON: `structured_input` on a message, or direct `POST /profiles`.
- Geographic coordinates (bonus): `EnvironmentalProfile.latitude/longitude`
  fields exist in the schema and model; the reasoning engine does not yet use
  them for spatial reasoning (e.g. nearest-climate-zone lookups) — accepted
  and stored, not yet load-bearing. Stated honestly as partial.

## 8. Output requirements (recommendation, metrics, time horizon, confidence)

All four present on every `RecommendationOut` — see section 5 above. UI
renders all four via badges/labels in `RecommendationCard.tsx`.

## 9. Explicit rejections handled

| Rejected pattern | How this system avoids it |
|---|---|
| Generic LLM-only solution | Reasoning/retrieval/verification are deterministic Python; LLM is optional and phrasing-only (see architecture.md) |
| Shallow/obvious recommendations | Candidates are evidence-linked and constraint-checked, not templated generic advice; agroforestry example explicitly reports mixed/weak evidence rather than a blanket endorsement |

## 10. Non-negotiable scientific integrity

Full policy: `docs/scientific-grounding.md`. Summary of what's verifiable in
code: `ScientificClaim.claim_type` enum enforced at the schema level;
`evidence/verification.py` automated status computation including a
numeric-figure cross-check against the retrieved excerpt; the mandated
"Evidence is insufficient..." sentence appears verbatim in two real code
paths (`reasoning/engine.py::INSUFFICIENT_VARIABLES_MESSAGE` and seed edge
`e17`, not just as documentation prose).

## 11. Testing coverage

- Backend: 45 pytest tests — unit (extraction, evidence verification),
  integration (every API endpoint via `TestClient`), schema validation,
  retrieval, knowledge graph, missing-data gate, constraint engine (exercised
  through `test_assessments.py`), monitoring-plan honesty, error handling
  (404s, validation errors, oversized requests, rate limiting), a
  Postgres-column-width regression test, and a 6-case evaluation benchmark.
  Verified passing against both SQLite and real PostgreSQL (see
  `docs/evaluation-report.md`).
- Frontend: 13 vitest tests — component rendering, loading/empty/error
  states, evidence display, the distinct confidence/evidence-strength/
  data-completeness badges, and the "never fabricate a numeric target"
  invariant.
- End-to-end manual verification: full workspace flow (ambiguous message →
  clarifying questions → structured facts → assessment → expand evidence →
  monitoring plan) driven in a real headless browser during development and
  visually confirmed (see `docs/demo-script.md`); the same flow was also run
  against the fully containerized Docker Compose stack with real PostgreSQL,
  which surfaced and led to fixing two real bugs invisible under SQLite (see
  `docs/engineering-audit.md`).

## 12. Known gaps (stated once here, referenced from README)

- No live deployment.
- No authentication (anonymous sessions only).
- pgvector not wired into queries (JSON column + Python cosine similarity).
- Hashing embeddings by default (deterministic, not semantic-neural).
- Geographic coordinates accepted but not yet used in reasoning.
- Prototype heuristic ranking, explicitly labeled as such everywhere it appears.
- Rule-based (not LLM-based) natural-language extraction, by deliberate
  design choice for scientific integrity and testability — documented as a
  trade-off, not hidden.
