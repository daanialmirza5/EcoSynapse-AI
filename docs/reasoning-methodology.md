# Reasoning methodology

`apps/api/app/reasoning/engine.py::run_assessment` implements the ten-step
pipeline required by the challenge (section 11). This document walks through
each step with the actual code path and a worked example (the challenge's
illustrative semi-arid wheat scenario: soil organic carbon 0.3%, low
rainfall, monoculture wheat, semi-arid region).

## Step 1 — Build environmental state
`_known_facts(profile)` produces a list of `{field, value, unit, source}`
entries for every non-null profile field. Nothing is inferred here — it is a
direct read of what the user provided.

## Step 2 — Identify relevant variables
`_variables_considered(profile)` returns the names of known variable
*categories* (`soil_ph`, `soil_organic_carbon`, `soil_moisture`, `rainfall`,
`temperature`, `land_use_type`, `biodiversity_indicators`,
`human_impact_indicators`). **If fewer than 3 are known, the pipeline stops
here** and returns an `Assessment` with `status="insufficient_data"`,
`recommendations=[]`, and an `overall_limitations` entry stating the exact
mandated sentence: *"Evidence is insufficient to support a reliable
quantitative estimate for this condition."* This is the literal mechanism
behind "must not force three variables into every answer" — it is a hard
gate, not a prompt instruction.

For the worked example: `soil_organic_carbon`, `rainfall`, `land_use_type`,
`biodiversity_indicators` → 4 known variables → pipeline proceeds.

## Step 3 — Identify relevant ecological relationships
`constraints.py::detect_concerns` applies threshold rules (documented, not
hidden): SOC < 1%, rainfall low/<500mm, soil moisture <20%, pH outside
5.5–8.5, monoculture land use, pesticide/deforestation flags, declining
biodiversity trend. For the worked example this fires: `low_soil_organic_carbon`,
`water_scarcity`, `monoculture_land_use`, `declining_biodiversity`.

## Step 4 — Gather evidence
Each concern maps to candidate `Intervention` ids via
`CONCERN_TO_INTERVENTIONS` (a documented, explicit dict — not an LLM guess).
For each candidate, `_build_recommendation` walks its direct
`KnowledgeEdge` rows, resolves the linked `ScientificClaim` →
`ScientificSource` → `EvidenceChunk`, and additionally extends one hop
downstream through the graph toward `species_richness` to surface secondary,
biodiversity-indicator-level effects (e.g. agroforestry → habitat_diversity →
species_richness).

## Step 5 — Generate candidate interventions
Concerns → candidates (deduplicated, capped at 5). For the worked example:
*Cover cropping*, *Agroforestry*, *Water harvesting*, *Crop diversification*,
*Native hedgerows*.

## Step 6 — Check constraints
`constraints.py::check_constraints` flags: water-sensitivity conflicts (low
rainfall + a `medium`/`high` water-sensitivity intervention), user-stated
constraints (budget, irrigation, conservation restrictions) matched against
the intervention's own constraint flags, and ecosystem-context mismatches
(the intervention's evidence was studied in a different ecosystem than the
profile's).

## Step 7 — Identify trade-offs and risks
Every edge's `limitations` string is surfaced verbatim in the
recommendation's `trade_offs`, plus any constraint-engine unknowns (prefixed
`"Unknown factor: ..."`) and an explicit low-evidence warning whenever the
average supporting evidence is `weak` or `hypothesis`.

## Step 8 — Generate the structured recommendation
Assembled into the exact schema from challenge section 14
(`app/schemas/assessment.py::RecommendationOut`): title, what-to-do,
why-it-may-work (concatenated edge mechanisms — real sentences from the
claims, not synthesized prose), impacted metrics, time horizon (from the
intervention catalog), feasibility constraints, trade-offs, confidence
(level + reason), evidence table, monitoring plan, and the heuristic score.

## Step 9 — Verify claims
`evidence/verification.py::verify_claim` runs for every claim attached to a
recommendation:
- `source_supported` + a real source → `supported` (or `partially_supported`
  if ecosystem context mismatches, or if a number in the claim text can't be
  matched against the retrieved excerpt).
- `model_derived` → always `partially_supported` (a documented inference,
  not a direct measurement).
- `hypothesis` / `unknown` → always `insufficient_evidence`.

This is a real, automated check — see
`apps/api/tests/test_evidence_verification.py` for cases including the
number-mismatch downgrade.

## Step 10 — Generate the monitoring plan
`monitoring/plans.py::generate_monitoring_entry`, once per impacted metric:
measurement method + frequency come from a metric-specific template (real
methodologies: lab SOC tests, standardized species transects, trap counts,
etc.). **The target field is never a fabricated number.** It is either:
- *"Establish a baseline first; a defensible target cannot be determined
  from the current information"* (no `EnvironmentalObservation` recorded for
  that metric on this profile), or
- *"Compare future measurements against the recorded baseline observation;
  a specific numeric improvement target is not established by current
  evidence"* (a baseline exists).

`expected_direction` (`increase`/`decrease`) is only set when a `strong` or
`moderate` supporting edge exists for that specific metric; otherwise it is
`null` and the uncertainty note says so explicitly.

## The prototype ranking heuristic

`constraints.py::compute_heuristic_score` combines three named, weighted
factors — evidence strength (40%), constraint fit (35%), ecosystem-context
match (25%) — into a single number shown in the UI labeled
`"prototype_decision_support_heuristic"` with the disclaimer *"Not a
validated or universal biodiversity index."* The weights and component
scores are always returned alongside the total so the ranking is auditable,
never a hidden black-box score.

## Reassessment

`POST /assessments/{id}/reassess` re-runs the full pipeline against the
current (possibly edited) profile and computes `diff_from_previous`:
per-field value changes and added/removed recommendation titles, by
comparing `Assessment.known_facts` and recommendation titles between the two
versions (`engine.py::_compute_diff`). This is what powers "change an input,
reassess, see what changed and why" in the demo script.
