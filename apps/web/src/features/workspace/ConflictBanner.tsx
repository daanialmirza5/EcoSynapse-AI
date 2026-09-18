interface ConflictEntry {
  field: string;
  previous_value: unknown;
  new_value: unknown;
}

/**
 * Surfaces conflicting values the backend already detects
 * (app/conversations/service.py::apply_extraction_to_profile) but which
 * previously never reached the UI. The system always keeps the most
 * recently stated value (a user correction is assumed authoritative) --
 * this banner makes that overwrite visible instead of silent.
 */
export default function ConflictBanner({
  conflicts,
  hasExistingAssessment,
}: {
  conflicts: ConflictEntry[];
  hasExistingAssessment: boolean;
}) {
  if (conflicts.length === 0) return null;

  return (
    <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm space-y-2">
      <div className="font-medium text-red-800">Conflict detected</div>
      {conflicts.map((c, i) => (
        <div key={i} className="text-red-900">
          <span className="font-medium">{c.field.replace(/_/g, " ")}</span>: previous value{" "}
          <code className="bg-white/60 px-1 rounded">{String(c.previous_value)}</code> &rarr; new value{" "}
          <code className="bg-white/60 px-1 rounded">{String(c.new_value)}</code>. Current reasoning now uses{" "}
          <strong>{String(c.new_value)}</strong>.
        </div>
      ))}
      {hasExistingAssessment && (
        <div className="text-red-800 text-xs">
          This changes the environmental profile used by your existing assessment &mdash; click{" "}
          <strong>Reassess</strong> below to recalculate recommendations with the corrected value.
        </div>
      )}
    </div>
  );
}
