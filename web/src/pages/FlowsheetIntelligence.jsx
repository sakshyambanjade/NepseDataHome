import React, { useState, useEffect } from 'react';
import { Search, Filter, Info, ShieldCheck, AlertCircle, ChevronUp, ChevronDown, Table, BarChart3, Activity } from 'lucide-react';
import { Link } from 'react-router-dom';

export function FlowsheetIntelligence() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [sortConfig, setSortConfig] = useState({ key: 'operator_like_score', direction: 'desc' });

  useEffect(() => {
    const isDev = import.meta.env.DEV;
    const base = isDev ? "/" : (import.meta.env.BASE_URL || "/");
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

  const sortedData = [...data]
    .filter(item => {
      const searchLower = searchTerm.toLowerCase();
      const topBuyers = item.top_net_buyers || [];
      const topSellers = item.top_net_sellers || [];
      
      return (
        item.symbol.toLowerCase().includes(searchLower) ||
        topBuyers.some(b => b.broker.toLowerCase().includes(searchLower)) ||
        topSellers.some(s => s.broker.toLowerCase().includes(searchLower))
      );
    })
    .sort((a, b) => {
      if (a[sortConfig.key] < b[sortConfig.key]) return sortConfig.direction === 'asc' ? -1 : 1;
      if (a[sortConfig.key] > b[sortConfig.key]) return sortConfig.direction === 'asc' ? 1 : -1;
      return 0;
    });

  const getScoreColor = (score) => {
    if (score >= 85) return "text-red-500 bg-red-500/10";
    if (score >= 70) return "text-orange-500 bg-orange-500/10";
    if (score >= 50) return "text-amber-500 bg-amber-500/10";
    if (score >= 30) return "text-blue-500 bg-blue-500/10";
    return "text-gray-400 bg-gray-400/10";
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-24">
        <Activity className="w-12 h-12 text-blue-500 animate-spin mb-4" />
        <p className="text-gray-400 animate-pulse">Analyzing after-market floorsheet intelligence...</p>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-in fade-in duration-700">
      {/* Header & Explanation */}
      <div className="glass-morphism rounded-3xl p-8 border border-white/5 relative overflow-hidden">
        <div className="absolute top-0 right-0 p-12 opacity-5 pointer-events-none">
          <Table className="w-64 h-64 text-blue-400" />
        </div>
        
        <div className="relative z-10">
          <div className="flex items-center space-x-3 mb-4">
            <div className="bg-blue-600/20 p-2 rounded-xl">
              <BarChart3 className="text-blue-400 w-6 h-6" />
            </div>
            <h2 className="text-3xl font-bold text-white tracking-tight">Flowsheet Intelligence</h2>
          </div>
          <p className="text-gray-400 max-w-3xl leading-relaxed">
            Real-time analysis of the entire daily NEPSE floorsheet. Our engine scans every transaction to detect 
            accumulation pressure, distribution channels, and unusual broker-flow anomalies using transaction 
            sequence pattern recognition.
          </p>
          
          <div className="mt-6 flex items-start p-4 bg-blue-500/5 border border-blue-500/10 rounded-2xl">
            <Info className="w-5 h-5 text-blue-400 mr-3 mt-0.5" />
            <p className="text-xs text-blue-300/70">
              <span className="font-bold text-blue-300">Important:</span> Broker codes represent institutional and individual 
              broker channels, not verified individual identities. This intelligence highlights flow anomalies, not trade advice.
            </p>
          </div>
        </div>
      </div>

      {/* Search & Filters */}
      <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
        <div className="relative w-full md:w-96 group">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500 group-focus-within:text-blue-400 transition-colors" />
          <input 
            type="text" 
            placeholder="Search symbol or broker..."
            className="w-full bg-gray-900/50 border border-white/10 rounded-2xl py-3 pl-12 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all placeholder:text-gray-600"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        
        <div className="flex items-center space-x-2 text-xs text-gray-500">
          <span className="bg-white/5 px-3 py-1.5 rounded-full border border-white/5">
            {sortedData.length} Symbols Tracked
          </span>
          <span className="bg-white/5 px-3 py-1.5 rounded-full border border-white/5">
            Updated: {data[0]?.date || "N/A"}
          </span>
        </div>
      </div>

      {/* Main Table */}
      <div className="glass-morphism rounded-3xl border border-white/5 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-white/5 border-b border-white/5">
                <th onClick={() => handleSort('symbol')} className="px-6 py-4 text-xs font-bold text-gray-400 uppercase tracking-wider cursor-pointer hover:text-white transition-colors">
                  Symbol {sortConfig.key === 'symbol' && (sortConfig.direction === 'desc' ? <ChevronDown className="w-3 h-3 inline ml-1" /> : <ChevronUp className="w-3 h-3 inline ml-1" />)}
                </th>
                <th onClick={() => handleSort('accumulation_score')} className="px-4 py-4 text-xs font-bold text-gray-400 uppercase tracking-wider cursor-pointer hover:text-white transition-colors">
                  Acc. Score
                </th>
                <th onClick={() => handleSort('distribution_score')} className="px-4 py-4 text-xs font-bold text-gray-400 uppercase tracking-wider cursor-pointer hover:text-white transition-colors">
                  Dist. Score
                </th>
                <th onClick={() => handleSort('operator_like_score')} className="px-4 py-4 text-xs font-bold text-gray-400 uppercase tracking-wider cursor-pointer hover:text-white transition-colors">
                  Op Score
                </th>
                <th onClick={() => handleSort('total_qty')} className="px-4 py-4 text-xs font-bold text-gray-400 uppercase tracking-wider cursor-pointer hover:text-white transition-colors">
                  Volume
                </th>
                <th onClick={() => handleSort('vwap')} className="px-4 py-4 text-xs font-bold text-gray-400 uppercase tracking-wider cursor-pointer hover:text-white transition-colors">
                  VWAP
                </th>
                <th className="px-6 py-4 text-xs font-bold text-gray-400 uppercase tracking-wider">Top Net Players</th>
                <th className="px-6 py-4 text-xs font-bold text-gray-400 uppercase tracking-wider">Intelligence Flags</th>
                <th className="px-6 py-4 text-xs font-bold text-gray-400 uppercase tracking-wider">Data Quality</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {sortedData.map((row) => {
                const topBuyer = row.top_net_buyers?.[0];
                const topSeller = row.top_net_sellers?.[0];
                const flags = row.flags || [];
                const warnings = row.data_quality?.warnings || [];

                return (
                  <tr key={row.symbol} className="hover:bg-white/5 transition-colors group">
                    <td className="px-6 py-5">
                      <Link to={`/flowsheet/${String(row.symbol).replace("/", "-")}`} className="flex flex-col group/sym">
                        <span className="text-lg font-bold text-white group-hover/sym:text-blue-400 transition-colors">{row.symbol}</span>
                        <span className="text-[10px] text-gray-500 font-medium">{row.trade_count} Trades</span>
                      </Link>
                    </td>
                    <td className="px-4 py-5">
                      <div className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-bold ${getScoreColor(row.accumulation_score)}`}>
                        {row.accumulation_score}
                      </div>
                    </td>
                    <td className="px-4 py-5">
                      <div className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-bold ${getScoreColor(row.distribution_score)}`}>
                        {row.distribution_score}
                      </div>
                    </td>
                    <td className="px-4 py-5">
                      <div className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-bold ${getScoreColor(row.operator_like_score)}`}>
                        {row.operator_like_score}
                      </div>
                    </td>
                    <td className="px-4 py-5">
                      <div className="text-sm font-bold text-gray-300">{(row.total_qty / 1000).toFixed(1)}k</div>
                      <div className="text-[10px] text-gray-500 font-medium">Qty</div>
                    </td>
                    <td className="px-4 py-5">
                      <div className="text-sm font-bold text-gray-300">Rs. {row.vwap}</div>
                      <div className="text-[10px] text-gray-500 font-medium">Avg Rate</div>
                    </td>
                    <td className="px-6 py-5">
                      <div className="flex flex-col space-y-1">
                        <div className="flex items-center text-xs">
                          <span className="text-blue-400 font-bold w-12">Buyer:</span>
                          <Link to={`/broker/${topBuyer?.broker}`} className="text-gray-300 bg-blue-500/10 px-1.5 py-0.5 rounded ml-1 hover:bg-blue-500/20 hover:text-white transition-all">
                            B{topBuyer?.broker || "N/A"} ({topBuyer ? (topBuyer.net_qty / 1000).toFixed(1) : 0}k)
                          </Link>
                        </div>
                        <div className="flex items-center text-xs">
                          <span className="text-red-400 font-bold w-12">Seller:</span>
                          <Link to={`/broker/${topSeller?.broker}`} className="text-gray-300 bg-red-500/10 px-1.5 py-0.5 rounded ml-1 hover:bg-red-500/20 hover:text-white transition-all">
                            B{topSeller?.broker || "N/A"} ({topSeller ? (topSeller.net_qty / 1000).toFixed(1) : 0}k)
                          </Link>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-5">
                      <div className="flex flex-wrap gap-1.5">
                        {flags.length > 0 ? (
                          flags.map((flag, idx) => {
                            const isNegative = flag.toLowerCase().includes('sell') || flag.toLowerCase().includes('distribution');
                            return (
                              <span key={idx} className={`text-[9px] font-bold border px-2 py-0.5 rounded uppercase ${isNegative ? 'bg-red-500/5 border-red-500/10 text-red-400/80' : 'bg-blue-500/5 border-blue-500/10 text-blue-400/80'}`}>
                                {flag}
                              </span>
                            );
                          })
                        ) : (
                          <span className="text-[10px] text-gray-600 italic">Neutral flow</span>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-5">
                      <div className="flex items-center">
                        {warnings.length === 0 ? (
                          <ShieldCheck className="w-5 h-5 text-emerald-500/50" />
                        ) : (
                          <div className="group relative">
                            <AlertCircle className="w-5 h-5 text-amber-500/50 cursor-help" />
                            <div className="absolute bottom-full right-0 mb-2 w-48 p-2 bg-gray-900 border border-white/10 rounded-xl text-[10px] text-gray-400 invisible group-hover:visible z-50">
                              {warnings.join(", ").replace(/_/g, " ")}
                            </div>
                          </div>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
