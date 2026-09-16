import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { ConfidenceBadge, EmptyState, ErrorState, EvidenceStatusBadge, LoadingState } from "./ui";

describe("ui primitives", () => {
  it("renders confidence level text", () => {
    render(<ConfidenceBadge level="low" />);
    expect(screen.getByText(/low confidence/i)).toBeInTheDocument();
  });

  it("renders evidence status with underscores replaced", () => {
    render(<EvidenceStatusBadge status="partially_supported" />);
    expect(screen.getByText("partially supported")).toBeInTheDocument();
  });

  it("renders empty state message", () => {
    render(<EmptyState message="Nothing here yet" />);
    expect(screen.getByText("Nothing here yet")).toBeInTheDocument();
  });

  it("renders loading state message", () => {
    render(<LoadingState message="Please wait" />);
    expect(screen.getByText("Please wait")).toBeInTheDocument();
  });

  it("renders error state message", () => {
    render(<ErrorState message="Something broke" />);
    expect(screen.getByText("Something broke")).toBeInTheDocument();
  });
});
