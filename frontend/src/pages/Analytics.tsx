import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { BarChart3, RefreshCw, ShieldCheck, TrendingUp } from "lucide-react";
import { api } from "../api/client";
import StatCard from "../components/StatCard";
import type { AnalyticsSummary } from "../types";

const SEVERITY_COLOR: Record<string, string> = {
  critical: "#f43f5e",
  high: "#f59e0b",
  medium: "#e8a55a",
  low: "#0269c2",
  unknown: "#6c6a64",
};

const TOOLTIP_STYLE = { backgroundColor: "#0f172a", borderColor: "#334155", borderRadius: "12px", fontSize: "12px" };
const AXIS_TICK = { fontSize: 11, fill: "#94a3b8" };
const AXIS_LINE = { stroke: "#334155" };

export default function Analytics() {
  const [data, setData] = useState<AnalyticsSummary | null>(null);
  const [loading, setLoading] = useState(true);

  async function loadData() {
    const summary = await api.analyticsSummary();
    setData(summary);
    setLoading(false);
  }

  useEffect(() => {
    loadData();
  }, []);

  if (loading || !data) {
    return (
      <div className="flex flex-col items-center justify-center h-96 gap-3">
        <BarChart3 className="w-8 h-8 text-brand-400 animate-spin" />
        <p className="text-slate-400 text-sm font-medium">Crunching disruption history...</p>
      </div>
    );
  }

  if (data.total_cases === 0) {
    return (
      <div className="space-y-8 animate-fade-in">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <BarChart3 className="w-6 h-6 text-brand-400" /> Analytics
          </h2>
        </div>
        <div className="card p-12 text-center">
          <p className="text-sm text-slate-400">
            No disruption history yet - run a monitoring sweep to generate the first cases, then trends will appear here.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <BarChart3 className="w-6 h-6 text-brand-400" /> Analytics
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Historical trends across every disruption ever recorded, aggregated with pandas on the backend.
          </p>
        </div>
        <button
          onClick={() => {
            setLoading(true);
            loadData();
          }}
          className="py-2 px-3.5 rounded-xl text-xs font-semibold flex items-center gap-2 border bg-slate-850 text-slate-400 border-slate-800 hover:border-slate-700 transition-all"
        >
          <RefreshCw className="w-3.5 h-3.5" /> Refresh
        </button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
        <StatCard label="Total Disruption Cases" value={data.total_cases} icon={<TrendingUp className="w-5 h-5 text-brand-400" />} />
        <StatCard label="Total Alerts Raised" value={data.total_alerts} icon={<BarChart3 className="w-5 h-5 text-amber-400" />} />
        <StatCard
          label="Reviewer Revision Rate"
          value={`${data.reviewer_revision_rate.revision_rate_pct}%`}
          subtitle={`${data.reviewer_revision_rate.cases_revised} of ${data.reviewer_revision_rate.total_cases} cases sent back for revision`}
          icon={<ShieldCheck className="w-5 h-5 text-emerald-400" />}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h3 className="text-base font-bold text-white mb-1">Disruptions by material</h3>
          <p className="text-xs text-slate-400 mb-4">Which materials generate the most cases overall</p>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={data.disruption_frequency_by_material} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
              <XAxis dataKey="material" tick={AXIS_TICK} axisLine={AXIS_LINE} />
              <YAxis tick={AXIS_TICK} axisLine={AXIS_LINE} allowDecimals={false} />
              <Tooltip contentStyle={TOOLTIP_STYLE} />
              <Bar dataKey="count" fill="#0269c2" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <h3 className="text-base font-bold text-white mb-1">Severity mix</h3>
          <p className="text-xs text-slate-400 mb-4">How serious cases have been, across their full history</p>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={data.severity_distribution} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
              <XAxis dataKey="severity" tick={AXIS_TICK} axisLine={AXIS_LINE} />
              <YAxis tick={AXIS_TICK} axisLine={AXIS_LINE} allowDecimals={false} />
              <Tooltip contentStyle={TOOLTIP_STYLE} />
              <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                {data.severity_distribution.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={SEVERITY_COLOR[entry.severity] ?? "#6c6a64"} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <h3 className="text-base font-bold text-white mb-1">Alert load by team</h3>
          <p className="text-xs text-slate-400 mb-4">Total vs. still-open alerts assigned to each responsible team</p>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={data.alerts_by_team} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
              <XAxis dataKey="team" tick={AXIS_TICK} axisLine={AXIS_LINE} />
              <YAxis tick={AXIS_TICK} axisLine={AXIS_LINE} allowDecimals={false} />
              <Tooltip contentStyle={TOOLTIP_STYLE} />
              <Bar dataKey="total_alerts" name="Total" fill="#5db8a6" radius={[6, 6, 0, 0]} />
              <Bar dataKey="open_alerts" name="Still open" fill="#f59e0b" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <h3 className="text-base font-bold text-white mb-1">Cases over the last 14 days</h3>
          <p className="text-xs text-slate-400 mb-4">New or re-confirmed disruption cases per day</p>
          {data.cases_per_day.length === 0 ? (
            <div className="h-[220px] flex items-center justify-center text-xs text-slate-500">No activity in this window yet.</div>
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={data.cases_per_day} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                <XAxis dataKey="date" tick={AXIS_TICK} axisLine={AXIS_LINE} />
                <YAxis tick={AXIS_TICK} axisLine={AXIS_LINE} allowDecimals={false} />
                <Tooltip contentStyle={TOOLTIP_STYLE} />
                <Line type="monotone" dataKey="count" stroke="#cc785c" strokeWidth={2} dot={{ r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      <div className="card">
        <h3 className="text-base font-bold text-white mb-1">Average mitigation window by severity</h3>
        <p className="text-xs text-slate-400 mb-4">How many days of runway cases at each severity level have had, on average</p>
        {data.avg_mitigation_window_by_severity.length === 0 ? (
          <p className="text-xs text-slate-500">Not enough calculable stockout dates yet to average.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="pb-2 font-semibold uppercase tracking-wider">Severity</th>
                  <th className="pb-2 font-semibold uppercase tracking-wider">Avg. mitigation window (days)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {data.avg_mitigation_window_by_severity.map((row) => (
                  <tr key={row.severity}>
                    <td className="py-2.5 capitalize text-slate-200">{row.severity}</td>
                    <td className="py-2.5 font-mono text-white">{row.avg_mitigation_window_days}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
