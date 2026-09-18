# Deployment

## Current status

**As of 2026-09-18, this has been verified locally and via Docker Compose
(see docs/evaluation-report.md), but not deployed to a live public URL.**
Live deployment (Railway for the backend + Postgres, Vercel for the
frontend) requires the account owner to complete a one-time CLI login on
their own machine -- see "Deploying" below for the exact commands. Do not
represent this project as having a live demo URL unless one has actually
been deployed and smoke-tested after these docs were written; check the top
of `README.md` for whether that has since happened.

## Chosen architecture

```
Vercel (static React/Vite build)  --VITE_API_BASE_URL-->  Railway (FastAPI, Docker)
                                                                  |
                                                          Railway-managed PostgreSQL
```

- **Backend + DB: Railway.** Deploys straight from `apps/api/Dockerfile`
  (repo-root build context, see `docs/database-schema.md` and
  `docs/engineering-audit.md` #1 for why the context matters), with a
  Railway Postgres plugin providing `DATABASE_URL`.
- **Frontend: Vercel.** Static Vite build, with `VITE_API_BASE_URL` set at
  build time to the Railway backend's public URL. `apps/web/vercel.json`
  adds the SPA rewrite React Router needs (so refreshing `/workspace`
  doesn't 404).

This split-host setup is why `apps/web/src/lib/api.ts` was made
configurable (`VITE_API_BASE_URL`) rather than assuming same-origin, and why
`Settings.resolved_database_url` normalizes Railway's `postgres://`-style
connection string to the `postgresql+psycopg://` driver this app installs.

## Deploying (exact steps)

These are written to be run by whoever owns the Railway/Vercel accounts.
**Do not paste API tokens into a chat session with an AI assistant** --
run `railway login` / `vercel login` yourself in a terminal; both open a
browser for OAuth and persist the session to your local CLI config.

### 1. Backend (Railway)

```bash
railway login
cd apps/api
railway init                      # create/link a Railway project
railway add --plugin postgresql   # provision a Postgres database
railway up                        # builds from apps/api/Dockerfile (repo-root context)
```

In the Railway dashboard for the API service, set these variables
(Postgres's `DATABASE_URL` is injected automatically by the plugin as
`${{Postgres.DATABASE_URL}}` -- reference it, don't hardcode it):

| Variable | Value |
|---|---|
| `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` (Railway reference variable) |
| `ENVIRONMENT` | `production` |
| `APP_SECRET` | a real random secret, not the dev placeholder |
| `CORS_ORIGINS` | your Vercel URL once known, e.g. `https://ecosynapse.vercel.app` |
| `LLM_PROVIDER` | `mock` (or `openai` + `OPENAI_API_KEY` if desired) |
| `EMBEDDING_PROVIDER` | `hashing` (or `openai`) |

Set the healthcheck path to `/health/ready` in Railway's service settings
(Deploy tab) so Railway only routes traffic once the database is reachable.

Verify: `curl https://<your-railway-domain>/health` should return
`{"status": "ok", ...}` with `knowledge_base.sources: 12`. If `sources` is
`0`, seeding failed -- check the deploy logs (this exact failure mode is
what `docs/engineering-audit.md` finding #1 fixed; if it recurs, check that
`SEED_DATA_DIR=/app/data/seed` is set and the image was built with the
repo-root context).

### 2. Frontend (Vercel)

```bash
vercel login
cd apps/web
vercel link
vercel env add VITE_API_BASE_URL production   # paste your Railway backend URL, e.g. https://ecosynapse-api.up.railway.app
vercel --prod
```

Vercel auto-detects the Vite framework preset (build command `npm run
build`, output directory `dist`) from `apps/web`; no `vercel.json` build
config is needed beyond the SPA rewrite already committed.

### 3. Close the loop

Update the `api` service's `CORS_ORIGINS` on Railway to include the real
Vercel URL once assigned, and redeploy. Then run the live smoke test in
`docs/demo-script.md` against the real URLs and record the results in
`docs/competition-readiness.md`.

## Local Docker Compose (verified working)

```bash
docker compose up --build
```

Verified on 2026-09-18: all three containers (`db`, `api`, `web`) reach a
healthy state; `GET http://localhost:8000/health` reports 12 sources / 23
graph nodes / 22 graph edges; a full conversation -> assessment -> export
flow was run successfully against the containerized stack. See
`docs/evaluation-report.md` for the exact commands and output.

## Environment variables for production

See `.env.example` (backend) and `apps/web/.env.example` (frontend). Set
real values for `DATABASE_URL`, `APP_SECRET`, and `CORS_ORIGINS` at minimum;
everything else has a safe offline default.

## What a real deployment would still need beyond this

- HTTPS is handled by Railway/Vercel automatically for their default
  domains; a custom domain would need its own TLS setup on each platform.
- The in-memory rate limiter (`app/main.py::InMemoryRateLimiter`) does not
  coordinate across multiple Railway instances -- fine for a single-instance
  demo deployment, not for horizontal scaling without a shared store (Redis).
- If the knowledge base grows well beyond the current ~25 evidence chunks,
  wire the `pgvector` column type and an ANN index instead of the current
  Python-side cosine-similarity scan (see `docs/database-schema.md`).
