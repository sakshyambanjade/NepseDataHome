import React from "react";
import { cn } from "./utils";

const toneMap = {
  accumulation: [
    [75, "bg-emerald-400/15 text-emerald-200 ring-emerald-400/30"],
    [50, "bg-emerald-400/10 text-emerald-300 ring-emerald-400/20"],
    [0, "bg-slate-400/10 text-slate-300 ring-slate-400/20"],
  ],
  distribution: [
    [75, "bg-rose-400/15 text-rose-200 ring-rose-400/30"],
    [50, "bg-rose-400/10 text-rose-300 ring-rose-400/20"],
    [0, "bg-slate-400/10 text-slate-300 ring-slate-400/20"],
  ],
  warning: [
    [75, "bg-amber-400/15 text-amber-200 ring-amber-400/30"],
    [50, "bg-amber-400/10 text-amber-300 ring-amber-400/20"],
    [0, "bg-slate-400/10 text-slate-300 ring-slate-400/20"],
  ],
  neutral: [
    [75, "bg-cyan-400/15 text-cyan-200 ring-cyan-400/30"],
    [50, "bg-cyan-400/10 text-cyan-300 ring-cyan-400/20"],
    [0, "bg-slate-400/10 text-slate-300 ring-slate-400/20"],
  ],
};

function classesFor(score = 0, tone = "neutral") {
  const scale = toneMap[tone] || toneMap.neutral;
  return scale.find(([threshold]) => Number(score) >= threshold)?.[1] || scale.at(-1)[1];
}

export function ScoreBadge({ score, tone = "neutral", suffix = "", className = "" }) {
  const value = Number.isFinite(Number(score)) ? Number(score).toFixed(Number(score) % 1 === 0 ? 0 : 1) : "N/A";

  return (
    <span
      className={cn(
        "inline-flex min-w-[3.75rem] items-center justify-center rounded-full px-3 py-1 text-xs font-bold tabular-nums ring-1",
        classesFor(score, tone),
        className
      )}
    >
      {value}{suffix}
    </span>
  );
}
