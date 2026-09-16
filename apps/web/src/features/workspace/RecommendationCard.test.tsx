import { describe, expect, it } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import RecommendationCard from "./RecommendationCard";
import type { RecommendationOut } from "../../types/api";

const sampleRec: RecommendationOut = {
  id: "rec-1",
  title: "Crop diversification / intercropping",
  what_to_do: "Grow two crops together.",
  why_it_may_work: "Intercropping increases beneficial arthropod abundance.",
  impacted_metrics: ["beneficial_arthropod_abundance", "species_richness"],
  time_horizon: "short",
  feasibility_constraints: [],
  trade_offs: ["Meta-analytic average effect; magnitude varies."],
  confidence: { level: "medium", reason: "Average supporting evidence strength is moderate." },
  evidence: [
    {
      claim: "Intercropping increases beneficial arthropod abundance.",
      claim_type: "source_supported",
      source_id: "src-1",
      source_title: "Intercropping meta-analysis",
      citation: "https://example.org/doi",
      excerpt: "Abundance increased by 36%.",
      limitations: "Magnitude varies by crop combination.",
      evidence_status: "supported",
    },
  ],
  monitoring_plan: [
    {
      metric: "beneficial_arthropod_abundance",
      baseline_requirement: "No baseline recorded.",
      target: "Establish a baseline first; a defensible target cannot be determined.",
      measurement_method: "Standardized trapping.",
      measurement_frequency: "Multiple times per season.",
      time_horizon: "short",
      unit: "count per trap",
      expected_direction: "increase",
      success_criteria: "Sustained increase across two cycles.",
      uncertainty: "Natural variability.",
    },
  ],
  heuristic_score: {
    label: "prototype_decision_support_heuristic",
    disclaimer: "Not a validated biodiversity index.",
    weights: { evidence_strength: 0.4, constraint_fit: 0.35, context_match: 0.25 },
    components: { evidence_strength: 0.65, constraint_fit: 1.0, context_match: 0.5 },
    total: 0.735,
  },
};

describe("RecommendationCard", () => {
  it("renders the recommendation summary by default, evidence hidden", () => {
    render(<RecommendationCard rec={sampleRec} />);
    expect(screen.getByText(sampleRec.title)).toBeInTheDocument();
    expect(screen.getByText(/medium confidence/i)).toBeInTheDocument();
    expect(screen.queryByText(/Claim-level evidence/i)).not.toBeInTheDocument();
  });

  it("never invents a numeric monitoring target when none is established", () => {
    render(<RecommendationCard rec={sampleRec} />);
    fireEvent.click(screen.getByText(/Show evidence table & monitoring plan/i));
    expect(screen.getByText(/establish a baseline first/i)).toBeInTheDocument();
  });

  it("expands to show claim-level evidence with source and status", () => {
    render(<RecommendationCard rec={sampleRec} />);
    fireEvent.click(screen.getByText(/Show evidence table & monitoring plan/i));
    expect(screen.getByText(/Claim-level evidence/i)).toBeInTheDocument();
    expect(screen.getByText(/Intercropping meta-analysis/i)).toBeInTheDocument();
    expect(screen.getByText("supported")).toBeInTheDocument();
  });

  it("labels the heuristic score as a prototype, never a validated index", () => {
    render(<RecommendationCard rec={sampleRec} />);
    fireEvent.click(screen.getByText(/Show evidence table & monitoring plan/i));
    expect(screen.getByText(/prototype only/i)).toBeInTheDocument();
    expect(screen.getByText(/Not a validated biodiversity index/i)).toBeInTheDocument();
  });
});
