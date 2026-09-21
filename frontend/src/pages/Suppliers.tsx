import { useEffect, useState } from "react";
import { AlertTriangle, Filter, RotateCcw, Search, Users } from "lucide-react";
import { api } from "../api/client";
import Badge from "../components/Badge";
import type { Supplier } from "../types";

export default function Suppliers() {
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [filterPrimary, setFilterPrimary] = useState(false);
  const [busyCode, setBusyCode] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  async function loadData() {
    const s = await api.suppliers();
    setSuppliers(s);
    setLoading(false);
  }

  useEffect(() => {
    loadData();
  }, []);

  async function handleSimulateLeadTimeIncrease(s: Supplier) {
    if (s.lead_time_days == null) return;
    setBusyCode(s.supplier_code);
    try {
      await api.simulateLeadTimeIncrease(s.supplier_code, Math.round(s.lead_time_days * 2.2));
      setNotice(`${s.supplier_code}'s quoted lead time was raised well above its baseline - check Disruption Alerts.`);
      await loadData();
    } finally {
      setBusyCode(null);
      setTimeout(() => setNotice(null), 5000);
    }
  }

  async function handleRestoreLeadTime(s: Supplier) {
    setBusyCode(s.supplier_code);
    try {
      await api.simulateLeadTimeRestore(s.supplier_code);
      setNotice(`${s.supplier_code}'s lead time was restored to baseline.`);
      await loadData();
    } finally {
      setBusyCode(null);
      setTimeout(() => setNotice(null), 5000);
    }
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-96 gap-3">
        <Users className="w-8 h-8 text-brand-400 animate-spin" />
        <p className="text-slate-400 text-sm font-medium">Loading suppliers...</p>
      </div>
    );
  }

  const filteredSuppliers = suppliers.filter((s) => {
    const matchesSearch =
      s.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      s.material.toLowerCase().includes(searchTerm.toLowerCase()) ||
      s.supplier_code.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesPrimary = filterPrimary ? s.is_primary : true;
    return matchesSearch && matchesPrimary;
  });

  return (
    <div className="space-y-8 animate-fade-in">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
          <Users className="w-6 h-6 text-brand-400" /> Supplier Directory
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Primary and alternative material suppliers, with lead time, pricing, on-hand quantity, and ongoing capacity.
        </p>
      </div>

      {notice && (
        <div className="p-3.5 rounded-xl bg-brand-500/15 border border-brand-500/30 text-xs text-brand-300 flex items-center gap-2 animate-fade-in">
          <AlertTriangle className="w-4 h-4 shrink-0 text-brand-400" />
          <span>{notice}</span>
        </div>
      )}

      <div className="card p-4 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
          <input
            type="text"
            placeholder="Search material, code, or supplier name..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-9 pr-4 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-brand-500 transition-colors"
          />
        </div>

        <button
          onClick={() => setFilterPrimary(!filterPrimary)}
          className={`py-2 px-3.5 rounded-xl text-xs font-semibold flex items-center gap-2 border transition-all ${
            filterPrimary
              ? "bg-brand-600/20 text-brand-300 border-brand-500/40 shadow-glow"
              : "bg-slate-850 text-slate-400 border-slate-800 hover:border-slate-700"
          }`}
        >
          <Filter className="w-3.5 h-3.5" />
          {filterPrimary ? "Primary vendors only" : "All vendors"}
        </button>
      </div>

      <div className="card overflow-hidden p-0">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-850/80 border-b border-slate-800 text-slate-400">
              <tr>
                <th className="py-3.5 px-5 font-semibold uppercase tracking-wider">Vendor Code</th>
                <th className="py-3.5 px-5 font-semibold uppercase tracking-wider">Supplier Name</th>
                <th className="py-3.5 px-5 font-semibold uppercase tracking-wider">Material</th>
                <th className="py-3.5 px-5 font-semibold uppercase tracking-wider">Lead Time</th>
                <th className="py-3.5 px-5 font-semibold uppercase tracking-wider">Unit Price</th>
                <th className="py-3.5 px-5 font-semibold uppercase tracking-wider">Available Qty</th>
                <th className="py-3.5 px-5 font-semibold uppercase tracking-wider">Capacity / mo</th>
                <th className="py-3.5 px-5 font-semibold uppercase tracking-wider">Primary</th>
                <th className="py-3.5 px-5 font-semibold uppercase tracking-wider">Status</th>
                <th className="py-3.5 px-5 font-semibold uppercase tracking-wider text-right">Demo Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {filteredSuppliers.map((s) => {
                const leadTimeElevated =
                  s.lead_time_days != null && s.baseline_lead_time_days != null && s.lead_time_days > s.baseline_lead_time_days;
                return (
                  <tr key={s.id} className="hover:bg-slate-850/50 transition-colors">
                    <td className="py-4 px-5 font-mono text-brand-400 font-bold">{s.supplier_code}</td>
                    <td className="py-4 px-5 font-bold text-white">{s.name}</td>
                    <td className="py-4 px-5 text-slate-300">{s.material}</td>
                    <td className="py-4 px-5 font-medium">
                      {s.lead_time_days != null ? (
                        <span className={leadTimeElevated ? "text-rose-400" : "text-cyan-400"}>
                          {s.lead_time_days} days
                          {leadTimeElevated && (
                            <span className="ml-1.5 text-[10px] text-rose-400/80">
                              (baseline {s.baseline_lead_time_days}d)
                            </span>
                          )}
                        </span>
                      ) : (
                        <span className="text-slate-500 italic">unverified</span>
                      )}
                    </td>
                    <td className="py-4 px-5 font-medium text-slate-200">
                      {s.price_per_unit != null ? `${s.currency} ${s.price_per_unit.toFixed(2)}` : <span className="text-slate-500 italic">unverified</span>}
                    </td>
                    <td className="py-4 px-5 font-medium text-slate-300">
                      {s.available_quantity != null ? `${s.available_quantity.toLocaleString()} units` : <span className="text-slate-500 italic">unverified</span>}
                    </td>
                    <td className="py-4 px-5 font-medium text-slate-300">
                      {s.capacity_units_per_month != null ? `${s.capacity_units_per_month.toLocaleString()} / mo` : <span className="text-slate-500 italic">unverified</span>}
                    </td>
                    <td className="py-4 px-5">
                      {s.is_primary ? (
                        <span className="badge bg-brand-500/20 text-brand-300 border border-brand-500/30">Primary</span>
                      ) : (
                        <span className="text-slate-500 text-[11px]">Alternative</span>
                      )}
                    </td>
                    <td className="py-4 px-5">
                      <Badge text={s.status} />
                    </td>
                    <td className="py-4 px-5 text-right space-x-2 whitespace-nowrap">
                      <button
                        disabled={busyCode === s.supplier_code || s.lead_time_days == null || s.status !== "active"}
                        onClick={() => handleSimulateLeadTimeIncrease(s)}
                        className="py-1.5 px-3 rounded-lg bg-amber-500/15 hover:bg-amber-500/25 border border-amber-500/30 text-amber-300 text-[11px] font-semibold transition-all disabled:opacity-40"
                      >
                        Raise lead time
                      </button>
                      <button
                        disabled={busyCode === s.supplier_code || !leadTimeElevated}
                        onClick={() => handleRestoreLeadTime(s)}
                        className="py-1.5 px-3 rounded-lg bg-emerald-500/15 hover:bg-emerald-500/25 border border-emerald-500/30 text-emerald-300 text-[11px] font-semibold transition-all disabled:opacity-40 inline-flex items-center gap-1"
                      >
                        <RotateCcw className="w-3 h-3" /> Restore
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
