import { Routes, Route } from "react-router-dom";
import Sidebar from "./components/Sidebar";
import TopBar from "./components/TopBar";
import Dashboard from "./pages/Dashboard";
import SatelliteAnalysis from "./pages/SatelliteAnalysis";
import DriftAnalysis from "./pages/DriftAnalysis";
import AisVessels from "./pages/AisVessels";
import Investigation from "./pages/Investigation";
import Reports from "./pages/Reports";
import Settings from "./pages/Settings";

export default function App() {
  return (
    <div className="flex min-h-screen bg-[var(--bg-primary)]">
      <Sidebar />
      <div className="flex-1 flex flex-col">
        <TopBar />
        <main className="flex-1 p-6 overflow-auto">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/satellite" element={<SatelliteAnalysis />} />
            <Route path="/drift" element={<DriftAnalysis />} />
            <Route path="/ais" element={<AisVessels />} />
            <Route path="/investigation" element={<Investigation />} />
            <Route path="/reports" element={<Reports />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}