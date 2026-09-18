# Team handoff

Written for a teammate who has never seen this repository. Start here, then
follow the links for depth.

## What this is

EcoSynapse AI: an evidence-grounded ecological decision-support system. Not
a chatbot -- a deterministic reasoning pipeline (extraction -> retrieval ->
knowledge graph -> constraint checking -> claim verification -> monitoring
plan) with a conversational UI on top. Read `docs/judge-story.md` for the
elevator pitch and `docs/architecture.md` for the technical shape.

Two competition-focused documents worth reading before anything else:
`docs/darukaa-requirement-matrix.md` (every challenge requirement mapped to
its implementation/test/status) and `docs/knowledge-coverage-matrix.md`
(every mandatory metric traced through sources -> graph -> retrieval ->
reasoning -> recommendations -> monitoring, including the one honest gap:
soil pH has no cataloged intervention yet).

## Repository structure

```
apps/api/     FastAPI backend -- see "Backend" below
apps/web/     React + TypeScript + Vite + Tailwind frontend
data/seed/    The 12-source scientific corpus + knowledge graph edges
              + intervention catalog (JSON, hand-curated, validated by
              scripts/validate_knowledge.py)
docs/         Everything you're reading now
tests/        Cross-repo evaluation cases (JSON scenarios run by
              apps/api/tests/test_evaluation_benchmark.py)
scripts/      Standalone tooling (currently: validate_knowledge.py)
```

## How to run it

See README.md §11 for the full Windows/macOS/Linux commands. Short version:

```powershell
cd apps\api
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```
```powershell
cd apps\web
npm install
npm run dev
```
Or `docker compose up --build` for the full containerized stack (verified
working as of 2026-09-18, see `docs/evaluation-report.md`).

No API keys or accounts are needed to run the full demo -- everything
defaults to deterministic, offline providers.

## Environment variables

`.env.example` (backend) and `apps/web/.env.example` (frontend) document
every variable. Nothing is required for local dev.

## Backend

- **Entry point**: `apps/api/app/main.py` -- FastAPI app, middleware stack
  (request logging, rate limiting, body-size cap), `/health` and
  `/health/ready`.
- **Routes**: `apps/api/app/api/v1/*.py`, thin, delegate to services.
- **The reasoning engine** (the actual product): `apps/api/app/reasoning/engine.py`.
  Read `docs/reasoning-methodology.md` before touching this file.
- **Retrieval**: `apps/api/app/retrieval/hybrid.py`.
- **Knowledge graph**: `apps/api/app/knowledge/graph.py` builds a NetworkX
  graph from the `KnowledgeNode`/`KnowledgeEdge` tables on every call.
- **Models**: `apps/api/app/models/*.py` (SQLAlchemy 2.0), migrations in
  `apps/api/alembic/versions/`.
- **Config**: `apps/api/app/core/config.py` -- every setting has an offline
  default; read the docstrings before adding a new required env var.

## Frontend

- **Entry point**: `apps/web/src/App.tsx` -- routes, wrapped in
  `WorkspaceProvider` (`apps/web/src/hooks/useWorkspaceState.tsx`), which
  holds the active conversation/profile/assessment IDs in `localStorage` so
  they survive a page refresh.
- **API client**: `apps/web/src/lib/api.ts`. If you add a backend endpoint,
  add its typed wrapper here and its type in `apps/web/src/types/api.ts`.
- **The flagship screen**: `apps/web/src/pages/Workspace.tsx` +
  `apps/web/src/features/workspace/*.tsx`.
- **Shared UI primitives** (badges, cards, states): `apps/web/src/components/ui.tsx`.

## Database

SQLite by default (zero setup), Postgres in production via `DATABASE_URL`.
**Read `docs/engineering-audit.md` findings #1 and #2 before assuming SQLite
behavior generalizes to Postgres** -- two real bugs were only visible under
Postgres because SQLite doesn't enforce VARCHAR lengths and has a different
Docker-context path-resolution story. When adding a new bounded `String(N)`
column for free-form generated text, ask whether it should be `Text` instead.

## How to add a scientific source

1. Verify it yourself (live search, not memory) -- title, organization,
   year, DOI or URL, and what it actually claims.
2. Add an entry to `data/seed/sources.json` with a unique `id`. Every source
   needs a `limitations` field, even if brief.
3. Add one or more entries to `data/seed/relationships.json` linking a
   `from_node`/`to_node` pair to this source, with the correct `claim_type`
   (`source_supported` only if this exact source supports the claim) and
   `evidence_strength`.
4. Run `python scripts/validate_knowledge.py` -- it checks for duplicates,
   malformed URLs, and orphaned references.
