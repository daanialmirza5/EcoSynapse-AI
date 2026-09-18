# Competition readiness

A factual assessment against the challenge brief's own evaluation
dimensions (Depth of reasoning 30%, Scientific grounding 25%, Knowledge
system design 20%, Conversational intelligence 15%, Output clarity 10%).
**No numeric score is assigned here** -- only a judge applying the actual
rubric can produce one; what follows is evidence for and against each
dimension, plus honest gaps.

See also: `docs/darukaa-requirement-matrix.md` (every requirement mapped to
implementation/test/status), `docs/darukaa-evaluation.md` (the same rubric
categories mapped to what/how/test), and `docs/knowledge-coverage-matrix.md`
(every mandatory metric traced end-to-end through sources, graph, retrieval,
reasoning, and monitoring).

## Technical completeness

- Backend: FastAPI + SQLAlchemy + Alembic, 45 passing tests (SQLite and
  Postgres), all mandatory API endpoints implemented and documented
  (`docs/api-reference.md`).
- Frontend: 11 routes, all functional against the live backend (not static
  mockups), 13 passing tests.
- Docker Compose verified end-to-end against real Postgres (see
  `docs/evaluation-report.md`); two real bugs found and fixed during that
  verification (see `docs/engineering-audit.md`).
- Live deployment: not completed as of this writing -- see
  `docs/deployment.md` for exact status and required next step (owner
  completes `railway login`/`vercel login`).

## Scientific grounding (25% of rubric)

- 12 sources, each independently verified via live search during
  development (not recalled from model memory), with real DOIs/URLs --
  methodology and verification notes in `docs/scientific-grounding.md`.
- Automated structural validation of the corpus
  (`scripts/validate_knowledge.py`): 0 errors.
- Every claim classified into one of 5 types
  (`source_supported`/`model_derived`/`hypothesis`/`user_observation`/`unknown`);
  automated verification cross-checks numeric figures against retrieved
  excerpts and downgrades unverifiable ones.
- Demonstrated honesty under pressure: the agroforestry recommendation
  reports its cited meta-analysis's actual finding of "no unequivocal
  effect," rather than smoothing it into generic positive advice (see
  `docs/judge-story.md`).
- Gap: 12 sources is a demo-scale corpus, not a systematic literature
  review; several ecologically plausible edges are honestly marked
  `hypothesis` because no source in the corpus covers them.

## Knowledge system design (20% of rubric)

- Hybrid retrieval (semantic + lexical + knowledge-graph term expansion),
  fully inspectable via `POST /retrieval/inspect` and the Evidence Explorer
  UI -- not asserted, demonstrably runnable. Each result now reports its
  semantic score, lexical score, and matched graph concepts *separately*
  (previously only a combined score was shown), so a judge can see exactly
  how much each retrieval channel contributed.
- `docs/knowledge-coverage-matrix.md` traces every mandatory metric
  end-to-end through sources, graph nodes, retrieval vocabulary, reasoning
  rules, recommendation types, and monitoring indicators -- and honestly
  flags the one metric (soil pH) with no cataloged intervention yet.
- Typed knowledge graph (23 nodes, 22 edges) with evidence-strength labels
  on every edge; multi-hop traversal used by the reasoning engine.
- Gap (documented, not hidden): default embedding is a deterministic
  hashing scheme, not a trained neural embedding; pgvector is present in
  the Docker Postgres image but not wired into any query (see
  `docs/database-schema.md` for the reasoning and upgrade path).

## Depth of reasoning (30% of rubric)

- 10-step deterministic pipeline (concern detection -> candidate
  interventions -> constraint checks -> claim verification -> monitoring
  plan), documented step-by-step with exact function references in
  `docs/reasoning-methodology.md`.
- Hard gate on <3 known variables -- the system refuses to force a shallow
  answer and states the limitation explicitly instead (verified by a
  dedicated test).
- Multi-variable reasoning demonstrated for all three mandated pairings
  (soil health <-> biodiversity, water <-> species survival, land use <->
  fragmentation) plus additional pairings (pollution, deforestation,
  climate).
- Constraint/trade-off engine flags water-sensitivity conflicts,
  user-stated limits, and ecosystem-context mismatches per recommendation.
- Confidence, evidence strength, and data completeness are reported as
  three distinct values (not conflated into one opaque number), each with
  a documented calculation.
- Per-recommendation "Why this recommendation?" drill-down: shows the exact
  detected conditions, knowledge-graph steps, and evidence that produced
  *that specific* recommendation (not a generic assessment-wide trace),
  correlated via the recommendation's own `intervention_id`.
