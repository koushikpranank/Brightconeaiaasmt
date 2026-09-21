import { useEffect, useState } from "react";
import { AlertCircle, CheckCircle2, ShieldCheck, Truck, UserCheck, XCircle } from "lucide-react";
import { api } from "../api/client";
import Badge from "../components/Badge";
import type { ApprovalRequest, DisruptionCase } from "../types";

const ACTION_TYPE_LABELS: Record<string, string> = {
  place_purchase_order: "Place Purchase Order",
  change_supplier: "Change Supplier",
  commit_expenditure: "Commit Expenditure",
  modify_delivery_commitment: "Modify Delivery Commitment",
};

export default function Mitigation() {
  const [cases, setCases] = useState<DisruptionCase[]>([]);
  const [approvals, setApprovals] = useState<ApprovalRequest[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [approver, setApprover] = useState("supply.manager@example.com");
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);

  async function loadData() {
    try {
      const [c, a] = await Promise.all([api.cases(), api.approvals()]);
      setCases(c);
      setApprovals(a);
      setSelected((prev) => prev ?? c[0]?.case_number ?? null);
    } catch (err) {
      console.error("Failed to load mitigation data:", err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-96 gap-3">
        <ShieldCheck className="w-8 h-8 text-brand-400 animate-spin" />
        <p className="text-slate-400 text-sm font-medium">Loading mitigation plans...</p>
      </div>
    );
  }

  if (cases.length === 0) {
    return (
      <div className="card p-12 text-center flex flex-col items-center justify-center">
        <CheckCircle2 className="w-10 h-10 text-emerald-400 mb-3" />
        <h3 className="text-base font-bold text-white">No active mitigation required</h3>
        <p className="text-xs text-slate-400 mt-1">No pending disruption cases require a supplier substitution.</p>
      </div>
    );
  }

  const current = cases.find((c) => c.case_number === selected) ?? cases[0];
  const mitigation = current.mitigation || {};
  const approval = approvals.find((a) => a.case_id === current.id && a.status === "pending");

  async function decide(decision: "approved" | "rejected") {
    if (!approval) return;
    setBusy(true);
    try {
      await api.decideApproval(
        approval.id,
        approver,
        decision,
        decision === "approved" ? "Approved via Mitigation Planning page" : "Rejected - needs revisiting"
      );
      setNotice(`Approval request #${approval.id} marked as ${decision}.`);
      await loadData();
    } catch (err: any) {
      setNotice(`Decision submission error: ${err.message}`);
    } finally {
      setBusy(false);
      setTimeout(() => setNotice(null), 5000);
    }
  }

  return (
    <div className="space-y-8 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <ShieldCheck className="w-6 h-6 text-brand-400" /> Mitigation Planning
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Alternative supplier comparison. Every procurement commitment requires human approval below.
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

      {notice && (
        <div className="p-3.5 rounded-xl bg-brand-500/15 border border-brand-500/30 text-xs text-brand-300 flex items-center gap-2 animate-fade-in">
          <CheckCircle2 className="w-4 h-4 shrink-0 text-brand-400" />
          <span>{notice}</span>
        </div>
      )}

      <div className="card space-y-4">
        <h3 className="text-base font-bold text-white flex items-center gap-2">
          <Truck className="w-4 h-4 text-brand-400" /> Alternative supplier comparison
        </h3>

        {!mitigation.options || mitigation.options.length === 0 ? (
          <p className="text-xs text-slate-400 italic">No approved alternative suppliers on file for {current.material}.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-850/80 border-b border-slate-800 text-slate-400">
                <tr>
                  <th className="py-3 px-4 font-semibold uppercase tracking-wider">Vendor Code</th>
                  <th className="py-3 px-4 font-semibold uppercase tracking-wider">Supplier Name</th>
                  <th className="py-3 px-4 font-semibold uppercase tracking-wider">Lead Time</th>
                  <th className="py-3 px-4 font-semibold uppercase tracking-wider">Unit Price</th>
                  <th className="py-3 px-4 font-semibold uppercase tracking-wider">Available Stock</th>
                  <th className="py-3 px-4 font-semibold uppercase tracking-wider">Capacity / mo</th>
                  <th className="py-3 px-4 font-semibold uppercase tracking-wider">Meets Demand</th>
                  <th className="py-3 px-4 font-semibold uppercase tracking-wider">Meets Capacity</th>
                  <th className="py-3 px-4 font-semibold uppercase tracking-wider">Confidence</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {mitigation.options.map((o) => (
                  <tr key={o.supplier_code} className="hover:bg-slate-850/50 transition-colors">
                    <td className="py-3.5 px-4 font-mono font-bold text-brand-400">{o.supplier_code}</td>
                    <td className="py-3.5 px-4 font-bold text-white">{o.name}</td>
                    <td className="py-3.5 px-4 text-cyan-400 font-semibold">
                      {o.lead_time_days != null ? `${o.lead_time_days} days` : "Unverified"}
                    </td>
                    <td className="py-3.5 px-4 text-slate-200">
                      {o.price_per_unit != null ? `$${o.price_per_unit.toFixed(2)}` : "Unverified"}
                    </td>
                    <td className="py-3.5 px-4 text-slate-300">
                      {o.available_quantity != null ? `${o.available_quantity} units` : "Unverified"}
                    </td>
                    <td className="py-3.5 px-4 text-slate-300">
                      {o.capacity_units_per_month != null ? `${o.capacity_units_per_month} / mo` : "Unverified"}
                    </td>
                    <td className="py-3.5 px-4">
                      {o.meets_required_quantity === null ? (
                        <span className="text-slate-500">Unknown</span>
                      ) : o.meets_required_quantity ? (
                        <span className="text-emerald-400 font-semibold flex items-center gap-1">
                          <CheckCircle2 className="w-3.5 h-3.5" /> Meets demand
                        </span>
                      ) : (
                        <span className="text-rose-400 font-semibold flex items-center gap-1">
                          <AlertCircle className="w-3.5 h-3.5" /> Shortfall
                        </span>
                      )}
                    </td>
                    <td className="py-3.5 px-4">
                      {o.meets_capacity === null ? (
                        <span className="text-slate-500">Unknown</span>
                      ) : o.meets_capacity ? (
                        <span className="text-emerald-400 font-semibold flex items-center gap-1">
                          <CheckCircle2 className="w-3.5 h-3.5" /> Sufficient
                        </span>
                      ) : (
                        <span className="text-rose-400 font-semibold flex items-center gap-1">
                          <AlertCircle className="w-3.5 h-3.5" /> Insufficient
                        </span>
                      )}
                    </td>
                    <td className="py-3.5 px-4">
                      <Badge text={o.data_confidence} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {mitigation.verification_needed && mitigation.verification_needed.length > 0 && (
          <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0 text-amber-400" />
            <span>Requires verification: {mitigation.verification_needed.join(", ")}</span>
          </div>
        )}
      </div>

      <div className="card space-y-3">
        <h3 className="text-base font-bold text-white">Recommended actions</h3>
        <ul className="list-disc list-inside text-xs text-slate-300 space-y-1.5 leading-relaxed">
          {(mitigation.recommended_actions ?? []).map((a, i) => (
            <li key={i}>{a}</li>
          ))}
        </ul>
      </div>

      <div className="card-glow-amber space-y-4">
        <div className="flex items-center gap-2 border-b border-amber-500/30 pb-3">
          <UserCheck className="w-5 h-5 text-amber-400" />
          <h3 className="text-base font-bold text-white">Human Approval</h3>
        </div>

        {!approval ? (
          <p className="text-xs text-slate-400">
            No pending approval request for this case - a decision has already been recorded, or the case has resolved.
          </p>
        ) : (
          <div className="space-y-4">
            <div className="p-4 rounded-xl bg-slate-850 border border-slate-800 space-y-2">
              <div className="flex items-center gap-2">
                <span className="text-[10px] uppercase font-bold text-slate-400">Proposed action</span>
                <span className="badge bg-amber-500/20 text-amber-300 border border-amber-500/40">
                  {ACTION_TYPE_LABELS[approval.action_type] ?? approval.action_type}
                </span>
              </div>
              <p className="text-xs text-white font-medium">{approval.description}</p>
              {approval.estimated_cost != null && (
                <p className="text-xs text-amber-400 font-bold">
                  Estimated additional cost: ${approval.estimated_cost.toLocaleString()}
                </p>
              )}
            </div>

            <div className="flex flex-col sm:flex-row items-center gap-3">
              <input
                type="email"
                value={approver}
                onChange={(e) => setApprover(e.target.value)}
                className="w-full sm:flex-1 bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-xs text-white focus:outline-none focus:border-brand-500"
                placeholder="Approver email"
              />
              <div className="flex items-center gap-2 w-full sm:w-auto">
                <button
                  disabled={busy}
                  onClick={() => decide("approved")}
                  className="flex-1 sm:flex-none py-2.5 px-5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs flex items-center justify-center gap-2 shadow-glow-emerald transition-all disabled:opacity-50"
                >
                  <CheckCircle2 className="w-4 h-4" /> Approve
                </button>
                <button
                  disabled={busy}
                  onClick={() => decide("rejected")}
                  className="flex-1 sm:flex-none py-2.5 px-5 rounded-xl bg-rose-600/20 hover:bg-rose-600/30 text-rose-300 border border-rose-500/40 font-bold text-xs flex items-center justify-center gap-2 transition-all disabled:opacity-50"
                >
                  <XCircle className="w-4 h-4" /> Reject
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
