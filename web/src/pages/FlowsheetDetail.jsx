import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ChevronLeft, BarChart3, Users, Activity, Zap, ShieldCheck, AlertTriangle, ArrowRight, Table, Info } from 'lucide-react';

export function FlowsheetDetail() {
  const { symbol } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const base = import.meta.env.BASE_URL || "/";
    fetch(`${base}data/symbols/${symbol}_broker_flow.json`)
      .then(res => {
        if (!res.ok) throw new Error("Symbol data not found");
        return res.json();
      })
      .then(json => {
        setData(json);
        setLoading(false);
      })
      .catch(err => {
        console.error("Error loading flowsheet detail:", err);
        setError(err.message);
        setLoading(false);
      });
  }, [symbol]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-32">
        <Activity className="w-12 h-12 text-blue-500 animate-spin mb-4" />
        <p className="text-gray-400">Performing deep-dive analysis on {symbol} floorsheet...</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="text-center py-32">
        <div className="bg-red-500/10 text-red-500 inline-flex p-4 rounded-full mb-4">
          <AlertTriangle className="w-8 h-8" />
        </div>
        <h2 className="text-2xl font-bold text-white mb-2">Symbol Data Unavailable</h2>
        <p className="text-gray-400 mb-6">{error || "No floorsheet intelligence found for this symbol today."}</p>
        <Link to="/flowsheet" className="text-blue-400 hover:text-blue-300 font-bold transition-colors flex items-center justify-center">
          <ChevronLeft className="w-4 h-4 mr-1" /> Back to Flowsheet Intelligence
        </Link>
      </div>
    );
  }

  const getScoreColor = (score) => {
    if (score >= 85) return "text-red-500 bg-red-500/10 border-red-500/20";
    if (score >= 70) return "text-orange-500 bg-orange-500/10 border-orange-500/20";
    if (score >= 50) return "text-amber-500 bg-amber-500/10 border-amber-500/20";
    if (score >= 30) return "text-blue-500 bg-blue-500/10 border-blue-500/20";
    return "text-gray-400 bg-gray-400/10 border-white/5";
  };

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700 pb-16">
      {/* Header Section */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div className="space-y-4">
          <Link to="/flowsheet" className="text-gray-500 hover:text-blue-400 text-sm font-medium transition-colors flex items-center">
            <ChevronLeft className="w-4 h-4 mr-1" /> Flowsheet Table
          </Link>
          <div className="flex items-center space-x-6">
            <div className="bg-gradient-to-br from-blue-600 to-indigo-700 p-4 rounded-[2rem] shadow-xl shadow-blue-500/10">
              <Zap className="w-8 h-8 text-white fill-white" />
            </div>
            <div>
              <div className="flex items-center space-x-3">
                <h1 className="text-5xl font-black text-white tracking-tighter">{data.symbol}</h1>
                <div className={`px-4 py-1.5 rounded-full border text-xs font-black uppercase tracking-widest ${getScoreColor(data.operator_like_score)}`}>
                  OP SCORE: {data.operator_like_score}
                </div>
              </div>
              <p className="text-gray-400 mt-1 font-medium">Daily Broker-Flow Intelligence • {data.date}</p>
            </div>
          </div>
        </div>

        <div className="flex flex-wrap gap-4">
          <div className="glass-morphism rounded-3xl px-6 py-4 border border-white/5 flex flex-col items-center">
            <span className="text-[10px] text-gray-500 font-bold uppercase mb-1 leading-none">Total Trades</span>
            <span className="text-2xl font-black text-white leading-none">{data.trade_count}</span>
          </div>
          <div className="glass-morphism rounded-3xl px-6 py-4 border border-white/5 flex flex-col items-center">
            <span className="text-[10px] text-gray-500 font-bold uppercase mb-1 leading-none">VWAP</span>
            <span className="text-2xl font-black text-white leading-none">Rs. {data.vwap}</span>
          </div>
        </div>
      </div>

      {/* Main Scoring Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="glass-morphism rounded-[2.5rem] p-8 border border-white/5 bg-gradient-to-br from-blue-500/5 to-transparent relative overflow-hidden">
          <div className="absolute -top-12 -right-12 w-32 h-32 bg-blue-500/10 rounded-full blur-3xl" />
          <h3 className="text-xs font-black text-blue-400 uppercase tracking-widest mb-6 flex items-center">
            <TrendingUp className="w-4 h-4 mr-2" /> Accumulation Profile
          </h3>
          <div className="flex items-end justify-between mb-4">
            <div className="text-6xl font-black text-white">{data.accumulation_score}</div>
            <div className="text-gray-500 text-xs font-bold mb-2">/ 100</div>
          </div>
          <div className="w-full bg-white/5 h-2 rounded-full overflow-hidden">
            <div className="h-full bg-blue-500 rounded-full" style={{ width: `${data.accumulation_score}%` }} />
          </div>
          <p className="mt-6 text-xs text-gray-500 leading-relaxed">
            Measures concentration among top buyers and unusual buy-side transaction sequences.
          </p>
        </div>

        <div className="glass-morphism rounded-[2.5rem] p-8 border border-white/5 bg-gradient-to-br from-red-500/5 to-transparent relative overflow-hidden">
          <div className="absolute -top-12 -right-12 w-32 h-32 bg-red-500/10 rounded-full blur-3xl" />
          <h3 className="text-xs font-black text-red-400 uppercase tracking-widest mb-6 flex items-center">
            <TrendingDown className="w-4 h-4 mr-2" /> Distribution Profile
          </h3>
          <div className="flex items-end justify-between mb-4">
            <div className="text-6xl font-black text-white">{data.distribution_score}</div>
            <div className="text-gray-500 text-xs font-bold mb-2">/ 100</div>
          </div>
          <div className="w-full bg-white/5 h-2 rounded-full overflow-hidden">
            <div className="h-full bg-red-500 rounded-full" style={{ width: `${data.distribution_score}%` }} />
          </div>
          <p className="mt-6 text-xs text-gray-500 leading-relaxed">
            Measures concentration among top sellers and automated-like selling pressure.
          </p>
        </div>

        <div className="glass-morphism rounded-[2.5rem] p-8 border border-white/5 bg-gradient-to-br from-purple-500/5 to-transparent relative overflow-hidden">
          <div className="absolute -top-12 -right-12 w-32 h-32 bg-purple-500/10 rounded-full blur-3xl" />
          <h3 className="text-xs font-black text-purple-400 uppercase tracking-widest mb-6 flex items-center">
            <Zap className="w-4 h-4 mr-2" /> Surprise Signals
          </h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-[10px] text-gray-500 font-bold uppercase">Volume Spike</span>
              <span className={`font-mono text-sm ${data.volume_spike_score > 30 ? 'text-purple-400' : 'text-gray-400'}`}>
                {data.volume_spike_score.toFixed(1)}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-[10px] text-gray-500 font-bold uppercase">Conc. Surprise</span>
              <span className={`font-mono text-sm ${data.concentration_surprise_score > 20 ? 'text-purple-400' : 'text-gray-400'}`}>
                {data.concentration_surprise_score.toFixed(1)}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-[10px] text-gray-500 font-bold uppercase">HHI (Buy/Sell)</span>
              <span className="font-mono text-xs text-gray-400">{data.buyer_hhi} / {data.seller_hhi}</span>
            </div>
          </div>
          <div className="mt-8 flex flex-wrap gap-1.5">
            {data.flags?.map((flag, idx) => (
              <span key={idx} className="text-[8px] font-black bg-white/5 border border-white/10 text-gray-400 px-2 py-0.5 rounded-full uppercase tracking-tighter">
                {flag}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Drilldown Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Net Flow Concentration */}
        <div className="space-y-6">
          <div className="glass-morphism rounded-[2rem] border border-white/5 overflow-hidden">
            <div className="px-8 py-6 border-b border-white/5 flex items-center justify-between bg-white/5">
              <h3 className="text-xl font-black text-white flex items-center">
                <Users className="w-5 h-5 mr-3 text-blue-400" /> Top Net Buyers
              </h3>
              <span className="text-[10px] text-gray-500 font-black uppercase tracking-widest">Market Share</span>
            </div>
            <div className="divide-y divide-white/5">
              {data.top_net_buyers?.map((b, idx) => (
                <Link to={`/broker/${b.broker}`} key={idx} className="px-8 py-4 flex items-center justify-between hover:bg-white/5 transition-all group">
                  <div className="flex items-center space-x-4">
                    <div className="w-10 h-10 bg-gray-900 border border-white/10 rounded-xl flex items-center justify-center font-bold text-gray-400 group-hover:text-blue-400 transition-colors">
                      {b.broker}
                    </div>
                    <div>
                      <div className="text-sm font-black text-white">Broker {b.broker}</div>
                      <div className="text-[10px] text-gray-500 font-bold uppercase">{(b.net_qty / 1000).toFixed(1)}k QTY Net</div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-lg font-black text-blue-400">{(b.share * 100).toFixed(1)}%</div>
                  </div>
                </Link>
              ))}
            </div>
          </div>

          <div className="glass-morphism rounded-[2rem] border border-white/5 overflow-hidden">
            <div className="px-8 py-6 border-b border-white/5 flex items-center justify-between bg-white/5">
              <h3 className="text-xl font-black text-white flex items-center">
                <Users className="w-5 h-5 mr-3 text-red-400" /> Top Net Sellers
              </h3>
              <span className="text-[10px] text-gray-500 font-black uppercase tracking-widest">Market Share</span>
            </div>
            <div className="divide-y divide-white/5">
              {data.top_net_sellers?.map((s, idx) => (
                <Link to={`/broker/${s.broker}`} key={idx} className="px-8 py-4 flex items-center justify-between hover:bg-white/5 transition-all group">
                  <div className="flex items-center space-x-4">
                    <div className="w-10 h-10 bg-gray-900 border border-white/10 rounded-xl flex items-center justify-center font-bold text-gray-400 group-hover:text-red-400 transition-colors">
                      {s.broker}
                    </div>
                    <div>
                      <div className="text-sm font-black text-white">Broker {s.broker}</div>
                      <div className="text-[10px] text-gray-500 font-bold uppercase">{(s.net_qty / 1000).toFixed(1)}k QTY Net</div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-lg font-black text-red-400">{(s.share * 100).toFixed(1)}%</div>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        </div>

        {/* Transaction Patterns */}
        <div className="space-y-8">
          {/* Broker Pairs */}
          <div className="glass-morphism rounded-[2rem] border border-white/5 overflow-hidden">
            <div className="px-8 py-6 border-b border-white/5 bg-white/5 flex items-center">
              <BarChart3 className="w-5 h-5 mr-3 text-purple-400" />
              <h3 className="text-xl font-black text-white">Repeating Broker Pairs</h3>
            </div>
            <div className="p-4">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="text-gray-500 uppercase tracking-widest font-black border-b border-white/5">
                    <th className="px-4 py-2">Pair (Buy → Sell)</th>
                    <th className="px-4 py-2 text-right">Volume</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {data.drilldown?.broker_pairs?.map((pair, idx) => (
                    <tr key={idx} className="hover:bg-white/5 transition-colors">
                      <td className="px-4 py-3 font-bold text-gray-300">
                        <Link to={`/broker/${pair.buyer_broker}`} className="hover:text-blue-400">B{pair.buyer_broker}</Link> 
                        <ArrowRight className="w-3 h-3 inline mx-2 opacity-30" /> 
                        <Link to={`/broker/${pair.seller_broker}`} className="hover:text-red-400">B{pair.seller_broker}</Link>
                      </td>
                      <td className="px-4 py-3 text-right font-mono text-gray-400">{(pair.quantity / 1000).toFixed(1)}k</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Cross Trades & Chunk Trades */}
          <div className="glass-morphism rounded-[2rem] border border-white/5 overflow-hidden">
            <div className="px-8 py-6 border-b border-white/5 bg-white/5 flex items-center">
              <Table className="w-5 h-5 mr-3 text-amber-400" />
              <h3 className="text-xl font-black text-white">Largest Transactions</h3>
            </div>
            <div className="p-4">
              <table className="w-full text-left text-[10px]">
                <thead>
                  <tr className="text-gray-500 uppercase tracking-widest font-black border-b border-white/5">
                    <th className="px-4 py-2">Brokers</th>
                    <th className="px-4 py-2">Qty</th>
                    <th className="px-4 py-2">Rate</th>
                    <th className="px-4 py-2 text-right">Amount</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {data.drilldown?.largest_trades?.map((trade, idx) => (
                    <tr key={idx} className="hover:bg-white/5 transition-colors">
                      <td className="px-4 py-3">
                        <span className="text-blue-400 font-bold">{trade.buyer_broker}</span>
                        <span className="mx-1 opacity-20">/</span>
                        <span className="text-red-400 font-bold">{trade.seller_broker}</span>
                      </td>
                      <td className="px-4 py-3 font-bold text-gray-300">{trade.quantity.toLocaleString()}</td>
                      <td className="px-4 py-3 text-gray-500">{trade.rate}</td>
                      <td className="px-4 py-3 text-right font-mono font-bold text-white">{(trade.amount / 1000000).toFixed(2)}M</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Cross Trades Warning if exists */}
          {data.cross_trade_ratio > 0.02 && (
            <div className="bg-amber-500/10 border border-amber-500/20 rounded-3xl p-6 flex items-start">
              <AlertTriangle className="w-6 h-6 text-amber-500 mr-4 mt-1" />
              <div>
                <h4 className="text-sm font-black text-amber-400 uppercase mb-2">Cross-Trade Watch</h4>
                <p className="text-xs text-amber-200/60 leading-relaxed">
                  {(data.cross_trade_ratio * 100).toFixed(1)}% of today's volume occurred where the same broker was both buyer and seller. High cross-trade ratios can indicate wash trading or internal churn.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Methodology Note */}
      <div className="glass-morphism rounded-3xl p-8 border border-white/5 text-center bg-white/2 overflow-hidden relative">
        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent -translate-x-full animate-[shimmer_5s_infinite]" />
        <div className="relative z-10">
          <Info className="w-8 h-8 text-blue-500/50 mx-auto mb-4" />
          <h4 className="text-sm font-bold text-white mb-2 uppercase">Intelligence Methodology</h4>
          <p className="text-xs text-gray-500 max-w-2xl mx-auto leading-relaxed">
            Scores are calculated using a weighted 7-factor model including HHI concentration, transaction sequence gaps, sliced run detection, and historical baseline normalization. Patterns detected are statistical anomalies and do not represent verified intentions.
          </p>
        </div>
      </div>
    </div>
  );
}
