import { useEffect, useState } from "react";
import { Activity, AlertOctagon, CheckCircle2, Clock, ShieldAlert } from "lucide-react";
import { api } from "../api/client";
import Badge from "../components/Badge";
import type { DisruptionCase } from "../types";

export default function ImpactAnalysis() {
  const [cases, setCases] = useState<DisruptionCase[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.cases().then((c) => {
      setCases(c);
      setSelected(c[0]?.case_number ?? null);
      setLoading(false);
    });
  }, []);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-96 gap-3">
        <Activity className="w-8 h-8 text-brand-400 animate-spin" />
        <p className="text-slate-400 text-sm font-medium">Loading impact analysis...</p>
      </div>
    );
  }

  if (cases.length === 0) {
    return (
      <div className="card p-12 text-center flex flex-col items-center justify-center">
        <CheckCircle2 className="w-10 h-10 text-emerald-400 mb-3" />
        <h3 className="text-base font-bold text-white">No disruption cases recorded</h3>
        <p className="text-xs text-slate-400 mt-1">The system currently has zero supply chain disruptions.</p>
      </div>
    );
  }

  const current = cases.find((c) => c.case_number === selected) ?? cases[0];
  const inv = current.inventory_analysis || {};
  const impact = current.impact || {};

  return (
    <div className="space-y-8 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <Activity className="w-6 h-6 text-brand-400" /> Impact Analysis
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Operational impact assessed by the Impact Assessment Agent, per case.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400 font-semibold">Case:</span>
          <select
            value={current.case_number}
            onChange={(e) => setSelected(e.target.value)}
            className="bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white font-mono focus:outline-none focus:border-brand-500"
          >
            {cases.map((c) => (
              <option key={c.case_number} value={c.case_number}>
                {c.case_number} — {c.material} ({c.disruption_type.replace(/_/g, " ")})
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="card space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <div className="flex items-center gap-2">
              <Clock className="w-5 h-5 text-brand-400" />
              <h3 className="text-base font-bold text-white">Inventory Position</h3>
            </div>
            {inv.reorder_required && <Badge text="at_risk" />}
          </div>

          <div className="space-y-3 text-xs">
            <div className="flex justify-between py-1.5 border-b border-slate-800">
              <span className="text-slate-400">Current quantity:</span>
              <span className="font-bold text-white">{inv.current_quantity ?? "N/A"}</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-slate-800">
              <span className="text-slate-400">Daily consumption:</span>
              <span className="font-bold text-amber-400">{inv.daily_consumption ?? "N/A"}</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-slate-800">
              <span className="text-slate-400">Coverage:</span>
              <span className="font-bold text-cyan-400">
                {inv.coverage_days != null ? `${inv.coverage_days.toFixed(1)} days` : "N/A"}
              </span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-slate-800">
              <span className="text-slate-400">Projected stockout:</span>
              <span className="font-bold text-rose-400">{inv.projected_stockout_date ?? "Not calculable"}</span>
            </div>
          </div>

          {inv.notes && inv.notes.length > 0 && (
            <div className="p-3 rounded-xl bg-slate-850 border border-slate-800/80">
              <span className="text-[10px] uppercase font-bold text-slate-400 block mb-1">Calculation notes</span>
              <ul className="list-disc list-inside text-[11px] text-slate-300 space-y-1">
                {inv.notes.map((n, i) => (
                  <li key={i}>{n}</li>
                ))}
              </ul>
            </div>
          )}
        </div>

        <div className="card space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <div className="flex items-center gap-2">
              <ShieldAlert className="w-5 h-5 text-rose-400" />
              <h3 className="text-base font-bold text-white">Severity & Mitigation Window</h3>
            </div>
            {impact.severity && <Badge text={impact.severity} />}
          </div>

          <div className="space-y-3 text-xs">
            <div className="flex justify-between py-1.5 border-b border-slate-800">
              <span className="text-slate-400">Estimated delay:</span>
              <span className="font-bold text-amber-400">{impact.estimated_delay_days ?? 0} days</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-slate-800">
              <span className="text-slate-400">Mitigation window:</span>
              <span className="font-bold text-cyan-400">
                {impact.mitigation_window_days != null ? `${impact.mitigation_window_days} days` : "Unknown"}
              </span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-slate-800">
              <span className="text-slate-400">Affected purchase orders:</span>
              <span className="font-mono text-cyan-300">{impact.affected_purchase_orders?.join(", ") || "None"}</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-slate-800">
              <span className="text-slate-400">Affected production orders:</span>
              <span className="font-semibold text-slate-200">{impact.affected_production_orders?.join(", ") || "None"}</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-slate-800">
              <span className="text-slate-400">Affected customers:</span>
              <span className="font-semibold text-white">{impact.affected_customers?.join(", ") || "None"}</span>
            </div>
          </div>

          {impact.summary && (
            <div className="p-3 rounded-xl bg-slate-850 border border-slate-800 text-xs text-slate-300 leading-relaxed">
              <span className="text-[10px] uppercase font-bold text-brand-400 block mb-1">Summary</span>
              {impact.summary}
            </div>
          )}
        </div>
      </div>

      {current.review?.issues && current.review.issues.length > 0 && (
        <div className="card border-purple-500/30 bg-purple-950/20 text-xs space-y-2">
          <div className="flex items-center gap-2 text-purple-300 font-bold text-sm">
            <AlertOctagon className="w-5 h-5 text-purple-400" />
            <span>Reviewer / Critic Agent findings</span>
          </div>
          <ul className="list-disc list-inside text-slate-300 space-y-1">
            {current.review.issues.map((issue, i) => (
              <li key={i}>{issue}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
