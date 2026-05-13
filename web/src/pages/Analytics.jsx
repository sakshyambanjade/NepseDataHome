import React, { useState, useEffect, useMemo } from 'react';
import { 
  TrendingUp, TrendingDown, Activity, Layers, 
  Search, Filter, ChevronRight, BarChart3, 
  ArrowUpRight, ArrowDownRight, Info,
  ExternalLink, Download, Clock
} from 'lucide-react';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, 
  Tooltip, ResponsiveContainer, AreaChart, Area,
  BarChart, Bar, Cell, PieChart, Pie
} from 'recharts';

// --- Components ---

const StatCard = ({ title, value, change, trend, icon: Icon }) => (
  <div className="glass-morphism rounded-3xl p-6 border border-white/5 hover:border-blue-500/30 transition-all duration-300 group">
    <div className="flex justify-between items-start mb-4">
      <div className="p-3 bg-blue-600/10 rounded-2xl group-hover:bg-blue-600/20 transition-colors">
        <Icon className="w-6 h-6 text-blue-400" />
      </div>
      {change && (
        <div className={`px-2 py-1 rounded-lg text-[10px] font-bold flex items-center ${trend === 'up' ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'}`}>
          {trend === 'up' ? <ArrowUpRight className="w-3 h-3 mr-1" /> : <ArrowDownRight className="w-3 h-3 mr-1" />}
          {change}
        </div>
      )}
    </div>
    <h3 className="text-gray-500 text-xs font-bold uppercase tracking-widest">{title}</h3>
    <p className="text-3xl font-black text-white mt-2 tracking-tight">{value}</p>
  </div>
);

const IndicatorBadge = ({ label, value, status }) => {
  const getStatusColor = () => {
    if (status === 'good') return 'bg-green-500/10 text-green-400 border-green-500/10';
    if (status === 'bad') return 'bg-red-500/10 text-red-400 border-red-500/10';
    return 'bg-blue-500/10 text-blue-400 border-blue-500/10';
  };
  
  return (
    <div className={`px-4 py-2 rounded-xl text-xs font-bold border ${getStatusColor()} flex justify-between items-center w-full`}>
      <span className="opacity-60">{label}</span>
      <span>{value}</span>
    </div>
  );
};

// --- Main Pages ---

