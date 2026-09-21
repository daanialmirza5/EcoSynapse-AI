# ADR 0001: Evidence-Grounded Hybrid Retrieval and Traceable Citations

## Context and Problem Statement
Ecological decision support systems must prevent ungrounded LLM hallucinations. Recommending inaccurate planting or conservation interventions in sensitive biomes can lead to ecological degradation or financial waste.

## Decision
We implement a hybrid evidence retrieval pipeline combining:
1. Lexical BM25 token overlap.
2. Dense semantic embeddings via deterministic hashing or OpenAI text-embedding.
3. 1-hop knowledge graph expansion of ecological concepts.
4. Strict chunk-level DOI citation tracing with confidence scoring.

## Consequences
- **Positive**: Every recommendation is anchored to peer-reviewed literature.
- **Positive**: Full traceability for judges, researchers, and agronomists.
- **Trade-off**: Requires pre-indexing and curated relationship taxonomy.
