import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import { useWorkspace } from "../hooks/useWorkspaceState";
import { Card, ConfidenceBadge, EmptyState, LoadingState, TimeHorizonBadge } from "../components/ui";

export default function RecommendationComparison() {
  const { assessmentId } = useWorkspace();
  const { data: assessment, isLoading } = useQuery({
    queryKey: ["assessment", assessmentId],
    queryFn: () => api.getAssessment(assessmentId!),
    enabled: !!assessmentId,
  });

  return (
    <div className="p-4 md:p-6 max-w-6xl mx-auto space-y-4">
      <div>
        <h1 className="text-xl font-semibold text-stone-900">Recommendation comparison</h1>
        <p className="text-sm text-stone-600">
          Side-by-side comparison of candidate interventions from the most recent assessment, ranked by the
          prototype decision-support heuristic (not a validated biodiversity index).
        </p>
      </div>

      {!assessmentId && (
        <EmptyState message={"No assessment yet. Run one from the Assessment Workspace first."} />
      )}
      {assessmentId && (
        <div className="mb-2">
          <Link to="/workspace" className="text-sm text-eco-700 underline">Back to workspace &rarr;</Link>
        </div>
      )}
      {isLoading && <LoadingState />}

      {assessment && (
        <Card>
          {assessment.recommendations.length === 0 ? (
            <EmptyState message="No recommendations were generated for this assessment." />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm border-collapse">
                <thead>
                  <tr className="text-left border-b border-stone-200 text-stone-500">
                    <th className="py-2 pr-4">Intervention</th>
                    <th className="py-2 pr-4">Time horizon</th>
                    <th className="py-2 pr-4">Confidence</th>
                    <th className="py-2 pr-4">Impacted metrics</th>
                    <th className="py-2 pr-4">Supported claims</th>
                    <th className="py-2 pr-4">Heuristic score</th>
                  </tr>
                </thead>
                <tbody>
                  {[...assessment.recommendations]
                    .sort((a, b) => b.heuristic_score.total - a.heuristic_score.total)
                    .map((rec) => (
                      <tr key={rec.id} className="border-b border-stone-100 align-top">
                        <td className="py-2 pr-4 font-medium">{rec.title}</td>
                        <td className="py-2 pr-4"><TimeHorizonBadge horizon={rec.time_horizon} /></td>
                        <td className="py-2 pr-4"><ConfidenceBadge level={rec.confidence.level} /></td>
                        <td className="py-2 pr-4 text-xs text-stone-600">{rec.impacted_metrics.join(", ")}</td>
                        <td className="py-2 pr-4 text-xs text-stone-600">
                          {rec.evidence.filter((e) => e.evidence_status === "supported").length} / {rec.evidence.length}
                        </td>
                        <td className="py-2 pr-4 text-xs text-stone-600">{rec.heuristic_score.total}</td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      )}
    </div>
  );
}
