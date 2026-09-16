import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../lib/api";
import { useWorkspace } from "../hooks/useWorkspaceState";
import { Card, EmptyState, ErrorState, LoadingState } from "../components/ui";
import type { EnvironmentalProfile } from "../types/api";

const NUMERIC_FIELDS: (keyof EnvironmentalProfile)[] = [
  "soil_ph", "soil_organic_carbon", "soil_moisture", "rainfall_mm_year", "temperature_c",
];
const TEXT_FIELDS: (keyof EnvironmentalProfile)[] = ["name", "region", "ecosystem_type", "land_use_type", "rainfall_qualitative"];

export default function ProfileEditor() {
  const { profileId, setProfileId } = useWorkspace();
  const queryClient = useQueryClient();
  const [form, setForm] = useState<Record<string, string>>({});
  const [jsonDraft, setJsonDraft] = useState("");
  const [jsonError, setJsonError] = useState<string | null>(null);

  const { data: profile, isLoading } = useQuery({
    queryKey: ["profile", profileId],
    queryFn: () => api.getProfile(profileId!),
    enabled: !!profileId,
  });

  useEffect(() => {
    if (profile) {
      const initial: Record<string, string> = {};
      [...NUMERIC_FIELDS, ...TEXT_FIELDS].forEach((f) => {
        const v = (profile as unknown as Record<string, unknown>)[f];
        initial[f as string] = v === null || v === undefined ? "" : String(v);
      });
      setForm(initial);
    }
  }, [profile]);

  const save = useMutation({
    mutationFn: () => {
      const payload: Record<string, unknown> = {};
      NUMERIC_FIELDS.forEach((f) => {
        const raw = form[f as string];
        payload[f as string] = raw === "" ? null : Number(raw);
      });
      TEXT_FIELDS.forEach((f) => {
        payload[f as string] = form[f as string] || null;
      });
      return api.updateProfile(profileId!, payload);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["profile", profileId] }),
  });

  const createFromJson = useMutation({
    mutationFn: async () => {
      const parsed = JSON.parse(jsonDraft);
      return api.createProfile(parsed);
    },
    onSuccess: (p) => {
      setProfileId(p.id);
      setJsonError(null);
    },
    onError: (e) => setJsonError(e instanceof Error ? e.message : "Invalid JSON"),
  });

  const createBlank = useMutation({
    mutationFn: () => api.createProfile({ name: "New land profile" }),
    onSuccess: (p) => setProfileId(p.id),
  });

  return (
    <div className="p-4 md:p-6 max-w-5xl mx-auto space-y-4">
      <div>
        <h1 className="text-xl font-semibold text-stone-900">Environmental profile editor</h1>
        <p className="text-sm text-stone-600">
          Directly edit the structured profile, or paste a JSON payload matching the EnvironmentalProfile schema.
        </p>
      </div>

      {!profileId && (
        <Card title="No active profile">
          <button className="text-sm bg-eco-600 text-white px-3 py-1.5 rounded-lg" onClick={() => createBlank.mutate()}>
            Create a blank profile
          </button>
        </Card>
      )}

      {profileId && isLoading && <LoadingState message="Loading profile..." />}

      {profileId && profile && (
        <Card
          title={`Editing: ${profile.name}`}
          actions={
            <button
              className="text-sm bg-eco-600 text-white px-3 py-1.5 rounded-lg disabled:opacity-50"
              onClick={() => save.mutate()}
              disabled={save.isPending}
            >
              {save.isPending ? "Saving..." : "Save changes"}
            </button>
          }
        >
          <div className="grid md:grid-cols-2 gap-3">
            {TEXT_FIELDS.map((f) => (
              <label key={f as string} className="text-sm">
                <span className="text-stone-500 text-xs block mb-1">{(f as string).replace(/_/g, " ")}</span>
                <input
                  className="w-full border border-stone-300 rounded-lg px-2.5 py-1.5"
                  value={form[f as string] || ""}
                  onChange={(e) => setForm((s) => ({ ...s, [f as string]: e.target.value }))}
                />
              </label>
            ))}
            {NUMERIC_FIELDS.map((f) => (
              <label key={f as string} className="text-sm">
                <span className="text-stone-500 text-xs block mb-1">{(f as string).replace(/_/g, " ")}</span>
                <input
                  type="number"
                  step="any"
                  className="w-full border border-stone-300 rounded-lg px-2.5 py-1.5"
                  value={form[f as string] || ""}
                  onChange={(e) => setForm((s) => ({ ...s, [f as string]: e.target.value }))}
                />
              </label>
            ))}
          </div>
          {profile.missing_fields.length > 0 && (
            <div className="mt-3 text-xs text-stone-500">
              Still missing: {profile.missing_fields.join(", ")}
            </div>
          )}
        </Card>
      )}

      <Card title="Load from JSON">
        <textarea
          className="w-full h-40 border border-stone-300 rounded-lg p-2.5 text-xs font-mono"
          placeholder='{"name": "Semi-arid wheat plot", "ecosystem_type": "semi-arid", "land_use_type": "monoculture wheat cropland", "soil_organic_carbon": 0.3, "rainfall_qualitative": "low"}'
          value={jsonDraft}
          onChange={(e) => setJsonDraft(e.target.value)}
        />
        {jsonError && <div className="mt-2"><ErrorState message={jsonError} /></div>}
        <button
          className="mt-2 text-sm bg-eco-600 text-white px-3 py-1.5 rounded-lg disabled:opacity-50"
          onClick={() => createFromJson.mutate()}
          disabled={!jsonDraft.trim() || createFromJson.isPending}
        >
          Create profile from JSON
        </button>
      </Card>

      {!profileId && !profile && <EmptyState message="Create or load a profile to begin editing." />}
    </div>
  );
}
