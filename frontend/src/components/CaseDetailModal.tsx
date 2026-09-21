import { useEffect, useState } from "react";
import { Bot, ChevronDown, ChevronRight, Clock, ShieldCheck, Truck, X } from "lucide-react";
import { api } from "../api/client";
import type { DisruptionCase, TraceEntry } from "../types";
import Badge from "./Badge";

interface CaseDetailModalProps {
  disruptionCase: DisruptionCase | null;
  onClose: () => void;
}

function RevisionIcon() {
  return <span className="animate-spin text-purple-400 font-bold">↻</span>;
}

function TraceStep({ entry, index }: { entry: TraceEntry; index: number }) {
  const [expanded, setExpanded] = useState(false);
  const evidenceEntries = Object.entries(entry.evidence ?? {});

  return (
    <div className="rounded-xl bg-slate-850 border border-slate-800 hover:border-slate-700 transition-all overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-start gap-4 p-3.5 text-left"
      >
        <div className="w-7 h-7 rounded-full bg-brand-500/20 border border-brand-500/40 text-brand-400 flex items-center justify-center font-bold text-xs shrink-0">
          {index + 1}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2">
            <h4 className="text-sm font-semibold text-white">{entry.agent_name}</h4>
            <span className="text-[10px] font-mono text-slate-500 shrink-0">
              {new Date(entry.created_at).toLocaleTimeString()}
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            <span className="text-slate-500">Read:</span> {entry.input_summary}
          </p>
          <p className="text-xs text-emerald-300/90 mt-1">
            <span className="text-slate-500">Concluded:</span> {entry.output_summary}
          </p>
        </div>
        {expanded ? (
          <ChevronDown className="w-4 h-4 text-slate-500 shrink-0 mt-1" />
        ) : (
          <ChevronRight className="w-4 h-4 text-slate-500 shrink-0 mt-1" />
        )}
      </button>
      {expanded && evidenceEntries.length > 0 && (
        <div className="px-4 pb-4 pt-1 border-t border-slate-800/80">
          <span className="text-[10px] uppercase font-bold text-slate-500 block mb-2">Evidence cited</span>
          <pre className="text-[11px] font-mono text-slate-300 bg-slate-950 rounded-lg p-3 overflow-x-auto whitespace-pre-wrap">
            {JSON.stringify(entry.evidence, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}

export default function CaseDetailModal({ disruptionCase, onClose }: CaseDetailModalProps) {
  const [activeTab, setActiveTab] = useState<"pipeline" | "inventory" | "suppliers" | "reviewer">("pipeline");
  const [trace, setTrace] = useState<TraceEntry[]>([]);
  const [traceLoading, setTraceLoading] = useState(false);

  useEffect(() => {
    if (!disruptionCase) return;
    setTraceLoading(true);
    api
      .caseTrace(disruptionCase.case_number)
      .then(setTrace)
      .catch(() => setTrace([]))
      .finally(() => setTraceLoading(false));
  }, [disruptionCase?.case_number]);

  if (!disruptionCase) return null;

  const inv = disruptionCase.inventory_analysis || {};
  const imp = disruptionCase.impact || {};
  const rev = disruptionCase.review || {};

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-slate-950/80 backdrop-blur-sm animate-fade-in">
      <div className="w-full max-w-2xl bg-slate-900 border-l border-slate-800 shadow-2xl h-full flex flex-col overflow-hidden">
        <div className="p-6 border-b border-slate-800 flex items-start justify-between bg-slate-900/90">
          <div>
            <div className="flex items-center gap-3">
              <span className="font-mono text-xs text-brand-400 font-bold px-2 py-0.5 rounded bg-brand-500/10 border border-brand-500/20">
                {disruptionCase.case_number}
              </span>
              <Badge text={disruptionCase.status} />
              {disruptionCase.revision_count > 0 && (
                <span className="text-xs text-purple-400 bg-purple-500/10 border border-purple-500/30 px-2 py-0.5 rounded-full flex items-center gap-1">
                  <RevisionIcon /> {disruptionCase.revision_count} revision loop(s)
                </span>
              )}
            </div>
            <h2 className="text-xl font-bold text-white mt-2">{disruptionCase.material} disruption</h2>
            <p className="text-xs text-slate-400 mt-1">{disruptionCase.description}</p>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white p-1.5 rounded-lg hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="flex border-b border-slate-800 bg-slate-900 px-6">
          <button
            onClick={() => setActiveTab("pipeline")}
            className={`py-3 px-4 text-xs font-semibold border-b-2 transition-colors flex items-center gap-2 ${
              activeTab === "pipeline"
                ? "border-brand-500 text-brand-400"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            <Bot className="w-4 h-4" /> Explainability Trace
          </button>
          <button
            onClick={() => setActiveTab("inventory")}
            className={`py-3 px-4 text-xs font-semibold border-b-2 transition-colors flex items-center gap-2 ${
              activeTab === "inventory"
                ? "border-brand-500 text-brand-400"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            <Clock className="w-4 h-4" /> Inventory & impact
          </button>
          <button
            onClick={() => setActiveTab("suppliers")}
            className={`py-3 px-4 text-xs font-semibold border-b-2 transition-colors flex items-center gap-2 ${
              activeTab === "suppliers"
                ? "border-brand-500 text-brand-400"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            <Truck className="w-4 h-4" /> Suppliers ({disruptionCase.supplier_options.length})
          </button>
          <button
            onClick={() => setActiveTab("reviewer")}
            className={`py-3 px-4 text-xs font-semibold border-b-2 transition-colors flex items-center gap-2 ${
              activeTab === "reviewer"
                ? "border-brand-500 text-brand-400"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            <ShieldCheck className="w-4 h-4" /> Reviewer
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {activeTab === "pipeline" && (
            <div className="space-y-4">
              <div>
                <h3 className="text-sm font-bold uppercase tracking-wider text-slate-400">Context Lake - what each agent actually did</h3>
                <p className="text-xs text-slate-500 mt-1">
                  Every step's real input, conclusion, and cited evidence, in the order it ran - not a generic description.
                </p>
              </div>

              {traceLoading ? (
                <p className="text-xs text-slate-500">Loading trace...</p>
              ) : trace.length === 0 ? (
                <p className="text-xs text-slate-500">No trace recorded for this case yet.</p>
              ) : (
                <div className="space-y-3">
                  {trace.map((entry, idx) => (
                    <TraceStep key={idx} entry={entry} index={idx} />
                  ))}
                </div>
              )}

              {inv.narrative && (
                <div className="p-4 rounded-xl bg-slate-850/60 border border-slate-800 mt-4">
                  <span className="text-xs font-semibold text-brand-400 uppercase tracking-wider block mb-1">
                    Case narrative
                  </span>
                  <p className="text-xs text-slate-300 leading-relaxed italic">"{inv.narrative}"</p>
                </div>
              )}
            </div>
          )}

          {activeTab === "inventory" && (
            <div className="space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 rounded-xl bg-slate-850 border border-slate-800">
                  <span className="text-xs text-slate-400">On-hand stock</span>
                  <p className="text-2xl font-bold text-white mt-1">{inv.current_quantity ?? "N/A"} tons</p>
                </div>
                <div className="p-4 rounded-xl bg-slate-850 border border-slate-800">
                  <span className="text-slate-400 text-xs">Daily consumption</span>
                  <p className="text-2xl font-bold text-amber-400 mt-1">{inv.daily_consumption ?? "N/A"} tons/day</p>
                </div>
                <div className="p-4 rounded-xl bg-slate-850 border border-slate-800">
                  <span className="text-slate-400 text-xs">Coverage runway</span>
                  <p className="text-2xl font-bold text-cyan-400 mt-1">
                    {inv.coverage_days != null ? `${inv.coverage_days.toFixed(1)} days` : "N/A"}
                  </p>
                </div>
                <div className="p-4 rounded-xl bg-slate-850 border border-slate-800">
                  <span className="text-slate-400 text-xs">Projected stockout</span>
                  <p className="text-xl font-bold text-rose-400 mt-1">{inv.projected_stockout_date ?? "Not calculable"}</p>
                </div>
              </div>

              <div className="card bg-slate-850 border-slate-800">
                <h4 className="text-sm font-bold text-white mb-3">Operational impact</h4>
                <div className="space-y-2 text-xs">
                  <div className="flex justify-between py-1.5 border-b border-slate-800">
                    <span className="text-slate-400">Severity:</span>
                    <Badge text={imp.severity || "medium"} />
                  </div>
                  <div className="flex justify-between py-1.5 border-b border-slate-800">
                    <span className="text-slate-400">Mitigation window:</span>
                    <span className="font-semibold text-white">
                      {imp.mitigation_window_days != null ? `${imp.mitigation_window_days} days` : "N/A"}
                    </span>
                  </div>
                  <div className="flex justify-between py-1.5 border-b border-slate-800">
                    <span className="text-slate-400">Affected purchase orders:</span>
                    <span className="font-mono text-cyan-400">{imp.affected_purchase_orders?.join(", ") || "None"}</span>
                  </div>
                  <div className="flex justify-between py-1.5">
                    <span className="text-slate-400">Downstream customers:</span>
                    <span className="font-semibold text-white">{imp.affected_customers?.join(", ") || "None"}</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === "suppliers" && (
            <div className="space-y-4">
              <h4 className="text-sm font-bold text-white mb-2">Evaluated mitigation suppliers</h4>
              {disruptionCase.supplier_options.length === 0 ? (
                <p className="text-xs text-slate-400">No alternative suppliers available.</p>
              ) : (
                <div className="space-y-3">
                  {disruptionCase.supplier_options.map((opt, i) => (
                    <div
                      key={i}
                      className="p-4 rounded-xl bg-slate-850 border border-slate-800 hover:border-slate-700 transition-colors space-y-2"
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <span className="text-xs font-mono text-slate-400">{opt.supplier_code}</span>
                          <h5 className="text-sm font-bold text-white">{opt.name}</h5>
                        </div>
                        <span
                          className={`badge ${
                            opt.data_confidence === "confirmed"
                              ? "bg-emerald-500/15 text-emerald-400"
                              : "bg-amber-500/15 text-amber-400"
                          }`}
                        >
                          {opt.data_confidence === "confirmed" ? "Verified" : "Requires verification"}
                        </span>
                      </div>
                      <div className="grid grid-cols-4 gap-2 text-xs pt-2 border-t border-slate-800/60 text-slate-300">
                        <div>
                          <span className="text-slate-400 block">Lead time</span>
                          <span className="font-semibold">{opt.lead_time_days ?? "N/A"} days</span>
                        </div>
                        <div>
                          <span className="text-slate-400 block">Price / unit</span>
                          <span className="font-semibold">${opt.price_per_unit ?? "N/A"}</span>
                        </div>
                        <div>
                          <span className="text-slate-400 block">Available stock</span>
                          <span className="font-semibold">{opt.available_quantity ?? "N/A"} units</span>
                        </div>
                        <div>
                          <span className="text-slate-400 block">Capacity / mo</span>
                          <span className="font-semibold">{opt.capacity_units_per_month ?? "N/A"}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === "reviewer" && (
            <div className="space-y-4">
              <div className="card bg-slate-850 border-slate-800 space-y-3">
                <div className="flex items-center gap-2">
                  <ShieldCheck className="w-5 h-5 text-emerald-400" />
                  <h4 className="text-sm font-bold text-white">Reviewer agent verdict</h4>
                </div>
                <div className="flex items-center gap-2 text-xs">
                  <span className="text-slate-400">Status:</span>
                  <span
                    className={`badge ${
                      rev.approved !== false ? "bg-emerald-500/20 text-emerald-300" : "bg-purple-500/20 text-purple-300"
                    }`}
                  >
                    {rev.approved !== false ? "Verified & approved" : "Revision needed"}
                  </span>
                </div>

                {rev.issues && rev.issues.length > 0 ? (
                  <div className="space-y-2 pt-2 border-t border-slate-800">
                    <span className="text-xs font-semibold text-rose-400">Issues found:</span>
                    <ul className="list-disc list-inside text-xs text-slate-300 space-y-1">
                      {rev.issues.map((issue, idx) => (
                        <li key={idx}>{issue}</li>
                      ))}
                    </ul>
                  </div>
                ) : (
                  <p className="text-xs text-slate-400 pt-2 border-t border-slate-800">
                    No mathematical or evidence flaws detected. Calculations and supplier checks match the evidence.
                  </p>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
