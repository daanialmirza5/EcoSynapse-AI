# Evaluation

**This is a prototype evaluation.** There are no expert-labeled ground-truth
answers here — 3 hand-curated scenarios with automatically checkable
structural properties. Treat every number below as "this ran and passed on
this machine on this date," not as a validated accuracy metric.

## What is actually run

`apps/api/tests/test_evaluation_benchmark.py` loads
`tests/evaluation_cases/*.json` (3 cases: the challenge's illustrative
semi-arid wheat scenario, a deliberately under-specified profile, and a
tropical deforestation-pressure scenario) and checks, per case:

| Challenge evaluation criterion | Automated check performed |
|---|---|
| Multi-variable coverage | `len(variables_considered) >= expected_minimum` |
| Missing-information detection | The insufficient-data gate fires exactly when the case has <3 known variables, never otherwise |
| Output schema validity | Every recommendation has a valid `time_horizon`, `confidence.level`, non-empty `impacted_metrics`, non-empty `monitoring_plan` |
| Citation coverage | Every `source_supported` evidence entry has a non-null citation |
| Unsupported-claim rate | Every `hypothesis`/`unknown`-typed claim is reported with `evidence_status == "insufficient_evidence"`, never `"supported"` |
| Recommendation consistency | The expected intervention family (e.g. agroforestry/hedgerow/pest-management for a deforestation+pesticide scenario) appears among the candidates |

Run it: `cd apps/api && pytest tests/test_evaluation_benchmark.py -v`. As of
the last local run, **4/4 parametrized cases pass** (3 scenario cases + 1
benchmark-coverage guard).

## Criteria not automatable at this scale

The challenge's evaluation section also lists **retrieval relevance** and
**reassessment behavior** as things to evaluate. These are exercised by:

- `apps/api/tests/test_retrieval.py` — checks retrieval returns non-zero
  semantic candidates and that graph expansion actually adds terms (e.g.
  "monoculture land use" → expands to include `habitat_fragmentation`).
  Judging whether the *top-ranked* result is the single best possible one
  would require human relevance labels, which this prototype does not have.
- `apps/api/tests/test_assessments.py::test_reassess_reflects_profile_change`
  — confirms a profile edit produces a new assessment version and a non-empty
  `diff_from_previous`.

## Source-metadata correctness

Every seed source's `is_verified=True` flag and DOI/URL was checked against a
live web search during development (see
[scientific-grounding.md](scientific-grounding.md)) rather than machine-graded
— this is a one-time manual verification step, not a repeatable automated
test, and is disclosed as such.

## Honest summary

- Backend: 26 pytest tests pass (extraction, clarifying questions, the full
  reasoning pipeline, evidence verification, retrieval, knowledge graph, and
  the 4-case evaluation benchmark above).
- Frontend: 12 vitest tests pass (component rendering, loading/empty/error
  states, and the "never fabricate a numeric monitoring target" invariant).
- No claim is made about retrieval precision/recall, recommendation quality
  versus a human expert, or user-satisfaction — none of these were measured.
