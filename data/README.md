# Data directory

- `seed/sources.json` — verified scientific/institutional sources (title, authors/org, year, DOI or URL, verified via live web search during development; see `docs/scientific-grounding.md`). None of these are fabricated citations; where a detail (e.g. exact publication year or DOI) could not be confirmed, it is left `null` and the gap is recorded in that source's `limitations` field.
- `seed/relationships.json` — ecological knowledge-graph edges. Each edge carries a `claim_type` (`source_supported`, `model_derived`, `hypothesis`, or `unknown`) and, where applicable, a link to the source that supports it. Edges without a real supporting source are explicitly labeled `hypothesis` or `unknown` rather than presented as findings.
- `seed/interventions.json` — the candidate intervention catalog used by the reasoning engine.
- `sample_profiles/` — example `EnvironmentalProfile` JSON payloads, including the challenge's illustrative semi-arid wheat scenario.
- `schemas/` — JSON Schema files describing the structured input formats accepted by the API (see `apps/api/app/schemas`).

Run `python -m app.knowledge.seed` (from `apps/api`) to load this data into the database.
