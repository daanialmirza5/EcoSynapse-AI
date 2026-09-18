import { useState } from "react";
import type { ReasoningPath, RecommendationOut } from "../../types/api";

/**
 * Surfaces the exact reasoning path(s) that produced THIS recommendation,
 * not a generic assessment-wide trace. Every fact shown here already exists
 * in the assessment response (reasoning_paths + evidence) -- this component
 * only re-presents it as "Because X -> connects through Y -> Evidence Z ->
 * Therefore this recommendation," which is what a skeptical reviewer needs
 * to audit the reasoning without reading raw JSON.
 */
export default function WhyThisRecommendation({
  rec,
  reasoningPaths,
}: {
  rec: RecommendationOut;
  reasoningPaths: ReasoningPath[];
}) {
  const [open, setOpen] = useState(false);

  const matchingPaths = rec.intervention_id
    ? reasoningPaths.filter((p) => p.variables.includes(rec.intervention_id!))
    : [];

  if (matchingPaths.length === 0) return null;

  const detectedConditions = Array.from(
    new Set(matchingPaths.flatMap((p) => p.variables.filter((v) => v !== rec.intervention_id)))
  );

  return (
    <div className="mt-2">
      <button
        className="text-sm text-eco-700 font-medium underline"
        onClick={() => setOpen((o) => !o)}
      >
        {open ? "Hide “Why this recommendation?”" : "Why this recommendation?"}
      </button>
      {open && (
        <div className="mt-2 bg-sky-50 border border-sky-200 rounded-lg p-3 text-sm space-y-2">
          <div>
            <span className="font-medium text-sky-900">Because these conditions were detected: </span>
            <span className="text-sky-800">{detectedConditions.map((v) => v.replace(/_/g, " ")).join(", ")}</span>
          </div>
          <div>
            <span className="font-medium text-sky-900">They connect through: </span>
            <div className="mt-1 flex flex-wrap gap-1">
              {matchingPaths.flatMap((p) => p.steps).map((s, i) => (
                <span key={i} className="badge bg-white border border-sky-200 text-sky-800">
                  {s.from_node.replace(/_/g, " ")} &rarr;[{s.relation}, {s.evidence_strength}]&rarr; {s.to_node.replace(/_/g, " ")}
                </span>
              ))}
            </div>
          </div>
          <div>
            <span className="font-medium text-sky-900">Evidence: </span>
            <span className="text-sky-800">
              {rec.evidence.length > 0
                ? rec.evidence.map((e) => e.source_title || e.claim_type).join("; ")
                : "no direct source-backed claim for this specific link (see evidence table below)"}
            </span>
          </div>
          <div>
            <span className="font-medium text-sky-900">Therefore: </span>
            <span className="text-sky-800">{rec.what_to_do}</span>
          </div>
        </div>
      )}
    </div>
  );
}
