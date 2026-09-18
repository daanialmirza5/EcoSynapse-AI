import type {
  AssessmentOut,
  ConversationOut,
  ConversationTurnResponse,
  EnvironmentalProfile,
  HealthStatus,
  KnowledgeGraphOut,
  MessageOut,
  RetrievalTrace,
  ScientificSourceOut,
} from "../types/api";

// In local dev and same-origin deployments (Docker Compose's nginx proxy),
// leaving this empty keeps requests relative and works via the dev-server
// proxy / nginx location blocks. For a split deployment (e.g. a Vercel
// frontend calling a separately-hosted Railway backend), set
// VITE_API_BASE_URL at build time to the backend's full origin
// (e.g. https://ecosynapse-api.up.railway.app) -- see docs/deployment.md.
const API_ROOT = (
  import.meta.env.VITE_API_BASE_URL ||
  (typeof window !== "undefined" && window.location.hostname !== "localhost" && window.location.hostname !== "127.0.0.1"
    ? "https://ecosynapse-ai.onrender.com"
    : "")
).replace(/\/$/, "");
const API_BASE = `${API_ROOT}/api/v1`;

class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit, absolute = false): Promise<T> {
  const resp = await fetch(absolute ? path : `${API_BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
  });
  if (!resp.ok) {
    let detail = resp.statusText;
    try {
      const body = await resp.json();
      detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    } catch {
      /* ignore parse error */
    }
    throw new ApiError(resp.status, detail || "Request failed");
  }
  if (resp.status === 204) return undefined as T;
  return resp.json();
}

export const api = {
  health: () => request<HealthStatus>(`${API_ROOT}/health`, undefined, true),

  createConversation: (title?: string) =>
    request<ConversationOut>("/conversations", { method: "POST", body: JSON.stringify({ title }) }),
  listConversations: () => request<ConversationOut[]>("/conversations"),
  getConversation: (id: string) => request<ConversationOut>(`/conversations/${id}`),
  listMessages: (id: string) => request<MessageOut[]>(`/conversations/${id}/messages`),
  postMessage: (id: string, content: string, structuredInput?: Record<string, unknown>) =>
    request<ConversationTurnResponse>(`/conversations/${id}/messages`, {
      method: "POST",
      body: JSON.stringify({ content, structured_input: structuredInput }),
    }),

  createProfile: (payload: Partial<EnvironmentalProfile>) =>
    request<EnvironmentalProfile>("/profiles", { method: "POST", body: JSON.stringify(payload) }),
  getProfile: (id: string) => request<EnvironmentalProfile>(`/profiles/${id}`),
  updateProfile: (id: string, payload: Partial<EnvironmentalProfile>) =>
    request<EnvironmentalProfile>(`/profiles/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
  addObservation: (
    id: string,
    payload: { metric: string; value: number; unit?: string; source?: string; confidence?: string; notes?: string }
  ) => request(`/profiles/${id}/observations`, { method: "POST", body: JSON.stringify(payload) }),
  listObservations: (id: string) => request(`/profiles/${id}/observations`),

  createAssessment: (profileId: string, conversationId?: string) =>
    request<AssessmentOut>("/assessments", {
      method: "POST",
      body: JSON.stringify({ profile_id: profileId, conversation_id: conversationId }),
    }),
  getAssessment: (id: string) => request<AssessmentOut>(`/assessments/${id}`),
  reassess: (id: string) => request<AssessmentOut>(`/assessments/${id}/reassess`, { method: "POST" }),
  exportAssessmentUrl: (id: string) => `${API_BASE}/assessments/${id}/export`,

  listSources: () => request<ScientificSourceOut[]>("/knowledge/sources"),
  getSource: (id: string) => request<ScientificSourceOut>(`/knowledge/sources/${id}`),
  getKnowledgeGraph: () => request<KnowledgeGraphOut>("/knowledge/graph"),
  inspectRetrieval: (query: string, profileId?: string, topK = 6) =>
    request<RetrievalTrace>("/retrieval/inspect", {
      method: "POST",
      body: JSON.stringify({ query, profile_id: profileId, top_k: topK }),
    }),
  ingestSource: (payload: Record<string, unknown>) =>
    request<{ source_id: string; chunk_count: number; warnings: string[] }>("/knowledge/ingest", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
};

export { ApiError };
