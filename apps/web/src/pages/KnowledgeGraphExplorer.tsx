import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";
import { Card, LoadingState } from "../components/ui";

const STRENGTH_COLOR: Record<string, string> = {
  strong: "bg-eco-100 text-eco-800",
  moderate: "bg-sky-100 text-sky-800",
  weak: "bg-amber-100 text-amber-800",
  hypothesis: "bg-stone-200 text-stone-700",
};

export default function KnowledgeGraphExplorer() {
  const { data, isLoading } = useQuery({ queryKey: ["graph"], queryFn: api.getKnowledgeGraph });
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [typeFilter, setTypeFilter] = useState<string>("all");

  const nodesById = useMemo(() => {
    const map = new Map<string, string>();
    data?.nodes.forEach((n) => map.set(n.id, n.canonical_name));
    return map;
  }, [data]);

  const nodeTypes = useMemo(() => Array.from(new Set(data?.nodes.map((n) => n.node_type) ?? [])).sort(), [data]);

  const filteredNodes = useMemo(
    () => (data?.nodes ?? []).filter((n) => typeFilter === "all" || n.node_type === typeFilter),
    [data, typeFilter]
  );

  const visibleEdges = useMemo(() => {
    if (!data) return [];
    if (!selectedNode) return data.edges;
    return data.edges.filter(
      (e) => nodesById.get(e.source_node_id) === selectedNode || nodesById.get(e.target_node_id) === selectedNode
    );
  }, [data, selectedNode, nodesById]);

  return (
    <div className="p-4 md:p-6 max-w-6xl mx-auto space-y-4">
      <div>
        <h1 className="text-xl font-semibold text-stone-900">Ecological knowledge graph</h1>
        <p className="text-sm text-stone-600">
          Typed nodes and edges connecting environmental metrics, ecological mechanisms, interventions, and
          constraints. Edge color reflects evidence strength &mdash; graph connectivity alone is never treated as
          proof of causation; hypothesis-level edges are explicitly labeled.
        </p>
      </div>

      {isLoading && <LoadingState message="Loading knowledge graph..." />}

      {data && (
        <div className="grid md:grid-cols-3 gap-4">
          <Card title={`Nodes (${filteredNodes.length})`}>
            <select
              className="w-full border border-stone-300 rounded-lg px-2 py-1.5 text-sm mb-3"
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
            >
              <option value="all">All types</option>
              {nodeTypes.map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
            <div className="max-h-[520px] overflow-y-auto space-y-1">
              {filteredNodes.map((n) => (
                <button
                  key={n.id}
                  onClick={() => setSelectedNode(selectedNode === n.canonical_name ? null : n.canonical_name)}
                  className={`w-full text-left text-xs px-2 py-1.5 rounded-lg border ${
                    selectedNode === n.canonical_name
                      ? "bg-eco-600 text-white border-eco-600"
                      : "border-stone-200 hover:bg-stone-50"
                  }`}
                >
                  <div className="font-medium">{n.canonical_name.replace(/_/g, " ")}</div>
                  <div className={selectedNode === n.canonical_name ? "text-eco-100" : "text-stone-400"}>{n.node_type}</div>
                </button>
              ))}
            </div>
          </Card>

          <div className="md:col-span-2">
            <Card title={selectedNode ? `Relationships involving "${selectedNode.replace(/_/g, " ")}"` : `All relationships (${visibleEdges.length})`}>
              {selectedNode && (
                <button className="text-xs text-eco-700 underline mb-2" onClick={() => setSelectedNode(null)}>
                  Clear selection
                </button>
              )}
              <div className="max-h-[520px] overflow-y-auto space-y-2">
                {visibleEdges.map((e) => (
                  <div key={e.id} className="border border-stone-200 rounded-lg p-2.5 text-xs">
                    <div className="flex items-center gap-1.5 flex-wrap">
                      <span className="font-medium">{nodesById.get(e.source_node_id)?.replace(/_/g, " ")}</span>
                      <span className="text-stone-400">&rarr;[{e.relation_type}]&rarr;</span>
                      <span className="font-medium">{nodesById.get(e.target_node_id)?.replace(/_/g, " ")}</span>
                      <span className={`badge ${STRENGTH_COLOR[e.evidence_strength] || "bg-stone-100"}`}>
                        {e.evidence_strength}
                      </span>
                    </div>
                    {e.mechanism && <div className="text-stone-600 mt-1">{e.mechanism}</div>}
                    {e.limitations && <div className="text-stone-400 mt-1">Limitations: {e.limitations}</div>}
                  </div>
                ))}
              </div>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}
