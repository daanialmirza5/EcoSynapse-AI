import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";
import { Card, ErrorState, LoadingState } from "../components/ui";

export default function SystemStatus() {
  const { data, isLoading, error, refetch, isRefetching } = useQuery({ queryKey: ["health"], queryFn: api.health });

  return (
    <div className="p-4 md:p-6 max-w-3xl mx-auto space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-stone-900">System status & demo mode</h1>
          <p className="text-sm text-stone-600">Live backend health, provider configuration, and knowledge-base size.</p>
        </div>
        <button className="text-sm border border-stone-300 px-3 py-1.5 rounded-lg" onClick={() => refetch()}>
          {isRefetching ? "Refreshing..." : "Refresh"}
        </button>
      </div>

      {isLoading && <LoadingState />}
      {error && <ErrorState message="Backend unreachable. Start it with `uvicorn app.main:app` in apps/api." />}

      {data && (
        <>
          <Card title="Status">
            <dl className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <dt className="text-stone-500">Overall</dt>
                <dd className={`font-medium ${data.status !== "ok" ? "text-amber-700" : ""}`}>{data.status}</dd>
              </div>
              <div><dt className="text-stone-500">Environment</dt><dd className="font-medium">{data.environment}</dd></div>
              <div><dt className="text-stone-500">Database</dt><dd className="font-medium">{data.database}</dd></div>
              <div><dt className="text-stone-500">LLM provider</dt><dd className="font-medium">{data.llm_provider}</dd></div>
              <div><dt className="text-stone-500">Embedding provider</dt><dd className="font-medium">{data.embedding_provider}</dd></div>
            </dl>
          </Card>

          <Card title="Knowledge base">
            <dl className="grid grid-cols-3 gap-4 text-sm">
              <div><dt className="text-stone-500">Sources</dt><dd className="font-medium">{data.knowledge_base.sources}</dd></div>
              <div><dt className="text-stone-500">Graph nodes</dt><dd className="font-medium">{data.knowledge_base.graph_nodes}</dd></div>
              <div><dt className="text-stone-500">Graph edges</dt><dd className="font-medium">{data.knowledge_base.graph_edges}</dd></div>
            </dl>
          </Card>

          {data.notes.length > 0 && (
            <Card title="Active warnings">
              <ul className="text-sm text-amber-800 bg-amber-50 border border-amber-200 rounded-lg p-3 list-disc list-inside space-y-1">
                {data.notes.map((n, i) => <li key={i}>{n}</li>)}
              </ul>
            </Card>
          )}

          <Card title="Demo mode notes">
            <ul className="text-sm text-stone-700 list-disc list-inside space-y-1">
              <li>The system runs fully offline by default: the "mock-deterministic" LLM provider and the "hashing" embedding provider require no API key.</li>
              <li>Setting OPENAI_API_KEY and LLM_PROVIDER=openai enables higher-quality phrasing assistance only; all scientific claims still come exclusively from the deterministic reasoning engine and evidence store.</li>
              <li>If the AI provider or database is unavailable, the API returns a degraded status rather than crashing; conversation extraction and the reasoning engine do not depend on either being reachable beyond the DB itself.</li>
            </ul>
          </Card>
        </>
      )}
    </div>
  );
}
