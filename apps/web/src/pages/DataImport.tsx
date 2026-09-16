import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { api } from "../lib/api";
import { Card, ErrorState } from "../components/ui";

export default function DataImport() {
  const [title, setTitle] = useState("");
  const [text, setText] = useState("");
  const [organization, setOrganization] = useState("");
  const [url, setUrl] = useState("");
  const [doi, setDoi] = useState("");
  const [year, setYear] = useState("");
  const [isVerified, setIsVerified] = useState(false);

  const ingest = useMutation({
    mutationFn: () =>
      api.ingestSource({
        title,
        text: text || null,
        organization: organization || null,
        url: url || null,
        doi: doi || null,
        publication_year: year ? Number(year) : null,
        source_type: "user_uploaded",
        is_verified: isVerified,
      }),
  });

  return (
    <div className="p-4 md:p-6 max-w-3xl mx-auto space-y-4">
      <div>
        <h1 className="text-xl font-semibold text-stone-900">Data import: knowledge ingestion</h1>
        <p className="text-sm text-stone-600">
          Add a document, report, or dataset abstract to the evidence store. It will be chunked and embedded for
          retrieval. Sources you add here are marked <strong>unverified</strong> by default &mdash; distinct from the
          curated, verified seed corpus &mdash; until you explicitly confirm verification.
        </p>
      </div>

      <Card title="New source">
        <div className="space-y-3">
          <label className="text-sm block">
            <span className="block text-xs text-stone-500 mb-1">Title *</span>
            <input className="w-full border border-stone-300 rounded-lg px-2.5 py-1.5" value={title} onChange={(e) => setTitle(e.target.value)} />
          </label>
          <div className="grid md:grid-cols-3 gap-3">
            <label className="text-sm block">
              <span className="block text-xs text-stone-500 mb-1">Organization / authors</span>
              <input className="w-full border border-stone-300 rounded-lg px-2.5 py-1.5" value={organization} onChange={(e) => setOrganization(e.target.value)} />
            </label>
            <label className="text-sm block">
              <span className="block text-xs text-stone-500 mb-1">Year</span>
              <input type="number" className="w-full border border-stone-300 rounded-lg px-2.5 py-1.5" value={year} onChange={(e) => setYear(e.target.value)} />
            </label>
            <label className="text-sm block">
              <span className="block text-xs text-stone-500 mb-1">DOI</span>
              <input className="w-full border border-stone-300 rounded-lg px-2.5 py-1.5" value={doi} onChange={(e) => setDoi(e.target.value)} />
            </label>
          </div>
          <label className="text-sm block">
            <span className="block text-xs text-stone-500 mb-1">URL</span>
            <input className="w-full border border-stone-300 rounded-lg px-2.5 py-1.5" value={url} onChange={(e) => setUrl(e.target.value)} />
          </label>
          <label className="text-sm block">
            <span className="block text-xs text-stone-500 mb-1">Text / abstract</span>
            <textarea className="w-full h-32 border border-stone-300 rounded-lg px-2.5 py-1.5 text-sm" value={text} onChange={(e) => setText(e.target.value)} />
          </label>
          <label className="text-sm flex items-center gap-2">
            <input type="checkbox" checked={isVerified} onChange={(e) => setIsVerified(e.target.checked)} />
            I have personally verified this citation is accurate
          </label>

          {ingest.isError && <ErrorState message="Ingestion failed. Check the fields above." />}
          {ingest.data && (
            <div className="bg-eco-50 border border-eco-200 rounded-lg p-3 text-sm text-eco-800">
              Ingested source {ingest.data.source_id} with {ingest.data.chunk_count} evidence chunk(s).
              {ingest.data.warnings.length > 0 && (
                <ul className="list-disc list-inside mt-1 text-xs">
                  {ingest.data.warnings.map((w: string, i: number) => <li key={i}>{w}</li>)}
                </ul>
              )}
            </div>
          )}

          <button
            className="bg-eco-600 text-white text-sm px-4 py-2 rounded-lg disabled:opacity-50"
            onClick={() => ingest.mutate()}
            disabled={!title.trim() || ingest.isPending}
          >
            {ingest.isPending ? "Ingesting..." : "Ingest source"}
          </button>
        </div>
      </Card>
    </div>
  );
}
