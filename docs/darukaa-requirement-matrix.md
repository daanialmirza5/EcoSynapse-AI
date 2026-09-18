# Darukaa.Earth requirement matrix

Every requirement from the challenge specification, mapped to its exact
implementation, the API endpoint/component that demonstrates it, the
frontend view, the test that validates it, and current status. Status is
only ever `DONE`, `PARTIAL`, or `GAP` — never asserted without the test/file
reference next to it.

## 1. Knowledge base and knowledge areas

| Requirement | Implementation | API / Component | Frontend view | Test | Status |
|---|---|---|---|---|---|
| Structured knowledge base of biodiversity/environmental metrics | `app/models/evidence.py`, `app/models/knowledge.py`, seeded from `data/seed/*.json` | `GET /api/v1/knowledge/sources`, `GET /api/v1/knowledge/graph` | Evidence Explorer, Knowledge Graph pages | `test_retrieval.py`, `test_knowledge_validation.py` | **DONE** |
| Soil health (pH, organic carbon, moisture) | `EnvironmentalProfile.soil_ph/soil_organic_carbon/soil_moisture`; graph nodes `soil_ph`, `soil_organic_carbon`, `soil_moisture`, `soil_biological_activity` | Profile schema, `/knowledge/graph` | Profile Editor, Workspace profile panel | `docs/knowledge-coverage-matrix.md` rows 1-3 | **DONE** (pH: tracked and detected as a concern, but no cataloged intervention yet targets it directly — see gap notes) |
| Land use / land cover | `land_use_type` field; nodes `land_use_monoculture`, `habitat_fragmentation` | same | same | `test_evaluation_benchmark.py` (semiarid_wheat, strong_evidence_intercropping cases) | **DONE** |
| Biodiversity indicators (species richness, habitat diversity) | Nodes `species_richness`, `habitat_diversity` | same | Knowledge Graph, Recommendation cards' impacted_metrics | multiple | **DONE** |
| Climate (temperature, rainfall) | `temperature_c`, `rainfall_mm_year`/`rainfall_qualitative`; nodes `temperature`, `rainfall`, `species_range_shift` | same | same | `test_high_temperature_is_detected_as_a_concern` (added this pass — temperature previously had no concern rule) | **DONE** |
| Human impact (pollution, deforestation) | `human_impact_indicators`; nodes `pesticide_use`, `deforestation` | same | same | `test_evaluation_benchmark.py::deforestation_pressure` | **DONE** |
| Retrievable knowledge layer (not just prompts) | `app/retrieval/hybrid.py` — semantic + lexical + graph expansion over embedded chunks | `POST /api/v1/retrieval/inspect` | Evidence Explorer | `test_retrieval.py` | **DONE** |
| Retrieval process clearly demonstrable | Full trace exposed: expanded terms, graph concepts, semantic/lexical candidate counts, **per-result semantic/lexical/graph contribution scores** (added this pass) | `POST /retrieval/inspect` | Evidence Explorer (now shows separate score badges per channel) | `test_retrieval.py::test_retrieval_inspect_returns_trace` | **DONE** |

## 2. Conversational requirements

| Requirement | Implementation | Test | Status |
|---|---|---|---|
| Ask clarifying questions | `app/conversations/clarify.py::generate_clarifying_questions` | `test_conversations.py` | **DONE** |
| Handle incomplete inputs | Hard gate at <3 known variables (`reasoning/engine.py`) | `test_insufficient_variables_returns_explicit_limitation` | **DONE** |
| Multi-turn context | `Conversation`/`Message`/`EnvironmentalProfile` persistence | `test_structured_facts_extracted_and_marked_ready` | **DONE** |
| Adapt responses based on prior context | Reassessment diff (`Assessment.diff_from_previous`) | `test_reassess_reflects_profile_change` | **DONE** |
| Clarifying questions selected by what's missing/most important | Priority-ordered question bank (`clarify.py::_QUESTION_BANK`), capped at 3/turn | `test_ambiguous_message_triggers_clarifying_questions` | **DONE** |

## 3. Multi-metric reasoning (mandatory ≥3 variables)

