import { useEffect, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { api } from "../lib/api";
import { useWorkspace } from "../hooks/useWorkspaceState";
import ChatPanel from "../features/workspace/ChatPanel";
import ProfilePanel from "../features/workspace/ProfilePanel";
import AssessmentPanel from "../features/workspace/AssessmentPanel";
import ConflictBanner from "../features/workspace/ConflictBanner";
import type { ClarifyingQuestion, ConversationTurnResponse } from "../types/api";
import { LoadingState } from "../components/ui";

export default function Workspace() {
  const { conversationId, profileId, assessmentId, setConversationId, setProfileId, setAssessmentId } =
    useWorkspace();
  const [clarifyingQuestions, setClarifyingQuestions] = useState<ClarifyingQuestion[]>([]);
  const [completeness, setCompleteness] = useState<number | null>(null);
  const [readyForAssessment, setReadyForAssessment] = useState(false);
  const [conflicts, setConflicts] = useState<ConversationTurnResponse["conflicts"]>([]);

  const createConversation = useMutation({
    mutationFn: () => api.createConversation("Assessment workspace session"),
    onSuccess: (conv) => setConversationId(conv.id),
  });

  useEffect(() => {
    if (!conversationId && !createConversation.isPending) {
      createConversation.mutate();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [conversationId]);

  if (!conversationId) {
    return (
      <div className="p-10">
        <LoadingState message="Starting a new assessment session..." />
      </div>
    );
  }

  return (
    <div className="p-4 md:p-6 max-w-7xl mx-auto space-y-4">
      <div>
        <h1 className="text-xl font-semibold text-stone-900">Environmental assessment workspace</h1>
        <p className="text-sm text-stone-600">
          Talk to the assistant to build a land profile, then run the reasoning engine to get grounded intervention
          candidates.
        </p>
      </div>

      <div className="grid lg:grid-cols-2 gap-4 items-start">
        <ChatPanel
          conversationId={conversationId}
          onTurn={(turn) => {
            setProfileId(turn.profile_id);
            setClarifyingQuestions(turn.clarifying_questions);
            setCompleteness(turn.profile_completeness);
            setReadyForAssessment(turn.ready_for_assessment);
            setConflicts(turn.conflicts);
          }}
        />
        {profileId ? (
          <ProfilePanel profileId={profileId} clarifyingQuestions={clarifyingQuestions} completeness={completeness} />
        ) : (
          <div className="card p-5 text-sm text-stone-500 italic">
            Send a message to start building an environmental profile.
          </div>
        )}
      </div>

      <ConflictBanner conflicts={conflicts} hasExistingAssessment={!!assessmentId} />

      {profileId && (
        <AssessmentPanel
          profileId={profileId}
          conversationId={conversationId}
          assessmentId={assessmentId}
          readyForAssessment={readyForAssessment}
          onAssessmentCreated={setAssessmentId}
        />
      )}
    </div>
  );
}
