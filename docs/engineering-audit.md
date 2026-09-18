# Engineering audit

Conducted by inspecting the repository, running the app locally, running it
under Docker Compose against real PostgreSQL, and driving it in a real
headless browser. This is a point-in-time audit (2026-09-18); see git
history for what has since changed.

Severity key: **CRITICAL** (breaks core function or is unsafe) / **HIGH**
(should fix before relying on this) / **MEDIUM** (real but not urgent) /
**LOW** (polish) / **OPTIONAL** (would need to justify the added complexity).

## Findings and their disposition

| # | Finding | Severity | Status |
|---|---|---|---|
| 1 | Docker image for the API never included `data/seed/*.json` (build context was `apps/api`, excluding the repo-root `data/` dir); a deployed container booted with an **empty knowledge base** and no visible error beyond a logged traceback. | CRITICAL | **Fixed** -- build context moved to repo root, `SEED_DATA_DIR` env override added, `/health` now reports `degraded` with an explanatory note when this happens again. |
| 2 | `monitoring_plans.unit` / `measurement_frequency` were bounded `VARCHAR(40)`/`VARCHAR(80)`. SQLite does not enforce declared VARCHAR lengths, so the entire SQLite-backed test suite passed; a real generated unit string ("structural/habitat diversity index (method-dependent)", 55 chars) caused every assessment against Postgres to 500. | CRITICAL | **Fixed** -- widened to `Text`; added a direct regression test (`test_monitoring_plan_field_widths.py`) and a Postgres-backed CI job so this class of bug can't return silently. |
| 3 | Request body size limit only checked the `Content-Length` header -- omittable via chunked transfer encoding, or simply falsified. | HIGH | **Fixed** -- rewritten as an ASGI-level middleware that counts real bytes received. |
| 4 | No rate limiting of any kind. | HIGH | **Fixed (basic)** -- in-memory sliding-window limiter, documented as single-process-only (not shared across horizontally-scaled instances; would need Redis for that). |
| 5 | No request ID / structured per-request logging; diagnosing a production issue from logs alone would have been difficult. | HIGH | **Fixed** -- `X-Request-ID` header + method/path/status/latency logged per request; included in the generic-error JSON body for support correlation. |
| 6 | Only one `/health` endpoint, conflating liveness and readiness; a DB hiccup mid-request wasn't distinguishable from "app is down." | MEDIUM | **Fixed** -- added `/health/ready` (strict, 503 if DB unreachable) alongside the existing informational `/health`. |
| 7 | No test exercised a 404, a validation error, a malformed JSON body, or an oversized request -- error-handling behavior was implicitly assumed to work. | MEDIUM | **Fixed** -- 7 new tests in `test_error_handling.py`. |
| 8 | Confidence, evidence strength, and data completeness were conflated into a single `confidence.level` + free-text reason; a reader couldn't see the raw evidence-strength signal separately from how constraints adjusted it. | MEDIUM | **Fixed** -- `evidence_strength_summary` and `data_completeness` are now distinct fields on every recommendation, shown as separate badges in the UI. |
| 9 | `docker-compose.yml` published Postgres on host port 5432, which collided with a pre-existing Postgres instance on the development machine (`docker compose up` failed outright). | MEDIUM | **Fixed** -- DB port is no longer published to the host at all (the `api` service only needs the internal Docker network); this is also a minor security improvement (DB not reachable from the host network). |
| 10 | The frontend API client used relative paths (`/api/v1/...`) unconditionally, which only works for same-origin deployments (local dev proxy, Docker/nginx). A split deployment (Vercel frontend + a separately-hosted backend) would 404 every request. | HIGH (for the chosen deployment architecture) | **Fixed** -- `VITE_API_BASE_URL` build-time env var, documented in `apps/web/.env.example` and `docs/deployment.md`. |
| 11 | A managed Postgres add-on (Railway, Heroku, etc.) commonly hands out a bare `postgres://` or `postgresql://` URL; this app's installed driver requires `postgresql+psycopg://`. | MEDIUM | **Fixed** -- `Settings.resolved_database_url` normalizes both legacy schemes automatically. |
| 12 | API container ran as root. | LOW | **Fixed** -- non-root `appuser` in `apps/api/Dockerfile`. |
| 13 | No automated check that the seed corpus itself is internally consistent (duplicate ids, malformed URLs, orphaned references). | MEDIUM | **Fixed** -- `scripts/validate_knowledge.py`, wired into CI and the pytest suite. Currently reports 0 errors, 1 informational warning (an intentional cross-reference, see script output). |
| 14 | Evaluation benchmark only covered 3 scenarios; several evaluation-relevant behaviors (ecosystem-context mismatch flagging, monitoring-plan behavior once a baseline is recorded, a genuinely strong-evidence candidate) weren't exercised. | MEDIUM | **Fixed** -- 3 new cases added (6 scenario cases total), each asserting a real, previously-unverified behavior. |
| 15 | `pgvector` Postgres image is used in `docker-compose.yml`, but the `vector` column type and ANN index are not used by any query. | LOW (documented trade-off, not a defect) | **Not changed.** At the current corpus scale (~25 evidence chunks), a Python-side cosine-similarity scan is effectively free; wiring pgvector would add real complexity (a new migration path, a Postgres-only code branch, a SQLite fallback) for no measurable benefit at this scale. Documented explicitly in `docs/database-schema.md` rather than silently left unmentioned. |
| 16 | No authentication. | LOW (documented trade-off for a hackathon prototype) | **Not changed.** Adding a full auth system for a single-team demo would be scope creep with no judge-visible benefit; documented as an explicit, intentional omission (see README limitations). |
| 17 | `httpx`/`starlette.testclient` combination emits a deprecation warning ("install httpx2 instead") on every test run. | LOW | **Not changed.** Cosmetic; the warning is from the test-client transport, not application code, and doesn't affect behavior. Left as a known, harmless warning rather than chasing a dependency churn item with no functional payoff. |
| 18 | Frontend production bundle is a single ~630KB JS chunk (Vite's default warning threshold is 500KB). | LOW | **Not changed.** Code-splitting (e.g. per-route lazy imports) would reduce initial load time but the app is a single-team demo with ~10 routes, not a high-traffic public product; flagged here rather than spending the remaining time on a UX improvement with limited demo-time payoff. |

## Areas reviewed with no material findings

- **Security**: no raw SQL/`eval`/`exec`/`subprocess` anywhere in the backend (grepped); all DB access goes through the SQLAlchemy ORM (parameterized automatically). CORS is explicit-allowlist by default, not wildcard. No secrets are committed (`.env.example`/`apps/web/.env.example` only, `.gitignore` excludes `.env`/`*.db`/`.venv`/`node_modules`).
- **Scientific integrity**: `scripts/validate_knowledge.py` found no duplicate sources, no malformed URLs, no orphaned claim/edge references, and no `source_supported` claim missing a source.
- **HTTPException handling**: verified directly (not assumed) that a 404 raised inside a route handler is not swallowed by the app's generic `Exception` handler into a misleading 500 -- see `test_error_handling.py::test_404_is_not_swallowed_into_a_generic_500`.
- **Accessibility**: routes use semantic `<nav>`/`<main>` landmarks (`AppLayout.tsx`), form inputs have associated `<label>` text, color is never the only signal (badges pair color with text), and the layout is responsive at phone width (`grid md:grid-cols-2`-style breakpoints throughout). Not independently audited with a screen reader.

## What this audit deliberately did not do

- A full penetration test (out of scope for a hackathon-timeline audit; the "areas reviewed" section above covers the OWASP-relevant basics that are checkable by code inspection).
- Load/performance testing under concurrent load (the app has never been exposed to production traffic; no data exists to report here, and fabricating numbers would violate this project's own scientific-integrity standard applied to itself).
- Forcing the `npm audit` fixes below, which all require breaking major-version upgrades -- see `docs/evaluation-report.md` for the exact findings and the reasoning for deferring them rather than force-upgrading React Router with no regression-testing time left. (`pip-audit` was run against the backend: 0 known vulnerabilities.)
