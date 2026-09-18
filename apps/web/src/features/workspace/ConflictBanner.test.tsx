import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import ConflictBanner from "./ConflictBanner";

describe("ConflictBanner", () => {
  it("renders nothing when there are no conflicts", () => {
    const { container } = render(<ConflictBanner conflicts={[]} hasExistingAssessment={false} />);
    expect(container).toBeEmptyDOMElement();
  });

  it("shows previous and new values and which one is now used", () => {
    render(
      <ConflictBanner
        conflicts={[{ field: "rainfall_qualitative", previous_value: "low", new_value: "high" }]}
        hasExistingAssessment={false}
      />
    );
    expect(screen.getByText("Conflict detected")).toBeInTheDocument();
    expect(screen.getByText("low")).toBeInTheDocument();
    expect(screen.getAllByText("high").length).toBeGreaterThanOrEqual(1);
  });

  it("prompts reassessment when an assessment already exists", () => {
    render(
      <ConflictBanner
        conflicts={[{ field: "soil_ph", previous_value: 6.5, new_value: 8.0 }]}
        hasExistingAssessment={true}
      />
    );
    expect(screen.getByText(/Reassess/)).toBeInTheDocument();
  });
});
