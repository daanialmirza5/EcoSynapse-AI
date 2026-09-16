import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

interface WorkspaceState {
  conversationId: string | null;
  profileId: string | null;
  assessmentId: string | null;
  setConversationId: (id: string | null) => void;
  setProfileId: (id: string | null) => void;
  setAssessmentId: (id: string | null) => void;
}

const WorkspaceContext = createContext<WorkspaceState | null>(null);

const STORAGE_KEY = "ecosynapse.workspace.v1";

function loadInitial() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return JSON.parse(raw);
  } catch {
    /* ignore */
  }
  return { conversationId: null, profileId: null, assessmentId: null };
}

export function WorkspaceProvider({ children }: { children: ReactNode }) {
  const initial = loadInitial();
  const [conversationId, setConversationId] = useState<string | null>(initial.conversationId);
  const [profileId, setProfileId] = useState<string | null>(initial.profileId);
  const [assessmentId, setAssessmentId] = useState<string | null>(initial.assessmentId);

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({ conversationId, profileId, assessmentId }));
    } catch {
      /* private browsing / storage unavailable: non-fatal, state stays in-memory only */
    }
  }, [conversationId, profileId, assessmentId]);

  return (
    <WorkspaceContext.Provider
      value={{ conversationId, profileId, assessmentId, setConversationId, setProfileId, setAssessmentId }}
    >
      {children}
    </WorkspaceContext.Provider>
  );
}

export function useWorkspace() {
  const ctx = useContext(WorkspaceContext);
  if (!ctx) throw new Error("useWorkspace must be used within WorkspaceProvider");
  return ctx;
}
