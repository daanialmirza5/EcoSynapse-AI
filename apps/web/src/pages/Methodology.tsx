import { Card } from "../components/ui";

export default function Methodology() {
  return (
    <div className="p-4 md:p-6 max-w-3xl mx-auto space-y-4 pb-16">
      <div>
        <h1 className="text-xl font-semibold text-stone-900">Methodology & scientific integrity</h1>
        <p className="text-sm text-stone-600">A short version of docs/scientific-grounding.md and docs/reasoning-methodology.md.</p>
      </div>

      <Card title="Claim classification">
        <p className="text-sm text-stone-700 mb-2">Every scientific statement the system makes is labeled as one of:</p>
        <ul className="text-sm text-stone-700 list-disc list-inside space-y-1">
          <li><strong>Source-supported fact</strong> &mdash; directly backed by a verified source and excerpt.</li>
          <li><strong>Model-derived inference</strong> &mdash; a logical inference from a source finding, not itself directly tested.</li>
          <li><strong>Hypothesis</strong> &mdash; ecologically plausible but not evidenced in this corpus.</li>
          <li><strong>User-provided observation</strong> &mdash; a fact the user reported, not verified independently.</li>
          <li><strong>Unknown / insufficient</strong> &mdash; explicitly flagged rather than guessed.</li>
        </ul>
      </Card>

      <Card title="Retrieval pipeline">
        <ol className="text-sm text-stone-700 list-decimal list-inside space-y-1">
          <li>Parse the query and identify environmental entities via a shared vocabulary.</li>
          <li>Expand matched concepts one hop through the ecological knowledge graph.</li>
          <li>Semantic search: cosine similarity over chunk embeddings (deterministic hashing embedding by default, or an OpenAI-compatible provider if configured).</li>
          <li>Lexical keyword search over the same chunk corpus.</li>
          <li>Merge, dedupe, and rerank by a weighted combination of semantic and lexical scores.</li>
          <li>Return sources with excerpts and an explicit reason each result matched.</li>
        </ol>
      </Card>

      <Card title="Reasoning pipeline">
        <ol className="text-sm text-stone-700 list-decimal list-inside space-y-1">
          <li>Build a known/unknown environmental state from the profile.</li>
          <li>Require at least three known variables before generating recommendations; otherwise state the limitation explicitly.</li>
          <li>Detect concerns from threshold rules (e.g. SOC &lt; 1%, rainfall low, monoculture land use).</li>
          <li>Map concerns to candidate interventions via the knowledge graph.</li>
          <li>Check each candidate against constraints (water sensitivity, user-stated limits, ecosystem-context mismatch).</li>
          <li>Verify every attached claim against its source excerpt, including a check for unverified numeric figures.</li>
          <li>Score candidates with a transparent, labeled prototype heuristic (never called a validated biodiversity index).</li>
          <li>Generate a monitoring plan per impacted metric, with no fabricated numeric targets.</li>
        </ol>
      </Card>

      <Card title="What this system will not do">
        <ul className="text-sm text-stone-700 list-disc list-inside space-y-1">
          <li>It will not invent a DOI, author, or dataset.</li>
          <li>It will not present a model-derived inference as an observed result.</li>
          <li>It will not state a numeric improvement (e.g. "+20% biodiversity") unless a cited source states that exact figure under compatible conditions.</li>
          <li>It will not force three environmental variables into an assessment the data does not support.</li>
        </ul>
      </Card>

      <Card title="Known limitations">
        <ul className="text-sm text-stone-700 list-disc list-inside space-y-1">
          <li>The seed corpus is a small (12-source) curated demo corpus, not a comprehensive literature review.</li>
          <li>The default embedding provider is a deterministic hashing scheme, not a trained neural embedding model &mdash; adequate for demonstrating a working hybrid pipeline, not for production-grade semantic search.</li>
          <li>The heuristic ranking is an explicitly labeled prototype, not a peer-reviewed decision model.</li>
          <li>Vector storage uses a portable JSON column with Python-side cosine similarity rather than a wired pgvector index; the schema supports migrating to pgvector in Postgres (see docs/database-schema.md).</li>
        </ul>
      </Card>
    </div>
  );
}
