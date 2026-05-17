import React from "react";
import { Card } from "./Card";

export function PageHeader({ eyebrow, title, description, icon: Icon, children }) {
  return (
    <Card className="relative overflow-hidden p-6 sm:p-8">
      <div className="absolute right-0 top-0 h-48 w-48 rounded-full bg-cyan-400/10 blur-3xl" />
      <div className="relative flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
        <div className="max-w-3xl">
          <div className="mb-4 flex items-center gap-3">
            {Icon ? (
              <div className="rounded-2xl border border-cyan-400/20 bg-cyan-400/10 p-3 text-cyan-300">
                <Icon className="h-6 w-6" />
              </div>
            ) : null}
            {eyebrow ? <p className="text-xs font-bold uppercase tracking-[0.24em] text-cyan-300/80">{eyebrow}</p> : null}
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-white sm:text-5xl">{title}</h1>
          {description ? <p className="mt-4 max-w-2xl text-base leading-7 text-slate-400">{description}</p> : null}
        </div>
        {children ? <div className="shrink-0">{children}</div> : null}
      </div>
    </Card>
  );
}
