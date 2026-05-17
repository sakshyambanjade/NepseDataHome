import React from "react";
import { ChevronDown, ChevronUp } from "lucide-react";
import { cn } from "./utils";

export function DataTable({ columns, data, sortConfig, onSort, rowKey, onRowClick, emptyState }) {
  if (!data?.length) {
    return emptyState || null;
  }

  return (
    <div className="overflow-hidden rounded-3xl border border-white/10 bg-white/[0.035] backdrop-blur-xl">
      <div className="overflow-x-auto">
        <table className="w-full min-w-[1100px] border-collapse text-left">
          <thead className="sticky top-0 z-10 bg-slate-950/95 backdrop-blur-xl">
            <tr className="border-b border-white/10">
              {columns.map((column) => {
                const sortable = Boolean(column.sortKey);
                const active = sortConfig?.key === column.sortKey;
                return (
                  <th
                    key={column.key}
                    onClick={sortable ? () => onSort(column.sortKey) : undefined}
                    className={cn(
                      "px-5 py-4 text-xs font-bold uppercase tracking-[0.16em] text-slate-500",
                      sortable && "cursor-pointer select-none transition hover:text-white",
                      column.className
                    )}
                  >
                    <span className="inline-flex items-center gap-1.5">
                      {column.header}
                      {active && (sortConfig.direction === "desc" ? <ChevronDown className="h-3.5 w-3.5" /> : <ChevronUp className="h-3.5 w-3.5" />)}
                    </span>
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {data.map((row, index) => (
              <tr
                key={rowKey ? rowKey(row) : row.id || row.symbol || index}
                onClick={onRowClick ? () => onRowClick(row) : undefined}
                className={cn(
                  "group transition duration-150 hover:bg-cyan-400/[0.055]",
                  onRowClick && "cursor-pointer"
                )}
              >
                {columns.map((column) => (
                  <td key={column.key} className={cn("px-5 py-4 align-middle", column.cellClassName)}>
                    {column.render ? column.render(row) : row[column.key]}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
