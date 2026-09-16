import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import { Card, ErrorState, LoadingState } from "../components/ui";

export default function Overview() {
  const { data, isLoading, error } = useQuery({ queryKey: ["health"], queryFn: api.health });

  return (
    <div className="max-w-4xl mx-auto p-6 md:p-10 space-y-6">
      <div>
        <h1 className="text-2xl md:text-3xl font-semibold text-stone-900">EcoSynapse AI</h1>
        <p className="text-stone-600 mt-2 max-w-2xl">
          Evidence-grounded ecological intelligence and intervention planning. Describe a piece of land or a
          biodiversity concern; the system builds a structured environmental profile, retrieves scientific evidence,
          traverses an ecological knowledge graph, and produces intervention recommendations with explicit
          confidence, trade-offs, and monitoring plans &mdash; never a generic LLM answer.
        </p>
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        <Link to="/workspace" className="card p-5 hover:border-eco-400 transition-colors">
          <div className="font-semibold text-eco-700">Start an assessment &rarr;</div>
          <div className="text-sm text-stone-600 mt-1">
            Talk to the assistant, submit a structured profile, or load the challenge demo scenario.
          </div>
        </Link>
        <Link to="/docs" className="card p-5 hover:border-eco-400 transition-colors">
          <div className="font-semibold text-eco-700">Read the methodology &rarr;</div>
          <div className="text-sm text-stone-600 mt-1">
            How retrieval, the knowledge graph, and the reasoning engine work &mdash; and their limitations.
          </div>
        </Link>
      </div>

      <Card title="System status">
        {isLoading && <LoadingState message="Checking backend..." />}
        {error && <ErrorState message="Could not reach the backend API. Is it running on port 8000?" />}
        {data && (
          <dl className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <dt className="text-stone-500">Status</dt>
              <dd className="font-medium">{data.status}</dd>
            </div>
            <div>
              <dt className="text-stone-500">LLM provider</dt>
              <dd className="font-medium">{data.llm_provider}</dd>
            </div>
            <div>
              <dt className="text-stone-500">Sources indexed</dt>
              <dd className="font-medium">{data.knowledge_base.sources}</dd>
            </div>
            <div>
              <dt className="text-stone-500">Graph edges</dt>
              <dd className="font-medium">{data.knowledge_base.graph_edges}</dd>
            </div>
          </dl>
        )}
      </Card>

      <Card title="Mandatory knowledge areas covered">
        <ul className="text-sm text-stone-700 grid md:grid-cols-2 gap-x-8 gap-y-1 list-disc list-inside">
          <li>Soil health: pH, organic carbon, moisture</li>
          <li>Land use / land cover</li>
          <li>Biodiversity indicators: species richness, habitat diversity</li>
          <li>Climate factors: temperature, rainfall</li>
          <li>Human impact: pollution, deforestation</li>
        </ul>
      </Card>
    </div>
  );
}
