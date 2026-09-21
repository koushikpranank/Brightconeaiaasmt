import { useState } from "react";
import { AlertOctagon, CheckCircle2, Play, RefreshCw, RotateCcw, X } from "lucide-react";
import { api } from "../api/client";

interface SimulationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

// Defaults match the steel-plate scenario seeded by backend/app/seed_data.py.
const WORKED_EXAMPLE_PO = "PO-1001";

export default function SimulationModal({ isOpen, onClose, onSuccess }: SimulationModalProps) {
  const [activeTab, setActiveTab] = useState<"preset" | "custom">("preset");
  const [poNumber, setPoNumber] = useState(WORKED_EXAMPLE_PO);
  const [material, setMaterial] = useState("Steel Plate");
  const [supplierCode, setSupplierCode] = useState("SUP-001");
  const [delayDays, setDelayDays] = useState(10);
  const [reason, setReason] = useState("Production line breakdown at mill");
  const [loading, setLoading] = useState(false);
  const [feedback, setFeedback] = useState<{ type: "success" | "error"; message: string } | null>(null);

  if (!isOpen) return null;

  async function handleSimulateDelay() {
    setLoading(true);
    setFeedback(null);
    try {
      await api.simulateDelay(poNumber, material, supplierCode, Number(delayDays), reason);
      const sweep = await api.runMonitoring();
      setFeedback({
        type: "success",
        message: `Disruption simulated successfully! Monitoring sweep processed ${sweep.cases_processed.length} case(s).`,
      });
      setTimeout(() => {
        onSuccess();
        onClose();
      }, 1500);
    } catch (err: any) {
      setFeedback({ type: "error", message: err.message || "Failed to simulate delay." });
    } finally {
      setLoading(false);
    }
  }

  async function handleSimulateRestore() {
    setLoading(true);
    setFeedback(null);
    try {
      await api.simulateRestore(WORKED_EXAMPLE_PO);
      const sweep = await api.runMonitoring();
      setFeedback({
        type: "success",
        message: `Delivery date restored! Sweep verified candidate resolution (${sweep.cases_processed.length} case(s) updated).`,
      });
      setTimeout(() => {
        onSuccess();
        onClose();
      }, 1500);
    } catch (err: any) {
      setFeedback({ type: "error", message: err.message || "Failed to restore delivery." });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fade-in">
      <div className="card w-full max-w-lg bg-slate-900 border-slate-800 shadow-2xl relative">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-3 pb-4 border-b border-slate-800">
          <div className="p-2.5 rounded-xl bg-brand-500/20 text-brand-400">
            <Play className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-white">Disruption Simulator</h3>
            <p className="text-xs text-slate-400">Inject test scenarios into the 7-agent AI pipeline</p>
          </div>
        </div>

        <div className="flex border-b border-slate-800 mt-4">
          <button
            onClick={() => setActiveTab("preset")}
            className={`flex-1 py-2.5 text-xs font-semibold border-b-2 transition-colors ${
              activeTab === "preset"
                ? "border-brand-500 text-brand-400"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            Specification Test Presets
          </button>
          <button
            onClick={() => setActiveTab("custom")}
            className={`flex-1 py-2.5 text-xs font-semibold border-b-2 transition-colors ${
              activeTab === "custom"
                ? "border-brand-500 text-brand-400"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            Custom Scenario Form
          </button>
        </div>

        <div className="py-4 space-y-4">
          {activeTab === "preset" ? (
            <div className="space-y-3">
              <div className="p-4 rounded-xl bg-slate-850 border border-slate-800 hover:border-slate-700 transition-colors">
                <div className="flex items-start justify-between">
                  <div>
                    <span className="badge bg-amber-500/20 text-amber-300 border-amber-500/40 mb-1">
                      Spec Worked Example (TC-01)
                    </span>
                    <h4 className="text-sm font-semibold text-white mt-1">10-Day Steel Plate Supplier Delay</h4>
                    <p className="text-xs text-slate-400 mt-1">
                      {WORKED_EXAMPLE_PO} (25t on-hand stock, 5t/day burn rate = 5 days runway). Stockout occurs
                      Sept 24 before delayed delivery Sept 30.
                    </p>
                  </div>
                </div>
                <button
                  onClick={handleSimulateDelay}
                  disabled={loading}
                  className="mt-3 w-full py-2 px-4 rounded-xl bg-amber-600 hover:bg-amber-500 text-white font-medium text-xs flex items-center justify-center gap-2 transition-colors disabled:opacity-50"
                >
                  {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <AlertOctagon className="w-4 h-4" />}
                  Inject TC-01 disruption (10-day delay)
                </button>
              </div>

              <div className="p-4 rounded-xl bg-slate-850 border border-slate-800 hover:border-slate-700 transition-colors">
                <div className="flex items-start justify-between">
                  <div>
                    <span className="badge bg-emerald-500/20 text-emerald-300 border-emerald-500/40 mb-1">
                      Auto-Resolution (TC-05)
                    </span>
                    <h4 className="text-sm font-semibold text-white mt-1">Restore Promised Delivery Date</h4>
                    <p className="text-xs text-slate-400 mt-1">
                      Resets {WORKED_EXAMPLE_PO} back to its original delivery date. Re-confirmation in the
                      Detection Agent marks the case resolved.
                    </p>
                  </div>
                </div>
                <button
                  onClick={handleSimulateRestore}
                  disabled={loading}
                  className="mt-3 w-full py-2 px-4 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-xs flex items-center justify-center gap-2 transition-colors disabled:opacity-50"
                >
                  {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <RotateCcw className="w-4 h-4" />}
                  Inject TC-05 restoration (reset PO date)
                </button>
              </div>
            </div>
          ) : (
            <div className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-400 mb-1 font-medium">Purchase Order Number</label>
                <input
                  type="text"
                  value={poNumber}
                  onChange={(e) => setPoNumber(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-brand-500"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 mb-1 font-medium">Material Name</label>
                  <input
                    type="text"
                    value={material}
                    onChange={(e) => setMaterial(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-brand-500"
                  />
                </div>
                <div>
                  <label className="block text-slate-400 mb-1 font-medium">Supplier Code</label>
                  <input
                    type="text"
                    value={supplierCode}
                    onChange={(e) => setSupplierCode(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-brand-500"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 mb-1 font-medium">Delay (Days)</label>
                  <input
                    type="number"
                    value={delayDays}
                    onChange={(e) => setDelayDays(Number(e.target.value))}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-brand-500"
                  />
                </div>
                <div>
                  <label className="block text-slate-400 mb-1 font-medium">Reason Note</label>
                  <input
                    type="text"
                    value={reason}
                    onChange={(e) => setReason(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-brand-500"
                  />
                </div>
              </div>

              <button
                onClick={handleSimulateDelay}
                disabled={loading}
                className="mt-2 w-full py-2.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-semibold text-xs flex items-center justify-center gap-2 transition-colors disabled:opacity-50"
              >
                {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                Run custom simulation & trigger sweep
              </button>
            </div>
          )}

          {feedback && (
            <div
              className={`p-3 rounded-xl text-xs flex items-center gap-2 ${
                feedback.type === "success"
                  ? "bg-emerald-500/10 border border-emerald-500/30 text-emerald-400"
                  : "bg-rose-500/10 border border-rose-500/30 text-rose-400"
              }`}
            >
              {feedback.type === "success" ? <CheckCircle2 className="w-4 h-4 shrink-0" /> : <X className="w-4 h-4 shrink-0" />}
              <span>{feedback.message}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
