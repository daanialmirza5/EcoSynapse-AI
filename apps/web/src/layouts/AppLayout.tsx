import { NavLink, Outlet } from "react-router-dom";

const NAV_ITEMS = [
  { to: "/", label: "Overview", end: true },
  { to: "/workspace", label: "Assessment Workspace" },
  { to: "/profile", label: "Profile Editor" },
  { to: "/evidence", label: "Evidence Explorer" },
  { to: "/graph", label: "Knowledge Graph" },
  { to: "/compare", label: "Recommendation Comparison" },
  { to: "/monitoring", label: "Monitoring Dashboard" },
  { to: "/import", label: "Data Import" },
  { to: "/status", label: "System Status" },
  { to: "/docs", label: "Methodology" },
];

export default function AppLayout() {
  return (
    <div className="min-h-screen flex flex-col md:flex-row">
      <aside className="md:w-64 shrink-0 bg-eco-900 text-eco-50 md:min-h-screen">
        <div className="p-5 border-b border-eco-800">
          <div className="font-semibold text-lg tracking-tight">EcoSynapse AI</div>
          <div className="text-xs text-eco-200 mt-1">Evidence-grounded ecological intelligence</div>
        </div>
        <nav className="p-3 flex flex-row md:flex-col gap-1 overflow-x-auto md:overflow-visible">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                `whitespace-nowrap px-3 py-2 rounded-lg text-sm transition-colors ${
                  isActive ? "bg-eco-700 text-white" : "text-eco-100 hover:bg-eco-800"
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <main className="flex-1 min-w-0 bg-stone-50">
        <Outlet />
      </main>
    </div>
  );
}
