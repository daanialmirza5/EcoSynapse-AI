import { Route, Routes } from "react-router-dom";
import AppLayout from "./layouts/AppLayout";
import { WorkspaceProvider } from "./hooks/useWorkspaceState";
import Overview from "./pages/Overview";
import Workspace from "./pages/Workspace";
import ProfileEditor from "./pages/ProfileEditor";
import EvidenceExplorer from "./pages/EvidenceExplorer";
import KnowledgeGraphExplorer from "./pages/KnowledgeGraphExplorer";
import RecommendationComparison from "./pages/RecommendationComparison";
import MonitoringDashboard from "./pages/MonitoringDashboard";
import DataImport from "./pages/DataImport";
import SystemStatus from "./pages/SystemStatus";
import Methodology from "./pages/Methodology";

export default function App() {
  return (
    <WorkspaceProvider>
      <Routes>
        <Route element={<AppLayout />}>
          <Route path="/" element={<Overview />} />
          <Route path="/workspace" element={<Workspace />} />
          <Route path="/profile" element={<ProfileEditor />} />
          <Route path="/evidence" element={<EvidenceExplorer />} />
          <Route path="/graph" element={<KnowledgeGraphExplorer />} />
          <Route path="/compare" element={<RecommendationComparison />} />
          <Route path="/monitoring" element={<MonitoringDashboard />} />
          <Route path="/import" element={<DataImport />} />
          <Route path="/status" element={<SystemStatus />} />
          <Route path="/docs" element={<Methodology />} />
        </Route>
      </Routes>
    </WorkspaceProvider>
  );
}