5. Run `pytest apps/api/tests/test_knowledge_validation.py` (this runs the
   same script as part of the suite) and reseed locally:
   ```powershell
   .\.venv\Scripts\python.exe -c "from app.db.session import SessionLocal; from app.knowledge.seed import seed_all; db = SessionLocal(); print(seed_all(db, force=True)); db.close()"
   ```

## How to add a recommendation (intervention)

1. Add an entry to `data/seed/interventions.json` with a semantic `id`
   (e.g. `mulching`), `target_metrics`, `ecosystem_context`,
   `water_sensitivity`, and `typical_time_horizon`.
2. Add at least one relationship in `data/seed/relationships.json` from
   your new intervention id to a metric node, backed by a real source (or
   explicitly marked `hypothesis`/`unknown` if none exists -- see the
   cover-cropping example in `docs/scientific-grounding.md` for how to be
   honest about missing evidence).
3. Add it to `CONCERN_TO_INTERVENTIONS` in
   `apps/api/app/reasoning/constraints.py` so the engine knows which
   detected concerns should surface it as a candidate.
4. Reseed and run the evaluation benchmark to confirm it appears where expected.

## How to modify the reasoning engine

Read `docs/reasoning-methodology.md` first -- it maps every one of the 10
pipeline steps to its exact function. The engine is deliberately deterministic
Python, not an LLM prompt; keep it that way (see `docs/judge-story.md` for
why this matters to the project's core claim). Any new behavior should be
covered by a test in `apps/api/tests/test_assessments.py` or
`test_evaluation_benchmark.py`.

## How to modify the frontend

Follow the existing pattern: a page in `apps/web/src/pages/`, feature
components in `apps/web/src/features/<feature>/`, shared primitives in
`apps/web/src/components/ui.tsx`. Every page should handle loading, empty,
and error states explicitly (see `apps/web/src/components/ui.tsx`'s
`LoadingState`/`EmptyState`/`ErrorState`) -- don't let a fetch fail silently.

## How to run the evaluation

```bash
cd apps/api
pytest tests/test_evaluation_benchmark.py -v
```
To add a case: drop a new JSON file in `tests/evaluation_cases/` (see the
existing ones for the schema) -- the test file picks up every `*.json` in
that directory automatically.

## How to create a demo

`docs/demo-script.md` has 60-second, 3-minute, and 5-minute versions. The
"load the challenge demo scenario" button in the Workspace chat panel drives
the canonical demo path end to end.

## Common errors and their fixes

| Symptom | Cause | Fix |
|---|---|---|
| `/health` shows `sources: 0` | Seeding failed | Check startup logs; in Docker, confirm `SEED_DATA_DIR` and that the image was built from the repo root (see `apps/api/Dockerfile`'s header comment) |
| Assessment 500s only in production/Postgres, works locally | A bounded `String(N)` column too narrow for real generated text -- SQLite doesn't enforce lengths, Postgres does | Widen the column to `Text` if it's free-form generated content, add a migration with `op.batch_alter_table` (needed for SQLite compatibility) |
| Frontend calls hit 404 after a split deployment | `VITE_API_BASE_URL` not set at build time | Set it in the hosting platform's env vars and rebuild (it's a build-time, not runtime, Vite env var) |
| `docker compose up` fails with "port already allocated" | Something else on the host is using that port (commonly 5432) | The `db` service intentionally doesn't publish 5432 to the host anymore; check `docker ps`/`Get-NetTCPConnection` for the actual conflicting process before assuming it's this project |
| A new Alembic migration fails on SQLite with "near ALTER: syntax error" | SQLite has no native `ALTER COLUMN` | Wrap the operation in `with op.batch_alter_table(...) as batch_op:` |
| A keyword extractor rule fires on the wrong input (e.g. an ecosystem name accidentally matches a climate/soil keyword) | Substring matching is order- and collision-sensitive -- see the "semi-arid" vs. "arid" bug in `docs/engineering-audit.md`/`test_extraction.py` | Prefer a direct-statement regex first, fall back to indirect keyword matching only when no direct pattern hits, and explicitly guard known collision substrings |

**Before adding any new regex/keyword rule to `app/conversations/extraction.py`, add an adversarial test to `tests/test_red_team_hallucination.py` first** -- two real extraction bugs were found this way (an "assume X" instruction accepted as fact, and "semi-arid" silently overriding an explicit "rainfall is high" statement), not by inspection.

## Contributing

See `CONTRIBUTING.md` for branch/commit conventions and the testing bar for
a PR.

## Deployment

See `docs/deployment.md`. As of this writing, deployment credentials
(Railway + Vercel) had not yet been provided to complete a live deployment --
check that document's "Current status" line for whether that has changed.
