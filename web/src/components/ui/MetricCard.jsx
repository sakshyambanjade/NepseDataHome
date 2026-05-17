import React from "react";
import { ArrowDownRight, ArrowUpRight } from "lucide-react";
import { Card } from "./Card";
import { cn } from "./utils";

const toneClasses = {
  emerald: "text-emerald-300 bg-emerald-400/10 border-emerald-400/20",
  rose: "text-rose-300 bg-rose-400/10 border-rose-400/20",
  amber: "text-amber-300 bg-amber-400/10 border-amber-400/20",
  cyan: "text-cyan-300 bg-cyan-400/10 border-cyan-400/20",
  slate: "text-slate-300 bg-slate-400/10 border-slate-400/20",
};

export function MetricCard({
  label,
  value,
  detail,
  icon: Icon,
  tone = "cyan",
  direction,
  className = "",
}) {
  const DirectionIcon = direction === "down" ? ArrowDownRight : direction === "up" ? ArrowUpRight : null;

  return (
    <Card className={cn("p-5", className)} interactive>
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">{label}</p>
          <p className="mt-3 truncate text-2xl font-bold tracking-tight text-white">{value}</p>
          {detail ? <p className="mt-2 line-clamp-2 text-sm text-slate-400">{detail}</p> : null}
        </div>
        {Icon ? (
          <div className={cn("rounded-2xl border p-3", toneClasses[tone] || toneClasses.cyan)}>
            <Icon className="h-5 w-5" />
          </div>
        ) : null}
      </div>
      {DirectionIcon ? (
        <DirectionIcon className={cn("mt-4 h-5 w-5", direction === "down" ? "text-rose-300" : "text-emerald-300")} />
      ) : null}
    </Card>
  );
}
