import React, { useState, useEffect } from 'react';
import { Search, Filter, ShieldCheck, AlertCircle, ChevronUp, ChevronDown, Table, BarChart3, TrendingUp, TrendingDown, Users, Repeat, Activity, AlertTriangle } from 'lucide-react';
import { Link } from 'react-router-dom';
import { Card, MetricCard, ScoreBadge, PageHeader, LoadingState, EmptyState, InfoPill } from '../components/ui';

export function FlowsheetIntelligence() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [filter, setFilter] = useState("All");
  const [sortConfig, setSortConfig] = useState({ key: 'operator_like_score', direction: 'desc' });

  useEffect(() => {
    const base = import.meta.env.BASE_URL === '/' ? '/NepseDataHome/' : (import.meta.env.BASE_URL || '/NepseDataHome/');
    fetch(`${base}data/flowsheet_table.json`)
      .then(res => res.json())
      .then(json => {
        setData(json);
        setLoading(false);
      })
      .catch(err => {
        console.error("Error loading flowsheet data:", err);
        setLoading(false);
      });
  }, []);

  const handleSort = (key) => {
    let direction = 'desc';
    if (sortConfig.key === key && sortConfig.direction === 'desc') {
      direction = 'asc';
    }
    setSortConfig({ key, direction });
  };

  const filteredData = data.filter(item => {
    const searchLower = searchTerm.toLowerCase();
    const topBuyers = item.top_net_buyers || [];
    const topSellers = item.top_net_sellers || [];
    
    const matchesSearch = item.symbol.toLowerCase().includes(searchLower) ||
      topBuyers.some(b => b.broker.toLowerCase().includes(searchLower)) ||
      topSellers.some(s => s.broker.toLowerCase().includes(searchLower));

    if (!matchesSearch) return false;

    switch (filter) {
      case "Accumulation": return item.accumulation_score >= 50;
      case "Distribution": return item.distribution_score >= 50;
      case "Flow Watch": return item.operator_like_score >= 50;
      case "Cross-trade": return item.cross_trade_ratio >= 15;
      case "Repeated pair": return item.repeated_pair_score >= 50;
      case "High net buy": return item.net_buy_strength >= 50;
      case "High net sell": return item.net_sell_strength >= 50;
      default: return true;
    }
  });

  const sortedData = [...filteredData].sort((a, b) => {
    if (a[sortConfig.key] < b[sortConfig.key]) return sortConfig.direction === 'asc' ? -1 : 1;
    if (a[sortConfig.key] > b[sortConfig.key]) return sortConfig.direction === 'asc' ? 1 : -1;
    return 0;
  });

  if (loading) {
    return <LoadingState text="Analyzing after-market flowsheet intelligence..." />;
  }

  // Calculate highest values for summary cards
  const highestAcc = data.reduce((max, obj) => obj.accumulation_score > (max.accumulation_score || 0) ? obj : max, data[0] || {});
  const highestDist = data.reduce((max, obj) => obj.distribution_score > (max.distribution_score || 0) ? obj : max, data[0] || {});
  const highestPattern = data.reduce((max, obj) => obj.operator_like_score > (max.operator_like_score || 0) ? obj : max, data[0] || {});
  const highestPair = data.reduce((max, obj) => obj.repeated_pair_score > (max.repeated_pair_score || 0) ? obj : max, data[0] || {});

  const filterOptions = [
    "All", "Accumulation", "Distribution", "Flow Watch", "Cross-trade", "Repeated pair", "High net buy", "High net sell"
  ];

  return (
    <div className="space-y-8 animate-in fade-in duration-700">
      <PageHeader 
        title="Flowsheet Intelligence" 
        subtitle="Real-time analysis of the entire daily NEPSE floorsheet. Our engine scans every transaction to detect accumulation pressure, distribution channels, and unusual broker-flow anomalies."
        icon={<Table />}
        rightElement={
          <div className="flex flex-col items-end">
            <span className="text-[10px] text-gray-500 font-bold uppercase tracking-widest">Last Updated</span>
            <span className="text-xl font-black text-white">{data[0]?.date || "N/A"}</span>
            <div className="mt-2 px-3 py-1 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 rounded-full text-[10px] font-bold">
              {data.length} Symbols Active
            </div>
          </div>
        }
      />

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard 
          title="Strongest Accumulation" 
          value={highestAcc?.symbol || "-"} 
          subtitle={`Score: ${highestAcc?.accumulation_score || 0}`}
          icon={<TrendingUp />} 
          colorClass="text-emerald-400" 
          bgClass="bg-emerald-500/10"
        />
        <MetricCard 
          title="Strongest Distribution" 
          value={highestDist?.symbol || "-"} 
          subtitle={`Score: ${highestDist?.distribution_score || 0}`}
          icon={<TrendingDown />} 
          colorClass="text-rose-400" 
          bgClass="bg-rose-500/10"
        />
        <MetricCard 
          title="Highest Pattern Score" 
          value={highestPattern?.symbol || "-"} 
          subtitle={`Score: ${highestPattern?.operator_like_score || 0}`}
          icon={<Activity />} 
          colorClass="text-amber-400" 
          bgClass="bg-amber-500/10"
        />
        <MetricCard 
          title="Repeated Broker Pair" 
          value={highestPair?.symbol || "-"} 
          subtitle={`Score: ${highestPair?.repeated_pair_score || 0}`}
          icon={<Repeat />} 
          colorClass="text-blue-400" 
          bgClass="bg-blue-500/10"
        />
      </div>

      <div className="flex flex-col xl:flex-row gap-4 items-start xl:items-center justify-between mt-8 mb-4">
        <div className="relative w-full xl:w-96 group">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500 group-focus-within:text-blue-400 transition-colors" />
          <input 
            type="text" 
            placeholder="Search symbol or broker (e.g., NABIL, 58)..."
            className="w-full bg-white/5 border border-white/10 rounded-2xl py-3 pl-12 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all text-white placeholder:text-gray-500"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        
        <div className="flex flex-wrap gap-2">
          <div className="flex items-center mr-2 text-gray-500">
            <Filter className="w-4 h-4 mr-2" />
            <span className="text-xs font-bold uppercase tracking-wider">Filters:</span>
          </div>
          {filterOptions.map(opt => (
            <button 
              key={opt}
              onClick={() => setFilter(opt)}
              className={`px-3 py-1.5 rounded-full text-xs font-bold transition-colors border ${filter === opt ? 'bg-blue-600/20 text-blue-400 border-blue-500/30' : 'bg-white/5 text-gray-400 border-white/5 hover:bg-white/10'}`}
            >
              {opt}
            </button>
          ))}
        </div>
      </div>

      <Card noPadding className="overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse min-w-[1000px]">
            <thead className="bg-white/[0.02] border-b border-white/5 sticky top-0 z-20 backdrop-blur-md">
              <tr>
                <th onClick={() => handleSort('symbol')} className="px-6 py-4 text-xs font-bold text-gray-400 uppercase tracking-wider cursor-pointer hover:text-white transition-colors whitespace-nowrap">
                  Symbol {sortConfig.key === 'symbol' && (sortConfig.direction === 'desc' ? <ChevronDown className="w-3 h-3 inline ml-1" /> : <ChevronUp className="w-3 h-3 inline ml-1" />)}
                </th>
                <th onClick={() => handleSort('accumulation_score')} className="px-4 py-4 cursor-pointer hover:text-white transition-colors">
                  <InfoPill text="Accumulation" tooltip="Measures buying pressure, buyer concentration, and sliced buying patterns." />
                  {sortConfig.key === 'accumulation_score' && (sortConfig.direction === 'desc' ? <ChevronDown className="w-3 h-3 inline ml-1 text-gray-400" /> : <ChevronUp className="w-3 h-3 inline ml-1 text-gray-400" />)}
                </th>
                <th onClick={() => handleSort('distribution_score')} className="px-4 py-4 cursor-pointer hover:text-white transition-colors">
                  <InfoPill text="Distribution" tooltip="Measures selling pressure, seller concentration, and structured offloading." />
                  {sortConfig.key === 'distribution_score' && (sortConfig.direction === 'desc' ? <ChevronDown className="w-3 h-3 inline ml-1 text-gray-400" /> : <ChevronUp className="w-3 h-3 inline ml-1 text-gray-400" />)}
                </th>
                <th onClick={() => handleSort('operator_like_score')} className="px-4 py-4 cursor-pointer hover:text-white transition-colors">
                  <InfoPill text="Pattern Score" tooltip="Detects coordinated trading, wash-like patterns, and high broker churn." />
                  {sortConfig.key === 'operator_like_score' && (sortConfig.direction === 'desc' ? <ChevronDown className="w-3 h-3 inline ml-1 text-gray-400" /> : <ChevronUp className="w-3 h-3 inline ml-1 text-gray-400" />)}
                </th>
                <th onClick={() => handleSort('net_buy_strength')} className="px-4 py-4 cursor-pointer hover:text-white transition-colors">
                  <InfoPill text="Buy Strength" tooltip="Intensity of the top net buyers taking liquidity from the market." />
                  {sortConfig.key === 'net_buy_strength' && (sortConfig.direction === 'desc' ? <ChevronDown className="w-3 h-3 inline ml-1 text-gray-400" /> : <ChevronUp className="w-3 h-3 inline ml-1 text-gray-400" />)}
                </th>
                <th onClick={() => handleSort('net_sell_strength')} className="px-4 py-4 cursor-pointer hover:text-white transition-colors">
                  <InfoPill text="Sell Strength" tooltip="Intensity of the top net sellers providing liquidity to the market." />
                  {sortConfig.key === 'net_sell_strength' && (sortConfig.direction === 'desc' ? <ChevronDown className="w-3 h-3 inline ml-1 text-gray-400" /> : <ChevronUp className="w-3 h-3 inline ml-1 text-gray-400" />)}
                </th>
                <th className="px-4 py-4 text-xs font-bold text-gray-400 uppercase tracking-wider whitespace-nowrap">Net Buyer</th>
                <th className="px-4 py-4 text-xs font-bold text-gray-400 uppercase tracking-wider whitespace-nowrap">Net Seller</th>
                <th className="px-6 py-4 text-xs font-bold text-gray-400 uppercase tracking-wider min-w-[200px]">Intelligence Flags</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {sortedData.length > 0 ? sortedData.map((row) => {
                const topBuyer = row.top_net_buyers?.[0];
                const topSeller = row.top_net_sellers?.[0];
                const flags = row.flags || [];

                return (
                  <tr key={row.symbol} className="hover:bg-white/5 transition-colors group">
                    <td className="px-6 py-5">
                      <Link to={`/flowsheet/${String(row.symbol).replace("/", "-")}`} className="flex flex-col">
                        <span className="text-lg font-black text-white group-hover:text-blue-400 transition-colors">{row.symbol}</span>
                        <span className="text-[10px] text-gray-500 font-medium">Vol: {(row.total_qty / 1000).toFixed(1)}k</span>
                      </Link>
                    </td>
                    <td className="px-4 py-5"><ScoreBadge score={row.accumulation_score} type="accumulation" /></td>
                    <td className="px-4 py-5"><ScoreBadge score={row.distribution_score} type="distribution" /></td>
                    <td className="px-4 py-5"><ScoreBadge score={row.operator_like_score} type="pattern" /></td>
                    <td className="px-4 py-5">
                      <div className="text-sm font-bold text-emerald-400">{row.net_buy_strength || 0}</div>
                    </td>
                    <td className="px-4 py-5">
                      <div className="text-sm font-bold text-rose-400">{row.net_sell_strength || 0}</div>
                    </td>
                    <td className="px-4 py-5">
                      {topBuyer ? (
                        <Link to={`/broker/${topBuyer.broker}`} className="inline-flex flex-col p-1.5 rounded-lg hover:bg-emerald-500/10 transition-colors">
                          <span className="text-emerald-400 font-bold text-sm">B{topBuyer.broker}</span>
                          <span className="text-[10px] text-gray-500">{(topBuyer.net_qty / 1000).toFixed(1)}k qty</span>
                        </Link>
                      ) : <span className="text-xs text-gray-600">-</span>}
                    </td>
                    <td className="px-4 py-5">
                      {topSeller ? (
                        <Link to={`/broker/${topSeller.broker}`} className="inline-flex flex-col p-1.5 rounded-lg hover:bg-rose-500/10 transition-colors">
                          <span className="text-rose-400 font-bold text-sm">B{topSeller.broker}</span>
                          <span className="text-[10px] text-gray-500">{(topSeller.net_qty / 1000).toFixed(1)}k qty</span>
                        </Link>
                      ) : <span className="text-xs text-gray-600">-</span>}
                    </td>
                    <td className="px-6 py-5">
                      <div className="flex flex-wrap gap-1.5">
                        {flags.length > 0 ? (
                          flags.map((flag, idx) => {
                            const isNegative = flag.toLowerCase().includes('sell') || flag.toLowerCase().includes('distribution');
                            const isWarning = flag.toLowerCase().includes('wash') || flag.toLowerCase().includes('pattern');
                            let color = isNegative ? 'text-rose-400 bg-rose-500/10 border-rose-500/20' : 'text-blue-400 bg-blue-500/10 border-blue-500/20';
                            if (isWarning) color = 'text-amber-400 bg-amber-500/10 border-amber-500/20';
                            
                            return (
                              <span key={idx} className={`text-[9px] font-bold border px-2 py-0.5 rounded-md uppercase tracking-wider ${color}`}>
                                {flag}
                              </span>
                            );
                          })
                        ) : (
                          <span className="text-[10px] text-gray-600 italic">Neutral flow</span>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              }) : (
                <tr>
                  <td colSpan="9">
                    <EmptyState 
                      icon={<AlertTriangle />} 
                      title="No Symbols Found" 
                      description="Try adjusting your filters or search term." 
                    />
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
