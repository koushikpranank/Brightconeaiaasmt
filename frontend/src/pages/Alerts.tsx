import { useEffect, useState } from "react";
import { AlertTriangle, Bell, Filter, Search } from "lucide-react";
import { api } from "../api/client";
import Badge from "../components/Badge";
import type { Alert } from "../types";

export default function Alerts() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedTeam, setSelectedTeam] = useState<string>("all");

  useEffect(() => {
    api
      .alerts()
      .then(setAlerts)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-96 gap-3">
        <Bell className="w-8 h-8 text-brand-400 animate-spin" />
        <p className="text-slate-400 text-sm font-medium">Loading disruption alerts...</p>
      </div>
    );
  }

  const filteredAlerts = alerts.filter((a) => {
    const matchesSearch =
      a.material.toLowerCase().includes(searchTerm.toLowerCase()) ||
      a.disruption_type.toLowerCase().includes(searchTerm.toLowerCase()) ||
      a.expected_impact.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesTeam = selectedTeam === "all" || a.responsible_team.toLowerCase() === selectedTeam.toLowerCase();
    return matchesSearch && matchesTeam;
  });

  const teams = Array.from(new Set(alerts.map((a) => a.responsible_team)));

  return (
    <div className="space-y-8 animate-fade-in">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
          <AlertTriangle className="w-6 h-6 text-brand-400" /> Disruption Alerts
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Consolidated alerts from the Alert & Response Planning Agent. Repeated detections update the same
          alert instead of creating duplicates.
        </p>
      </div>

      <div className="card p-4 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
          <input
            type="text"
            placeholder="Search alerts by material or description..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-9 pr-4 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-brand-500 transition-colors"
          />
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          <Filter className="w-3.5 h-3.5 text-slate-400" />
          <select
            value={selectedTeam}
            onChange={(e) => setSelectedTeam(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-brand-500"
          >
            <option value="all">All teams</option>
            {teams.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="space-y-4">
        {filteredAlerts.length === 0 ? (
          <div className="card p-12 text-center flex flex-col items-center justify-center">
            <Bell className="w-10 h-10 text-slate-600 mb-3" />
            <h3 className="text-base font-bold text-white">No disruption alerts found</h3>
            <p className="text-xs text-slate-400 mt-1">Run a monitoring sweep to scan suppliers, inventory, and logistics feeds.</p>
          </div>
        ) : (
          filteredAlerts.map((a) => (
            <div key={a.id} className="card border-slate-800/90 hover:border-brand-500/40 transition-all space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="badge bg-brand-500/20 text-brand-300 border border-brand-500/30 font-mono">
                      {a.material}
                    </span>
                    <h3 className="text-base font-bold text-white capitalize">{a.disruption_type.replace(/_/g, " ")}</h3>
                  </div>
                  <p className="text-[11px] text-slate-400 font-mono">
                    Source: <span className="text-slate-300">{a.source}</span> • Key: {a.dedup_key}
                  </p>
                </div>

                <div className="flex items-center gap-2">
                  <span className="badge bg-cyan-500/15 text-cyan-300 border border-cyan-500/30">
                    Team: {a.responsible_team}
                  </span>
                  <span className="badge bg-slate-800 text-slate-300 border border-slate-700 font-mono">
                    {a.occurrence_count}x
                  </span>
                  <Badge text={a.status} />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-3 border-t border-slate-800/80 text-xs">
                <div className="p-3.5 rounded-xl bg-slate-850 border border-slate-800">
                  <span className="text-slate-400 uppercase font-semibold text-[10px] block mb-1">Expected impact</span>
                  <p className="text-slate-200 leading-relaxed">{a.expected_impact}</p>
                </div>
                <div className="p-3.5 rounded-xl bg-slate-850 border border-slate-800">
                  <span className="text-slate-400 uppercase font-semibold text-[10px] block mb-1">Recommended action</span>
                  <p className="text-brand-300 font-medium leading-relaxed">{a.recommended_action}</p>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
