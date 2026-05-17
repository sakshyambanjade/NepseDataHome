import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  TrendingUp, TrendingDown, Activity, Layers, 
  ArrowRight, ShieldAlert, Share2, Briefcase, 
  FileText, ArrowRightLeft, Users, AlertTriangle, CheckCircle2,
  Bell
} from 'lucide-react';
import { Card, PageHeader, LoadingState, ScoreBadge } from '../components/ui';

export function AnalyticsDashboard() {
  const [alerts, setAlerts] = useState([]);
  const [marketData, setMarketData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const base = import.meta.env.BASE_URL === '/' ? '/NepseDataHome/' : (import.meta.env.BASE_URL || '/NepseDataHome/');
        const [alertsRes, marketRes] = await Promise.all([
          fetch(`${base}data/alerts.json`).then(r => r.ok ? r.json() : []),
          fetch(`${base}data/market_overview.json`).then(r => r.ok ? r.json() : null)
        ]);
        setAlerts(alertsRes);
        setMarketData(marketRes);
      } catch (err) {
        console.error("Failed to load landing data", err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) return <LoadingState text="Initializing Intelligence Engine..." />;

  const modules = [
    { title: "Flow Map", path: "/flow", icon: ArrowRightLeft, color: "blue", desc: "After-market flow replay and broker-to-broker transaction mapping." },
    { title: "Broker Intelligence", path: "/brokers", icon: Users, color: "emerald", desc: "Analyze broker positioning, cross-trades, and daily net flow." },
    { title: "Holding Intelligence", path: "/holdings", icon: Briefcase, color: "purple", desc: "Estimate institutional accumulation based on daily flow intensity." },
    { title: "Flowsheet Table", path: "/flowsheet", icon: Activity, color: "rose", desc: "Raw market-wide transaction flow and pattern analytics." },
    { title: "Daily Report", path: "/report", icon: FileText, color: "amber", desc: "EOD printable market summary and top targets." },
    { title: "Data Health", path: "/data", icon: CheckCircle2, color: "gray", desc: "Live diagnostics of the intelligence generation pipeline." }
  ];

  return (
    <div className="space-y-12 animate-in fade-in duration-700 max-w-6xl mx-auto pb-16">
      <div className="text-center space-y-6 pt-12 pb-8">
        <h1 className="text-5xl md:text-6xl font-black text-white tracking-tighter">
          NepSense
        </h1>
        <p className="text-xl md:text-2xl text-blue-400 font-bold max-w-2xl mx-auto">
          After-market NEPSE intelligence platform.
        </p>
        <div className="inline-block px-4 py-2 bg-blue-500/10 border border-blue-500/20 rounded-xl text-blue-300 text-sm font-medium mt-4 max-w-3xl">
          <AlertTriangle className="w-4 h-4 inline-block mr-2 mb-0.5 text-blue-400" />
          This platform analyzes public floorsheet and market data. Broker codes represent broker channels, not verified individual investors.
        </div>
      </div>

      {marketData && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="glass-morphism p-6 rounded-3xl border border-white/5 text-center">
            <div className="text-[10px] uppercase font-bold text-gray-500 tracking-widest mb-1">Turnover</div>
            <div className="text-2xl font-black text-white">Rs. {(marketData.total_turnover / 10000000).toFixed(2)}Cr</div>
          </div>
          <div className="glass-morphism p-6 rounded-3xl border border-white/5 text-center">
            <div className="text-[10px] uppercase font-bold text-gray-500 tracking-widest mb-1">Volume</div>
            <div className="text-2xl font-black text-white">{(marketData.total_volume / 1000000).toFixed(2)}M</div>
          </div>
          <div className="glass-morphism p-6 rounded-3xl border border-white/5 text-center">
            <div className="text-[10px] uppercase font-bold text-gray-500 tracking-widest mb-1">Advancers</div>
            <div className="text-2xl font-black text-emerald-400">{marketData.advancers}</div>
          </div>
          <div className="glass-morphism p-6 rounded-3xl border border-white/5 text-center">
            <div className="text-[10px] uppercase font-bold text-gray-500 tracking-widest mb-1">Decliners</div>
            <div className="text-2xl font-black text-rose-400">{marketData.decliners}</div>
          </div>
        </div>
      )}

      <div>
        <h2 className="text-2xl font-black mb-6 flex items-center">
          <Layers className="w-6 h-6 mr-3 text-blue-500" /> Intelligence Modules
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {modules.map(mod => (
            <Link to={mod.path} key={mod.title} className="group glass-morphism rounded-3xl p-6 border border-white/5 hover:border-blue-500/30 transition-all duration-300">
              <div className={`w-12 h-12 rounded-2xl bg-${mod.color}-500/10 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform`}>
                <mod.icon className={`w-6 h-6 text-${mod.color}-400`} />
              </div>
              <h3 className="text-xl font-black text-white mb-2 group-hover:text-blue-400 transition-colors">{mod.title}</h3>
              <p className="text-sm text-gray-400 font-medium leading-relaxed">{mod.desc}</p>
            </Link>
          ))}
        </div>
      </div>

      {alerts && alerts.length > 0 && (
        <div>
          <h2 className="text-2xl font-black mb-6 flex items-center">
            <Bell className="w-6 h-6 mr-3 text-amber-500" /> Today's Flow Alerts
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {alerts.slice(0, 8).map((alert) => (
              <Link to={alert.link} key={alert.id} className="block glass-morphism rounded-2xl p-5 border border-white/5 hover:border-amber-500/30 transition-colors">
                <div className="flex justify-between items-start mb-3">
                  <div className="flex items-center">
                    {alert.severity === 'high' && <span className="w-2 h-2 rounded-full bg-rose-500 mr-2 animate-pulse"></span>}
                    {alert.severity === 'medium' && <span className="w-2 h-2 rounded-full bg-amber-500 mr-2"></span>}
                    {alert.severity === 'low' && <span className="w-2 h-2 rounded-full bg-blue-500 mr-2"></span>}
                    <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">{alert.category}</span>
                  </div>
                  <ScoreBadge score={alert.score} />
                </div>
                <h4 className="text-lg font-black text-white mb-1">{alert.title}</h4>
                <p className="text-sm text-gray-400">{alert.reason}</p>
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
