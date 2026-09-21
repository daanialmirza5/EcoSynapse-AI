# ADR 0002: Explicit Ecological Knowledge Graph Reasoning

## Context and Problem Statement
Ecological variables (e.g., soil organic carbon, soil moisture, biodiversity, rainfall) interact through complex non-linear causal webs. Black-box LLMs frequently miss secondary ecological risks (e.g., high water demand during dry establishment phases).

## Decision
We decouple knowledge graph relationships from generative LLM reasoning:
1. Directed causal relationships (`increases`, `decreases`, `buffers`, `modulates`) are persisted in a relational graph structure.
2. Invariant constraints (water scarcity, soil pH limits, budget thresholds) are evaluated deterministically.
3. Trade-offs and uncertainties are explicitly surfaced in the output payload.

## Consequences
- **Positive**: Complete auditability of ecological trade-offs and constraint conflicts.
- **Positive**: Deterministic testability in automated CI suites.
- **Trade-off**: Requires explicit schema modeling for ecological entities and edges.
