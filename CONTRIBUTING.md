# Contributing

## Branch strategy

- `main` is always deployable (CI must pass before merging).
- Work in a feature branch (`feature/<short-description>` or
  `fix/<short-description>`), open a PR into `main`.
- No direct pushes to `main` for anything beyond a trivial doc typo.

## Commit conventions

- One logical change per commit where practical; avoid a pile of "wip" commits.
- Write the *why*, not just the *what*, in the body when the change isn't
  self-explanatory from the diff -- see this repo's own commit history for
  the expected level of detail, especially for bug fixes (what broke, how it
  was found, why the fix is correct).
- Never commit `.env`, `*.db`, `.venv/`, `node_modules/`, or anything else
  covered by `.gitignore`. Run `git status` before `git add -A` and look for
  anything that looks out of place.

## Testing requirements for a PR

- Backend changes: `cd apps/api && pytest -q` must pass. If you touch a
  model with a bounded `String(N)` column, or add one, consider whether it
  should be `Text` instead (see `docs/engineering-audit.md` #2 for why this
  matters) -- and if you're not sure, test against real Postgres, not just
  SQLite (see `docs/team-handoff.md`'s "Database" section for the exact
  commands).
- Frontend changes: `cd apps/web && npm test && npx tsc --noEmit && npm run
  lint` must all pass.
- If you touch `data/seed/*.json`: run `python scripts/validate_knowledge.py`.
- New backend behavior needs a test. "It worked when I tried it manually" is
  not sufficient for anything beyond a one-line copy change.
- If you touch the reasoning engine, retrieval, or knowledge graph, run
  `pytest apps/api/tests/test_evaluation_benchmark.py -v` and check the
  scenario cases still pass.

## Environment setup

See `README.md` §11 (Windows/macOS/Linux) or `docs/team-handoff.md`.

## Code style

- Backend: `ruff check app tests` must pass (run from `apps/api`). Follow
  the existing pattern of a short module-level docstring explaining *why*
  a file exists, not just what it contains.
- Frontend: ESLint + TypeScript strict mode. Prefer the existing shared UI
  primitives (`apps/web/src/components/ui.tsx`) over ad-hoc styling.
- Comments: only where the *why* isn't obvious from the code (a constraint,
  a workaround, a non-obvious invariant). Don't restate what the code does.

## Scientific evidence rules (non-negotiable)

This project's core credibility rests on never fabricating a citation,
DOI, dataset, or numeric estimate. Before adding or editing anything in
`data/seed/`:

- Verify every source yourself (live search, not memory) before adding it.
- Every claim must be labeled with the correct `claim_type`
  (`source_supported` / `model_derived` / `hypothesis` / `user_observation`
  / `unknown`) -- see `docs/scientific-grounding.md` for the definitions and
  worked examples of getting this right (including cases where the honest
  answer is "evidence is insufficient").
- Never state a numeric claim unless the cited source states that exact
  figure under compatible conditions.
- Run `python scripts/validate_knowledge.py` before committing corpus changes.

## Security rules

- Never commit secrets. `.env.example` / `apps/web/.env.example` contain
  placeholders only.
- All database access goes through the SQLAlchemy ORM -- no raw SQL string
  interpolation.
- New endpoints accepting user input need Pydantic validation, not manual
  parsing.
- If you add a new external call (LLM provider, embedding provider,
  anything network-facing), it must degrade gracefully when unavailable --
  see `app/ai/llm.py` and `app/ai/embeddings.py` for the existing pattern.
