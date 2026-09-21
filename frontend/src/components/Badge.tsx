import { AlertTriangle, CheckCircle, Clock, FileCheck, XCircle } from "lucide-react";

interface BadgeProps {
  text: string;
  className?: string;
  showIcon?: boolean;
}

export default function Badge({ text, className = "", showIcon = true }: BadgeProps) {
  const normalized = text.toLowerCase().replace(/_/g, " ");

  const style = (() => {
    if (["approved", "resolved", "completed", "low", "success"].includes(text)) {
      return {
        bg: "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30",
        icon: <CheckCircle className="w-3 h-3 text-emerald-400" />,
      };
    }
    if (["pending_approval", "in_progress", "medium", "warning", "open"].includes(text)) {
      return {
        bg: "bg-amber-500/15 text-amber-400 border border-amber-500/30",
        icon: <Clock className="w-3 h-3 text-amber-400" />,
      };
    }
    if (["needs_revision"].includes(text)) {
      return {
        bg: "bg-purple-500/15 text-purple-300 border border-purple-500/30",
        icon: <AlertTriangle className="w-3 h-3 text-purple-400" />,
      };
    }
    if (["rejected", "critical", "high", "danger", "delayed"].includes(text)) {
      return {
        bg: "bg-rose-500/15 text-rose-400 border border-rose-500/30",
        icon: <XCircle className="w-3 h-3 text-rose-400" />,
      };
    }
    return {
      bg: "bg-cyan-500/15 text-cyan-400 border border-cyan-500/30",
      icon: <FileCheck className="w-3 h-3 text-cyan-400" />,
    };
  })();

  return (
    <span className={`badge ${style.bg} ${className}`}>
      {showIcon && style.icon}
      <span className="capitalize">{normalized}</span>
    </span>
  );
}
