import { useEffect, useState } from "react";
import { CheckSquare, Search } from "lucide-react";
import { api } from "../api/client";
import Badge from "../components/Badge";
import type { ActionItem } from "../types";

const STATUSES = ["open", "in_progress", "done"];

export default function ActionTracker() {
  const [actions, setActions] = useState<ActionItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");

  async function loadData() {
    try {
      const data = await api.actions();
      setActions(data);
    } catch (err) {
      console.error("Failed to load action items:", err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  async function handleChangeStatus(id: number, newStatus: string) {
    await api.updateAction(id, newStatus);
    await loadData();
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-96 gap-3">
        <CheckSquare className="w-8 h-8 text-brand-400 animate-spin" />
        <p className="text-slate-400 text-sm font-medium">Loading action tracker...</p>
      </div>
    );
  }

  const filteredActions = actions.filter(
    (a) =>
      a.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
      a.responsible_team.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-8 animate-fade-in">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
          <CheckSquare className="w-6 h-6 text-brand-400" /> Action Tracker
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Tasks assigned to responsible teams by the Alert & Response Agent.
        </p>
      </div>

      <div className="card p-4">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
          <input
            type="text"
            placeholder="Search by team or description..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-9 pr-4 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-brand-500 transition-colors"
          />
        </div>
      </div>

      <div className="card space-y-4">
        {filteredActions.length === 0 ? (
          <p className="text-xs text-slate-400 italic">No action items assigned yet.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-850/80 border-b border-slate-800 text-slate-400">
                <tr>
                  <th className="py-3.5 px-4 font-semibold uppercase tracking-wider">Description</th>
                  <th className="py-3.5 px-4 font-semibold uppercase tracking-wider">Responsible Team</th>
                  <th className="py-3.5 px-4 font-semibold uppercase tracking-wider">Status</th>
                  <th className="py-3.5 px-4 font-semibold uppercase tracking-wider text-right">Update</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {filteredActions.map((a) => (
                  <tr key={a.id} className="hover:bg-slate-850/50 transition-colors">
                    <td className="py-4 px-4 font-medium text-white max-w-md leading-relaxed">{a.description}</td>
                    <td className="py-4 px-4">
                      <span className="badge bg-cyan-500/15 text-cyan-300 border border-cyan-500/30">
                        {a.responsible_team}
                      </span>
                    </td>
                    <td className="py-4 px-4">
                      <Badge text={a.status} />
                    </td>
                    <td className="py-4 px-4 text-right">
                      <select
                        value={a.status}
                        onChange={(e) => handleChangeStatus(a.id, e.target.value)}
                        className="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-brand-500 capitalize"
                      >
                        {STATUSES.map((s) => (
                          <option key={s} value={s}>
                            {s.replace(/_/g, " ")}
                          </option>
                        ))}
                      </select>
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
