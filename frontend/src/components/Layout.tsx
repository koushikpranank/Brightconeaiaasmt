import { useState, type ReactNode } from "react";
import { NavLink } from "react-router-dom";
import {
  Activity,
  AlertTriangle,
  BarChart3,
  Boxes,
  CheckSquare,
  Clock,
  FileText,
  LineChart,
  Play,
  RefreshCw,
  ShieldCheck,
  Truck,
  Users,
} from "lucide-react";
import { api } from "../api/client";
import SimulationModal from "./SimulationModal";

const NAV_ITEMS = [
  { to: "/", label: "Dashboard", icon: <BarChart3 className="w-4 h-4" /> },
  { to: "/suppliers", label: "Suppliers", icon: <Users className="w-4 h-4" /> },
  { to: "/inventory", label: "Inventory", icon: <Boxes className="w-4 h-4" /> },
  { to: "/shipments", label: "Shipments", icon: <Truck className="w-4 h-4" /> },
  { to: "/alerts", label: "Disruption Alerts", icon: <AlertTriangle className="w-4 h-4" /> },
  { to: "/impact", label: "Impact Analysis", icon: <Activity className="w-4 h-4" /> },
  { to: "/mitigation", label: "Mitigation Planning", icon: <ShieldCheck className="w-4 h-4" /> },
  { to: "/actions", label: "Action Tracker", icon: <CheckSquare className="w-4 h-4" /> },
  { to: "/analytics", label: "Analytics", icon: <LineChart className="w-4 h-4" /> },
  { to: "/reports", label: "Reports", icon: <FileText className="w-4 h-4" /> },
];

export default function Layout({ children }: { children: ReactNode }) {
  const [running, setRunning] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [simulatorOpen, setSimulatorOpen] = useState(false);

  async function handleRunSweep() {
    setRunning(true);
    setMessage(null);
    try {
      const result = await api.runMonitoring();
      setMessage(`Sweep finished — ${result.cases_processed.length} case(s) updated.`);
    } catch (e) {
      setMessage("Sweep failed — verify backend.");
      console.error(e);
    } finally {
      setRunning(false);
      setTimeout(() => setMessage(null), 4000);
    }
  }

  return (
    <div className="min-h-screen flex bg-slate-950 text-slate-100">
      <aside className="w-64 shrink-0 bg-slate-900/90 backdrop-blur-md border-r border-slate-800 flex flex-col justify-between z-20">
        <div>
          <div className="p-5 border-b border-slate-800/80 flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-brand-600 to-cyan-500 flex items-center justify-center shadow-glow text-white font-black text-lg">
              AI
            </div>
            <div>
              <h1 className="text-sm font-bold tracking-wide text-white leading-snug">Agentic AI</h1>
              <p className="text-[11px] text-cyan-400 font-medium">Supply Chain Operations</p>
            </div>
          </div>

          <nav className="p-3 space-y-1">
            {NAV_ITEMS.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === "/"}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all duration-200 ${
                    isActive
                      ? "bg-brand-600/20 text-brand-300 border border-brand-500/40 shadow-glow"
                      : "text-slate-400 hover:bg-slate-800/60 hover:text-slate-200"
                  }`
                }
              >
                {item.icon}
                <span>{item.label}</span>
              </NavLink>
            ))}
          </nav>
        </div>

        <div className="p-4 border-t border-slate-800/80 space-y-2.5 bg-slate-900/60">
          <button
            onClick={() => setSimulatorOpen(true)}
            className="w-full rounded-xl bg-slate-800 hover:bg-slate-700 text-brand-300 border border-brand-500/30 text-xs font-bold py-2.5 px-3 flex items-center justify-center gap-2 transition-all shadow-sm hover:border-brand-500/60"
          >
            <Play className="w-3.5 h-3.5 text-brand-400" />
            Launch Disruption Simulator
          </button>

          <button
            onClick={handleRunSweep}
            disabled={running}
            className="w-full rounded-xl bg-gradient-to-r from-brand-600 to-brand-700 hover:from-brand-500 hover:to-brand-600 disabled:opacity-50 text-white text-xs font-bold py-2.5 px-3 flex items-center justify-center gap-2 transition-all shadow-glow"
          >
            {running ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Activity className="w-3.5 h-3.5" />}
            {running ? "Scanning sources..." : "Run monitoring sweep"}
          </button>

          {message && (
            <div className="p-2 rounded-lg bg-brand-500/10 border border-brand-500/20 text-[11px] text-brand-300 text-center animate-fade-in">
              {message}
            </div>
          )}
        </div>
      </aside>

      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <header className="h-14 bg-slate-900/60 backdrop-blur-md border-b border-slate-800/80 px-8 flex items-center justify-between z-10">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span className="text-xs font-semibold text-slate-300">7-agent pipeline live</span>
          </div>

          <div className="flex items-center gap-4 text-xs">
            <div className="flex items-center gap-1.5 text-slate-400 bg-slate-850 px-3 py-1.5 rounded-lg border border-slate-800">
              <Clock className="w-3.5 h-3.5 text-slate-400" />
              <span>Auto sweep every 60s</span>
            </div>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto p-8">{children}</main>
      </div>

      <SimulationModal isOpen={simulatorOpen} onClose={() => setSimulatorOpen(false)} onSuccess={() => {}} />
    </div>
  );
}
