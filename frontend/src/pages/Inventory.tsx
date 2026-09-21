import { useEffect, useState } from "react";
import { Boxes } from "lucide-react";
import { api } from "../api/client";
import Badge from "../components/Badge";
import type { InventoryItem } from "../types";

export default function Inventory() {
  const [items, setItems] = useState<InventoryItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.inventory().then((i) => {
      setItems(i);
      setLoading(false);
    });
  }, []);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-96 gap-3">
        <Boxes className="w-8 h-8 text-brand-400 animate-spin" />
        <p className="text-slate-400 text-sm font-medium">Loading inventory...</p>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-fade-in">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
          <Boxes className="w-6 h-6 text-brand-400" /> Inventory & Burn Rate
        </h2>
        <p className="text-xs text-slate-400 mt-1">On-hand stock, daily consumption, and stockout runway.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {items.map((item) => {
          const coverage = item.daily_consumption > 0 ? item.current_quantity / item.daily_consumption : null;
          const atRisk = coverage !== null && coverage <= item.reorder_point_days;
          const progressPercent = Math.min(100, Math.max(10, ((coverage ?? 0) / (item.reorder_point_days * 2)) * 100));

          return (
            <div
              key={item.id}
              className={`card ${
                atRisk ? "border-amber-500/40 bg-amber-950/10 shadow-glow-amber" : "border-slate-800 hover:border-slate-700"
              }`}
            >
              <div className="flex items-start justify-between">
                <div>
                  <span className="text-[11px] font-mono text-slate-400 uppercase tracking-wider block">Material</span>
                  <h3 className="text-lg font-bold text-white mt-0.5">{item.material}</h3>
                </div>
                <Badge text={atRisk ? "at_risk" : "active"} />
              </div>

              <div className="mt-5 space-y-3 text-xs">
                <div className="flex justify-between py-1.5 border-b border-slate-800">
                  <span className="text-slate-400">On-hand quantity:</span>
                  <span className="font-bold text-white">
                    {item.current_quantity} {item.unit}
                  </span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-slate-800">
                  <span className="text-slate-400">Daily consumption:</span>
                  <span className="font-bold text-amber-400">
                    {item.daily_consumption} {item.unit}/day
                  </span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-slate-800">
                  <span className="text-slate-400">Reorder threshold:</span>
                  <span className="font-semibold text-slate-300">{item.reorder_point_days} days</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-slate-800">
                  <span className="text-slate-400">Coverage:</span>
                  <span className={`font-extrabold ${atRisk ? "text-rose-400" : "text-emerald-400"}`}>
                    {coverage !== null ? `${coverage.toFixed(1)} days` : "N/A"}
                  </span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-800/60">
                  <span className="text-slate-400">Snapshot:</span>
                  <span className="text-[11px] text-slate-400 font-mono">
                    {item.snapshot_at ? new Date(item.snapshot_at).toLocaleString() : "Unavailable"}
                  </span>
                </div>
              </div>

              <div className="mt-4 pt-2">
                <div className="flex justify-between text-[10px] text-slate-400 mb-1">
                  <span>Stock runway</span>
                  <span>{coverage !== null ? `${coverage.toFixed(1)}d / ${item.reorder_point_days}d threshold` : ""}</span>
                </div>
                <div className="w-full h-2 rounded-full bg-slate-800 overflow-hidden">
                  <div
                    className={`h-full transition-all duration-500 rounded-full ${
                      atRisk ? "bg-gradient-to-r from-amber-500 to-rose-500" : "bg-gradient-to-r from-cyan-500 to-emerald-500"
                    }`}
                    style={{ width: `${progressPercent}%` }}
                  />
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
