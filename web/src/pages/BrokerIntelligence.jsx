import React, { useState, useEffect } from 'react';
import { Shield, TrendingUp, Users, AlertTriangle, ArrowRight, Info, Search } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';

export function BrokerIntelligence() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [searchBroker, setSearchBroker] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    
    const base = import.meta.env.BASE_URL === '/' ? '/NepseDataHome/' : (import.meta.env.BASE_URL || '/NepseDataHome/');
    fetch(`${base}data/broker_overview.json`)
      .then(res => res.json())
      .then(d => {
        setData(d);
        setLoading(false);
      })
      .catch(err => {
        console.error("Error loading broker data:", err);
        setLoading(false);
      });
  }, []);

  if (loading) return <div className="p-12 text-center text-gray-500">Scanning Floorsheet...</div>;
  if (!data) return <div className="p-12 text-center text-gray-500">No broker intelligence data available today.</div>;

  return (
    <div className="space-y-8 animate-in fade-in duration-700">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h2 className="text-3xl font-black text-white">Broker <span className="text-blue-500">Intelligence</span></h2>
          <p className="text-gray-400 mt-1">Analyzing floorsheet patterns for accumulation and smart money flow.</p>
        </div>
        <div className="px-4 py-2 bg-white/5 rounded-full border border-white/10 text-[10px] font-bold text-gray-400 uppercase tracking-widest">
          Last Snapshot: {data.date}
        </div>
      </div>

      {/* Broker Search Card */}
      <div className="glass-morphism rounded-3xl p-6 border border-white/5 flex flex-col md:flex-row items-center justify-between gap-6">
        <div className="flex items-center space-x-4">
          <div className="p-3 bg-blue-500/10 rounded-2xl">
            <Search className="w-6 h-6 text-blue-400" />
          </div>
          <div>
            <h3 className="text-xl font-bold text-white">Find Broker Portfolio</h3>
            <p className="text-sm text-gray-400">Enter a broker ID to see their net accumulation, distribution, and top counterparties.</p>
          </div>
        </div>
        <form 
          onSubmit={(e) => {
            e.preventDefault();
            if (searchBroker.trim()) navigate(`/broker/${searchBroker.trim()}`);
          }} 
          className="flex w-full md:w-auto"
        >
          <input 
            type="number" 
            placeholder="Broker ID (e.g. 58)" 
            value={searchBroker}
            onChange={(e) => setSearchBroker(e.target.value)}
            className="bg-white/5 border border-white/10 rounded-l-xl px-4 py-3 text-white focus:outline-none focus:border-blue-500 transition-colors w-full md:w-48"
            min="1"
            max="100"
            required
          />
          <button 
            type="submit"
            className="bg-blue-600 hover:bg-blue-500 text-white px-6 py-3 rounded-r-xl font-bold transition-colors border border-blue-600 hover:border-blue-500"
          >
            Go
          </button>
        </form>
      </div>

      {/* Top Ranking Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <section className="glass-morphism rounded-3xl p-6 border border-white/5">
          <div className="flex items-center space-x-3 mb-6">
            <div className="p-2 bg-green-500/10 rounded-xl">
              <TrendingUp className="text-green-500 w-5 h-5" />
            </div>
            <h3 className="text-lg font-bold text-white">Top Accumulation</h3>
          </div>
          <div className="space-y-4">
            {data.most_accumulated?.map((item, i) => (
              <Link to={`/flowsheet/${String(item.symbol).replace("/", "-")}`} key={item.symbol} className="flex items-center justify-between p-3 rounded-2xl bg-white/5 border border-white/5 hover:border-green-500/30 transition-all group">
                <div className="flex items-center space-x-3">
                  <span className="text-gray-600 font-mono text-xs w-4">{i + 1}</span>
                  <span className="font-bold text-white group-hover:text-green-400 transition-colors">{item.symbol}</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="h-1.5 w-16 bg-gray-800 rounded-full overflow-hidden">
                    <div className="h-full bg-green-500" style={{ width: `${item.accumulation_score}%` }}></div>
                  </div>
                  <span className="text-green-500 font-mono text-xs font-bold">{item.accumulation_score}</span>
                </div>
              </Link>
            ))}
          </div>
        </section>

        <section className="glass-morphism rounded-3xl p-6 border border-white/5">
          <div className="flex items-center space-x-3 mb-6">
            <div className="p-2 bg-blue-500/10 rounded-xl">
              <Shield className="text-blue-500 w-5 h-5" />
            </div>
            <h3 className="text-lg font-bold text-white">Smart Money Flow</h3>
          </div>
          <div className="space-y-4">
            {data.smart_money_ranking?.map((item, i) => (
              <Link to={`/flowsheet/${String(item.symbol).replace("/", "-")}`} key={item.symbol} className="flex items-center justify-between p-3 rounded-2xl bg-white/5 border border-white/5 hover:border-blue-500/30 transition-all group">
                <div className="flex items-center space-x-3">
                  <span className="text-gray-600 font-mono text-xs w-4">{i + 1}</span>
                  <span className="font-bold text-white group-hover:text-blue-400 transition-colors">{item.symbol}</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-blue-400 font-mono text-xs font-bold">{item.operator_like_score}</span>
                  <ArrowRight className="w-3 h-3 text-gray-700" />
                </div>
              </Link>
            ))}
          </div>
        </section>

        <section className="glass-morphism rounded-3xl p-6 border border-white/5">
          <div className="flex items-center space-x-3 mb-6">
            <div className="p-2 bg-amber-500/10 rounded-xl">
              <Users className="text-amber-500 w-5 h-5" />
            </div>
            <h3 className="text-lg font-bold text-white">Broker Flow Watch</h3>
          </div>
          <div className="space-y-3">
            {data.operator_watchlist?.slice(0, 8).map((item) => (
              <Link to={`/flowsheet/${String(item.symbol).replace("/", "-")}`} key={item.symbol} className="block p-3 rounded-2xl bg-white/5 border border-white/5 hover:border-amber-500/30 transition-all group">
                <div className="flex justify-between items-start mb-1">
                  <span className="font-bold text-white group-hover:text-amber-500 transition-colors">{item.symbol}</span>
                  <span className="text-[10px] font-bold text-amber-500 uppercase tracking-tighter">Flow Alert</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-[10px] text-gray-500">Pattern Score</span>
                  <span className="text-xs font-mono text-gray-300">{item.operator_like_score}</span>
                </div>
              </Link>
            ))}
          </div>
        </section>
      </div>

      {/* Methodology Note */}
      <div className="p-6 bg-blue-600/5 rounded-3xl border border-blue-500/10 flex items-start space-x-4">
        <Info className="text-blue-400 w-6 h-6 mt-1 flex-shrink-0" />
        <div className="space-y-1">
          <h4 className="text-blue-400 font-bold">Important: Activity Patterns</h4>
          <p className="text-gray-400 text-sm leading-relaxed">
            These scores detect statistical patterns in floorsheet data such as broker concentration, 
            net accumulation, and repetitive pairing. High scores highlight statistical outliers and 
            institutional or coordinated trading behavior through specific broker channels.
          </p>
        </div>
      </div>
    </div>
  );
}
