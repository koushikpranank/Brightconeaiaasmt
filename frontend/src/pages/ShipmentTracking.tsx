import { useEffect, useState } from "react";
import { CheckCircle2, Truck } from "lucide-react";
import { api } from "../api/client";
import Badge from "../components/Badge";
import type { PurchaseOrder } from "../types";

export default function ShipmentTracking() {
  const [orders, setOrders] = useState<PurchaseOrder[]>([]);
  const [loading, setLoading] = useState(true);
  const [delayDays, setDelayDays] = useState(10);
  const [busyPo, setBusyPo] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  async function loadData() {
    try {
      const data = await api.purchaseOrders();
      setOrders(data);
    } catch (err) {
      console.error("Failed to load POs:", err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  async function handleSimulateDelay(po: PurchaseOrder) {
    setBusyPo(po.po_number);
    try {
      await api.simulateDelay(po.po_number, po.material, po.supplier_code, delayDays, "Supplier announced delay");
      const sweep = await api.runMonitoring();
      setNotice(`Simulated ${delayDays}-day delay on ${po.po_number}! Monitoring sweep updated ${sweep.cases_processed.length} case(s).`);
      await loadData();
    } catch (err: any) {
      setNotice(`Failed to simulate delay: ${err.message}`);
    } finally {
      setBusyPo(null);
      setTimeout(() => setNotice(null), 5000);
    }
  }

  async function handleRestore(po: PurchaseOrder) {
    setBusyPo(po.po_number);
    try {
      await api.simulateRestore(po.po_number);
      const sweep = await api.runMonitoring();
      setNotice(`Restored schedule for ${po.po_number}! Detection Agent auto-resolved ${sweep.cases_processed.length} case(s).`);
      await loadData();
    } catch (err: any) {
      setNotice(`Failed to restore PO: ${err.message}`);
    } finally {
      setBusyPo(null);
      setTimeout(() => setNotice(null), 5000);
    }
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-96 gap-3">
        <Truck className="w-8 h-8 text-brand-400 animate-spin" />
        <p className="text-slate-400 text-sm font-medium">Loading purchase order tracking data...</p>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-fade-in">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
          <Truck className="w-6 h-6 text-brand-400" /> Purchase Orders & Shipment Tracking
        </h2>
        <p className="text-xs text-slate-400 mt-1">Track deliveries, detect schedule variances, and trigger test signals.</p>
      </div>

      {notice && (
        <div className="p-3.5 rounded-xl bg-brand-500/15 border border-brand-500/30 text-xs text-brand-300 flex items-center gap-2 animate-fade-in">
          <CheckCircle2 className="w-4 h-4 shrink-0 text-brand-400" />
          <span>{notice}</span>
        </div>
      )}

      <div className="card space-y-4">
        <div className="flex items-center gap-3 pb-4 border-b border-slate-800/80">
          <span className="text-xs text-slate-400 font-semibold">Test delay (days):</span>
          <input
            type="number"
            min={1}
            max={60}
            value={delayDays}
            onChange={(e) => setDelayDays(Number(e.target.value))}
            className="w-20 bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1 text-xs text-white text-center focus:outline-none focus:border-brand-500"
          />
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="text-slate-400 border-b border-slate-800">
              <tr>
                <th className="pb-3.5 font-semibold uppercase tracking-wider">PO Number</th>
                <th className="pb-3.5 font-semibold uppercase tracking-wider">Material</th>
                <th className="pb-3.5 font-semibold uppercase tracking-wider">Supplier</th>
                <th className="pb-3.5 font-semibold uppercase tracking-wider">Original Delivery</th>
                <th className="pb-3.5 font-semibold uppercase tracking-wider">Revised Delivery</th>
                <th className="pb-3.5 font-semibold uppercase tracking-wider">Status</th>
                <th className="pb-3.5 font-semibold uppercase tracking-wider text-right">Demo Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {orders.map((po) => (
                <tr key={po.id} className="hover:bg-slate-850/50 transition-colors">
                  <td className="py-4 font-mono font-bold text-brand-400">{po.po_number}</td>
                  <td className="py-4 font-bold text-white">{po.material}</td>
                  <td className="py-4 text-slate-300 font-mono">{po.supplier_code}</td>
                  <td className="py-4 text-slate-300">{po.original_delivery_date}</td>
                  <td className="py-4">
                    {po.revised_delivery_date ? (
                      <span className="font-semibold text-rose-400">{po.revised_delivery_date}</span>
                    ) : (
                      <span className="text-slate-500 italic">On schedule</span>
                    )}
                  </td>
                  <td className="py-4">
                    <Badge text={po.status} />
                  </td>
                  <td className="py-4 text-right space-x-2">
                    <button
                      disabled={busyPo === po.po_number}
                      onClick={() => handleSimulateDelay(po)}
                      className="py-1.5 px-3 rounded-lg bg-amber-500/15 hover:bg-amber-500/25 border border-amber-500/30 text-amber-300 text-[11px] font-semibold transition-all disabled:opacity-50"
                    >
                      {busyPo === po.po_number ? "Simulating..." : "Simulate delay"}
                    </button>
                    <button
                      disabled={busyPo === po.po_number || po.status !== "delayed"}
                      onClick={() => handleRestore(po)}
                      className="py-1.5 px-3 rounded-lg bg-emerald-500/15 hover:bg-emerald-500/25 border border-emerald-500/30 text-emerald-300 text-[11px] font-semibold transition-all disabled:opacity-50"
                    >
                      Restore schedule
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
