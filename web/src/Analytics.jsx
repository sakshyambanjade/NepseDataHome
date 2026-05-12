import React, { useState, useEffect, useMemo } from 'react';
import { 
  TrendingUp, TrendingDown, Activity, Layers, 
  Search, Filter, ChevronRight, BarChart3, 
  ArrowUpRight, ArrowDownRight, Info
} from 'lucide-react';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, 
  Tooltip, ResponsiveContainer, AreaChart, Area,
  BarChart, Bar, Cell
} from 'recharts';

// --- Components ---

const StatCard = ({ title, value, change, trend, icon: Icon }) => (
  <div className="analytics-card glass">
    <div className="flex justify-between items-start mb-4">
      <div className="p-2 bg-blue-500/10 rounded-lg">
        <Icon className="w-5 h-5 text-blue-400" />
      </div>
      {change && (
        <span className={`text-xs font-medium flex items-center ${trend === 'up' ? 'text-green-400' : 'text-red-400'}`}>
          {trend === 'up' ? <ArrowUpRight className="w-3 h-3 mr-1" /> : <ArrowDownRight className="w-3 h-3 mr-1" />}
          {change}
        </span>
      )}
    </div>
    <h3 className="text-gray-400 text-sm font-medium">{title}</h3>
    <p className="text-2xl font-bold text-white mt-1">{value}</p>
  </div>
);

