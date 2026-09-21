import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Activity, AlertTriangle, Boxes, CheckCircle2, Clock, Eye, ShieldAlert } from "lucide-react";
import { api } from "../api/client";
import Badge from "../components/Badge";
import CaseDetailModal from "../components/CaseDetailModal";
import StatCard from "../components/StatCard";
import type { Alert, DashboardSummary, DisruptionCase } from "../types";

export default function Dashboard() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [cases, setCases] = useState<DisruptionCase[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCase, setSelectedCase] = useState<DisruptionCase | null>(null);

  async function loadData() {
    try {
      const [s, c, a] = await Promise.all([api.dashboardSummary(), api.cases(), api.alerts()]);
      setSummary(s);
      setCases(c);
      setAlerts(a);
    } catch (err) {
      console.error("Dashboard fetch error:", err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 15000);
    return () => clearInterval(interval);
  }, []);

  if (loading || !summary) {
    return (
      <div className="flex flex-col items-center justify-center h-96 gap-3">
        <Activity className="w-8 h-8 text-brand-400 animate-spin" />
        <p className="text-slate-400 text-sm font-medium">Loading dashboard...</p>
      </div>
    );
  }

  const coverageData = summary.at_risk_materials.map((m) => ({
    material: m.material,
    coverage_days: m.coverage_days,
  }));

  const activeCases = cases.filter((c) => ["in_progress", "needs_revision", "pending_approval"].includes(c.status));

  return (
    <div className="space-y-8 animate-fade-in">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-white">Supply Chain Control Center</h2>
        <p className="text-xs text-slate-400 mt-1">Real-time multi-agent monitoring & disruption mitigation.</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <StatCard
          label="Active Disruptions"
          value={summary.active_disruptions}
          tone={summary.active_disruptions > 0 ? "danger" : "success"}
          subtitle={`${summary.severity_breakdown.critical || 0} critical severity`}
          icon={<ShieldAlert className="w-5 h-5 text-rose-400" />}
        />
        <StatCard
          label="Open Alerts"
          value={summary.open_alerts}
          tone={summary.open_alerts > 0 ? "warning" : "default"}
          subtitle="Deduplicated team notifications"
          icon={<AlertTriangle className="w-5 h-5 text-amber-400" />}
        />
        <StatCard
          label="Pending Approvals"
          value={summary.pending_approvals}
          tone={summary.pending_approvals > 0 ? "warning" : "default"}
          subtitle="Requires manager decision"
          icon={<Clock className="w-5 h-5 text-cyan-400" />}
        />
        <StatCard
          label="Open Action Items"
          value={summary.open_action_items}
          tone="default"
          subtitle="Assigned across departments"
          icon={<Boxes className="w-5 h-5 text-brand-400" />}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <div className="mb-6">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <Boxes className="w-4 h-4 text-brand-400" /> At-risk material runway (days)
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">Coverage days remaining before stockout</p>
          </div>

          {coverageData.length === 0 ? (
            <div className="h-60 flex flex-col items-center justify-center border border-dashed border-slate-800 rounded-xl p-4">
              <CheckCircle2 className="w-8 h-8 text-emerald-400 mb-2" />
              <p className="text-xs text-slate-400">All inventory items are above safety reorder thresholds.</p>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={coverageData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                <XAxis dataKey="material" tick={{ fontSize: 11, fill: "#94a3b8" }} axisLine={{ stroke: "#334155" }} />
                <YAxis tick={{ fontSize: 11, fill: "#94a3b8" }} axisLine={{ stroke: "#334155" }} />
                <Tooltip
                  contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155", borderRadius: "12px", fontSize: "12px" }}
                  itemStyle={{ color: "#38bdf8" }}
                />
                <Bar dataKey="coverage_days" radius={[6, 6, 0, 0]}>
                  {coverageData.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={entry.coverage_days <= 5 ? "#f43f5e" : entry.coverage_days <= 10 ? "#f59e0b" : "#0269c2"}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        <div className="card">
          <div className="mb-4">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <Activity className="w-4 h-4 text-amber-400" /> Active disruption cases
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">Click a case to inspect its agent execution trace</p>
          </div>

          <div className="space-y-3 max-h-[260px] overflow-y-auto pr-1">
            {activeCases.length === 0 ? (
              <div className="h-48 flex flex-col items-center justify-center border border-dashed border-slate-800 rounded-xl">
                <CheckCircle2 className="w-8 h-8 text-emerald-400 mb-2" />
                <p className="text-xs text-slate-400">No active disruption cases.</p>
              </div>
            ) : (
              activeCases.map((c) => (
                <div
                  key={c.case_number}
                  onClick={() => setSelectedCase(c)}
                  className="p-3.5 rounded-xl bg-slate-850/80 border border-slate-800/80 hover:border-brand-500/50 hover:bg-slate-800 transition-all cursor-pointer flex items-center justify-between group"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-bold text-brand-400">{c.case_number}</span>
                      <h4 className="text-xs font-bold text-white group-hover:text-brand-300 transition-colors">
                        {c.material}
                      </h4>
                    </div>
                    <p className="text-[11px] text-slate-400 capitalize">
                      {c.disruption_type.replace(/_/g, " ")} • {c.description}
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
                    <Badge text={c.status} />
                    <Eye className="w-4 h-4 text-slate-500 group-hover:text-brand-400 transition-colors" />
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      <div className="card">
        <div className="mb-4">
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-brand-400" /> Alert feed
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">Deduplicated notifications from the Alert & Response Agent</p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="text-slate-400 border-b border-slate-800">
                <th className="pb-3 font-semibold uppercase tracking-wider">Material</th>
                <th className="pb-3 font-semibold uppercase tracking-wider">Disruption Type</th>
                <th className="pb-3 font-semibold uppercase tracking-wider">Responsible Team</th>
                <th className="pb-3 font-semibold uppercase tracking-wider">Status</th>
                <th className="pb-3 font-semibold uppercase tracking-wider">Sweeps Detected</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {alerts.slice(0, 6).map((a) => (
                <tr key={a.id} className="hover:bg-slate-850/50 transition-colors">
                  <td className="py-3 font-bold text-white">{a.material}</td>
                  <td className="py-3 capitalize text-slate-300">{a.disruption_type.replace(/_/g, " ")}</td>
                  <td className="py-3 text-cyan-400 font-medium">{a.responsible_team}</td>
                  <td className="py-3">
                    <Badge text={a.status} />
                  </td>
                  <td className="py-3 font-mono text-slate-400">{a.occurrence_count}x</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <CaseDetailModal disruptionCase={selectedCase} onClose={() => setSelectedCase(null)} />
    </div>
  );
}
