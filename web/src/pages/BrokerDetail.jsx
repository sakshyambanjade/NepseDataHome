import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ChevronLeft, ArrowUpRight, ArrowDownRight, Activity, Users, TrendingUp, TrendingDown, Layers, BarChart } from 'lucide-react';

export function BrokerDetail() {
  const { brokerId } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const isDev = import.meta.env.DEV;
    const base = isDev ? "/" : (import.meta.env.BASE_URL || "/");
    fetch(`${base}data/brokers/${brokerId}.json`)
      .then(res => {
        if (!res.ok) throw new Error("Broker data not found");
        return res.json();
      })
      .then(json => {
        setData(json);
        setLoading(false);
      })
      .catch(err => {
        console.error("Error loading broker detail:", err);
        setError(err.message);
        setLoading(false);
      });
  }, [brokerId]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-32">
        <Activity className="w-12 h-12 text-blue-500 animate-spin mb-4" />
        <p className="text-gray-400">Fetching Broker {brokerId} intelligence...</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="text-center py-32">
        <div className="bg-red-500/10 text-red-500 inline-flex p-4 rounded-full mb-4">
          <ChevronLeft className="w-8 h-8" />
        </div>
        <h2 className="text-2xl font-bold text-white mb-2">Data Unavailable</h2>
        <p className="text-gray-400 mb-6">{error || "Could not find intelligence for this broker today."}</p>
        <Link to="/brokers" className="text-blue-400 hover:text-blue-300 font-bold transition-colors flex items-center justify-center">
          <ChevronLeft className="w-4 h-4 mr-1" /> Back to Broker List
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      {/* Breadcrumb & Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <Link to="/brokers" className="text-gray-500 hover:text-blue-400 text-sm font-medium transition-colors flex items-center mb-4">
            <ChevronLeft className="w-4 h-4 mr-1" /> Broker Intelligence
          </Link>
          <div className="flex items-center space-x-4">
            <div className="w-16 h-16 bg-blue-600/20 rounded-2xl flex items-center justify-center border border-blue-500/20">
              <span className="text-2xl font-black text-blue-400">B{data.broker}</span>
            </div>
            <div>
              <h1 className="text-4xl font-black text-white tracking-tight">Broker {data.broker}</h1>
              <p className="text-gray-400">Daily Activity Profile • {data.date}</p>
            </div>
          </div>
        </div>
        
        <div className="flex items-center space-x-3">
          <div className={`px-4 py-2 rounded-2xl border ${data.total_net_qty >= 0 ? 'bg-emerald-500/5 border-emerald-500/10 text-emerald-400' : 'bg-red-500/5 border-red-500/10 text-red-400'}`}>
            <span className="text-[10px] uppercase font-bold block opacity-60 leading-none mb-1">Daily Net Position</span>
            <span className="text-lg font-black leading-none">
              {data.total_net_qty >= 0 ? '+' : ''}{ (data.total_net_qty / 1000).toFixed(1) }k <span className="text-xs opacity-60">QTY</span>
            </span>
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: "Total Buy Volume", value: `${(data.total_buy_qty / 1000).toFixed(1)}k`, icon: ArrowUpRight, color: "text-blue-400" },
          { label: "Total Sell Volume", value: `${(data.total_sell_qty / 1000).toFixed(1)}k`, icon: ArrowDownRight, color: "text-red-400" },
          { label: "Total Buy Amount", value: `Rs. ${(data.total_buy_amt / 1000000).toFixed(2)}M`, icon: TrendingUp, color: "text-emerald-400" },
          { label: "Total Sell Amount", value: `Rs. ${(data.total_sell_amt / 1000000).toFixed(2)}M`, icon: TrendingDown, color: "text-rose-400" },
        ].map((stat, i) => (
          <div key={i} className="glass-morphism rounded-3xl p-6 border border-white/5">
            <stat.icon className={`w-5 h-5 ${stat.color} mb-3`} />
            <div className="text-[10px] text-gray-500 font-bold uppercase tracking-wider mb-1">{stat.label}</div>
            <div className="text-2xl font-black text-white">{stat.value}</div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Exposure Section */}
        <div className="lg:col-span-2 space-y-6">
          <div className="glass-morphism rounded-3xl border border-white/5 overflow-hidden">
            <div className="px-6 py-4 border-b border-white/5 flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Layers className="w-5 h-5 text-blue-400" />
                <h3 className="text-lg font-bold text-white">Dominant Exposures</h3>
              </div>
              <span className="text-[10px] text-gray-500 font-bold uppercase">Market Weight</span>
            </div>
            <div className="p-6">
              {data.exposure && data.exposure.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {data.exposure.map((exp, idx) => (
                    <Link to={`/flowsheet/${String(exp.symbol).replace("/", "-")}`} key={idx} className="group p-4 bg-white/5 hover:bg-white/10 border border-white/5 rounded-2xl transition-all">
                      <div className="flex justify-between items-start mb-2">
                        <span className="text-xl font-black text-white group-hover:text-blue-400 transition-colors">{exp.symbol}</span>
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase ${exp.type === 'accumulation' ? 'bg-blue-500/20 text-blue-400' : 'bg-red-500/20 text-red-400'}`}>
                          {exp.type}
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <div className="text-[10px] text-gray-500 font-bold uppercase">Flow Intensity</div>
                        <div className="text-sm font-bold text-gray-300">{exp.score} / 100</div>
                      </div>
                      <div className="mt-2 w-full bg-white/5 h-1.5 rounded-full overflow-hidden">
                        <div 
                          className={`h-full rounded-full ${exp.type === 'accumulation' ? 'bg-blue-500' : 'bg-red-500'}`} 
                          style={{ width: `${exp.score}%` }}
                        />
                      </div>
                    </Link>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-600 text-sm">No high-intensity exposures detected today.</div>
              )}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Top Net Buying */}
            <div className="glass-morphism rounded-3xl border border-white/5 overflow-hidden">
              <div className="px-6 py-4 border-b border-white/5 bg-blue-500/5">
                <h3 className="text-sm font-bold text-blue-400 flex items-center uppercase tracking-wider">
                  <ArrowUpRight className="w-4 h-4 mr-2" /> Top Net Buys
                </h3>
              </div>
              <div className="divide-y divide-white/5">
                {data.net_buy_stocks?.slice(0, 8).map((stock, idx) => (
                  <div key={idx} className="px-6 py-3 flex justify-between items-center hover:bg-white/5 transition-colors">
                    <span className="font-bold text-gray-300">{stock.symbol}</span>
                    <span className="text-sm font-mono text-emerald-400">+{stock.net_qty.toLocaleString()}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Top Net Selling */}
            <div className="glass-morphism rounded-3xl border border-white/5 overflow-hidden">
              <div className="px-6 py-4 border-b border-white/5 bg-red-500/5">
                <h3 className="text-sm font-bold text-red-400 flex items-center uppercase tracking-wider">
                  <ArrowDownRight className="w-4 h-4 mr-2" /> Top Net Sells
                </h3>
              </div>
              <div className="divide-y divide-white/5">
                {data.net_sell_stocks?.slice(0, 8).map((stock, idx) => (
                  <div key={idx} className="px-6 py-3 flex justify-between items-center hover:bg-white/5 transition-colors">
                    <span className="font-bold text-gray-300">{stock.symbol}</span>
                    <span className="text-sm font-mono text-rose-400">-{stock.net_qty.toLocaleString()}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Counterparty Sidebar */}
        <div className="space-y-6">
          <div className="glass-morphism rounded-3xl border border-white/5 overflow-hidden">
            <div className="px-6 py-4 border-b border-white/5">
              <div className="flex items-center space-x-2">
                <Users className="w-5 h-5 text-purple-400" />
                <h3 className="text-lg font-bold text-white">Top Counterparties</h3>
              </div>
            </div>
            <div className="p-4 space-y-3">
              {data.top_counterparties?.map((cp, idx) => (
                <Link to={`/broker/${cp.broker}`} key={idx} className="block group">
                  <div className="flex items-center justify-between p-3 bg-white/5 group-hover:bg-purple-500/10 border border-white/5 group-hover:border-purple-500/20 rounded-2xl transition-all">
                    <div className="flex items-center space-x-3">
                      <div className="w-8 h-8 rounded-lg bg-gray-900 border border-white/10 flex items-center justify-center text-[10px] font-bold text-gray-400 group-hover:text-purple-400 transition-colors">
                        B{cp.broker}
                      </div>
                      <span className="text-xs font-bold text-gray-300 group-hover:text-white">Broker {cp.broker}</span>
                    </div>
                    <div className="text-right">
                      <div className="text-[10px] text-gray-500 font-bold uppercase leading-none">Shared Vol</div>
                      <div className="text-xs font-black text-gray-400 group-hover:text-purple-400">{(cp.qty / 1000).toFixed(1)}k</div>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          </div>
          
          <div className="glass-morphism rounded-3xl p-6 border border-white/5 bg-gradient-to-br from-blue-600/10 to-transparent">
            <BarChart className="w-8 h-8 text-blue-500/50 mb-4" />
            <h4 className="text-sm font-bold text-white mb-2 uppercase">Broker Profile Note</h4>
            <p className="text-xs text-gray-500 leading-relaxed">
              Broker {brokerId}'s activity profile is generated from consolidated floorsheet data. Shared volume represents total quantity exchanged where this broker was on the opposing side of the transaction.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
