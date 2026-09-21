import { useEffect, useState } from "react";
import { Download, FileText } from "lucide-react";
import { api } from "../api/client";
import Badge from "../components/Badge";
import type { DisruptionCase } from "../types";

export default function Reports() {
  const [cases, setCases] = useState<DisruptionCase[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.cases().then((c) => {
      setCases(c);
      setLoading(false);
    });
  }, []);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-96 gap-3">
        <FileText className="w-8 h-8 text-brand-400 animate-spin" />
        <p className="text-slate-400 text-sm font-medium">Loading reports...</p>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-fade-in">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
          <FileText className="w-6 h-6 text-brand-400" /> Reports
        </h2>
        <p className="text-xs text-slate-400 mt-1">Export a Disruption Assessment Report for any case.</p>
      </div>

      <div className="card space-y-4">
        {cases.length === 0 ? (
          <p className="text-xs text-slate-400 italic">No disruption cases yet.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-850/80 border-b border-slate-800 text-slate-400">
                <tr>
                  <th className="py-3.5 px-4 font-semibold uppercase tracking-wider">Case Number</th>
                  <th className="py-3.5 px-4 font-semibold uppercase tracking-wider">Material</th>
                  <th className="py-3.5 px-4 font-semibold uppercase tracking-wider">Disruption Type</th>
                  <th className="py-3.5 px-4 font-semibold uppercase tracking-wider">Status</th>
                  <th className="py-3.5 px-4 font-semibold uppercase tracking-wider">Last Updated</th>
                  <th className="py-3.5 px-4 font-semibold uppercase tracking-wider text-right">Report</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {cases.map((c) => (
                  <tr key={c.case_number} className="hover:bg-slate-850/50 transition-colors">
                    <td className="py-4 px-4 font-mono font-bold text-brand-400">{c.case_number}</td>
                    <td className="py-4 px-4 font-bold text-white">{c.material}</td>
                    <td className="py-4 px-4 capitalize text-slate-300">{c.disruption_type.replace(/_/g, " ")}</td>
                    <td className="py-4 px-4">
                      <Badge text={c.status} />
                    </td>
                    <td className="py-4 px-4 text-slate-400 font-mono text-[11px]">
                      {new Date(c.updated_at).toLocaleString()}
                    </td>
                    <td className="py-4 px-4 text-right">
                      <a
                        href={api.reportPdfUrl(c.case_number)}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-2 py-2 px-4 rounded-xl bg-gradient-to-r from-brand-600 to-brand-700 hover:from-brand-500 hover:to-brand-600 text-white font-bold text-xs shadow-glow transition-all"
                      >
                        <Download className="w-3.5 h-3.5" /> Download PDF
                      </a>
                    </td>
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
