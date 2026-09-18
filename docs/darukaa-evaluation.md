# Darukaa.Earth evaluation matrix

Uses the challenge's own weighting. No independent ranking is invented —
this maps what the rubric evaluates to what EcoSynapse implements, how it's
demonstrated, and how it's tested.

## Depth of Reasoning — 30%

| What the challenge evaluates | What EcoSynapse implements | How we demonstrate it | How we test it |
|---|---|---|---|
| Genuine combination of multiple environmental variables | Concern detection reads soil, climate, land-use, and human-impact fields together; candidate interventions are the *union* of concerns triggered by the combination, not a per-variable lookup | Run the semi-arid wheat demo scenario; the assessment summary lists every triggered concern and which variables produced it | `test_evaluation_case` across 8 scenario cases (`tests/evaluation_cases/*.json`), each combining ≥3 variables |
| Explainability: why does recommendation X follow from variables A, B, C? | "Why this recommendation?" drill-down (`WhyThisRecommendation.tsx`) shows the exact detected conditions, the knowledge-graph steps connecting them, the evidence, and the conclusion, per recommendation | Click "Why this recommendation?" on any card in the Workspace | `test_recommendation_links_to_its_own_reasoning_path` |
| Judge can inspect the reasoning, not just trust a final answer | Full `reasoning_paths` array on every assessment response; per-recommendation correlation via `intervention_id` | `GET`/`POST /api/v1/assessments` response body; AssessmentPanel's expandable reasoning trace | `test_assessments.py`, `test_evaluation_benchmark.py` |
| Hard refusal to force a shallow answer | <3 known variables → explicit "Evidence is insufficient..." message, zero recommendations | Submit a one-line profile in the Workspace | `test_insufficient_variables_returns_explicit_limitation` |

## Scientific Grounding — 25%

| What the challenge evaluates | What EcoSynapse implements | How we demonstrate it | How we test it |
|---|---|---|---|
| Recommendations backed by credible sources | 12 sources, each independently verified via live web search during development (not model memory), with real DOIs/URLs | `docs/scientific-grounding.md`, Evidence Explorer | `scripts/validate_knowledge.py` (0 structural errors) |
| Every important claim traceable to evidence | `EvidenceRef` per claim: text, type, source, citation, excerpt, limitations, computed status | Expand any recommendation's evidence table | `test_no_source_supported_claim_lacks_a_real_citation_anywhere_in_a_full_assessment` |
| Unsupported numbers prevented | Numeric figures in a claim are cross-checked against the retrieved excerpt; mismatches downgrade the claim's status. Extraction never invents a number the user didn't state, and now rejects hedged/hypothetical phrasing ("assume X") | `docs/scientific-grounding.md`'s cover-cropping example (explicit "insufficient evidence" case) | `test_evidence_verification.py`, `test_red_team_hallucination.py` (10 adversarial tests) |
| Honest reporting even when evidence is mixed | Agroforestry recommendation reports its cited meta-analysis's actual "no unequivocal effect" finding rather than a rosier summary | `docs/judge-story.md` | `test_agroforestry_recommendation_is_not_overclaimed` |

## Knowledge System Design — 20%

| What the challenge evaluates | What EcoSynapse implements | How we demonstrate it | How we test it |
|---|---|---|---|
| A real retrievable knowledge layer, not prompt-stuffing | `app/retrieval/hybrid.py`: parse → graph-expand → semantic search → lexical search → merge/rerank | `POST /api/v1/retrieval/inspect` | `test_retrieval.py` |
| Judge can see semantic vs. lexical vs. graph contribution | Per-result `semantic_score`, `lexical_score`, `matched_graph_concepts` fields (added this pass, previously only a combined score was shown) | Evidence Explorer's per-result score badges | `test_retrieval_inspect_returns_trace` |
| Typed knowledge graph with real relationships | 23 nodes (9 types), 22 edges, each carrying `evidence_strength` and `source_claim_id` where applicable | Knowledge Graph page, filterable by node type | `test_knowledge_graph_endpoint_returns_typed_nodes` |
| Full coverage of mandatory knowledge areas | See `docs/knowledge-coverage-matrix.md` for the metric-by-metric trace through sources → graph → retrieval → reasoning → recommendations → monitoring | same document | `scripts/validate_knowledge.py`, `test_evaluation_benchmark.py` |

## Conversational Intelligence — 15%

| What the challenge evaluates | What EcoSynapse implements | How we demonstrate it | How we test it |
|---|---|---|---|
| Useful, prioritized clarifying questions | Up to 3 per turn, priority-ordered by ecological importance, not exhaustive forms | Send an ambiguous message in the Workspace | `test_ambiguous_message_triggers_clarifying_questions` |
| Multi-turn memory | Profile persists and accumulates across turns in a conversation | Send facts across multiple messages | `test_structured_facts_extracted_and_marked_ready` |
| Conflict handling | Conflicting values are detected, the newer value is used, and — **added this pass** — the UI now shows a "Conflict detected: previous value → new value, current reasoning uses X" banner (previously computed by the backend but never surfaced) | Workspace: state a value, then contradict it | `test_conflicting_value_is_flagged`, `ConflictBanner.test.tsx` |
| Adapts to accumulated context | Reassessment picks up all previously-stated facts, not just the latest message | Change a value, click Reassess, see the diff | `test_reassess_reflects_profile_change` |

## Output Clarity — 10%

| What the challenge evaluates | What EcoSynapse implements | How we demonstrate it | How we test it |
|---|---|---|---|
| Actionable recommendations | Every card: what to do, why, impacted metrics, time horizon | RecommendationCard | `test_evaluation_case` schema checks |
| Clear metrics and time horizons | Explicit `impacted_metrics` list and `time_horizon` enum, never freehand text | same | same |
| Evidence easy to inspect | One-click expand to claim-level evidence table | same | `RecommendationCard.test.tsx` |
| Uncertainty is understandable | Confidence, evidence strength, and data completeness shown as three distinct, separately-explained values, not one opaque score | same | `RecommendationCard.test.tsx::reports confidence, evidence strength, and data completeness as distinct values` |

## What is not scored here

This document does not assign EcoSynapse a percentage or place it against
other submissions — only an actual judge applying the rubric can do that.
It states, per weighted category, exactly what was built and how to verify
it, so the scoring is based on inspection rather than a claim.
