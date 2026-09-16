import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "../lib/api";
import { useWorkspace } from "../hooks/useWorkspaceState";
import { Card, EmptyState, LoadingState } from "../components/ui";

export default function MonitoringDashboard() {
  const { assessmentId, profileId } = useWorkspace();
  const queryClient = useQueryClient();
  const [obsMetric, setObsMetric] = useState("");
  const [obsValue, setObsValue] = useState("");

  const { data: assessment, isLoading } = useQuery({
    queryKey: ["assessment", assessmentId],
    queryFn: () => api.getAssessment(assessmentId!),
    enabled: !!assessmentId,
  });

  const addObservation = useMutation({
    mutationFn: () => api.addObservation(profileId!, { metric: obsMetric, value: Number(obsValue), source: "user_reported" }),
    onSuccess: () => {
      setObsMetric("");
      setObsValue("");
      queryClient.invalidateQueries({ queryKey: ["observations", profileId] });
    },
  });

  const allMetrics = useMemo(() => {
    const entries: { metric: string; horizon: string; recommendation: string }[] = [];
    assessment?.recommendations.forEach((rec) => {
      rec.monitoring_plan.forEach((m) => entries.push({ metric: m.metric, horizon: m.time_horizon, recommendation: rec.title }));
    });
    return entries;
  }, [assessment]);

  const chartData = useMemo(() => {
    const counts: Record<string, number> = { short: 0, medium: 0, long: 0 };
    allMetrics.forEach((m) => { counts[m.horizon] = (counts[m.horizon] || 0) + 1; });
    return Object.entries(counts).map(([horizon, count]) => ({ horizon, count }));
  }, [allMetrics]);

  return (
    <div className="p-4 md:p-6 max-w-6xl mx-auto space-y-4">
      <div>
        <h1 className="text-xl font-semibold text-stone-900">Monitoring dashboard</h1>
        <p className="text-sm text-stone-600">
          Aggregated monitoring plan across all recommendations in the current assessment. No numeric targets are
          shown unless a baseline observation has been recorded for that metric.
        </p>
      </div>

      {!assessmentId && <EmptyState message="No assessment yet. Run one from the Assessment Workspace first." />}
      {isLoading && <LoadingState />}

      {assessment && (
        <>
          <Card title="Monitoring cadence by time horizon">
            <div style={{ width: "100%", height: 220 }}>
              <ResponsiveContainer>
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e7e5e4" />
                  <XAxis dataKey="horizon" tick={{ fontSize: 12 }} />
                  <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Bar dataKey="count" fill="#468a54" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>

          <Card title="Record a new observation">
            <div className="flex flex-wrap gap-2 items-end">
              <label className="text-sm">
                <span className="block text-xs text-stone-500 mb-1">Metric</span>
                <input className="border border-stone-300 rounded-lg px-2.5 py-1.5" value={obsMetric} onChange={(e) => setObsMetric(e.target.value)} placeholder="e.g. species_richness" />
              </label>
              <label className="text-sm">
                <span className="block text-xs text-stone-500 mb-1">Value</span>
                <input type="number" step="any" className="border border-stone-300 rounded-lg px-2.5 py-1.5" value={obsValue} onChange={(e) => setObsValue(e.target.value)} />
              </label>
              <button
                className="bg-eco-600 text-white text-sm px-3 py-1.5 rounded-lg disabled:opacity-50"
                onClick={() => addObservation.mutate()}
                disabled={!obsMetric || !obsValue || !profileId || addObservation.isPending}
              >
                Record baseline
              </button>
            </div>
            <p className="text-xs text-stone-500 mt-2">
              Recording a baseline lets future assessments compare against it instead of stating "establish a
              baseline first."
            </p>
          </Card>

          <Card title={`All monitored metrics (${allMetrics.length})`}>
            {allMetrics.length === 0 ? (
              <EmptyState message="No monitoring entries in this assessment." />
            ) : (
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-stone-500 border-b border-stone-200">
                    <th className="py-1.5 pr-4">Metric</th>
                    <th className="py-1.5 pr-4">Horizon</th>
                    <th className="py-1.5 pr-4">From recommendation</th>
                  </tr>
                </thead>
                <tbody>
                  {allMetrics.map((m, i) => (
                    <tr key={i} className="border-b border-stone-100">
                      <td className="py-1.5 pr-4 font-medium">{m.metric.replace(/_/g, " ")}</td>
                      <td className="py-1.5 pr-4">{m.horizon}</td>
                      <td className="py-1.5 pr-4 text-stone-600">{m.recommendation}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </Card>
        </>
      )}
    </div>
  );
}
