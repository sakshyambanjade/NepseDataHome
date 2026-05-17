import React from "react";
import { Info } from "lucide-react";
import { cn } from "./utils";

export function InfoPill({ label, children, tone = "cyan", className = "" }) {
  const toneClass = tone === "amber"
    ? "border-amber-400/20 bg-amber-400/10 text-amber-200"
    : "border-cyan-400/20 bg-cyan-400/10 text-cyan-200";

  return (
    <span className={cn("group relative inline-flex", className)}>
      <span className={cn("inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-semibold", toneClass)}>
        <Info className="h-3.5 w-3.5" />
        {label}
      </span>
      <span className="pointer-events-none absolute left-0 top-full z-30 mt-2 w-72 rounded-2xl border border-white/10 bg-slate-950 p-3 text-left text-xs leading-5 text-slate-300 opacity-0 shadow-2xl shadow-black/40 transition group-hover:opacity-100">
        {children}
      </span>
    </span>
  );
}
