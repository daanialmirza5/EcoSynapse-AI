# Cross-cutting tests

- `evaluation_cases/*.json` — hand-curated scenario definitions (profile +
  expected structural properties) consumed by
  `apps/api/tests/test_evaluation_benchmark.py`. See
  [../docs/evaluation.md](../docs/evaluation.md) for what this benchmark does
  and does not prove.
- `fixtures/` — reserved for shared test fixtures if/when backend and
  frontend tests need to share sample data beyond the evaluation cases above.
  Currently empty: backend tests use `apps/api/tests/conftest.py` (an
  isolated temp SQLite DB, seeded once per test session) and inline fixtures;
  frontend tests use `apps/web/src/test/testUtils.tsx`.

Actual test suites live next to the code they test:
`apps/api/tests/` (pytest, 26 tests) and `apps/web/src/**/*.test.tsx`
(vitest, 12 tests). Run them via `pytest -q` / `npm test` respectively, or
see the root `Makefile`'s `test` target.
