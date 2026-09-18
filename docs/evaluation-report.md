# Evaluation report

This supersedes the counts in `docs/evaluation.md` with the results measured
during the production-hardening pass on 2026-09-18. Every number below was
actually run on this machine on this date -- see the command next to each
result to reproduce it.

## Test suite results

| Suite | Command | Result |
|---|---|---|
| Backend (pytest, SQLite) | `cd apps/api && pytest -q` | **45 passed**, 0 failed |
| Backend (pytest, real Postgres) | `DATABASE_URL=postgresql+psycopg://... pytest -q` (see below) | **45 passed**, 0 failed |
| Frontend (vitest) | `cd apps/web && npm test` | **13 passed**, 0 failed |
| Frontend type check | `cd apps/web && npx tsc --noEmit` | **PASS**, 0 errors |
| Frontend lint | `cd apps/web && npm run lint` | **PASS**, 0 errors/warnings |
| Backend lint | `cd apps/api && ruff check app tests` | **PASS**, 0 errors |
| Knowledge corpus validation | `python scripts/validate_knowledge.py` | **PASS**, 0 errors, 1 informational warning |
| Frontend production build | `cd apps/web && npm run build` | **PASS** (629.75 kB main chunk, gzip 182.38 kB; over Vite's 500kB advisory threshold -- see engineering-audit.md #18) |
| Docker Compose build (api + web) | `docker compose build` | **PASS** |
| Docker Compose startup (db + api + web) | `docker compose up -d` | **PASS** -- all 3 containers reached `healthy`/`running` |
| Full demo flow against Dockerized Postgres | manual, via `Invoke-RestMethod` against `localhost:8000` | **PASS** -- see below |

To reproduce the Postgres-backed backend run locally:
```powershell
docker run -d --name pg-test -e POSTGRES_USER=ecosynapse -e POSTGRES_PASSWORD=ecosynapse -e POSTGRES_DB=ecosynapse -p 15432:5432 pgvector/pgvector:pg16
cd apps/api
$env:DATABASE_URL = "postgresql+psycopg://ecosynapse:ecosynapse@localhost:15432/ecosynapse"
python -m pip install "psycopg[binary]" pgvector
alembic upgrade head
pytest -q
```
This exact sequence is what surfaced the `monitoring_plans.unit` VARCHAR
truncation bug (see engineering-audit.md #2) -- it passed 0/45 relevant tests
before the fix and 45/45 after.

## Docker/Postgres smoke test (manual, against the real running stack)

Ran the full demo scenario through the actual HTTP API of the Dockerized
stack (`db` on internal network, `api` on `localhost:8000`, `web` on
`localhost:8080`), not the pytest TestClient:

1. `POST /api/v1/conversations` -> 201
2. `POST .../messages` with the semi-arid wheat scenario text -> extracted
   4 fields correctly, `ready_for_assessment: true`
3. `POST /api/v1/assessments` -> **201, 5 recommendations**, each with
   correct `confidence`, `evidence_strength_summary` (distinct values:
   `hypothesis`, `weak`, `moderate` across the 5 candidates -- not a
   constant), `data_completeness: 0.44`, and non-empty monitoring plans
4. `GET /api/v1/assessments/{id}/export` -> 201, payload id matches

## Evaluation benchmark (prototype, hand-curated -- see docs/evaluation.md)

`pytest tests/test_evaluation_benchmark.py -v`: **7/7 passed** (6 scenario
cases -- semiarid_wheat, insufficient_data, deforestation_pressure,
strong_evidence_intercropping, ecosystem_mismatch, monitoring_baseline_case
-- plus 1 coverage guard). All structural checks passed on every case
(schema validity, citation coverage, unsupported-claim rate, ecosystem-
mismatch flagging, baseline-aware monitoring wording).

**This is still a prototype evaluation** with no expert-labeled ground
truth -- see `docs/evaluation.md` for what these numbers do and do not prove.

## Dependency vulnerability scan (`npm audit`, apps/web)

Ran `npm audit` on 2026-09-18. Result: **7 vulnerabilities (5 moderate, 1
high, 1 critical)**, all in transitive dependencies:

| Package | Severity | Advisory | Where it applies |
|---|---|---|---|
| `vitest` (via `@vitest/mocker`) | critical | Arbitrary file read/execute when the Vitest **UI** server is listening | Dev-only; this project never runs `vitest --ui` (CI/local runs use `vitest run`), and vitest is not part of the production build output |
| `vite` | high | Path traversal in dev-server `.map` handling / `server.fs.deny` bypass on Windows | Dev-server only; not present in `vite build` production output |
| `@vitest/mocker`, `vite-node` | moderate | Downstream of the above | Same as above -- dev/test tooling only |
| `esbuild` | moderate | Dev server accepts requests from any origin | Dev-server only (bundled inside Vite's dev server) |
| `react-router` / `react-router-dom` | moderate | Open redirect via backslash in `<Link>`/`useNavigate`; SSR hydration issue (this app does not use SSR) | **Ships in the production bundle** |

**Decision:** the dev-tooling advisories (vite/vitest/esbuild) require no
action -- they describe dev-server-only attack surface that never reaches a
built/deployed artifact. The react-router open-redirect is real and does
ship in production, but the only available fix is a major-version upgrade
(6.x -> 7.x, `react-router-dom@7.18.4`), which changes route-definition APIs
across every page in this app. Force-upgrading it with no remaining time to
regression-test all 10 routes would trade a moderate, low-likelihood
(requires an attacker-controlled link a user clicks) vulnerability for an
unverified risk of breaking navigation across the entire app. **Deferred as
a documented follow-up** (see `docs/team-handoff.md`) rather than silently
ignored or force-upgraded without verification.

## What was not measured

- Retrieval precision/recall against human relevance judgments (no labeled
  dataset exists).
- Load/concurrency behavior under production-scale traffic (never deployed
  to real traffic).
- A full penetration test.
- `pip-audit` on the backend's Python dependencies (not run in this pass).