const IndicatorBadge = ({ label, value, status }) => {
  const getStatusColor = () => {
    if (status === 'good') return 'bg-green-500/20 text-green-400 border-green-500/20';
    if (status === 'bad') return 'bg-red-500/20 text-red-400 border-red-500/20';
    return 'bg-blue-500/20 text-blue-400 border-blue-500/20';
  };
  
  return (
    <div className={`px-3 py-1.5 rounded-full text-xs font-semibold border ${getStatusColor()} flex items-center`}>
      <span className="mr-2 opacity-70">{label}</span>
      {value}
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
        const [marketResp, symbolsResp] = await Promise.all([
          fetch('./data/market_overview.json').then(r => r.json()),
          fetch('./data/symbols_index.json').then(r => r.json())
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

  if (loading) return <div className="flex items-center justify-center h-96"><Activity className="animate-spin text-blue-500" /></div>;

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      {/* Market Pulse */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard 
          title="Turnover" 
          value={`Rs. ${(marketData?.total_turnover / 1e7).toFixed(2)} Cr`} 
          icon={Activity} 
        />
        <StatCard 
          title="Advancers" 
          value={marketData?.advancers} 
          trend="up" 
          change={`${((marketData?.advancers / marketData?.active_symbols) * 100).toFixed(1)}%`}
          icon={TrendingUp} 
        />
        <StatCard 
          title="Decliners" 
          value={marketData?.decliners} 
          trend="down" 
          change={`${((marketData?.decliners / marketData?.active_symbols) * 100).toFixed(1)}%`}
          icon={TrendingDown} 
        />
        <StatCard 
          title="Total Volume" 
          value={(marketData?.total_volume / 1e6).toFixed(2) + ' M'} 
          icon={Layers} 
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Screener / Watchlist */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold flex items-center">
              <Search className="w-5 h-5 mr-2 text-blue-400" />
              Market Screener
            </h2>
            <div className="relative">
              <input 
                type="text" 
                placeholder="Search symbol..." 
                className="bg-gray-900/50 border border-gray-800 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 w-64"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
          </div>
          
          <div className="glass rounded-xl overflow-hidden overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-gray-900/50 text-gray-400 text-xs uppercase tracking-wider">
                  <th className="px-6 py-4 font-semibold">Symbol</th>
                  <th className="px-6 py-4 font-semibold text-right">Score</th>
                  <th className="px-6 py-4 font-semibold text-right">Price</th>
                  <th className="px-6 py-4 font-semibold text-right">Chg%</th>
                  <th className="px-6 py-4 font-semibold text-right">RSI</th>
                  <th className="px-6 py-4 font-semibold text-right">Trend</th>
                  <th className="px-6 py-4 font-semibold"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800">
                {filteredSymbols.slice(0, 15).map((s) => (
                  <tr 
                    key={s.symbol} 
                    className="hover:bg-blue-500/5 cursor-pointer transition-colors group"
                    onClick={() => setSelectedSymbol(s.symbol)}
                  >
                    <td className="px-6 py-4">
                      <div className="font-bold text-white group-hover:text-blue-400 transition-colors">{s.symbol}</div>
                      <div className="text-[10px] text-gray-500 truncate max-w-[150px]">{s.sector}</div>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div className="text-sm font-bold text-blue-400">{s.watch_score}</div>
                      <div className="text-[9px] text-gray-500">Watch Score</div>
                    </td>
                    <td className="px-6 py-4 text-right font-medium text-gray-200">{s.close}</td>
                    <td className={`px-6 py-4 text-right font-bold ${s.ret_1d >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {(s.ret_1d * 100).toFixed(2)}%
                    </td>
                    <td className="px-6 py-4 text-right">
                      <span className={`text-xs px-2 py-1 rounded ${s.rsi_14 > 70 ? 'bg-red-500/20 text-red-400' : s.rsi_14 < 30 ? 'bg-green-500/20 text-green-400' : 'bg-blue-500/10 text-gray-300'}`}>
                        {s.rsi_14?.toFixed(1)}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div className="flex justify-end">
                        {s.sma_20_gap > 0 ? <TrendingUp className="w-4 h-4 text-green-400" /> : <TrendingDown className="w-4 h-4 text-red-400" />}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <ChevronRight className="w-4 h-4 text-gray-600 group-hover:text-blue-400" />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Selected Symbol Detail Sidebar */}
        <div className="space-y-6">
          <h2 className="text-xl font-bold flex items-center">
            <BarChart3 className="w-5 h-5 mr-2 text-blue-400" />
            Symbol Insight
          </h2>
          
          {selectedSymbol ? (
            <SymbolInsight symbol={selectedSymbol} />
          ) : (
            <div className="glass rounded-xl p-8 text-center space-y-4">
              <div className="w-16 h-16 bg-blue-500/10 rounded-full flex items-center justify-center mx-auto">
                <Info className="w-8 h-8 text-blue-400" />
              </div>
              <p className="text-gray-400 text-sm">Select a symbol from the screener to see detailed technical indicators and charts.</p>
            </div>
          )}
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
    fetch(`./data/symbols/${symbol}.json`)
      .then(r => r.json())
      .then(d => {
        setData(d);
        setLoading(false);
      })
      .catch(err => console.error(err));
  }, [symbol]);

  if (loading) return <div className="glass rounded-xl p-12 flex justify-center"><Activity className="animate-spin text-blue-500" /></div>;

  // Prepare chart data
  const chartData = data.history.date.map((date, i) => ({
    date,
    close: data.history.close[i],
    rsi: data.history.rsi_14[i],
    volume: data.history.volume[i]
  })).slice(-30);

  const latestIdx = data.history.close.length - 1;
  const indicators = {
    rsi: data.history.rsi_14[latestIdx],
    macd: data.history.macd_hist[latestIdx],
    sma20: data.history.sma_20[latestIdx],
    vol: data.history.vol_20[latestIdx],
    watchScore: data.history.watch_score[latestIdx],
    pUp: data.history.p_up_5d?.[latestIdx]
  };

  return (
    <div className="space-y-6 animate-in slide-in-from-right-4 duration-500">
      <div className="glass rounded-xl p-6">
        <div className="flex justify-between items-start mb-6">
          <div>
            <h3 className="text-2xl font-bold text-white">{symbol}</h3>
            <p className="text-xs text-gray-500 uppercase tracking-widest">{data.history.sector?.[latestIdx] || 'Company'}</p>
          </div>
          <div className="text-right">
            <div className="text-3xl font-black text-blue-400">{indicators.watchScore}</div>
            <div className="text-[10px] text-gray-500 uppercase font-bold">Watch Score</div>
          </div>
        </div>

        <div className="h-48 w-full mb-6">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id="colorClose" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" vertical={false} />
              <XAxis dataKey="date" hide />
              <YAxis hide domain={['auto', 'auto']} />
              <Tooltip 
                contentStyle={{ backgroundColor: '#111827', border: '1px solid #374151', borderRadius: '8px' }}
                itemStyle={{ color: '#3b82f6' }}
              />
              <Area type="monotone" dataKey="close" stroke="#3b82f6" fillOpacity={1} fill="url(#colorClose)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <IndicatorBadge 
            label="RSI" 
            value={indicators.rsi?.toFixed(1)} 
            status={indicators.rsi > 70 ? 'bad' : indicators.rsi < 30 ? 'good' : 'neutral'} 
          />
          <IndicatorBadge 
            label="MACD" 
            value={indicators.macd?.toFixed(2)} 
            status={indicators.macd > 0 ? 'good' : 'bad'} 
          />
          <IndicatorBadge 
            label="Vol" 
            value={`${(indicators.vol * 100).toFixed(1)}%`} 
            status="neutral" 
          />
          <IndicatorBadge 
            label="Price/SMA" 
            value={(data.latest / indicators.sma20).toFixed(2)} 
            status={data.latest > indicators.sma20 ? 'good' : 'bad'} 
          />
          {indicators.pUp !== undefined && (
            <div className="col-span-2 glass bg-blue-500/5 p-3 rounded-lg border-blue-500/20">
              <div className="flex justify-between items-center">
                <span className="text-xs font-semibold text-blue-300">5-Day Up Probability</span>
                <span className="text-sm font-bold text-white">{(indicators.pUp * 100).toFixed(1)}%</span>
              </div>
              <div className="w-full bg-gray-800 h-1.5 rounded-full mt-2 overflow-hidden">
                <div className="bg-blue-500 h-full transition-all duration-1000" style={{ width: `${indicators.pUp * 100}%` }}></div>
              </div>
            </div>
          )}
        </div>
      </div>
      
      <div className="glass rounded-xl p-6">
        <h4 className="text-sm font-semibold mb-4 text-gray-400 uppercase tracking-wider">Volume Trend</h4>
        <div className="h-24 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData}>
              <Bar dataKey="volume">
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={index > 0 && entry.close >= chartData[index-1].close ? '#10b98140' : '#ef444440'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