- A 10-test adversarial ("red-team") suite
  (`apps/api/tests/test_red_team_hallucination.py`) actively tries to break
  the system's scientific-safety guarantees -- and found and fixed two real
  bugs in the process (see below).

## Conversational intelligence (15% of rubric)

- Rule-based (regex/keyword) extraction, by deliberate design choice
  (transparency and testability over LLM-based NLU) -- documented as a
  trade-off, not hidden.
- Up to 3 prioritized clarifying questions per turn, not an exhaustive form.
- Multi-turn memory via persisted `Conversation`/`EnvironmentalProfile`;
  conflicting values are detected and surfaced, not silently overwritten --
  **the UI now shows an explicit "Conflict detected: previous value -> new
  value" banner** (previously the backend computed this but it never reached
  the screen; fixed this pass).
- Both natural-language and structured-JSON input accepted in the same
  message, entering the same reasoning pipeline.
- Two real extraction bugs found by red-teaming and fixed this pass: (1) an
  adversarial "assume rainfall is 1000mm" instruction was being accepted as
  a real stated measurement; (2) "semi-arid" (an ecosystem descriptor) was
  falsely triggering "low rainfall" via a substring match on "arid",
  silently overriding an explicit "rainfall is high" statement in the same
  message. Both now have regression tests.
- Gap: extraction will still miss phrasings outside its regex patterns
  rather than attempting a best-effort guess -- a deliberate
  scientific-integrity trade-off, but a real coverage limitation for
  free-form phrasing.

## Output clarity (10% of rubric)

- Every recommendation includes: what to do, why it may work, impacted
  metrics, time horizon, confidence (+ reason), evidence strength, data
  completeness, feasibility constraints, trade-offs, claim-level evidence
  table, and monitoring plan -- the full challenge section 14 contract.
- UI renders all of the above with progressive disclosure (summary visible,
  evidence/monitoring behind an explicit expand action) rather than a wall
  of text.
- Ranking heuristic is labeled a prototype everywhere it's shown, with its
  exact weights and component scores visible, not hidden inside a single
  opaque score.

## UX

- 11 functional pages, verified rendering correctly in a real headless
  browser during development (not just "should work" -- screenshots taken).
- Loading/empty/error states implemented and tested for the core chat and
  recommendation-display components.
- Known gap: no independent accessibility audit (screen reader, full
  keyboard-navigation walkthrough) was performed; semantic landmarks and
  labeled inputs are in place but not exhaustively verified.

## Testing

- 61 backend tests (pytest), 18 frontend tests (vitest), all passing as of
  this writing against both SQLite and real Postgres.
- An 8-case evaluation benchmark exercising schema validity, citation
  coverage, unsupported-claim rate, ecosystem-mismatch detection, and
  baseline-aware monitoring -- explicitly labeled a prototype evaluation,
  not an expert-labeled benchmark (see `docs/evaluation.md`).
- A dedicated 10-test adversarial ("red-team") suite
  (`test_red_team_hallucination.py`) specifically targeting hallucination
  and scientific-safety failure modes -- found and fixed two real bugs (an
  "assume X" instruction being accepted as fact, and "semi-arid" falsely
  triggering "low rainfall") rather than only confirming things already worked.
- CI runs backend tests against both SQLite and a real Postgres service
  container, frontend lint/typecheck/test/build, a knowledge-corpus
  validation step, and a dependency vulnerability scan (`pip-audit`).

## Demo readiness

- `docs/demo-script.md` provides 60-second, 3-minute, 5-minute, and
  self-paced technical-judge-walkthrough versions, all exercisable against
  the actual running system (no scripted fake data).
- The "load the challenge demo scenario" shortcut in the Workspace chat
  reproduces the canonical demo path in one click.
- The conflict-detection and "why this recommendation?" features are now
  visible in the UI (previously computed by the backend but not surfaced),
  making the conversational-intelligence and depth-of-reasoning criteria
  directly observable rather than requiring API inspection.

## Summary of what would most improve the next iteration

In priority order: (1) complete the live deployment once credentials are
available, (2) expand the source corpus with a second research pass focused
on the currently-`hypothesis`-only edges and the soil-pH intervention gap
(see `docs/knowledge-coverage-matrix.md`), (3) an independent accessibility
audit, (4) a load/performance test once real usage patterns exist to test
against, (5) resolve the react-router moderate advisory via a tested v7
migration (deferred this pass -- see `docs/evaluation-report.md`).
