import { useQuery } from "@tanstack/react-query";
import { api } from "../../lib/api";
import { Card, LoadingState } from "../../components/ui";
import type { ClarifyingQuestion } from "../../types/api";

const FIELD_LABELS: Record<string, string> = {
  region: "Region",
  ecosystem_type: "Ecosystem type",
  land_use_type: "Land use",
  soil_ph: "Soil pH",
  soil_organic_carbon: "Soil organic carbon (%)",
  soil_moisture: "Soil moisture (%)",
  rainfall_mm_year: "Rainfall (mm/year)",
  rainfall_qualitative: "Rainfall (qualitative)",
  temperature_c: "Temperature (°C)",
};

export default function ProfilePanel({
  profileId,
  clarifyingQuestions,
  completeness,
}: {
  profileId: string;
  clarifyingQuestions: ClarifyingQuestion[];
  completeness: number | null;
}) {
  const { data: profile, isLoading } = useQuery({
    queryKey: ["profile", profileId],
    queryFn: () => api.getProfile(profileId),
  });

  return (
    <Card title="Environmental profile">
      {isLoading && <LoadingState message="Loading profile..." />}
      {profile && (
        <div className="space-y-4">
          {completeness !== null && (
            <div>
              <div className="flex justify-between text-xs text-stone-500 mb-1">
                <span>Profile completeness</span>
                <span>{Math.round(completeness * 100)}%</span>
              </div>
              <div className="h-2 bg-stone-100 rounded-full overflow-hidden">
                <div className="h-full bg-eco-500" style={{ width: `${Math.round(completeness * 100)}%` }} />
              </div>
            </div>
          )}

          <dl className="grid grid-cols-2 gap-x-3 gap-y-2 text-sm">
            {Object.entries(FIELD_LABELS).map(([key, label]) => {
              const value = (profile as unknown as Record<string, unknown>)[key];
              return (
                <div key={key}>
                  <dt className="text-stone-500 text-xs">{label}</dt>
                  <dd className={value === null || value === undefined ? "text-stone-400 italic" : "font-medium"}>
                    {value === null || value === undefined ? "unknown" : String(value)}
                  </dd>
                </div>
              );
            })}
          </dl>

          {Object.keys(profile.biodiversity_indicators).length > 0 && (
            <div>
              <div className="text-xs text-stone-500 mb-1">Biodiversity indicators (reported)</div>
              <pre className="text-xs bg-stone-50 rounded-lg p-2 overflow-x-auto">
                {JSON.stringify(profile.biodiversity_indicators, null, 2)}
              </pre>
            </div>
          )}
          {Object.keys(profile.human_impact_indicators).length > 0 && (
            <div>
              <div className="text-xs text-stone-500 mb-1">Human impact indicators (reported)</div>
              <pre className="text-xs bg-stone-50 rounded-lg p-2 overflow-x-auto">
                {JSON.stringify(profile.human_impact_indicators, null, 2)}
              </pre>
            </div>
          )}

          {clarifyingQuestions.length > 0 && (
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
              <div className="text-xs font-medium text-amber-800 mb-1">Missing information</div>
              <ul className="text-sm text-amber-900 space-y-1 list-disc list-inside">
                {clarifyingQuestions.map((q) => (
                  <li key={q.field}>{q.question}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </Card>
  );
}
