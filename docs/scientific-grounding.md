# Scientific grounding methodology

This document exists because the challenge brief is explicit and strict: **do
not fabricate citations, DOIs, author names, datasets, or numerical
estimates.** Here is exactly how that requirement was operationalized.

## The claim taxonomy

Every `ScientificClaim` row (and every `evidence[]` entry in an API response)
carries a `claim_type`:

| Type | Meaning | Example in this system |
|---|---|---|
| `source_supported` | Directly backed by a verified source and a retrievable excerpt | "Intercropping increased beneficial arthropod abundance by 36%..." (edge `e9`, source `s12`) |
| `model_derived` | A logical inference from a source finding, not itself directly tested | "IPM reduces pesticide use" inferred from the pesticide-hazard finding (edge `e12`) |
| `hypothesis` | Ecologically plausible, not evidenced in this corpus | "Microbial activity supports aboveground habitat diversity" (edge `e2`) |
| `user_observation` | Something the user reported (e.g. "pollinators seem to be declining") | Stored in `EnvironmentalProfile.biodiversity_indicators`, never treated as verified fact |
| `unknown` | Explicitly insufficient evidence | Cover cropping → soil organic carbon (edge `e17`) — see below |

The evidence-verification service (`app/evidence/verification.py`) computes a
downstream `evidence_status` for display: `supported`, `partially_supported`,
`insufficient_evidence`, or `unverified`. A `source_supported` claim is
automatically downgraded to `partially_supported` if either (a) the profile's
ecosystem context doesn't match the source's studied context, or (b) a
numeric figure in the claim text cannot be found in the retrieved excerpt —
an automated check against silently drifting a paraphrase into an unsupported
number.

## How the seed corpus was built

All 12 sources in `data/seed/sources.json` were located via live web search
during development (not recalled from training-data memory) specifically to
avoid the failure mode of a confident-sounding but wrong citation. For each:

- **Title, organization/journal, year** were taken from the search result
  snippet or the publisher's own page.
- **DOI/URL** is the actual link returned by the search, used as the citation
  (`https://doi.org/<doi>` or the source URL).
- Where a detail could not be confirmed with confidence (e.g. exact
  publication year for two sources, `s11` and `s12`), it is left `null` in
  the database and the gap is stated in that source's `limitations` field —
  never guessed.
- **`s7`'s DOI** was inferred from Frontiers' standard, publicly documented
  URL→DOI naming convention rather than an independent CrossRef lookup; this
  is disclosed explicitly in `s7.limitations`.
- Excerpts stored in `EvidenceChunk` are **paraphrased summaries of the
  search-result findings**, not verbatim reproductions of copyrighted
  article text — each is short and attributed.

Full list with the exact claim each source supports: see
`data/seed/sources.json` (metadata) and `data/seed/relationships.json`
(claims + which source backs each one).

## An honesty example: agroforestry

The challenge brief itself lists agroforestry as an illustrative example
intervention. It would have been easy to hard-code "agroforestry improves
biodiversity" as a confident claim. Instead, the two agroforestry sources
found during research were:

- Mupepele, Keller & Dormann (2021), *"European agroforestry has no
  unequivocal effect on biodiversity: a time-cumulative meta-analysis"* — the
  title itself states the finding.
- Boinot et al. (2022), a synthesis calling for standardized methodology
  because the existing evidence is heterogeneous.

The system's agroforestry recommendation (`edge e10`/`e10b` in
`relationships.json`) is deliberately worded to match: `evidence_strength:
"weak"`, and the `limitations` field states outright *"Do not present
agroforestry as a guaranteed biodiversity benefit; suitability must be
evaluated per-site."* This is visible end-to-end: the reasoning engine sets
`confidence.level: "low"` for this recommendation whenever water constraints
are also present, and the trade-offs list surfaces the "no unequivocal
effect" finding verbatim. See `apps/api/tests/test_assessments.py::test_agroforestry_recommendation_is_not_overclaimed`.

## An honesty example: cover cropping

No source in the corpus directly measures cover cropping's effect on soil
organic carbon. Rather than borrow a plausible-sounding number from general
soil science, edge `e17` in `relationships.json` is explicitly:

```json
{
  "claim_type": "unknown",
  "claim_text": "Evidence is insufficient to support a reliable quantitative estimate of cover cropping's effect on soil organic carbon for this condition.",
  "source_id": null
}
```

This is the literal mandated sentence from the challenge brief's scientific
integrity section, produced because it is genuinely true for this corpus —
not templated onto every answer.

## What the system will never do

- Invent a DOI, author list, or dataset that wasn't returned by an actual
  lookup.
- State a numeric improvement (e.g. "+20% biodiversity") unless a cited
  source states that exact figure and the profile's conditions are
  compatible with the source's stated conditions.
- Present a `hypothesis`- or `model_derived`-type claim as an observed
  result — the UI always shows the claim-type badge alongside the claim.
- Treat the challenge brief's illustrative example (agroforestry/intercropping
  for the semi-arid wheat scenario) as pre-validated scientific evidence; it
  is treated as one of several *candidate* interventions to investigate,
  scored the same way as any other candidate.

## Known corpus limitations

- 12 sources is a demo-scale corpus, not a systematic literature review.
  Several ecologically important edges are honestly marked `hypothesis`
  because no source in the corpus covers them yet (e.g. soil pH ↔ microbial
  activity, vegetation establishment ↔ species survival).
- Sources were selected to cover the challenge's mandatory knowledge areas
  breadth-first, not to exhaustively cover any one topic.
- No full-text PDFs are stored or redistributed — only metadata and short,
  paraphrased excerpts, in keeping with each source's `license_notes` field.