export function AnalyticsDashboard() {
  const [marketData, setMarketData] = useState(null);
  const [symbols, setSymbols] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [selectedSymbol, setSelectedSymbol] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const base = import.meta.env.BASE_URL === '/' ? '/NepseDataHome/' : (import.meta.env.BASE_URL || '/NepseDataHome/');
        const [marketResp, symbolsResp] = await Promise.all([
          fetch(`${base}data/market_overview.json`).then(r => {
            if (!r.ok) throw new Error("Market data not found");
            return r.json();
          }),
          fetch(`${base}data/symbols_index.json`).then(r => {
            if (!r.ok) throw new Error("Symbols index not found");
            return r.json();
          })
        ]);
        setMarketData(marketResp);
        setSymbols(symbolsResp);
      } catch (err) {
        console.error("Failed to fetch analytics data", err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const filteredSymbols = useMemo(() => {
    return symbols.filter(s => 
      s.symbol.toLowerCase().includes(search.toLowerCase()) ||
      (s.company_name && s.company_name.toLowerCase().includes(search.toLowerCase()))
    );
  }, [symbols, search]);

  if (loading) return (
    <div className="flex flex-col items-center justify-center h-[60vh] space-y-4">
      <div className="w-12 h-12 border-4 border-blue-600/20 border-t-blue-600 rounded-full animate-spin"></div>
      <p className="text-gray-500 font-medium animate-pulse text-sm uppercase tracking-widest">Inference Engine Booting...</p>
    </div>
  );

  if (!marketData) return (
    <div className="flex flex-col items-center justify-center h-[60vh] space-y-4">
      <div className="bg-red-500/10 p-6 rounded-full">
        <Activity className="text-red-500 w-12 h-12" />
      </div>
      <p className="text-gray-400 font-bold">Failed to load market intelligence data.</p>
      <button onClick={() => window.location.reload()} className="text-blue-400 hover:underline">Retry</button>
    </div>
  );

  return (
    <div className="space-y-10 animate-in fade-in duration-700">
      {/* Header Section */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center space-y-4 md:space-y-0">
        <div>
          <h2 className="text-3xl font-black text-white">Market Intelligence</h2>
          <p className="text-gray-500 text-sm font-medium">NEPSE Data Engine • {marketData?.date}</p>
        </div>
        <div className="flex items-center space-x-2 bg-white/5 rounded-2xl p-1 border border-white/5">
          <div className="flex items-center px-4 py-2 text-xs font-bold text-blue-400 bg-blue-600/10 rounded-xl">
             <Clock className="w-3 h-3 mr-2" />
             Live Feed
          </div>
          <button className="px-4 py-2 text-xs font-bold text-gray-500 hover:text-white transition-colors">
            Daily
          </button>
        </div>
      </div>

      {/* Market Pulse */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard 
          title="Daily Turnover" 
          value={`Rs. ${(marketData?.total_turnover / 1e7).toFixed(2)} Cr`} 
          icon={Activity} 
        />
        <StatCard 
          title="Market Breadth" 
          value={`${marketData?.advancers} Adv`} 
          trend={marketData?.advancers >= marketData?.decliners ? "up" : "down"}
          change={`${((marketData?.advancers / marketData?.active_symbols) * 100).toFixed(0)}%`}
          icon={TrendingUp} 
        />
        <StatCard 
          title="Decliners" 
          value={marketData?.decliners} 
          trend="down" 
          change={`${((marketData?.decliners / marketData?.active_symbols) * 100).toFixed(0)}%`}
          icon={TrendingDown} 
        />
        <StatCard 
          title="Traded Volume" 
          value={(marketData?.total_volume / 1e6).toFixed(1) + ' M'} 
          icon={Layers} 
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Sector & Rankings */}
        <div className="lg:col-span-1 space-y-8">
          <div className="glass-morphism rounded-3xl p-6 border border-white/5 h-full">
            <h3 className="text-sm font-black text-gray-400 uppercase tracking-widest mb-8 flex items-center">
              <Layers className="w-4 h-4 mr-2 text-blue-500" />
              Sector Performance
            </h3>
            <div className="space-y-6">
              {marketData?.sector_performance?.sort((a, b) => b.ret_1d - a.ret_1d).map((s, i) => (
                <div key={s.sector} className="group cursor-pointer">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-xs font-bold text-gray-300 group-hover:text-white transition-colors">{s.sector}</span>
                    <span className={`text-[10px] font-black ${s.ret_1d >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {(s.ret_1d * 100).toFixed(2)}%
                    </span>
                  </div>
                  <div className="w-full h-1.5 bg-white/5 rounded-full overflow-hidden">
                    <div 
                      className={`h-full transition-all duration-1000 ${s.ret_1d >= 0 ? 'bg-green-500' : 'bg-red-500'}`} 
                      style={{ width: `${Math.min(100, Math.abs(s.ret_1d * 500))}%` }}
                    ></div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Middle/Right Column: Screener & Insight */}
        <div className="lg:col-span-2 space-y-8">
          {/* Top Movers Bar */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="glass-morphism rounded-3xl p-6 border border-white/5">
              <h4 className="text-[10px] font-black text-green-500 uppercase tracking-[0.2em] mb-4">Top Gainers</h4>
              <div className="flex flex-wrap gap-2">
                {marketData?.top_gainers?.slice(0, 5).map(g => (
                  <button 
                    key={g.symbol} 
                    onClick={() => setSelectedSymbol(g.symbol)}
                    className="px-3 py-2 bg-green-500/5 hover:bg-green-500/10 border border-green-500/10 rounded-xl text-xs font-bold text-green-400 transition-all active:scale-95"
                  >
                    {g.symbol} +{(g.ret_1d * 100).toFixed(1)}%
                  </button>
                ))}
              </div>
            </div>
            <div className="glass-morphism rounded-3xl p-6 border border-white/5">
              <h4 className="text-[10px] font-black text-red-500 uppercase tracking-[0.2em] mb-4">Top Losers</h4>
              <div className="flex flex-wrap gap-2">
                {marketData?.top_losers?.slice(0, 5).map(l => (
                  <button 
                    key={l.symbol} 
                    onClick={() => setSelectedSymbol(l.symbol)}
                    className="px-3 py-2 bg-red-500/5 hover:bg-red-500/10 border border-red-500/10 rounded-xl text-xs font-bold text-red-400 transition-all active:scale-95"
                  >
                    {l.symbol} {(l.ret_1d * 100).toFixed(1)}%
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
            {/* Screener Table */}
            <div className="glass-morphism rounded-3xl border border-white/5 overflow-hidden flex flex-col h-[600px]">
              <div className="p-6 border-b border-white/5 bg-white/2">
                <div className="relative">
                  <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                  <input 
                    type="text" 
                    placeholder="Search stocks..." 
                    className="w-full bg-white/5 border border-white/5 rounded-2xl pl-12 pr-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/30 transition-all font-medium"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                  />
                </div>
              </div>
              <div className="flex-grow overflow-y-auto">
                {filteredSymbols.map((s) => (
                  <div 
                    key={s.symbol}
                    onClick={() => setSelectedSymbol(s.symbol)}
                    className={`flex justify-between items-center p-6 border-b border-white/5 cursor-pointer transition-all hover:bg-white/5 group ${selectedSymbol === s.symbol ? 'bg-blue-600/5' : ''}`}
                  >
                    <div className="flex items-center space-x-4">
                      <div className={`w-10 h-10 rounded-xl flex items-center justify-center font-black text-xs transition-colors ${selectedSymbol === s.symbol ? 'bg-blue-600 text-white' : 'bg-white/5 text-gray-500 group-hover:text-blue-400'}`}>
                        {s.symbol.substring(0, 2)}
                      </div>
                      <div>
                        <div className="text-sm font-black text-white">{s.symbol}</div>
                        <div className="text-[10px] text-gray-500 font-bold uppercase">{s.sector}</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-bold text-white">Rs. {s.close}</div>
                      <div className={`text-[10px] font-black ${s.ret_1d >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                        {s.ret_1d >= 0 ? '+' : ''}{(s.ret_1d * 100).toFixed(2)}%
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Insight Panel */}
            <div className="space-y-6">
              {selectedSymbol ? (
                <SymbolInsight symbol={selectedSymbol} />
              ) : (
                <div className="glass-morphism rounded-3xl p-12 border border-white/5 h-full flex flex-col items-center justify-center text-center">
                  <div className="w-20 h-20 bg-blue-600/10 rounded-3xl flex items-center justify-center mb-6">
                    <Info className="w-10 h-10 text-blue-500" />
                  </div>
                  <h4 className="text-white font-bold mb-2 text-xl">Select a Symbol</h4>
                  <p className="text-gray-500 text-sm max-w-[240px]">Select any company from the screener to run deep-dive technical analytics.</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function SymbolInsight({ symbol }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setData(null);
    setLoading(true);
    const base = import.meta.env.BASE_URL === '/' ? '/NepseDataHome/' : (import.meta.env.BASE_URL || '/NepseDataHome/');
    const safeSymbol = String(symbol).replace("/", "-");
    fetch(`${base}data/symbols/${safeSymbol}.json`)
      .then(r => r.json())
      .then(d => {
        setData(d);
        setLoading(false);
      })
      .catch(err => console.error(err));
  }, [symbol]);

  if (loading) return (
    <div className="glass-morphism rounded-3xl p-12 border border-white/5 flex flex-col items-center justify-center h-full">
      <div className="w-10 h-10 border-4 border-blue-600/20 border-t-blue-600 rounded-full animate-spin mb-4"></div>
      <p className="text-xs text-gray-500 font-bold uppercase tracking-widest">Hydrating Chart...</p>
    </div>
  );

  const chartData = data.history.date.map((date, i) => ({
    date,
    close: data.history.close[i],
    rsi: data.history.rsi_14[i],
    volume: data.history.volume[i]
  })).slice(-45);

  const latestIdx = data.history.close.length - 1;
  const indicators = {
    rsi: data.history.rsi_14[latestIdx],
    macd: data.history.macd_hist[latestIdx],
    sma20: data.history.sma_20[latestIdx],
    vol: data.history.vol_20[latestIdx],
    watchScore: data.history.watch_score[latestIdx],
    pUp: data.history.p_up_5d?.[latestIdx],
    sector: data.history.sector?.[latestIdx]
  };

  return (
    <div className="space-y-6 animate-in slide-in-from-right-4 duration-500">
      <div className="glass-morphism rounded-3xl p-8 border border-white/5 overflow-hidden relative">
        {/* Background Accent */}
        <div className="absolute top-0 right-0 w-32 h-32 bg-blue-600/10 blur-3xl -mr-16 -mt-16 rounded-full"></div>
        
        <div className="flex justify-between items-start mb-10 relative z-10">
          <div>
            <h3 className="text-3xl font-black text-white leading-none mb-2">{symbol}</h3>
            <p className="text-[10px] text-gray-500 font-black uppercase tracking-[0.3em]">{indicators.sector || 'Security Detail'}</p>
          </div>
          <div className="text-right">
            <div className="text-4xl font-black text-blue-500">{indicators.watchScore}</div>
            <div className="text-[9px] text-gray-500 font-black uppercase tracking-widest">Algorithm Score</div>
          </div>
        </div>

        <div className="h-48 w-full mb-8">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id="colorClose" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#2563eb" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#2563eb" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <XAxis dataKey="date" hide />
              <YAxis hide domain={['auto', 'auto']} />
              <Tooltip 
                contentStyle={{ backgroundColor: '#030712', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '16px', boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)' }}
                itemStyle={{ color: '#60a5fa', fontWeight: 'bold' }}
              />
              <Area 
                type="monotone" 
                dataKey="close" 
                stroke="#3b82f6" 
                strokeWidth={3}
                fillOpacity={1} 
                fill="url(#colorClose)" 
                animationDuration={1500}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div className="grid grid-cols-2 gap-3 mb-8">
          <IndicatorBadge 
            label="RSI (14)" 
            value={indicators.rsi?.toFixed(1)} 
            status={indicators.rsi > 70 ? 'bad' : indicators.rsi < 30 ? 'good' : 'neutral'} 
          />
          <IndicatorBadge 
            label="MACD Momentum" 
            value={indicators.macd?.toFixed(2)} 
            status={indicators.macd > 0 ? 'good' : 'bad'} 
          />
        </div>

        {indicators.pUp !== undefined && (
          <div className="p-6 bg-blue-600/5 rounded-3xl border border-blue-500/10">
            <div className="flex justify-between items-center mb-3">
              <span className="text-[10px] font-black text-blue-400 uppercase tracking-widest">Inference Probability (5D)</span>
              <span className="text-lg font-black text-white">{(indicators.pUp * 100).toFixed(1)}%</span>
            </div>
            <div className="w-full bg-white/5 h-2 rounded-full overflow-hidden">
              <div 
                className="bg-blue-500 h-full transition-all duration-1500 shadow-[0_0_15px_rgba(59,130,246,0.5)]" 
                style={{ width: `${indicators.pUp * 100}%` }}
              ></div>
            </div>
          </div>
        )}
      </div>
      
      <div className="glass-morphism rounded-3xl p-6 border border-white/5">
        <h4 className="text-[10px] font-black text-gray-500 uppercase tracking-[0.2em] mb-6">Volume Activity</h4>
        <div className="h-24 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData}>
              <Bar dataKey="volume" radius={[4, 4, 0, 0]}>
                {chartData.map((entry, index) => (
                  <Cell 
                    key={`cell-${index}`} 
                    fill={index > 0 && entry.close >= chartData[index-1].close ? '#10b98160' : '#ef444460'} 
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
