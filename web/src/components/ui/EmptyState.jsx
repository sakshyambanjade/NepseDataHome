import React from "react";
import { SearchX } from "lucide-react";
import { Card } from "./Card";

export function EmptyState({ title = "No matching data", message = "Try changing the search or filter.", icon: Icon = SearchX }) {
  return (
    <Card className="flex flex-col items-center justify-center px-6 py-16 text-center">
      <div className="rounded-2xl border border-white/10 bg-white/5 p-4 text-slate-400">
        <Icon className="h-7 w-7" />
      </div>
      <h3 className="mt-5 text-lg font-semibold text-white">{title}</h3>
      <p className="mt-2 max-w-sm text-sm text-slate-400">{message}</p>
    </Card>
  );
}
