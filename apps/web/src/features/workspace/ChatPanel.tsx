import { useEffect, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../../lib/api";
import { Card, LoadingState } from "../../components/ui";
import type { ConversationTurnResponse } from "../../types/api";

const DEMO_MESSAGE =
  "It is a semi-arid region with monoculture wheat cropland, low rainfall, soil organic carbon 0.3%, and pollinators seem to be declining.";

export default function ChatPanel({
  conversationId,
  onTurn,
}: {
  conversationId: string;
  onTurn: (turn: ConversationTurnResponse) => void;
}) {
  const queryClient = useQueryClient();
  const [draft, setDraft] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  const { data: messages, isLoading } = useQuery({
    queryKey: ["messages", conversationId],
    queryFn: () => api.listMessages(conversationId),
  });

  const send = useMutation({
    mutationFn: (content: string) => api.postMessage(conversationId, content),
    onSuccess: (turn) => {
      queryClient.invalidateQueries({ queryKey: ["messages", conversationId] });
      onTurn(turn);
      setDraft("");
    },
  });

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <Card title="Conversational assistant">
      <div className="flex flex-col h-[420px]">
        <div className="flex-1 overflow-y-auto space-y-3 pr-1">
          {isLoading && <LoadingState message="Loading conversation..." />}
          {messages?.length === 0 && (
            <div className="text-sm text-stone-500">
              Describe your land or biodiversity concern in plain language, or{" "}
              <button
                className="text-eco-700 underline"
                onClick={() => send.mutate(DEMO_MESSAGE)}
                disabled={send.isPending}
              >
                load the challenge demo scenario
              </button>
              .
            </div>
          )}
          {messages?.map((m) => (
            <div key={m.id} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
              <div
                className={`max-w-[85%] rounded-xl px-3 py-2 text-sm whitespace-pre-wrap ${
                  m.role === "user" ? "bg-eco-600 text-white" : "bg-stone-100 text-stone-800"
                }`}
              >
                {m.content}
              </div>
            </div>
          ))}
          <div ref={bottomRef} />
        </div>
        <form
          className="mt-3 flex gap-2"
          onSubmit={(e) => {
            e.preventDefault();
            if (draft.trim()) send.mutate(draft.trim());
          }}
        >
          <input
            className="flex-1 border border-stone-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-eco-400"
            placeholder="e.g. Biodiversity is declining on my land..."
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            disabled={send.isPending}
          />
          <button
            type="submit"
            className="bg-eco-600 text-white text-sm px-4 py-2 rounded-lg disabled:opacity-50"
            disabled={send.isPending || !draft.trim()}
          >
            {send.isPending ? "Sending..." : "Send"}
          </button>
        </form>
      </div>
    </Card>
  );
}
