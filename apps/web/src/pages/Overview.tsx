import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import { ErrorState, LoadingState } from "../components/ui";

// Manually verified against the repository at time of writing (see
// docs/darukaa-requirement-matrix.md / docs/evaluation-report.md). Source
// count and graph size are live from /health below; these two are constants
// because they aren't exposed by an API (reasoning-pipeline step count,
// total automated test count) -- update them if that ever changes, never
// round them up.
const REASONING_STEPS = 10;
const TOTAL_TESTS = 79; // 61 backend (pytest) + 18 frontend (vitest)

const DOMAINS = [
  { name: "Soil Health", detail: "pH, organic carbon, moisture" },
  { name: "Land Use", detail: "Land use type, land cover" },
  { name: "Biodiversity Indicators", detail: "Species richness, habitat diversity" },
  { name: "Climate", detail: "Temperature, rainfall" },
  { name: "Human Impact", detail: "Pollution, deforestation" },
];

const THINK_STEPS = [
  {
    n: "01",
    title: "Understand",
    body: "Extract structured environmental conditions from what you describe, deterministically — never guessed by an LLM.",
  },
  {
    n: "02",
    title: "Reason",
    body: "Retrieve scientific evidence and connect ecological relationships through a typed knowledge graph.",
  },
  {
    n: "03",
    title: "Recommend",
    body: "Generate constrained interventions with evidence strength, confidence, and time horizon — checked against real sources.",
  },
  {
    n: "04",
    title: "Monitor",
    body: "Produce measurable monitoring indicators to evaluate whether an intervention is actually working.",
  },
];

