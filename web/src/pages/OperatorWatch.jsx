import React, { useState, useEffect } from 'react';
import { ShieldAlert, Fingerprint, Search, Info, AlertTriangle, Scale, Activity } from 'lucide-react';

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

  if (loading) return (
    <div className="flex flex-col items-center justify-center min-h-[50vh] space-y-4">
      <div className="w-12 h-12 border-4 border-amber-600/20 border-t-amber-500 rounded-full animate-spin"></div>
      <p className="text-amber-500 font-bold uppercase tracking-widest text-xs">Scanning for Patterns...</p>
    </div>
  );

  if (!data) return <div className="p-12 text-center text-gray-500">No pattern data available.</div>;

  return (
    <div className="space-y-10 animate-in fade-in duration-700">
      {/* Hero Section */}
      <div className="relative overflow-hidden glass-morphism rounded-[2.5rem] p-8 md:p-12 border border-amber-500/10">
        <div className="absolute top-0 right-0 w-64 h-64 bg-amber-500/5 blur-3xl -mr-32 -mt-32 rounded-full"></div>
        <div className="relative z-10 max-w-2xl">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/20 text-amber-500 text-[10px] font-black uppercase tracking-widest mb-6">
            <Fingerprint className="w-3 h-3" />
            <span>Pattern Analysis V2</span>
          </div>
          <h2 className="text-4xl md:text-5xl font-black text-white leading-tight mb-4">
            Operator-Like <span className="text-amber-500 text-glow-amber">Activity Watch</span>
          </h2>
          <p className="text-gray-400 text-lg leading-relaxed">
            Statistical detection of unusual broker concentration, churn, and wash-like patterns in NEPSE floorsheet data.
          </p>
        </div>
      </div>

      {/* Main Watchlist */}
      <section className="space-y-6">
        <div className="flex items-center justify-between px-2">
          <h3 className="text-xl font-bold text-white flex items-center">
            <ShieldAlert className="w-5 h-5 mr-3 text-amber-500" />
            Live Pattern Watchlist
          </h3>
          <span className="text-[10px] text-gray-500 font-bold uppercase tracking-widest">Date: {data.date}</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {data.operator_watchlist.map((item) => (
            <div key={item.symbol} className="glass-morphism rounded-3xl p-6 border border-white/5 hover:border-amber-500/30 transition-all group">
              <div className="flex justify-between items-start mb-6">
                <div>
                  <h4 className="text-2xl font-black text-white group-hover:text-amber-500 transition-colors">{item.symbol}</h4>
                  <p className="text-[10px] font-bold text-gray-500 uppercase tracking-widest mt-1">{item.operator_pattern}</p>
                </div>
                <div className="text-right">
                  <div className={`text-3xl font-black ${item.operator_like_score > 70 ? 'text-amber-500 text-glow-amber' : 'text-white'}`}>
                    {item.operator_like_score}
                  </div>
                  <div className="text-[8px] text-gray-600 font-black uppercase tracking-tighter">Pattern Score</div>
                </div>
              </div>

              <div className="space-y-4">
                <div className="bg-white/2 rounded-2xl p-4 border border-white/5">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-[10px] text-gray-400 font-bold uppercase">Broker Churn</span>
                    <span className="text-xs font-mono text-white">{item.churn_score}</span>
                  </div>
                  <div className="h-1 w-full bg-white/5 rounded-full overflow-hidden">
                    <div className="h-full bg-amber-500/50" style={{ width: `${item.churn_score}%` }}></div>
                  </div>
                </div>

                <div className="flex justify-between items-center text-[10px]">
                  <div className="flex items-center text-gray-500 font-bold uppercase">
                    <Scale className="w-3 h-3 mr-2" />
                    Market Churn
                  </div>
                  <button className="text-amber-500 font-black hover:underline underline-offset-4">ANALYZE FLOW</button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Educational Footer */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 py-8 border-t border-white/5">
        <div className="flex space-x-4">
          <div className="p-3 bg-blue-600/10 rounded-2xl h-fit">
            <Info className="w-6 h-6 text-blue-400" />
          </div>
          <div>
            <h4 className="text-white font-bold mb-2">Algorithm Methodology</h4>
            <p className="text-gray-500 text-sm leading-relaxed">
              Our V2 scoring engine normalizes HHI against active broker counts and calculates "Concentration Surprise" 
              relative to 20-day averages. This separates standard institutional buying from unusual, one-off concentrated spikes.
            </p>
          </div>
        </div>
        <div className="flex space-x-4">
          <div className="p-3 bg-amber-600/10 rounded-2xl h-fit">
            <AlertTriangle className="w-6 h-6 text-amber-500" />
          </div>
          <div>
            <h4 className="text-white font-bold mb-2">Risk Disclaimer</h4>
            <p className="text-gray-500 text-sm leading-relaxed">
              Pattern detection is statistical, not investigative. These scores represent anomalous flow behavior, not confirmed identities. 
              Always cross-verify with fundamental data and official NEPSE disclosures before making decisions.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
