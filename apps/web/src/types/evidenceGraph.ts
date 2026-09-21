/**
 * TypeScript interface definitions for ecological evidence knowledge graph visualization
 * and citation linkage.
 */

export interface GraphNodeData {
  id: string;
  label: string;
  category: "driver" | "state" | "impact" | "response" | "indicator" | "intervention";
  description?: string;
  evidenceCount?: number;
  confidenceScore?: number;
  metadata?: Record<string, unknown>;
}

export interface GraphEdgeData {
  id: string;
  source: string;
  target: string;
  relationshipType: "increases" | "decreases" | "modulates" | "buffers" | "correlated";
  strength: "strong" | "moderate" | "weak" | "hypothesis";
  citationsCount?: number;
  sourceIds?: string[];
}

export interface EvidenceCitationBadge {
  sourceId: string;
  title: string;
  doi?: string;
  year?: number;
  authors?: string[];
  relevanceScore: number;
  excerptSnippet: string;
}

export interface GraphFilterState {
  searchQuery: string;
  selectedCategories: string[];
  minConfidence: number;
  highlightedNodeId: string | null;
  onlyWithEvidence: boolean;
}
