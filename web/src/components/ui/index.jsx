import React from 'react';
import { Info, Activity } from 'lucide-react';

export function Card({ children, className = '', noPadding = false }) {
  return (
    <div className={`glass-morphism rounded-3xl border border-white/5 overflow-hidden ${noPadding ? '' : 'p-6'} ${className}`}>
      {children}
    </div>
  );
}

export function MetricCard({ title, value, icon, subtitle, colorClass = "text-white", bgClass = "bg-white/5" }) {
  return (
    <Card className="flex flex-col h-full hover:bg-white/5 transition-colors">
      <div className="flex items-center space-x-3 mb-4">
        {icon && (
          <div className={`p-2 rounded-xl ${bgClass}`}>
            {React.cloneElement(icon, { className: `w-5 h-5 ${colorClass}` })}
          </div>
        )}
        <div className="text-[10px] text-gray-500 font-bold uppercase tracking-wider">{title}</div>
      </div>
      <div className="mt-auto">
        <div className={`text-3xl font-black ${colorClass}`}>{value}</div>
        {subtitle && <div className="text-xs text-gray-400 mt-1">{subtitle}</div>}
      </div>
    </Card>
  );
}

export function ScoreBadge({ score, type = 'neutral' }) {
  // Types: accumulation (emerald), distribution (rose), pattern (amber), neutral (blue/slate)
  let colorClass = "text-gray-400 bg-gray-400/10 border-gray-400/20";
  
  if (type === 'accumulation') {
    if (score >= 80) colorClass = "text-emerald-400 bg-emerald-500/10 border-emerald-500/20";
    else if (score >= 50) colorClass = "text-emerald-500/80 bg-emerald-500/5 border-emerald-500/10";
  } else if (type === 'distribution') {
    if (score >= 80) colorClass = "text-rose-400 bg-rose-500/10 border-rose-500/20";
    else if (score >= 50) colorClass = "text-rose-500/80 bg-rose-500/5 border-rose-500/10";
  } else if (type === 'pattern') {
    if (score >= 80) colorClass = "text-amber-400 bg-amber-500/10 border-amber-500/20 shadow-[0_0_10px_rgba(245,158,11,0.2)]";
    else if (score >= 50) colorClass = "text-amber-500/80 bg-amber-500/5 border-amber-500/10";
  } else {
    if (score >= 80) colorClass = "text-blue-400 bg-blue-500/10 border-blue-500/20";
    else if (score >= 50) colorClass = "text-blue-500/80 bg-blue-500/5 border-blue-500/10";
  }

  return (
    <div className={`inline-flex items-center justify-center px-3 py-1 rounded-full text-xs font-black border ${colorClass}`}>
      {score}
    </div>
  );
}

export function PageHeader({ title, subtitle, icon, rightElement, className = '' }) {
  return (
    <div className={`relative overflow-hidden glass-morphism rounded-[2.5rem] p-8 border border-white/5 mb-8 ${className}`}>
      {/* Subtle background glow */}
      <div className="absolute top-0 right-0 w-64 h-64 bg-blue-500/5 blur-3xl -mr-32 -mt-32 rounded-full pointer-events-none"></div>
      
      <div className="relative z-10 flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div className="max-w-3xl">
          <div className="flex items-center space-x-3 mb-4">
            {icon && (
              <div className="bg-blue-600/20 p-2 rounded-xl shadow-[inset_0_0_12px_rgba(59,130,246,0.2)]">
                {React.cloneElement(icon, { className: "text-blue-400 w-6 h-6" })}
              </div>
            )}
            <h2 className="text-3xl md:text-4xl font-black text-white tracking-tight">{title}</h2>
          </div>
          {subtitle && <p className="text-gray-400 text-lg leading-relaxed">{subtitle}</p>}
        </div>
        {rightElement && (
          <div className="flex-shrink-0">
            {rightElement}
          </div>
        )}
      </div>
    </div>
  );
}

export function InfoPill({ text, tooltip }) {
  return (
    <div className="group relative inline-flex items-center">
      <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">{text}</span>
      <Info className="w-3 h-3 text-gray-500 ml-1 cursor-help group-hover:text-blue-400 transition-colors" />
      <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-64 p-3 bg-gray-900 border border-white/10 rounded-xl text-xs text-gray-300 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-50 shadow-2xl">
        {tooltip}
      </div>
    </div>
  );
}

export function LoadingState({ text = "Loading..." }) {
  return (
    <div className="flex flex-col items-center justify-center py-24 animate-in fade-in duration-500">
      <Activity className="w-12 h-12 text-blue-500 animate-spin mb-4" />
      <p className="text-gray-400 animate-pulse font-medium">{text}</p>
    </div>
  );
}

export function EmptyState({ icon, title, description }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
      {icon && (
        <div className="bg-white/5 p-4 rounded-full mb-4">
          {React.cloneElement(icon, { className: "w-8 h-8 text-gray-500" })}
        </div>
      )}
      <h3 className="text-xl font-bold text-white mb-2">{title}</h3>
      <p className="text-gray-400 max-w-md mx-auto text-sm">{description}</p>
    </div>
  );
}