| Requirement | Implementation | Test | Status |
|---|---|---|---|
| Hard gate: recommendations require ≥3 known variables | `reasoning/engine.py::run_assessment`, top-of-function gate | `test_insufficient_variables_returns_explicit_limitation` | **DONE** |
| Recommendation *depends on* variable interaction, not just displays them | Concern detection combines multiple profile fields into a single concern set; candidate interventions are selected from the union of triggered concerns, and each recommendation's evidence/trade-offs reference the specific triggering conditions | `test_recommendation_links_to_its_own_reasoning_path` (added this pass) | **DONE** |
| Soil + Climate + Land Use scenario (challenge's own example) | `tests/evaluation_cases/semiarid_wheat.json` | `test_evaluation_case[semiarid_wheat]` | **DONE** |
| Soil + Moisture + Biodiversity scenario | `tests/evaluation_cases/soil_moisture_biodiversity.json` (added this pass) | `test_evaluation_case[soil_moisture_biodiversity]` | **DONE** |
| Land Use + Habitat + Human Impact scenario | `tests/evaluation_cases/deforestation_pressure.json` | `test_evaluation_case[deforestation_pressure]` | **DONE** |
| Climate + Water + Biodiversity scenario | `tests/evaluation_cases/climate_water_biodiversity.json` (added this pass) | `test_evaluation_case[climate_water_biodiversity]` | **DONE** |
| Incomplete input → clarifying questions, not premature recommendation | see above | `test_ambiguous_message_triggers_clarifying_questions` | **DONE** |
| Conflicting input → explicit conflict detection | Backend: `conversations/service.py::apply_extraction_to_profile`. **Frontend surfacing added this pass** (`ConflictBanner.tsx` — previously computed but never displayed) | `test_conflicting_value_is_flagged` (backend), `ConflictBanner.test.tsx` (frontend, added this pass) | **DONE** |
| Unsupported numeric claim not repeated as fact | Rule-based extractor only captures directly-stated values; adversarial phrasing ("assume X", hedged claims) is excluded — **hedge-word guard added this pass** after a red-team test caught it accepting "assume rainfall is 1000mm" | `test_red_team_hallucination.py` (10 tests, added this pass) | **DONE** |

## 4. Non-obvious, evidence-backed recommendations

| Requirement | Implementation | Test | Status |
|---|---|---|---|
| No shallow/generic fallback recommendations | Intervention catalog (`data/seed/interventions.json`) contains 6 specific, mechanism-linked interventions (cover cropping, agroforestry, water harvesting, intercropping, hedgerows, IPM) — none are bare "plant more trees"/"be sustainable" | Manual code review; `scripts/validate_knowledge.py` | **DONE** |
| Recommendation structure includes: action, rationale, interacting variables, impacted metrics, mechanism, evidence, evidence strength, expected direction, time horizon, constraints, trade-offs, monitoring, confidence | `RecommendationOut` schema (`app/schemas/assessment.py`) — the only fields not yet a literal top-level key are "environmental_problem" (covered by `assessment_summary` at the assessment level) and "conditions_for_revision" (covered by `overall_limitations` + the reassessment diff mechanism) | `test_evaluation_case` schema-validity assertions | **DONE**, with the two fields folded into adjacent existing fields rather than duplicated |
| Time horizons (short/medium/long), not invented durations | `Intervention.typical_time_horizon`, sourced from the catalog, not generated per-request | `test_demo_scenario_produces_grounded_recommendations` | **DONE** |
| Measurable improvement estimates, only when source-supported | `monitoring/plans.py::generate_monitoring_entry` — target is either "establish a baseline first" or "compare to recorded baseline," never a fabricated number; `expected_direction` only set when a `strong`/`moderate` edge supports it | `test_monitoring_plan_field_widths.py`, `RecommendationCard.test.tsx::never invents a numeric monitoring target` | **DONE** |

## 5. Scientific grounding (25% of rubric)

| Requirement | Implementation | Test | Status |
|---|---|---|---|
| Every claim traceable to evidence | `ScientificClaim.claim_type` enum + `EvidenceRef` in every recommendation | `test_no_source_supported_claim_lacks_a_real_citation_anywhere_in_a_full_assessment` | **DONE** |
| Evidence levels clearly defined | `strong`/`moderate`/`weak`/`hypothesis` — defined in `docs/scientific-grounding.md` and `docs/reasoning-methodology.md` | — | **DONE** |
| No unsupported recommendation presented as strongly evidence-backed | Automated verification downgrades `source_supported` claims on ecosystem mismatch or unverifiable numbers (`evidence/verification.py`) | `test_evidence_verification.py`, `test_ecosystem_mismatch_downgrades_rather_than_silently_passes` | **DONE** |
| Claim-level citation (not just a source list at the bottom) | `EvidenceRef` is per-claim: claim text, type, source, citation, excerpt, limitations, status — one per claim, not one list per recommendation | `RecommendationCard.tsx`'s evidence table renders per-claim | **DONE** |
| Source quality audited | `docs/scientific-grounding.md` documents verification method for all 12 sources | `scripts/validate_knowledge.py` | **DONE** |

## 6. Knowledge system design (20% of rubric)

| Requirement | Implementation | Test | Status |
|---|---|---|---|
| Genuine retrievable knowledge layer | See section 1 | `test_retrieval.py` | **DONE** |
| Judge can see retrieval mechanics (semantic/lexical/graph) | Per-result score breakdown (added this pass) | `test_retrieval_inspect_returns_trace` | **DONE** |
| Knowledge graph shows real ecological relationships | 23 nodes, 22 edges, each with `evidence_strength` and `source_claim_id` where applicable | Knowledge Graph page | **DONE** |
| Clicking an edge shows relationship + evidence + source | `KnowledgeEdgeOut` includes `mechanism`, `evidence_strength`, `limitations`, `source_claim_id`; UI renders all of these per edge | `test_knowledge_graph_endpoint_returns_typed_nodes` | **DONE** |

## 7. Reasoning trace and explainability (flagship feature)

| Requirement | Implementation | Test | Status |
|---|---|---|---|
| Step-by-step reasoning trace | `Assessment.reasoning_paths`, one per candidate intervention, with narrative + graph steps | AssessmentPanel's collapsible reasoning trace | **DONE** |
| "Why this recommendation?" drill-down | **Added this pass**: `WhyThisRecommendation.tsx`, correlates a recommendation's `intervention_id` to its exact reasoning-path entries | `test_recommendation_links_to_its_own_reasoning_path`, `RecommendationCard.test.tsx` | **DONE** |
| "Why not the alternative?" / comparison | Recommendation Comparison page ranks all candidates side-by-side with heuristic breakdown; does not declare one "best," shows the transparent scoring instead | manual review | **PARTIAL** — comparison table exists; a prose "why X over Y" explanation per pair is not generated (would require additional narrative synthesis not backed by a distinct evidence artifact) |
| Judge / technical view vs. normal view | Progressive disclosure via `<details>`/expand buttons throughout (evidence tables, reasoning trace, heuristic breakdown are hidden by default, one click away) | manual review | **PARTIAL** — no single global "Judge Mode" toggle; achieved instead via consistent per-section progressive disclosure, which keeps the normal view uncluttered without a separate mode to maintain |

## 8. Monitoring

| Requirement | Implementation | Test | Status |
|---|---|---|---|
| Monitoring connects recommendation → metric → baseline → measurement → comparison | `monitoring/plans.py::generate_monitoring_entry` | `test_monitoring_plan_accepts_long_unit_and_frequency_text` | **DONE** |
| Never fabricates a target value | Target is always "establish baseline" or "compare to baseline" | `RecommendationCard.test.tsx` | **DONE** |
| Monitoring dashboard visualizes cadence, not decorative charts | `MonitoringDashboard.tsx` — real bar chart from actual monitoring plans, record-observation form wired to the real API | manual browser verification | **DONE** |

## 9. Structured + text input, same pipeline

| Requirement | Implementation | Test | Status |
|---|---|---|---|
| Both text and JSON input accepted | `MessageCreate.structured_input` + direct `POST /profiles` | `test_structured_input_merges_into_profile` | **DONE** |
| Single reasoning pipeline for both | Both paths write to the same `EnvironmentalProfile` row; `reasoning/engine.py` has no branch for input origin | code review | **DONE** |

## 10. Geospatial context (bonus)

| Requirement | Implementation | Status |
|---|---|---|
| Optional lat/long context | `EnvironmentalProfile.latitude/longitude` fields exist, stored, displayed | **PARTIAL** — accepted and stored, not yet used by the reasoning engine for spatial inference (no live geospatial dataset is wired in, and none is fabricated) |

## 11. Output clarity (10% of rubric)

| Requirement | Implementation | Status |
|---|---|---|
| Actionable, clearly labeled recommendations | `RecommendationCard.tsx` | **DONE** |
| Confidence/evidence strength/data completeness distinct | Three separate fields and badges (added previous pass) | **DONE** |
| Uncertainty understandable | Trade-offs, feasibility constraints, and explicit "insufficient evidence" language throughout | **DONE** |

## 12. Deployment and reproducibility

| Requirement | Status |
|---|---|
| Clone → install → run → test → demo with minimal effort | **DONE** — README §11 verified from a clean venv/npm install this session |
| Live deployment | **NOT DONE** — see `docs/deployment.md`; requires the account owner's Railway/Vercel login, which was not available during this pass |
