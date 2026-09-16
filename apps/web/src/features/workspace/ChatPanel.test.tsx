import { describe, expect, it, vi, beforeEach } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import { renderWithQuery } from "../../test/testUtils";
import ChatPanel from "./ChatPanel";
import { api } from "../../lib/api";

vi.mock("../../lib/api", () => ({
  api: {
    listMessages: vi.fn(),
    postMessage: vi.fn(),
  },
}));

describe("ChatPanel", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows an empty-state prompt with a demo-scenario shortcut when there are no messages", async () => {
    vi.mocked(api.listMessages).mockResolvedValue([]);
    renderWithQuery(<ChatPanel conversationId="conv-1" onTurn={() => {}} />);
    await waitFor(() => expect(screen.getByText(/load the challenge demo scenario/i)).toBeInTheDocument());
  });

  it("renders existing messages by role", async () => {
    vi.mocked(api.listMessages).mockResolvedValue([
      {
        id: "m1",
        conversation_id: "conv-1",
        role: "user",
        content: "Biodiversity is declining.",
        structured_metadata: {},
        created_at: new Date().toISOString(),
      },
    ]);
    renderWithQuery(<ChatPanel conversationId="conv-1" onTurn={() => {}} />);
    await waitFor(() => expect(screen.getByText("Biodiversity is declining.")).toBeInTheDocument());
  });

  it("handles a failed listMessages call without crashing (API error handling)", async () => {
    vi.mocked(api.listMessages).mockRejectedValue(new Error("network down"));
    renderWithQuery(<ChatPanel conversationId="conv-1" onTurn={() => {}} />);
    await waitFor(() => expect(screen.queryByText(/Loading conversation/i)).not.toBeInTheDocument());
  });
});
