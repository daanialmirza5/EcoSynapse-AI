# EcoSynapse AI

**Evidence-grounded ecological intelligence and intervention planning.**

Built for the Darukaa.Earth AI Biodiversity Intelligence Chatbot Challenge.

> Repository: (add your GitHub URL here before submitting)
> Live demo: not deployed — run locally following the steps below (see [Known limitations](#known-limitations))

---

## 1. Product overview

EcoSynapse AI is a decision-support system, not a chatbot with environmental
words added to it. A user describes a piece of land, its environmental
conditions, or a biodiversity concern — in natural language, structured JSON,
or both. The system:

1. Extracts environmental variables with **deterministic, regex-based
   extraction** (never an LLM guessing numbers).
2. Detects missing/conflicting information and asks a small number of
   high-value clarifying questions.
3. Builds a structured `EnvironmentalProfile`.
4. Retrieves scientific evidence via **hybrid retrieval** (semantic + lexical
   + knowledge-graph term expansion) over a curated, verified source corpus.
5. Traverses a typed **ecological knowledge graph** to find relevant
   mechanisms linking the profile's variables to candidate interventions.
6. Runs those candidates through a **constraint engine** (water sensitivity,
   user-stated limits, ecosystem-context mismatch).
7. **Verifies every claim** against its source excerpt (including checking
   that numeric figures in a claim actually appear in the retrieved text).
8. Produces structured recommendations with mechanism, impacted metrics,
   time horizon, confidence, trade-offs, and a claim-level evidence table.
9. Generates a **monitoring plan** per impacted metric — never a fabricated
   numeric target.
10. Supports **reassessment**: change the profile, re-run, see exactly what
    changed and why.

## 2. Challenge alignment

| Requirement | Where it's implemented |
|---|---|
| Structured, retrievable knowledge base | `apps/api/app/models/evidence.py`, `app/models/knowledge.py`; seeded from `data/seed/*.json` |
| Understands ecosystem/land/climate queries | `app/conversations/extraction.py`, `app/retrieval/hybrid.py` |
| Non-obvious, evidence-backed recommendations | `app/reasoning/engine.py` |
| RAG / embeddings / knowledge graph | `app/ai/embeddings.py`, `app/retrieval/hybrid.py`, `app/knowledge/graph.py` |
| Clarifying questions, multi-turn memory | `app/conversations/clarify.py`, `app/conversations/service.py` |
| Recommendation fields (what/why/metrics/reference) | `app/schemas/assessment.py` (`RecommendationOut`) |
| Multi-metric reasoning (soil↔biodiversity, water↔survival, land use↔fragmentation) | `data/seed/relationships.json` edges `e1-e8`; `app/reasoning/engine.py` |
| Structured + natural-language input | `POST /conversations/{id}/messages` accepts both `content` and `structured_input` |
| Recommendation includes metrics, time horizon, confidence | `RecommendationOut` schema, enforced by tests |
| No fabricated citations | `data/seed/sources.json` — all 12 sources verified via live search during development (see [docs/scientific-grounding.md](docs/scientific-grounding.md)) |

See [docs/hackathon-audit.md](docs/hackathon-audit.md) for a line-by-line audit against every requirement in the brief, including test references and known limitations.

## 3. Architecture

```
Browser (React/Vite)  ── /api/v1, /health ──>  FastAPI (apps/api)
                                                    │
                        ┌───────────────────────────┼───────────────────────────┐
                        ▼                           ▼                           ▼
                 Conversation engine        Hybrid retrieval             Reasoning engine
                 (rule-based extraction,    (embeddings + lexical +      (concern detection →
                  clarifying questions)      graph expansion)             candidates → constraints →
                        │                           │                     verification → monitoring)
                        └─────────────┬─────────────┴─────────────┬──────────────┘
                                      ▼                           ▼
                              SQLAlchemy models          NetworkX knowledge graph
                              (SQLite dev / Postgres)    (built from KnowledgeNode/Edge tables)
```

Full diagram and component responsibilities: [docs/architecture.md](docs/architecture.md).

**Why this design, not "call an LLM and hope"**: the reasoning engine, retrieval
pipeline, constraint checks, and evidence verification are all deterministic
Python — traceable, testable, and reproducible. An LLM provider is
*optional* and, when configured, is used **only** to rephrase already-correct
template text for tone; it never originates a scientific claim, citation, or
number. This is what makes the "no fabricated citations" and "no generic
LLM-only solution" requirements structurally true rather than aspirational.

## 4. Database schema

SQLAlchemy 2.0 models, migrated with Alembic. Full entity list, relationships,
and design rationale: [docs/database-schema.md](docs/database-schema.md).

Core entities: `UserSession`, `Conversation`, `Message`, `EnvironmentalProfile`,
`EnvironmentalObservation`, `ScientificSource`, `EvidenceChunk`,
`ScientificClaim`, `KnowledgeNode`, `KnowledgeEdge`, `Intervention`,
`Assessment`, `Recommendation`, `MonitoringPlan`.

## 5. Knowledge ingestion

- Seed corpus: 12 real, verified sources (FAO, peer-reviewed journals with
  DOIs) covering every mandatory knowledge area, loaded by
  `app/knowledge/seed.py` from `data/seed/sources.json` +
  `data/seed/relationships.json` + `data/seed/interventions.json`.
- User-supplied ingestion: `POST /api/v1/knowledge/ingest` chunks text,
  embeds each chunk, and stores it as a **user-uploaded, unverified** source
  (distinct from the curated seed corpus) until a human confirms it.
- See [docs/scientific-grounding.md](docs/scientific-grounding.md) for exactly
  how each seed source was verified and what its limitations are.

## 6. RAG / hybrid retrieval pipeline

`app/retrieval/hybrid.py` implements: parse query → match known
entities/metrics → expand one hop via the knowledge graph → semantic search
(cosine similarity over chunk embeddings) → lexical keyword search → merge +
weighted rerank → return sources with excerpts and an explicit reason each
result matched. Inspect it live at `POST /api/v1/retrieval/inspect` or in the
**Evidence Explorer** page.

Embeddings are pluggable (`app/ai/embeddings.py`): the default
`HashingEmbeddingProvider` is a deterministic, offline bag-of-words hashing
scheme (an md5-based stable hash, not Python's randomized `hash()|`) — zero
cost, zero API key, fully reproducible. An OpenAI-compatible provider is
available via `EMBEDDING_PROVIDER=openai`.

## 7. Knowledge graph

`app/knowledge/graph.py` builds a typed `networkx.MultiDiGraph` from
`KnowledgeNode`/`KnowledgeEdge` rows on every request (the demo corpus is
small enough that this is instant and avoids stale-cache bugs). Node types:
`soil_property`, `climate_factor`, `land_use_type`, `habitat_characteristic`,
`biodiversity_indicator`, `human_pressure`, `ecological_mechanism`,
`intervention`, `constraint`. Every edge carries an `evidence_strength`
(`strong`/`moderate`/`weak`/`hypothesis`) and, where applicable, a
`source_claim_id` — graph connectivity is never treated as proof of
causation. Explore it in the **Knowledge Graph** page or `GET /api/v1/knowledge/graph`.

## 8. Reasoning engine

`app/reasoning/engine.py` — the 10-step pipeline described in
[docs/reasoning-methodology.md](docs/reasoning-methodology.md). Requires at
least 3 known environmental variables before generating recommendations;
otherwise it returns an assessment stating exactly that limitation instead of
forcing a shallow answer.

## 9. Scientific integrity rules

Every claim is classified as `source_supported`, `model_derived`,
`hypothesis`, `user_observation`, or `unknown`. See
[docs/scientific-grounding.md](docs/scientific-grounding.md) for the full
policy and the seed corpus's verification notes — including an honest example
(agroforestry) where the cited meta-analysis explicitly found **no
unequivocal biodiversity effect**, and the system reports that finding rather
than a rosier summary.

## 10. API endpoints

Full reference with request/response examples: [docs/api-reference.md](docs/api-reference.md).
Interactive OpenAPI docs at `http://localhost:8000/docs` once the backend is running.

```
GET  /health
GET  /health/ready
POST /api/v1/conversations
GET  /api/v1/conversations
GET  /api/v1/conversations/{id}
POST /api/v1/conversations/{id}/messages
POST /api/v1/profiles
GET  /api/v1/profiles/{id}
PATCH /api/v1/profiles/{id}
POST /api/v1/profiles/{id}/observations
POST /api/v1/assessments
GET  /api/v1/assessments/{id}
POST /api/v1/assessments/{id}/reassess
GET  /api/v1/assessments/{id}/export
POST /api/v1/knowledge/ingest
GET  /api/v1/knowledge/sources
GET  /api/v1/knowledge/sources/{id}
GET  /api/v1/knowledge/graph
POST /api/v1/retrieval/inspect
GET  /api/v1/recommendations/{id}
GET  /api/v1/recommendations/{id}/evidence
GET  /api/v1/recommendations/{id}/monitoring
```

## 11. Local setup

### Prerequisites
- Python 3.11+ (developed/tested on 3.14 locally, CI uses 3.12)
- Node.js 20+
- Git

No database server, no API keys, and no internet access are required to run
the full demo — SQLite + the deterministic providers are the defaults.

### Windows (PowerShell) — the primary path for this repo

```powershell
# --- Backend ---
cd apps\api
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
# Seed data loads automatically on first startup (idempotent).
```

In a second terminal:

```powershell
# --- Frontend ---
cd apps\web
npm install
npm run dev
# Open http://localhost:5173
```

### macOS / Linux

```bash
cd apps/api
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

```bash
cd apps/web
npm install
npm run dev
```

Or use the provided `Makefile` targets (`make api-install api-migrate api-dev`, `make web-install web-dev`) on Unix-like shells.

## 12. Environment variables

See [.env.example](.env.example) for the full list. Nothing is required to
run the demo; every variable has a safe, offline default.

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./ecosynapse.db` | Swap for a `postgresql+psycopg://...` URL in production |
| `LLM_PROVIDER` | `mock` | `mock` = deterministic offline phrasing; `openai` uses `OPENAI_API_KEY` for phrasing only |
| `EMBEDDING_PROVIDER` | `hashing` | `hashing` = deterministic offline embeddings; `openai` for higher quality |
| `CORS_ORIGINS` | `http://localhost:5173,...` | Comma-separated allowed origins |
| `APP_SECRET` | dev placeholder | Set a real secret in production |
| `RATE_LIMIT_PER_MINUTE` | `120` | Basic in-memory per-IP rate limit; `0` disables it (see `app/main.py::InMemoryRateLimiter`) |
| `SEED_DATA_DIR` | unset (auto-detected) | Override where `data/seed/*.json` lives; set automatically in the Docker image |
| `VITE_API_BASE_URL` (frontend) | unset (same-origin) | Set for a split deployment (e.g. Vercel frontend + Railway backend) — see [apps/web/.env.example](apps/web/.env.example) |

## 13. Database setup

Local dev uses SQLite by default — `alembic upgrade head` creates
`ecosynapse.db` with no further setup. For Postgres (recommended for
production, and required for the `pgvector` optional extra):

```bash
DATABASE_URL=postgresql+psycopg://ecosynapse:ecosynapse@localhost:5432/ecosynapse alembic upgrade head
```

See [docs/database-schema.md](docs/database-schema.md) for the pgvector
migration path and its current limitation.

## 14. Seed data setup

Seeding runs automatically on backend startup (see `app/main.py` lifespan)
and is idempotent — it skips if sources already exist. To force a reseed:

```powershell
.\.venv\Scripts\python.exe -c "from app.db.session import SessionLocal; from app.knowledge.seed import seed_all; db = SessionLocal(); print(seed_all(db, force=True)); db.close()"
```

## 15. Running frontend / backend

Covered above in [Local setup](#11-local-setup). Frontend dev server proxies
`/api` and `/health` to `http://127.0.0.1:8000` (see `apps/web/vite.config.ts`).

## 16. Running tests

```powershell
# Backend: 61 tests covering extraction, clarifying questions, the full
# reasoning pipeline (including the challenge demo scenario), evidence
# verification, retrieval, the knowledge graph, error handling, a
# regression test for a real Postgres-only bug, and a 10-test adversarial
# ("red-team") suite targeting hallucination/scientific-safety failure modes
# (see docs/engineering-audit.md and docs/darukaa-evaluation.md).
cd apps\api
.\.venv\Scripts\python.exe -m pytest -q

# Frontend: 18 component tests covering loading/empty/error states, evidence
# rendering, the "never fabricate a numeric target" invariant, the
# conflict-detection banner, and the "why this recommendation?" drill-down.
cd apps\web
npm test
```

Both suites currently pass in full against SQLite; the backend suite has
also been verified against real PostgreSQL (see
[docs/evaluation-report.md](docs/evaluation-report.md) for exact commands
and results, and [docs/evaluation.md](docs/evaluation.md) for the benchmark
methodology and its caveats).

## 17. Docker instructions

```bash
docker compose up --build
```

This starts Postgres (`pgvector/pgvector:pg16` image), the API (migrating and
seeding on startup), and the frontend (built and served via nginx, which
proxies `/api` and `/health` to the API container). Frontend at
`http://localhost:8080`, API at `http://localhost:8000`.

## 18. CI/CD

`.github/workflows/ci.yml` runs on every push/PR: backend lint (`ruff`) +
knowledge-corpus validation + migration check + `pytest` against SQLite,
**plus a second job running the full backend suite against a real
PostgreSQL service container** (added after a Postgres-only bug was found
during manual Docker verification — SQLite doesn't enforce `VARCHAR`
lengths, Postgres does; see
[docs/engineering-audit.md](docs/engineering-audit.md)); frontend lint +
`tsc --noEmit` + `vitest` + production build. See
[docs/deployment.md](docs/deployment.md) for the current deployment status
and the exact Railway/Vercel deployment steps.

## 19. Demo credentials

None required — the app has no authentication layer in this MVP (documented
as a known limitation below). Anonymous sessions/conversations are created
automatically.

## 20. Known limitations

- **No live deployment.** This has been run and verified locally and via
  Docker Compose, but is not deployed to a public URL. Do not claim otherwise.
- **Small seed corpus.** 12 verified sources — enough to demonstrate a real,
  working hybrid retrieval + graph + reasoning pipeline for the mandated
  knowledge areas, not a comprehensive literature review.
- **Hashing embeddings by default.** Deterministic and offline, but a
  bag-of-words hash, not a trained semantic embedding model. An OpenAI-compatible
  provider can be swapped in via env vars for higher retrieval quality.
- **pgvector not actively wired.** Embeddings are stored as a portable JSON
  column with Python-side cosine similarity (works identically on SQLite and
  Postgres). The `pgvector/pgvector` Postgres image is used in
  `docker-compose.yml` so the upgrade path exists, but the vector column type
  and index are not yet used in queries. See [docs/database-schema.md](docs/database-schema.md).
- **Prototype heuristic ranking.** The recommendation ranking score is an
  explicitly labeled, transparent weighted heuristic — not a validated or
  peer-reviewed decision model. The UI and API both surface this label.
- **No authentication.** Anonymous sessions only; not intended for multi-user
  production deployment as-is.
- **Rule-based NLU.** Environmental-fact extraction from free text is
  regex/keyword-based by design (for scientific-integrity/testability
  reasons stated above), so it will miss phrasings outside its patterns
  rather than guessing.
- **One moderate frontend dependency advisory deferred.** `npm audit` flags
  an open-redirect issue in `react-router`/`react-router-dom`; the fix
  requires a major-version upgrade (6.x → 7.x) that would need regression
  testing across all 10 frontend routes. Deferred rather than force-upgraded
  under time pressure — see [docs/evaluation-report.md](docs/evaluation-report.md).
- **Basic rate limiting only.** In-memory, single-process, resets on
  restart — adequate for a single-instance demo deployment, not for a
  horizontally-scaled production deployment without a shared store (Redis).

## 21. Project structure

```
daruka/
  apps/api/     FastAPI backend (see app/{core,api,models,schemas,services,
                repositories,db,ai,retrieval,reasoning,knowledge,evidence,
                monitoring,conversations}, alembic/, tests/)
  apps/web/     React + TypeScript + Vite + Tailwind frontend
  data/         Seed corpus (sources, relationships, interventions), sample profiles
  knowledge/    Standalone knowledge-engineering workspace (ingestion notes,
                evaluation harness) — see knowledge/README.md
  docs/         Architecture, schema, API reference, scientific grounding,
                reasoning methodology, evaluation, deployment, demo script,
                submission checklist, hackathon audit
  tests/        Cross-cutting fixtures/evaluation cases (see tests/README.md)
  scripts/      Standalone tooling (validate_knowledge.py)
  .github/workflows/ci.yml
  docker-compose.yml, apps/api/Dockerfile, apps/web/Dockerfile
```

## 22. Documentation index

- [docs/architecture.md](docs/architecture.md)
- [docs/database-schema.md](docs/database-schema.md)
- [docs/api-reference.md](docs/api-reference.md)
- [docs/scientific-grounding.md](docs/scientific-grounding.md)
- [docs/reasoning-methodology.md](docs/reasoning-methodology.md)
- [docs/evaluation.md](docs/evaluation.md) — evaluation methodology
- [docs/evaluation-report.md](docs/evaluation-report.md) — actual measured results
- [docs/engineering-audit.md](docs/engineering-audit.md) — findings from a full audit + Docker/Postgres verification pass
- [docs/deployment.md](docs/deployment.md)
- [docs/demo-script.md](docs/demo-script.md) — 60s / 3min / 5min scripts
- [docs/submission-checklist.md](docs/submission-checklist.md)
- [docs/hackathon-audit.md](docs/hackathon-audit.md)
- [docs/judge-story.md](docs/judge-story.md) — the narrative case for judges
- [docs/team-handoff.md](docs/team-handoff.md) — onboarding for a new teammate
- [docs/competition-readiness.md](docs/competition-readiness.md)
- [docs/darukaa-requirement-matrix.md](docs/darukaa-requirement-matrix.md) — every challenge requirement mapped to implementation/test/status
- [docs/darukaa-evaluation.md](docs/darukaa-evaluation.md) — the challenge's own rubric weighting mapped to what/how/test
- [docs/knowledge-coverage-matrix.md](docs/knowledge-coverage-matrix.md) — every mandatory metric traced through sources → graph → retrieval → reasoning → monitoring
- [CONTRIBUTING.md](CONTRIBUTING.md)
