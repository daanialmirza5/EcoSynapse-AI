# Knowledge engineering workspace

This directory holds knowledge-engineering *artifacts and notes* that inform
the runtime knowledge system. The actual runtime code that ingests,
retrieves, and traverses the knowledge base lives in `apps/api/app/knowledge/`,
`apps/api/app/retrieval/`, and `apps/api/app/reasoning/` — see
[../docs/architecture.md](../docs/architecture.md) for how they fit together.

- `ingestion/` — notes on how the seed corpus (`../data/seed/`) was compiled
  and verified. See [../docs/scientific-grounding.md](../docs/scientific-grounding.md)
  for the full methodology (every source was verified via live web search
  during development, not recalled from memory).
- `normalization/` — unit/vocabulary normalization is currently handled
  directly in `apps/api/app/knowledge/vocabulary.py` (the shared
  keyword→knowledge-graph-node map used by both retrieval and conversation
  extraction) rather than as a separate offline step, since the corpus is
  small enough that a single shared module is simpler and less error-prone
  than a multi-stage normalization pipeline.
- `graph/` — the knowledge graph's node/edge *data* lives in
  `../data/seed/relationships.json`; the graph-building/query code is
  `apps/api/app/knowledge/graph.py` (builds a NetworkX `MultiDiGraph` from
  the database on each call).
- `retrieval/` — the hybrid retrieval implementation is
  `apps/api/app/retrieval/hybrid.py`; this folder is a placeholder for future
  retrieval-tuning notes (e.g. reranking weight experiments).
- `evaluation/` — the runnable evaluation benchmark lives at
  `../tests/evaluation_cases/*.json` + `apps/api/tests/test_evaluation_benchmark.py`.
  See [../docs/evaluation.md](../docs/evaluation.md) for what it does and does
  not measure.

This split (data/engineering-notes here, executable code in `apps/api`) keeps
a clear separation between "what the knowledge is and how it was curated"
and "what the running system does with it," per the project's structure
guidelines.
