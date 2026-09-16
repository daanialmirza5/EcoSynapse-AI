# Database schema

SQLAlchemy 2.0 declarative models (`apps/api/app/models/`), migrated with
Alembic (`apps/api/alembic/versions/`). Default local dev database is SQLite
(`sqlite:///./ecosynapse.db`); production should use PostgreSQL via
`DATABASE_URL=postgresql+psycopg://...`.

## Entity-relationship summary

```
UserSession 1───* Conversation 1───* Message
                       │
                       └──1───* EnvironmentalProfile 1───* EnvironmentalObservation
                                        │
                                        └──1───* Assessment 1───* Recommendation 1───* MonitoringPlan
                                                                       │
                                                                       └──*───1 Intervention

ScientificSource 1───* EvidenceChunk
ScientificSource 1───* ScientificClaim ───* (evidence_chunk_id) EvidenceChunk
KnowledgeNode 1───* KnowledgeEdge *───1 KnowledgeNode
KnowledgeEdge *───1 ScientificClaim (source_claim_id, nullable)
```

## Tables

| Table | Key columns | Notes |
|---|---|---|
| `user_sessions` | `id`, `display_name`, `created_at` | Anonymous by default; no auth in this MVP. |
| `conversations` | `id`, `session_id`, `title`, timestamps | |
| `messages` | `id`, `conversation_id`, `role`, `content`, `structured_metadata` (JSON) | `structured_metadata` carries the extracted fields, clarifying questions, and conflicts for that turn — an audit trail of what the assistant "saw" and "asked." |
| `environmental_profiles` | soil/climate/land-use scalar columns, `biodiversity_indicators` (JSON), `human_impact_indicators` (JSON), `constraints` (JSON list), `missing_fields` (JSON list), `uncertainty_metadata` (JSON) | Every numeric field is nullable — "unknown" is a first-class state, never defaulted to 0 or a guess. |
| `environmental_observations` | `profile_id`, `metric`, `value`, `unit`, `source`, `confidence` | User-recorded baselines/measurements; referenced by monitoring-plan target logic. |
| `scientific_sources` | `title`, `authors` (JSON), `organization`, `publication_year`, `doi`, `url`, `source_type`, `is_verified`, `limitations` | `is_verified=False` marks anything ingested via the API that hasn't been human-confirmed — distinct from the curated seed corpus (`is_verified=True`, checked during development, see scientific-grounding.md). |
| `evidence_chunks` | `source_id`, `text`, `section`, `embedding` (JSON float array), `chunk_metadata` | See "Vector storage" below. |
| `scientific_claims` | `claim_text`, `claim_type`, `evidence_strength`, `source_id` (nullable), `evidence_chunk_id` (nullable), `conditions` (JSON), `limitations`, `verification_status` | `claim_type` is one of `source_supported / model_derived / hypothesis / user_observation / unknown` — the core scientific-integrity taxonomy. |
| `knowledge_nodes` | `node_type`, `canonical_name` (unique), `description`, `node_metadata` (JSON) | Typed per the challenge's category list. |
| `knowledge_edges` | `source_node_id`, `target_node_id`, `relation_type`, `mechanism`, `conditions` (JSON), `source_claim_id` (nullable), `evidence_strength`, `limitations` | An edge with `source_claim_id IS NULL` and `evidence_strength='hypothesis'` is explicitly a hypothesis, not a finding. |
| `interventions` | `id` (semantic slug, e.g. `agroforestry`), `target_metrics` (JSON), `prerequisites` (JSON), `constraints` (JSON), `ecosystem_context` (JSON), `water_sensitivity`, `typical_time_horizon` | Static catalog; suitability is decided at reasoning time, not baked in. |
| `assessments` | `profile_id`, `version`, `known_facts`/`unknowns`/`variables_considered`/`reasoning_paths`/`overall_limitations` (JSON), `previous_assessment_id`, `diff_from_previous` (JSON) | One row per reasoning-engine run; `version` increments on reassessment. |
| `recommendations` | `assessment_id`, `intervention_id`, `what_to_do`, `why_it_may_work`, `impacted_metrics` (JSON), `time_horizon`, `feasibility_constraints`/`trade_offs` (JSON), `confidence_level`/`confidence_reason`, `evidence` (JSON — verified claim rows), `heuristic_score` (JSON) | |
| `monitoring_plans` | `recommendation_id`, `metric`, `baseline_requirement`, `target`, `measurement_method`, `measurement_frequency`, `expected_direction`, `success_criteria`, `uncertainty` | `target` is only ever a "compare to baseline" or "establish a baseline first" statement — see reasoning-methodology.md. |

## Vector storage: current approach and pgvector upgrade path

Embeddings are stored as a plain `JSON` column (`evidence_chunks.embedding`,
a list of floats) rather than a native `pgvector` column. Similarity search
(`app/retrieval/hybrid.py`) computes cosine similarity in Python over all
chunks. This is a deliberate simplicity/portability trade-off:

- It works identically on SQLite (zero external services, used by default)
  and PostgreSQL.
- At the demo corpus's scale (~25 chunks), a full Python scan is effectively
  instant; there is no measurable benefit to an ANN index yet.
- `docker-compose.yml` uses the `pgvector/pgvector:pg16` Postgres image so
  the extension is available in that environment, but the schema does not
  yet use the `vector` column type or an ANN index.

**To upgrade to pgvector in production:** add the `pgvector` Python package
(already an optional dependency, `pip install -e ".[postgres]"`), change
`evidence_chunks.embedding` to `pgvector.sqlalchemy.Vector(N)` in a new
Alembic migration (Postgres-only — guard the migration or keep a
JSON-column SQLite dev path), and replace the Python cosine-similarity loop
in `hybrid.py` with an `ORDER BY embedding <-> :query_vector LIMIT k` query.
This is intentionally not done in this MVP so the implementation status is
accurately represented as "supported upgrade path," not "already wired."

## Migrations

```bash
cd apps/api
alembic revision --autogenerate -m "description"
alembic upgrade head
```

The initial migration (`alembic/versions/0b8199e6eacd_initial_schema.py`) was
autogenerated from the models above and applied against both a fresh SQLite
file (see Local setup in the README) during development.
