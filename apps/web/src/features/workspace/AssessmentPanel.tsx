import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../../lib/api";
import { Card, EmptyState, ErrorState, LoadingState } from "../../components/ui";
import RecommendationCard from "./RecommendationCard";

export default function AssessmentPanel({
  profileId,
  conversationId,
  assessmentId,
  readyForAssessment,
  onAssessmentCreated,
}: {
  profileId: string;
  conversationId: string;
  assessmentId: string | null;
  readyForAssessment: boolean;
  onAssessmentCreated: (id: string) => void;
}) {
  const queryClient = useQueryClient();

  const { data: assessment, isLoading } = useQuery({
    queryKey: ["assessment", assessmentId],
    queryFn: () => api.getAssessment(assessmentId!),
    enabled: !!assessmentId,
  });

  const runAssessment = useMutation({
    mutationFn: () => api.createAssessment(profileId, conversationId),
    onSuccess: (a) => onAssessmentCreated(a.id),
  });

  const reassess = useMutation({
    mutationFn: () => api.reassess(assessmentId!),
    onSuccess: (a) => {
      onAssessmentCreated(a.id);
      queryClient.invalidateQueries({ queryKey: ["assessment"] });
    },
  });

  return (
    <Card
      title="Assessment & recommendations"
      actions={
        <div className="flex gap-2">
          <button
            className="text-sm bg-eco-600 text-white px-3 py-1.5 rounded-lg disabled:opacity-50"
            onClick={() => runAssessment.mutate()}
            disabled={!readyForAssessment || runAssessment.isPending}
            title={!readyForAssessment ? "Need at least 3 known variables first" : ""}
          >
            {runAssessment.isPending ? "Running..." : assessmentId ? "Run new assessment" : "Run assessment"}
          </button>
          {assessmentId && (
            <>
              <button
                className="text-sm border border-stone-300 px-3 py-1.5 rounded-lg disabled:opacity-50"
                onClick={() => reassess.mutate()}
                disabled={reassess.isPending}
              >
                {reassess.isPending ? "Reassessing..." : "Reassess"}
              </button>
              <a
                className="text-sm border border-stone-300 px-3 py-1.5 rounded-lg"
                href={api.exportAssessmentUrl(assessmentId)}
                target="_blank"
                rel="noreferrer"
              >
                Export
              </a>
            </>
          )}
        </div>
      }
    >
      {!assessmentId && !isLoading && (
        <EmptyState message="No assessment yet. Provide at least three environmental variables, then run an assessment." />
      )}
      {isLoading && <LoadingState message="Loading assessment..." />}
      {runAssessment.isError && <ErrorState message="Failed to run assessment." />}

      {assessment && (
        <div className="space-y-5">
          <div className="text-sm text-stone-700 bg-eco-50 border border-eco-100 rounded-lg p-3">
            {assessment.assessment_summary}
          </div>

          {assessment.diff_from_previous.length > 0 && (
            <div className="bg-sky-50 border border-sky-200 rounded-lg p-3 text-sm">
              <div className="font-medium text-sky-800 mb-1">Changed since previous assessment (v{assessment.version - 1} &rarr; v{assessment.version})</div>
              <ul className="list-disc list-inside text-sky-900 text-xs space-y-0.5">
                {assessment.diff_from_previous.map((d, i) => (
                  <li key={i}>{JSON.stringify(d)}</li>
                ))}
              </ul>
            </div>
          )}

          <details className="text-sm">
            <summary className="cursor-pointer font-medium text-stone-800">
              Reasoning trace ({assessment.variables_considered.length} variables, {assessment.reasoning_paths.length} path(s))
            </summary>
            <div className="mt-2 space-y-2">
              {assessment.reasoning_paths.map((p, i) => (
                <div key={i} className="bg-stone-50 border border-stone-200 rounded-lg p-2.5 text-xs">
                  <div className="text-stone-700">{p.narrative}</div>
                  <div className="mt-1 flex flex-wrap gap-1 text-stone-500">
                    {p.steps.map((s, j) => (
                      <span key={j} className="badge bg-white border border-stone-200">
                        {s.from_node} &rarr;[{s.relation}, {s.evidence_strength}]&rarr; {s.to_node}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </details>

          {assessment.recommendations.length === 0 ? (
            <EmptyState message="No candidate interventions were generated for the currently known variables." />
          ) : (
            <div className="space-y-4">
              {assessment.recommendations.map((rec) => (
                <RecommendationCard key={rec.id} rec={rec} />
              ))}
            </div>
          )}

          {assessment.overall_limitations.length > 0 && (
            <div className="bg-stone-100 rounded-lg p-3 text-xs text-stone-600">
              <div className="font-medium mb-1">Overall limitations</div>
              <ul className="list-disc list-inside space-y-0.5">
                {assessment.overall_limitations.map((l, i) => <li key={i}>{l}</li>)}
              </ul>
            </div>
          )}
        </div>
      )}
    </Card>
  );
}
