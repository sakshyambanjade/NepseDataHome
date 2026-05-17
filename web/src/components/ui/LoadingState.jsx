import React from "react";
import { Activity } from "lucide-react";

export function LoadingState({ message = "Loading intelligence..." }) {
  return (
    <div className="flex min-h-[420px] flex-col items-center justify-center py-24">
      <div className="rounded-3xl border border-cyan-400/20 bg-cyan-400/10 p-5 text-cyan-300">
        <Activity className="h-9 w-9 animate-spin" />
      </div>
      <p className="mt-5 text-sm text-slate-400">{message}</p>
    </div>
  );
}
