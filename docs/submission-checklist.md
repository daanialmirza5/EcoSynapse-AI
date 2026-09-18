# Submission checklist

- [ ] Fill in the GitHub repository URL at the top of `README.md`.
- [ ] Fill in a live demo URL in `README.md` **only if actually deployed and
      smoke-tested** (see `docs/deployment.md`) — otherwise leave the current
      "not deployed" note in place.
- [x] README covers: architecture, database/schema, local setup (Windows +
      Unix), environment variables, running tests, Docker, CI/CD, known
      limitations.
- [x] No API keys or secrets committed (`.env.example` only; `.gitignore`
      excludes `.env`, `*.db`).
- [x] No fabricated scientific citations — all 12 seed sources verified via
      live search during development (`docs/scientific-grounding.md`).
- [x] No fabricated benchmark/test results — `docs/evaluation.md` states
      exactly what was run and its limitations.
- [x] Backend tests pass: `cd apps/api && pytest -q` (45 passed at last run,
      against both SQLite and real Postgres — see `docs/evaluation-report.md`).
- [x] Frontend tests pass: `cd apps/web && npm test` (13 passed at last run).
- [x] CI workflow present (`.github/workflows/ci.yml`): lint + knowledge-
      corpus validation + typecheck + test (SQLite AND Postgres) + build for
      both apps.
- [x] Docker Compose brings up db + api + web (`docker compose up --build`)
      — verified end-to-end including a full assessment run against the
      containerized stack (`docs/evaluation-report.md`).
- [x] `docs/hackathon-audit.md` maps every challenge requirement to its
      implementation, demonstration, and test.
- [x] `docs/engineering-audit.md` documents a full audit pass, including two
      real bugs found via Docker/Postgres verification and their fixes.
- [x] `docs/team-handoff.md`, `docs/competition-readiness.md`,
      `docs/judge-story.md`, `CONTRIBUTING.md` complete.
- [ ] Live deployment (Railway backend + Vercel frontend): prepared
      (`docs/deployment.md` has exact steps and all required code changes —
      configurable API base URL, DB URL normalization, SPA rewrite — are
      committed), but not yet executed; requires the account owner to run
      `railway login` / `vercel login` themselves. Update this line and the
      README's top banner once actually deployed and smoke-tested.
- [ ] Before presenting live: run `git log --oneline` and confirm the working
      tree is clean and pushed; run both test suites one final time.
- [ ] Remove or gitignore any local scratch artifacts (screenshots,
      `*.db` files, `.venv/`, `node_modules/`) before pushing — already
      covered by `.gitignore`, verify with `git status`.
