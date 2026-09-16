# Architecture

## System diagram

```
                                   ┌─────────────────────────────┐
                                   │   React + TS + Vite + TW    │
                                   │  (apps/web)                  │
                                   │  Workspace / Evidence /      │
                                   │  Graph / Monitoring / etc.   │
                                   └───────────────┬──────────────┘
                                                    │ HTTP (/api/v1, /health)
                                                    ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                          FastAPI app (apps/api)                            │
│                                                                             │
│  api/v1/*.py  ─── routes, thin, delegate to services                       │
│      │                                                                     │
│      ├── conversations/  extraction.py (regex NLU) → clarify.py            │
│      │                    (missing-field detection + questions)            │
│      │                    → service.py (turn orchestration)                │
│      │                                                                     │
│      ├── retrieval/hybrid.py  parse → graph-expand → semantic+lexical      │
│      │                         search → merge/rerank → trace               │
│      │                                                                     │
│      ├── knowledge/  graph.py (NetworkX from DB) · seed.py · ingestion.py  │
│      │               · vocabulary.py (shared keyword→node map)             │
│      │                                                                     │
│      ├── reasoning/engine.py  10-step pipeline (see reasoning-methodology) │
│      │   reasoning/constraints.py  concern detection + constraint checks   │
│      │                              + prototype heuristic scoring          │
│      │                                                                     │
│      ├── evidence/verification.py  claim → status (supported/partial/      │
│      │                              insufficient/unverified)               │
│      │                                                                     │
│      ├── monitoring/plans.py  metric → measurement method/frequency/       │
│      │                         target (never fabricated)                   │
│      │                                                                     │
│      └── ai/  embeddings.py (hashing | openai) · llm.py (mock | openai,    │
│               phrasing-only, never fact-generating)                        │
│                                                                             │
│  db/  SQLAlchemy 2.0 session + declarative base                            │
│  models/  ORM entities (see database-schema.md)                           │
│  schemas/  Pydantic v2 request/response contracts                         │
└───────────────────────────────────────┬───────────────────────────────────┘
                                         ▼
                          SQLite (dev, default) / PostgreSQL (prod)
```

## Why this shape

**The reasoning engine is the product, not the LLM.** The challenge explicitly
rejects "generic LLM-only solutions" and "shallow or obvious recommendations."
The architecture makes that structural rather than a prompt-engineering
promise: `app/reasoning/engine.py` is plain Python control flow over database
rows (claims, edges, interventions). An LLM is never in the path that
produces a number, a citation, or a scientific claim. It is only ever called
(and only when explicitly configured with an API key) to rephrase an
already-fully-determined template string for tone — see
`app/ai/llm.py`'s docstring and `app/conversations/service.py::compose_assistant_reply`.

**Retrieval is hybrid and inspectable, not a black box.** `app/retrieval/hybrid.py`
exposes every intermediate step (matched concepts, graph-expanded terms,
semantic candidate count, lexical candidate count, per-result match reasons)
through `POST /api/v1/retrieval/inspect`, satisfying the "retrieval trace"
requirement literally rather than describing it in a README only.

**The knowledge graph is rebuilt from the database on each call**, not
cached in a separate graph store. The demo corpus (23 nodes, 22 edges) makes
this instant, and it eliminates an entire class of staleness bugs where the
graph and the database disagree after an ingestion or edit. If the corpus
grows substantially, the natural next step is a cached/invalidated graph or
a dedicated graph database — noted as a scaling consideration, not implemented
here since it isn't needed at this scale.

**Vector storage is a portable JSON column**, not a wired pgvector index (see
[database-schema.md](database-schema.md) for the honest limitation). This was
a deliberate simplicity trade-off: it works identically on SQLite (zero
external services) and Postgres, and Python-side cosine similarity over ~25
chunks is effectively instant. It is not what you'd choose at 100k+ chunks.

## Request flow: one assessment, end to end

1. `POST /api/v1/conversations` → new `Conversation` row.
2. `POST /api/v1/conversations/{id}/messages` with free text and/or
   `structured_input` → `conversations/service.py::handle_user_turn`:
   regex-extract fields → merge into `EnvironmentalProfile` (flagging
   conflicts) → compute completeness → generate up to 3 clarifying questions
   → compose and store the assistant's reply.
3. Once ≥3 variables are known, `POST /api/v1/assessments` →
   `reasoning/engine.py::run_assessment`:
   - Build known/unknown state from the profile.
   - `constraints.py::detect_concerns` — threshold rules over the profile.
   - Map concerns → candidate `Intervention` rows via
     `CONCERN_TO_INTERVENTIONS`.
   - For each candidate: find its direct knowledge-graph edges, resolve each
     edge's linked `ScientificClaim`/`ScientificSource`/`EvidenceChunk`,
     verify the claim (`evidence/verification.py`), check constraints
     (water sensitivity, user-stated limits, ecosystem-context match),
     compute the prototype heuristic score, and generate a monitoring-plan
     entry per impacted metric.
   - Persist `Assessment` + `Recommendation` + `MonitoringPlan` rows.
4. Frontend renders the result via `apps/web/src/features/workspace/*` and
   `pages/*` — every displayed number/claim/citation comes from this response,
   never invented client-side.
5. `PATCH /api/v1/profiles/{id}` + `POST /api/v1/assessments/{id}/reassess`
   re-runs the pipeline and computes a diff against the previous run.
