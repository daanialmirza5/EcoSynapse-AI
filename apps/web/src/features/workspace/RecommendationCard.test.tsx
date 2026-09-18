import { describe, expect, it } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import RecommendationCard from "./RecommendationCard";
import type { ReasoningPath, RecommendationOut } from "../../types/api";

const sampleRec: RecommendationOut = {
  id: "rec-1",
  intervention_id: "crop_diversification_intercropping",
  title: "Crop diversification / intercropping",
  what_to_do: "Grow two crops together.",
  why_it_may_work: "Intercropping increases beneficial arthropod abundance.",
  impacted_metrics: ["beneficial_arthropod_abundance", "species_richness"],
  time_horizon: "short",
  feasibility_constraints: [],
  trade_offs: ["Meta-analytic average effect; magnitude varies."],
  confidence: { level: "medium", reason: "Average supporting evidence strength is moderate." },
  evidence_strength_summary: "moderate",
  data_completeness: 0.56,
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

const samplePaths: ReasoningPath[] = [
  {
    variables: ["monoculture_land_use", "declining_biodiversity", "crop_diversification_intercropping"],
    steps: [
      {
        from_node: "crop_diversification_intercropping",
        relation: "may_improve",
        to_node: "beneficial_arthropod_abundance",
        evidence_strength: "moderate",
        source_claim_id: "claim-1",
      },
    ],
    narrative:
      "Detected concern(s) [monoculture_land_use, declining_biodiversity] relate to candidate intervention 'Crop diversification / intercropping', which is linked in the knowledge graph to: beneficial_arthropod_abundance.",
  },
];

describe("RecommendationCard", () => {
  it("shows a 'Why this recommendation?' drill-down grounded in the real reasoning path", () => {
    render(<RecommendationCard rec={sampleRec} reasoningPaths={samplePaths} />);
    fireEvent.click(screen.getByText(/Why this recommendation\?/i));
    expect(screen.getByText(/Because these conditions were detected/i)).toBeInTheDocument();
    expect(screen.getByText(/monoculture land use/i)).toBeInTheDocument();
    expect(screen.getAllByText(/Grow two crops together\./).length).toBeGreaterThanOrEqual(1);
  });

  it("does not show the 'Why this recommendation?' drill-down when no matching path exists", () => {
    render(<RecommendationCard rec={sampleRec} reasoningPaths={[]} />);
    expect(screen.queryByText(/Why this recommendation\?/i)).not.toBeInTheDocument();
  });

  it("renders the recommendation summary by default, evidence hidden", () => {
    render(<RecommendationCard rec={sampleRec} />);
    expect(screen.getByText(sampleRec.title)).toBeInTheDocument();
    expect(screen.getByText(/medium confidence/i)).toBeInTheDocument();
    expect(screen.queryByText(/Claim-level evidence/i)).not.toBeInTheDocument();
  });

  it("reports confidence, evidence strength, and data completeness as distinct values", () => {
    render(<RecommendationCard rec={sampleRec} />);
    expect(screen.getByText(/medium confidence/i)).toBeInTheDocument();
    expect(screen.getByText(/evidence: moderate/i)).toBeInTheDocument();
    expect(screen.getByText(/56%/)).toBeInTheDocument();
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