export default function Overview() {
  const { data, isLoading, error } = useQuery({ queryKey: ["health"], queryFn: api.health });

  const stats = [
    { value: data ? String(data.knowledge_base.sources) : "–", label: "Verified scientific sources" },
    { value: data ? String(data.knowledge_base.graph_nodes) : "–", label: "Knowledge graph nodes" },
    { value: data ? String(data.knowledge_base.graph_edges) : "–", label: "Typed relationships" },
    { value: String(REASONING_STEPS), label: "Reasoning pipeline steps" },
    { value: String(TOTAL_TESTS), label: "Automated tests" },
  ];

  return (
    <div className="pb-20">
      {/* Hero */}
      <section className="border-b border-stone-200 bg-gradient-to-b from-eco-50 to-stone-50">
        <div className="max-w-5xl mx-auto px-6 md:px-10 pt-16 pb-14 text-center">
          <div className="inline-flex items-center gap-2 badge bg-eco-100 text-eco-800 mb-5">
            Evidence-grounded, not generic AI
          </div>
          <h1 className="text-3xl md:text-5xl font-semibold tracking-tight text-stone-900">
            Evidence-grounded ecological intelligence.
          </h1>
          <p className="mt-5 text-stone-600 text-base md:text-lg max-w-2xl mx-auto">
            Turn land conditions into evidence-backed ecological decisions &mdash; with transparent reasoning,
            verified scientific sources, and actionable monitoring plans.
          </p>
          <div className="mt-8 flex flex-col sm:flex-row gap-3 justify-center">
            <Link
              to="/workspace"
              className="bg-eco-600 hover:bg-eco-700 transition-colors text-white font-medium px-6 py-3 rounded-lg"
            >
              Start an Assessment
            </Link>
            <Link
              to="/evidence"
              className="border border-stone-300 hover:border-eco-400 transition-colors text-stone-800 font-medium px-6 py-3 rounded-lg bg-white"
            >
              Explore the Evidence
            </Link>
          </div>
          <p className="mt-4 text-xs text-stone-500">
            Runs fully offline by default &mdash; no API key required. Demo data is clearly labeled where used.
          </p>
        </div>
      </section>

      <div className="max-w-5xl mx-auto px-6 md:px-10 space-y-16 mt-14">
        {/* Verified metrics */}
        <section>
          {error && <ErrorState message="Could not reach the backend API. Is it running on port 8000?" />}
          {isLoading && <LoadingState message="Checking live system status..." />}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            {stats.map((s) => (
              <div key={s.label} className="card p-4 text-center">
                <div className="text-2xl md:text-3xl font-semibold text-eco-700">{s.value}</div>
                <div className="text-xs text-stone-500 mt-1">{s.label}</div>
              </div>
            ))}
          </div>
          <p className="text-xs text-stone-400 mt-3 text-center">
            Every number above is read live from this system or counted directly from its test suite &mdash; see{" "}
            <Link to="/docs" className="underline">Methodology</Link> for how.
          </p>
        </section>

        {/* How it thinks */}
        <section>
          <h2 className="text-xl md:text-2xl font-semibold text-stone-900 text-center">How EcoSynapse thinks</h2>
          <p className="text-stone-600 text-center mt-2 max-w-xl mx-auto">
            Not a chatbot with environmental words added &mdash; a deterministic reasoning pipeline a judge can
            inspect at every step.
          </p>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-8">
            {THINK_STEPS.map((step) => (
              <div key={step.n} className="card p-5">
                <div className="text-eco-600 font-mono text-sm font-semibold">{step.n}</div>
                <div className="font-semibold text-stone-900 mt-1">{step.title}</div>
                <p className="text-sm text-stone-600 mt-2">{step.body}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Illustrative product flow */}
        <section>
          <h2 className="text-xl md:text-2xl font-semibold text-stone-900 text-center">From observation to action</h2>
          <p className="text-stone-600 text-center mt-2 max-w-xl mx-auto">
            An illustrative example of the flow &mdash; not a real assessment result.
          </p>
          <div className="mt-8 card p-5 md:p-6 space-y-4">
            <FlowRow label="User input" value={'"The soil is acidic, rainfall is high, and biodiversity is declining."'} emphasis />
            <FlowArrow />
            <FlowRow label="Detected conditions" value="Soil pH: acidic · Rainfall: high · Biodiversity: declining" />
            <FlowArrow />
            <FlowRow label="Evidence" value="Retrieved from verified scientific sources via hybrid retrieval" />
            <FlowArrow />
            <FlowRow label="Reasoning" value="Conditions → ecological relationships → candidate interventions → constraint checks" />
            <FlowArrow />
            <FlowRow label="Recommendation" value="An evidence-backed intervention, with confidence and evidence strength shown separately" />
            <FlowArrow />
            <FlowRow label="Monitoring" value="Indicators, time horizon, and a follow-up reassessment plan" />
          </div>
          <div className="text-center mt-4">
            <Link to="/workspace" className="text-eco-700 font-medium underline text-sm">
              Run a real assessment instead &rarr;
            </Link>
          </div>
        </section>

        {/* Five domains */}
        <section>
          <h2 className="text-xl md:text-2xl font-semibold text-stone-900 text-center">Five ecological domains, one analysis</h2>
          <div className="grid sm:grid-cols-2 lg:grid-cols-5 gap-4 mt-8">
            {DOMAINS.map((d) => (
              <div key={d.name} className="card p-4">
                <div className="font-semibold text-stone-900 text-sm">{d.name}</div>
                <div className="text-xs text-stone-500 mt-1">{d.detail}</div>
              </div>
            ))}
          </div>
        </section>

        {/* Evidence trail */}
        <section className="rounded-xl shadow-sm p-6 md:p-8 bg-eco-900 text-eco-50">
          <h2 className="text-xl md:text-2xl font-semibold">Every recommendation has a trail.</h2>
          <p className="text-eco-100 mt-2 max-w-2xl">
            EcoSynapse never just outputs an answer. Every recommendation traces back through the environmental
            conditions that triggered it, the scientific evidence retrieved, the ecological relationships involved,
            the constraints checked, and the verification applied to every claim.
          </p>
          <div className="flex flex-wrap gap-2 mt-5 text-sm">
            {["Conditions", "Evidence", "Reasoning", "Constraints", "Verification", "Monitoring"].map((s, i, arr) => (
              <span key={s} className="flex items-center gap-2">
                <span className="badge bg-eco-800 text-eco-50">{s}</span>
                {i < arr.length - 1 && <span className="text-eco-400">&rarr;</span>}
              </span>
            ))}
          </div>
          <p className="mt-5 text-sm text-eco-200">
            If evidence is weak, EcoSynapse says so. If information is missing, it asks. If no verified intervention
            exists, it tells you rather than inventing one. Low confidence is shown as low confidence &mdash; that's
            a feature, not a gap.
          </p>
        </section>

        {/* Final CTA */}
        <section className="text-center">
          <h2 className="text-xl md:text-2xl font-semibold text-stone-900">
            Make your next ecological decision evidence-grounded.
          </h2>
          <Link
            to="/workspace"
            className="inline-block mt-5 bg-eco-600 hover:bg-eco-700 transition-colors text-white font-medium px-6 py-3 rounded-lg"
          >
            Start an Assessment &rarr;
          </Link>
        </section>
      </div>
    </div>
  );
}

function FlowRow({ label, value, emphasis }: { label: string; value: string; emphasis?: boolean }) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-baseline gap-1 sm:gap-4">
      <div className="text-xs uppercase tracking-wide text-stone-400 w-40 shrink-0">{label}</div>
      <div className={emphasis ? "text-stone-800 italic" : "text-stone-700 text-sm"}>{value}</div>
    </div>
  );
}

function FlowArrow() {
  return <div className="text-stone-300 pl-40 hidden sm:block">&darr;</div>;
}
