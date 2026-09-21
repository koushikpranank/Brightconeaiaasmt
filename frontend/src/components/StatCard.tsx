import type { ReactNode } from "react";
import { AlertTriangle, CheckCircle2, Info, ShieldAlert } from "lucide-react";

interface StatCardProps {
  label: string;
  value: number | string;
  tone?: "default" | "success" | "warning" | "danger";
  subtitle?: string;
  icon?: ReactNode;
}

const TONE_CLASSES: Record<string, string> = {
  default: "border-slate-800 hover:border-brand-500/50 bg-slate-900/80 text-brand-400",
  success: "border-emerald-500/30 hover:border-emerald-500/60 bg-emerald-950/20 text-emerald-400 shadow-glow-emerald",
  warning: "border-amber-500/30 hover:border-amber-500/60 bg-amber-950/20 text-amber-400 shadow-glow-amber",
  danger: "border-rose-500/30 hover:border-rose-500/60 bg-rose-950/20 text-rose-400 shadow-glow-rose",
};

export default function StatCard({ label, value, tone = "default", subtitle, icon }: StatCardProps) {
  const defaultIcons: Record<string, ReactNode> = {
    default: <Info className="w-5 h-5 text-brand-400" />,
    success: <CheckCircle2 className="w-5 h-5 text-emerald-400" />,
    warning: <AlertTriangle className="w-5 h-5 text-amber-400" />,
    danger: <ShieldAlert className="w-5 h-5 text-rose-400" />,
  };

  return (
    <div className={`card p-5 border transition-all duration-300 hover:scale-[1.02] ${TONE_CLASSES[tone]}`}>
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">{label}</span>
        <div className="p-2 rounded-xl bg-slate-800/80 backdrop-blur">{icon ?? defaultIcons[tone]}</div>
      </div>
      <div className="mt-3 flex items-baseline gap-2">
        <span className="text-3xl font-extrabold tracking-tight text-white">{value}</span>
      </div>
      {subtitle && <p className="mt-1 text-xs text-slate-400">{subtitle}</p>}
    </div>
  );
}
