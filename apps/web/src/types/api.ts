export interface ConversationOut {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface MessageOut {
  id: string;
  conversation_id: string;
  role: "user" | "assistant" | "system";
  content: string;
  structured_metadata: Record<string, unknown>;
  created_at: string;
}

export interface ClarifyingQuestion {
  field: string;
  question: string;
  reason: string;
  priority: number;
}

export interface ConversationTurnResponse {
  conversation_id: string;
  profile_id: string;
  assistant_message: MessageOut;
  clarifying_questions: ClarifyingQuestion[];
  profile_completeness: number;
  extracted_fields: Record<string, unknown>;
  conflicts: { field: string; previous_value: unknown; new_value: unknown }[];
  ready_for_assessment: boolean;
}

export interface EnvironmentalProfile {
  id: string;
  conversation_id: string | null;
  name: string;
  region: string | null;
  latitude: number | null;
  longitude: number | null;
  ecosystem_type: string | null;
  land_use_type: string | null;
  soil_ph: number | null;
  soil_organic_carbon: number | null;
  soil_moisture: number | null;
  rainfall_mm_year: number | null;
  rainfall_qualitative: string | null;
  temperature_c: number | null;
  biodiversity_indicators: Record<string, unknown>;
  human_impact_indicators: Record<string, unknown>;
  constraints: string[];
  data_source: string | null;
  unit_metadata: Record<string, unknown>;
  missing_fields: string[];
  uncertainty_metadata: Record<string, unknown>;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface ScientificSourceOut {
  id: string;
  title: string;
  authors: string[];
  organization: string | null;
  publication_year: number | null;
  doi: string | null;
  url: string | null;
  source_type: string;
  abstract: string | null;
  full_text_available: boolean;
  is_verified: boolean;
  ecosystem_context: string[];
  limitations: string | null;
}

export interface RetrievedEvidenceItem {
  chunk_id: string;
  source: ScientificSourceOut;
  excerpt: string;
  relevance_score: number;
  match_reasons: string[];
}

export interface RetrievalTrace {
  query: string;
  expanded_terms: string[];
  graph_concepts: string[];
  semantic_candidates: number;
  lexical_candidates: number;
  merged_candidates: number;
  results: RetrievedEvidenceItem[];
}

export interface KnowledgeNodeOut {
  id: string;
  node_type: string;
  canonical_name: string;
  description: string | null;
}

export interface KnowledgeEdgeOut {
  id: string;
  source_node_id: string;
  target_node_id: string;
  relation_type: string;
  mechanism: string | null;
  evidence_strength: string;
  limitations: string | null;
  source_claim_id: string | null;
}

export interface KnowledgeGraphOut {
  nodes: KnowledgeNodeOut[];
  edges: KnowledgeEdgeOut[];
}

export interface EvidenceRef {
  claim: string;
  claim_type: string;
  source_id: string | null;
  source_title: string | null;
  citation: string | null;
  excerpt: string | null;
  limitations: string | null;
  evidence_status: string;
  applicability_note?: string | null;
}

export interface MonitoringPlanItem {
  metric: string;
  baseline_requirement: string;
  target: string | null;
  measurement_method: string;
  measurement_frequency: string;
  time_horizon: "short" | "medium" | "long";
  unit: string | null;
  expected_direction: string | null;
  success_criteria: string | null;
  uncertainty: string | null;
}

export interface RecommendationOut {
  id: string;
  title: string;
  what_to_do: string;
  why_it_may_work: string;
  impacted_metrics: string[];
  time_horizon: "short" | "medium" | "long";
  feasibility_constraints: string[];
  trade_offs: string[];
  confidence: { level: "low" | "medium" | "high"; reason: string };
  evidence: EvidenceRef[];
  monitoring_plan: MonitoringPlanItem[];
  heuristic_score: {
    label: string;
    disclaimer: string;
    weights: Record<string, number>;
    components: Record<string, number>;
    total: number;
  };
}

export interface ReasoningPathStep {
  from_node: string;
  relation: string;
  to_node: string;
  evidence_strength: string;
  source_claim_id: string | null;
}

export interface ReasoningPath {
  variables: string[];
  steps: ReasoningPathStep[];
  narrative: string;
}

export interface AssessmentOut {
  id: string;
  conversation_id: string | null;
  profile_id: string;
  version: number;
  assessment_summary: string;
  known_facts: { field: string; value: unknown; unit: string | null; source: string }[];
  unknowns: string[];
  variables_considered: string[];
  reasoning_paths: ReasoningPath[];
  recommendations: RecommendationOut[];
  overall_limitations: string[];
  diff_from_previous: Record<string, unknown>[];
  created_at: string;
}

export interface HealthStatus {
  status: string;
  app: string;
  environment: string;
  database: string;
  llm_provider: string;
  embedding_provider: string;
  knowledge_base: { sources: number; graph_nodes: number; graph_edges: number };
}
