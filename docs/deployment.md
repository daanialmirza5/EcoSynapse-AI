# Deployment

## Current status

**Not deployed to a public URL.** This project has been run and verified:
- Locally via `uvicorn` + `vite dev` (see README §11).
- Via `docker compose up --build` (Postgres + API + nginx-served frontend).

Do not represent this as having a live demo URL unless one has actually been
deployed and smoke-tested after these docs were written — check `README.md`'s
top section for whether that has since been filled in.

## Docker Compose (recommended path if you deploy this)

```bash
docker compose up --build
```

- `db`: `pgvector/pgvector:pg16` — Postgres 16 with the pgvector extension
  available (not yet used by queries — see database-schema.md).
- `api`: builds `apps/api/Dockerfile`, runs `alembic upgrade head` then
  `uvicorn` on port 8000. Seeding happens automatically on first boot.
- `web`: builds `apps/web/Dockerfile` (multi-stage: `npm run build` → static
  files served by nginx on port 80, mapped to host `8080`), with `nginx.conf`
  proxying `/api` and `/health` to the `api` service.

## Environment variables for production

Set real values for (see `.env.example`):
- `DATABASE_URL` → your managed Postgres instance
- `APP_SECRET` → a real secret, not the dev placeholder
- `CORS_ORIGINS` → your actual frontend origin(s)
- `LLM_PROVIDER=openai` + `OPENAI_API_KEY` → optional, phrasing-only
- `EMBEDDING_PROVIDER=openai` + `OPENAI_API_KEY` → optional, better retrieval

## What a real deployment would still need

- A managed Postgres instance (or continue with SQLite for a low-traffic demo
  deployment — the app supports both).
- HTTPS termination (a reverse proxy or platform-level TLS; nginx config here
  is HTTP-only for simplicity).
- Authentication, if used by more than one trusted party (none exists in this
  MVP — see README limitations).
- Rate limiting (documented as a limitation, not implemented — see
  Security section of the README/hackathon-audit).
- If scaling the knowledge base beyond a few hundred sources: wire the
  pgvector column type and an ANN index (see database-schema.md's upgrade
  path) instead of the current Python-side cosine similarity scan.
