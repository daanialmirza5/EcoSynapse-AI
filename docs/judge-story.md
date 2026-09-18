# The story, for a judge

## The problem

Ask a generic LLM chatbot "biodiversity is declining on my land, what should
I do?" and it will confidently answer in one turn: "plant more trees, reduce
pesticide use, restore habitat." No clarifying questions. No evidence. No
acknowledgment that agroforestry's biodiversity benefit is, per the actual
peer-reviewed literature, inconsistent and context-dependent rather than
guaranteed. No monitoring plan beyond vague encouragement. That's the
"generic LLM-only solution" and "shallow or obvious recommendations" the
challenge brief explicitly rejects -- and it's the default behavior of
almost every chatbot built on top of a raw LLM call.

## Why existing chatbot approaches are insufficient

The failure isn't that LLMs don't know ecology -- they know quite a lot of
plausible-sounding ecology. The failure is that "plausible-sounding" and
"verified" are different properties, and a raw LLM call conflates them. Ask
it for a citation and it may invent a DOI. Ask it for a numeric improvement
estimate and it may invent a percentage that sounds right. This is precisely
what the challenge's scientific-integrity section warns against, and it's
also just bad decision support: a landholder acting on a fabricated 20%
biodiversity improvement claim is worse off than one told "evidence is
insufficient to support a reliable estimate here."

## The EcoSynapse architecture

The core design decision: **separate "understanding the user" from
"generating scientific content."** An LLM (optional, off by default) helps
with the former -- rephrasing an already-fully-determined template sentence
for tone. It never does the latter. Every scientific claim, every citation,
every numeric figure, every monitoring target traces back to one of exactly
three sources: a database row backed by a verified source, an explicit
`hypothesis`-labeled inference, or an explicit "evidence is insufficient"
statement. There is no fourth path where an LLM just makes something up,
because there's no code path that asks it to.

Concretely: a rule-based extractor reads the user's message and a
NetworkX-based ecological knowledge graph (23 nodes, 22 typed edges, each
carrying an evidence-strength label) connects the user's variables to
candidate interventions, each backed by claims resolved against 12
independently-verified scientific sources with real DOIs. A constraint
engine checks water sensitivity and ecosystem-context match. A verification
service cross-checks that numeric figures in a claim actually appear in the
retrieved source excerpt, downgrading the claim's status automatically if
not.

## Evidence grounding, demonstrated not asserted

The agroforestry recommendation in the demo scenario is the clearest proof
this isn't theater. The two cited sources for agroforestry -- a 2021
time-cumulative meta-analysis and a 2022 synthesis -- conclude, respectively,
that agroforestry has "no unequivocal effect on biodiversity" and that the
underlying evidence is too heterogeneous to draw a clean conclusion. Rather
than smoothing this into marketing copy, the system reports exactly that,
assigns the recommendation `low` confidence and `weak` evidence strength, and
lists the finding verbatim in the trade-offs. A generic LLM chatbot, asked
the same question, would very likely still recommend agroforestry
enthusiastically -- because agroforestry *sounds* like the right answer for
"declining biodiversity on farmland," and sounding right is exactly the
failure mode this system is built to avoid.

## Inspectability

Every layer exposes its own reasoning:
- **Retrieval**: `POST /retrieval/inspect` returns which graph concepts
  matched, which terms were added by graph expansion, semantic vs. lexical
  candidate counts, and a plain-language reason for every result.
- **Knowledge graph**: browsable in the UI, filterable by node type, with
  evidence-strength color coding on every edge.
- **Reasoning trace**: each recommendation's assessment includes the
  concern-to-intervention path that produced it.
- **Evidence table**: every claim, its type, its source, its citation, its
  excerpt, and its computed verification status.
- **Heuristic ranking**: shown with its exact weights and component scores,
  labeled a prototype, never presented as a validated index.

## Real demonstration, not a mockup

Every number in this system's demo comes from the running backend. There is
no hardcoded frontend data standing in for a broken pipeline. This was
verified by driving the actual app in a headless browser during development
(screenshots exist), by running the full pipeline against a real
containerized PostgreSQL database (not just SQLite), and by finding and
fixing two real bugs that only manifested under Postgres -- documented
transparently in `docs/engineering-audit.md` rather than hidden.

## Measured evaluation, honestly scoped

45 backend tests and 13 frontend tests pass, including a 6-case evaluation
benchmark checking schema validity, citation coverage, unsupported-claim
rate, and ecosystem-mismatch detection. This is explicitly a **prototype**
evaluation with hand-curated cases, not an expert-labeled benchmark -- stated
plainly in `docs/evaluation.md` rather than dressed up as more than it is.

## Impact

A landholder using this system gets: targeted clarifying questions instead
of a wall of forms; multiple candidate interventions instead of one
one-size-fits-all answer; explicit trade-offs and constraints instead of
unconditional enthusiasm; a monitoring plan that tells them to establish a
baseline instead of promising a number nobody can back up; and the ability
to update their data and see exactly what changed and why.

## Future scalability

The architecture scales along clear, already-documented seams: the seed
corpus can grow past 12 sources without any code change (just more
`data/seed/*.json` entries, validated automatically by
`scripts/validate_knowledge.py`); the embedding provider can be swapped from
the deterministic hashing default to a real neural embedding via one env
var; the vector storage can move to pgvector (the Postgres image is already
in place) once the corpus is large enough to need an ANN index; and the
knowledge graph can move to a dedicated graph database if it outgrows an
in-memory NetworkX rebuild-per-request.

This is not presented as a finished, production-scale product. It is
presented as a working, evidence-grounded reasoning system where a judge can
verify every claim above by actually running it -- and where, when something
was found broken during that verification, it was fixed and documented
rather than glossed over.
