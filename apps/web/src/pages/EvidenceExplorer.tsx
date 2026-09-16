import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";
import { Card, EmptyState, LoadingState } from "../components/ui";

export default function EvidenceExplorer() {
  const [query, setQuery] = useState("soil organic carbon and biodiversity in semi-arid cropland");
  const { data: sources, isLoading: sourcesLoading } = useQuery({ queryKey: ["sources"], queryFn: api.listSources });

  const inspect = useMutation({
    mutationFn: () => api.inspectRetrieval(query, undefined, 6),
  });

  return (
    <div className="p-4 md:p-6 max-w-6xl mx-auto space-y-4">
      <div>
        <h1 className="text-xl font-semibold text-stone-900">Evidence explorer</h1>
        <p className="text-sm text-stone-600">
          Browse the verified source corpus, or run a live retrieval query to see exactly which evidence chunks were
          matched and why (semantic similarity, keyword overlap, and knowledge-graph term expansion).
        </p>
      </div>

      <Card title="Try a retrieval query">
        <div className="flex gap-2">
          <input
            className="flex-1 border border-stone-300 rounded-lg px-3 py-2 text-sm"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <button
            className="bg-eco-600 text-white text-sm px-4 py-2 rounded-lg disabled:opacity-50"
            onClick={() => inspect.mutate()}
            disabled={inspect.isPending || !query.trim()}
          >
            {inspect.isPending ? "Retrieving..." : "Retrieve"}
          </button>
        </div>

        {inspect.data && (
          <div className="mt-4 space-y-3">
            <div className="text-xs text-stone-500 flex flex-wrap gap-x-4 gap-y-1">
              <span>Graph concepts matched: {inspect.data.graph_concepts.join(", ") || "none"}</span>
              <span>Expanded via graph: {inspect.data.expanded_terms.join(", ") || "none"}</span>
              <span>Semantic candidates: {inspect.data.semantic_candidates}</span>
              <span>Lexical candidates: {inspect.data.lexical_candidates}</span>
            </div>
            <div className="space-y-2">
              {inspect.data.results.map((r) => (
                <div key={r.chunk_id} className="border border-stone-200 rounded-lg p-3 text-sm">
                  <div className="flex justify-between items-start gap-2">
                    <div className="font-medium text-stone-800">{r.source.title}</div>
                    <span className="badge bg-eco-100 text-eco-800 shrink-0">score {r.relevance_score}</span>
                  </div>
                  <div className="text-xs text-stone-500 mt-0.5">
                    {r.source.organization} {r.source.publication_year ? `(${r.source.publication_year})` : ""}
                  </div>
                  <div className="text-xs text-stone-600 italic mt-1">&ldquo;{r.excerpt}&rdquo;</div>
                  <div className="text-xs text-stone-500 mt-1">Why matched: {r.match_reasons.join("; ")}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </Card>

      <Card title={`Verified source corpus (${sources?.length ?? 0})`}>
        {sourcesLoading && <LoadingState />}
        {sources && sources.length === 0 && <EmptyState message="No sources ingested yet." />}
        <div className="space-y-2">
          {sources?.map((s) => (
            <div key={s.id} className="border border-stone-200 rounded-lg p-3 text-sm">
              <div className="font-medium text-stone-800">{s.title}</div>
              <div className="text-xs text-stone-500">
                {s.organization} {s.publication_year ? `(${s.publication_year})` : ""} &middot; {s.source_type}
              </div>
              {s.url && (
                <a href={s.url} target="_blank" rel="noreferrer" className="text-xs text-eco-700 underline">
                  {s.doi ? `doi:${s.doi}` : s.url}
                </a>
              )}
              {s.limitations && <div className="text-xs text-stone-500 mt-1">Limitations: {s.limitations}</div>}
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
