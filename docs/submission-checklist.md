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
- [x] Backend tests pass: `cd apps/api && pytest -q` (26 passed at last run).
- [x] Frontend tests pass: `cd apps/web && npm test` (12 passed at last run).
- [x] CI workflow present (`.github/workflows/ci.yml`): lint + typecheck +
      test + build for both apps.
- [x] Docker Compose brings up db + api + web (`docker compose up --build`).
- [x] `docs/hackathon-audit.md` maps every challenge requirement to its
      implementation, demonstration, and test.
- [ ] Before presenting live: run `git log --oneline` and confirm the working
      tree is clean and pushed; run both test suites one final time.
- [ ] Remove or gitignore any local scratch artifacts (screenshots,
      `*.db` files, `.venv/`, `node_modules/`) before pushing — already
      covered by `.gitignore`, verify with `git status`.
