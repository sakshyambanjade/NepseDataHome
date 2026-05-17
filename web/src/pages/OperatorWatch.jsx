import React, { useState, useEffect } from 'react';
import { ShieldAlert, Fingerprint, Search, Info, AlertTriangle, Scale, Activity, TrendingUp, Users } from 'lucide-react';
import { Card, MetricCard, PageHeader, LoadingState, EmptyState, ScoreBadge, InfoPill } from '../components/ui';
import { Link } from 'react-router-dom';

export function OperatorWatch() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const base = import.meta.env.BASE_URL === '/' ? '/NepseDataHome/' : (import.meta.env.BASE_URL || '/NepseDataHome/');
    fetch(`${base}data/broker_overview.json`)
      .then(res => res.json())
      .then(d => {
        setData(d);
        setLoading(false);
      })
      .catch(err => {
        console.error("Error loading operator data:", err);
        setLoading(false);
      });
  }, []);

  if (loading) return <LoadingState text="Scanning for Flow Anomalies..." />;

  if (!data || !data.operator_watchlist || data.operator_watchlist.length === 0) {
    return (
      <div className="py-20">
        <EmptyState 
          icon={<ShieldCheck className="w-12 h-12 text-emerald-500" />}
          title="No Significant Anomalies Detected"
          description="The intelligence engine did not find any extreme pattern deviations or highly coordinated broker flows today."
        />
      </div>
    );
  }

  return (
    <div className="space-y-10 animate-in fade-in duration-700">
      <PageHeader 
        title="Flow Anomaly Watch"
        subtitle="Statistical detection of unusual broker concentration, churn, and wash-like patterns in NEPSE floorsheet data."
        icon={<Fingerprint />}
        rightElement={
          <div className="flex flex-col items-end">
            <span className="text-[10px] text-gray-500 font-bold uppercase tracking-widest">Date</span>
            <span className="text-xl font-black text-white">{data.date}</span>
            <div className="mt-2 px-3 py-1 bg-amber-500/10 border border-amber-500/20 text-amber-500 rounded-full text-[10px] font-bold uppercase tracking-wider">
              {data.operator_watchlist.length} Anomalies
            </div>
          </div>
        }
      />

      <section className="space-y-6">
        <div className="flex items-center justify-between px-2">
          <h3 className="text-xl font-bold text-white flex items-center">
            <ShieldAlert className="w-5 h-5 mr-3 text-amber-500" />
            Live Pattern Watchlist
          </h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {data.operator_watchlist.map((item) => (
            <Card key={item.symbol} className="group hover:border-amber-500/30 transition-all flex flex-col h-full relative overflow-hidden">
              {item.operator_like_score >= 80 && (
                <div className="absolute top-0 right-0 w-32 h-32 bg-amber-500/10 blur-2xl -mr-16 -mt-16 rounded-full pointer-events-none" />
              )}
              <div className="flex justify-between items-start mb-6 relative z-10">
                <div>
                  <Link to={`/flowsheet/${item.symbol}`} className="text-2xl font-black text-white group-hover:text-amber-400 transition-colors">
                    {item.symbol}
                  </Link>
                  <p className="text-[10px] font-bold text-gray-500 uppercase tracking-widest mt-1">{item.operator_pattern || "Mixed Anomaly"}</p>
                </div>
                <div className="text-right flex flex-col items-end">
                  <ScoreBadge score={item.operator_like_score} type="pattern" />
                  <div className="text-[9px] text-gray-500 font-bold uppercase tracking-widest mt-2">Pattern Score</div>
                </div>
              </div>

              <div className="space-y-4 flex-grow relative z-10">
                <div className="bg-white/5 rounded-2xl p-4 border border-white/5">
                  <div className="flex justify-between items-center mb-2">
                    <InfoPill text="Broker Churn" tooltip="Percentage of volume driven by brokers rapidly switching sides or wash trading." />
                    <span className="text-xs font-mono font-bold text-white">{item.churn_score || 0}</span>
                  </div>
                  <div className="h-1.5 w-full bg-white/10 rounded-full overflow-hidden">
                    <div className="h-full bg-amber-500/80 rounded-full" style={{ width: `${Math.min(100, item.churn_score || 0)}%` }}></div>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-white/5 rounded-2xl p-4 text-center">
                    <div className="text-[10px] font-bold text-gray-500 uppercase mb-1">Buy Conc.</div>
                    <div className="text-lg font-black text-emerald-400">{(item.buy_concentration * 100)?.toFixed(1) || 0}%</div>
                  </div>
                  <div className="bg-white/5 rounded-2xl p-4 text-center">
                    <div className="text-[10px] font-bold text-gray-500 uppercase mb-1">Sell Conc.</div>
                    <div className="text-lg font-black text-rose-400">{(item.sell_concentration * 100)?.toFixed(1) || 0}%</div>
                  </div>
                </div>
              </div>

              <div className="mt-6 flex justify-between items-center text-[10px] relative z-10 border-t border-white/10 pt-4">
                <div className="flex items-center text-gray-400 font-bold uppercase">
                  <Scale className="w-3 h-3 mr-2 text-gray-500" />
                  Market Anomalies
                </div>
                <Link to={`/flowsheet/${item.symbol}`} className="text-amber-500 font-black hover:text-amber-400 transition-colors uppercase flex items-center">
                  Analyze Flow <Activity className="w-3 h-3 ml-1" />
                </Link>
              </div>
            </Card>
          ))}
        </div>
      </section>

      {/* Educational Footer */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-8 mt-12 border-t border-white/5">
        <Card className="flex gap-4 p-6 bg-blue-900/10 border-blue-500/10">
          <div className="flex-shrink-0 p-3 bg-blue-500/20 rounded-xl h-fit border border-blue-500/20">
            <Info className="w-6 h-6 text-blue-400" />
          </div>
          <div>
            <h4 className="text-white font-bold mb-2">Algorithm Methodology</h4>
            <p className="text-gray-400 text-sm leading-relaxed">
              Our V2 scoring engine normalizes HHI against active broker counts and calculates "Concentration Surprise" 
              relative to 20-day averages. This separates standard institutional buying from unusual, one-off concentrated spikes.
            </p>
          </div>
        </Card>
        
        <Card className="flex gap-4 p-6 bg-amber-900/10 border-amber-500/10">
          <div className="flex-shrink-0 p-3 bg-amber-500/20 rounded-xl h-fit border border-amber-500/20">
            <AlertTriangle className="w-6 h-6 text-amber-500" />
          </div>
          <div>
            <h4 className="text-white font-bold mb-2">Risk Disclaimer</h4>
            <p className="text-gray-400 text-sm leading-relaxed">
              Pattern detection is statistical, not investigative. These scores represent anomalous flow behavior, not confirmed identities. 
              Always cross-verify with fundamental data and official NEPSE disclosures before making decisions.
            </p>
          </div>
        </Card>
      </div>
    </div>
  );
}
