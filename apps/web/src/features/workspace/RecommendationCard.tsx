import { useState } from "react";
import type { RecommendationOut } from "../../types/api";
import {
  ClaimTypeBadge,
  ConfidenceBadge,
  EvidenceStatusBadge,
  EvidenceStrengthBadge,
  TimeHorizonBadge,
} from "../../components/ui";

export default function RecommendationCard({ rec }: { rec: RecommendationOut }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="card p-4 md:p-5">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <h4 className="font-semibold text-stone-900 text-base">{rec.title}</h4>
        <div className="flex gap-2 flex-wrap">
          <TimeHorizonBadge horizon={rec.time_horizon} />
          <ConfidenceBadge level={rec.confidence.level} />
          <EvidenceStrengthBadge strength={rec.evidence_strength_summary} />
        </div>
      </div>

      <p className="text-sm text-stone-700 mt-2"><span className="font-medium">What to do: </span>{rec.what_to_do}</p>
      <p className="text-sm text-stone-700 mt-1"><span className="font-medium">Why it may work: </span>{rec.why_it_may_work}</p>
      <p className="text-xs text-stone-500 mt-1">
        {rec.confidence.reason} Data completeness at assessment time: {Math.round(rec.data_completeness * 100)}%.
      </p>
      <p className="text-[11px] text-stone-400 mt-1">
        Confidence, evidence strength, and data completeness are reported separately by design &mdash; see{" "}
        <a href="/docs" className="underline">Methodology</a> for how each is calculated.
      </p>

      <div className="mt-3 flex flex-wrap gap-1.5">
        {rec.impacted_metrics.map((m) => (
          <span key={m} className="badge bg-stone-100 text-stone-700">{m.replace(/_/g, " ")}</span>
        ))}
      </div>

      {rec.feasibility_constraints.length > 0 && (
        <div className="mt-3 bg-amber-50 border border-amber-200 rounded-lg p-2.5">
          <div className="text-xs font-medium text-amber-800 mb-1">Feasibility constraints</div>
          <ul className="text-xs text-amber-900 list-disc list-inside space-y-0.5">
            {rec.feasibility_constraints.map((c, i) => <li key={i}>{c}</li>)}
          </ul>
        </div>
      )}

      {rec.trade_offs.length > 0 && (
        <div className="mt-2 bg-stone-50 border border-stone-200 rounded-lg p-2.5">
          <div className="text-xs font-medium text-stone-700 mb-1">Trade-offs &amp; unknowns</div>
          <ul className="text-xs text-stone-700 list-disc list-inside space-y-0.5">
            {rec.trade_offs.map((c, i) => <li key={i}>{c}</li>)}
          </ul>
        </div>
      )}

      <button
        className="mt-3 text-sm text-eco-700 font-medium underline"
        onClick={() => setExpanded((e) => !e)}
      >
        {expanded ? "Hide evidence & monitoring plan" : "Show evidence table & monitoring plan"}
      </button>

      {expanded && (
        <div className="mt-3 space-y-4">
          <div>
            <div className="text-sm font-medium text-stone-800 mb-2">Claim-level evidence</div>
            <div className="space-y-2">
              {rec.evidence.map((e, i) => (
                <div key={i} className="border border-stone-200 rounded-lg p-2.5 text-xs space-y-1">
                  <div className="flex flex-wrap gap-1.5 items-center">
                    <ClaimTypeBadge type={e.claim_type} />
                    <EvidenceStatusBadge status={e.evidence_status} />
                  </div>
                  <div className="text-stone-800">{e.claim}</div>
                  {e.source_title && (
                    <div className="text-stone-600">
                      Source: {e.source_title}
                      {e.citation && (
                        <>
                          {" "}&middot;{" "}
                          <a href={e.citation} target="_blank" rel="noreferrer" className="text-eco-700 underline">
                            {e.citation}
                          </a>
                        </>
                      )}
                    </div>
                  )}
                  {e.excerpt && <div className="text-stone-500 italic">&ldquo;{e.excerpt}&rdquo;</div>}
                  {e.limitations && <div className="text-stone-500">Limitations: {e.limitations}</div>}
                </div>
              ))}
              {rec.evidence.length === 0 && (
                <div className="text-xs text-stone-500 italic">No linked evidence for this candidate.</div>
              )}
            </div>
          </div>

          <div>
            <div className="text-sm font-medium text-stone-800 mb-2">Monitoring plan</div>
            <div className="overflow-x-auto">
              <table className="w-full text-xs border-collapse">
                <thead>
                  <tr className="text-left text-stone-500 border-b border-stone-200">
                    <th className="py-1 pr-3">Metric</th>
                    <th className="py-1 pr-3">Method</th>
                    <th className="py-1 pr-3">Frequency</th>
                    <th className="py-1 pr-3">Target</th>
                  </tr>
                </thead>
                <tbody>
                  {rec.monitoring_plan.map((m, i) => (
                    <tr key={i} className="border-b border-stone-100 align-top">
                      <td className="py-1.5 pr-3 font-medium">{m.metric.replace(/_/g, " ")}</td>
                      <td className="py-1.5 pr-3 text-stone-600">{m.measurement_method}</td>
                      <td className="py-1.5 pr-3 text-stone-600">{m.measurement_frequency}</td>
                      <td className="py-1.5 pr-3 text-stone-600">{m.target}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div>
            <div className="text-sm font-medium text-stone-800 mb-1">
              Ranking heuristic: {rec.heuristic_score.total} <span className="text-xs font-normal text-stone-500">(prototype only)</span>
            </div>
            <div className="text-xs text-stone-500 mb-1">{rec.heuristic_score.disclaimer}</div>
            <div className="flex gap-3 text-xs text-stone-600">
              {Object.entries(rec.heuristic_score.components).map(([k, v]) => (
                <span key={k}>{k.replace(/_/g, " ")}: {v}</span>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
