import React, { useState, useEffect } from 'react';
import { Route, Routes, Link, useLocation, useNavigate, useSearchParams } from 'react-router-dom';
import { Activity, ArrowRight, Share2, Layers, Repeat, ArrowRightLeft, Database } from 'lucide-react';
import { PageHeader, LoadingState, EmptyState, MetricCard, Card, ScoreBadge } from '../components/ui';

export function FlowMap() {
  const [overview, setOverview] = useState(null);
  const [loading, setLoading] = useState(true);
  const [searchParams, setSearchParams] = useSearchParams();
  const [activeTab, setActiveTab] = useState(searchParams.get('tab') || 'replay');
  const symbolFilter = searchParams.get('symbol');
  const brokerFilter = searchParams.get('broker');

  useEffect(() => {
    const fetchOverview = async () => {
      try {
        const base = import.meta.env.BASE_URL === '/' ? '/NepseDataHome/' : (import.meta.env.BASE_URL || '/NepseDataHome/');
        const res = await fetch(`${base}data/flow/flow_overview.json`);
        const data = await res.json();
        setOverview(data);
      } catch (err) {
        console.error("Failed to load flow overview", err);
      } finally {
        setLoading(false);
      }
    };
    fetchOverview();
  }, []);

  if (loading) return <LoadingState text="Booting Flow Map Engine..." />;
  if (!overview) return <EmptyState icon={<Database />} title="No Flow Data" description="Flow map artifacts have not been generated yet." />;

  const handleTabChange = (tab) => {
    setActiveTab(tab);
    searchParams.set('tab', tab);
    setSearchParams(searchParams);
  };

  const tabs = [
    { id: 'replay', label: 'Transaction Replay', icon: <ArrowRightLeft className="w-4 h-4" /> },
    { id: 'pairs', label: 'Broker Pairs', icon: <Share2 className="w-4 h-4" /> },
    { id: 'rotation', label: 'Sector Rotation', icon: <Repeat className="w-4 h-4" /> }
  ];

  return (
    <div className="space-y-8 animate-in fade-in duration-700">
      <PageHeader 
        title={symbolFilter ? `Flow Map: ${symbolFilter}` : brokerFilter ? `Flow Map: Broker ${brokerFilter}` : "Market Flow Map"}
        subtitle="After-market replay engine. Track exact share movement from broker to broker, identify concentrated channels, and watch institutional rotation step-by-step."
        icon={<Share2 />}
        rightElement={
          (symbolFilter || brokerFilter) && (
            <button onClick={() => { searchParams.delete('symbol'); searchParams.delete('broker'); setSearchParams(searchParams); }} className="text-xs text-blue-400 hover:text-blue-300 font-bold border border-blue-500/30 px-3 py-1.5 rounded-lg bg-blue-500/10 transition-colors">
              Clear Filters
            </button>
          )
        }
      />

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <MetricCard title="Total Trades" value={overview.total_trades.toLocaleString()} />
        <MetricCard title="Total Flow" value={`Rs. ${(overview.total_amount / 10000000).toFixed(2)} Cr`} colorClass="text-blue-400" />
        <MetricCard title="Most Active" value={overview.top_flow_symbols?.[0]?.symbol || "-"} colorClass="text-emerald-400" />
        <MetricCard title="Top Buyer" value={`B${overview.top_broker_pairs?.[0]?.buyer || "-"}`} />
        <MetricCard title="Top Seller" value={`B${overview.top_broker_pairs?.[0]?.seller || "-"}`} />
        <MetricCard title="Cross Trades" value={overview.cross_trade_watch?.length || 0} colorClass="text-amber-400" />
      </div>

      <div className="flex space-x-2 border-b border-white/10 pb-px">
        {tabs.map(t => (
          <button
            key={t.id}
            onClick={() => handleTabChange(t.id)}
            className={`flex items-center px-6 py-3 rounded-t-xl font-bold transition-colors ${activeTab === t.id ? 'bg-white/10 text-white border-t border-l border-r border-white/10' : 'text-gray-500 hover:bg-white/5 hover:text-gray-300'}`}
          >
            <span className="mr-2">{t.icon}</span>
            {t.label}
          </button>
        ))}
      </div>

      <div className="min-h-[500px]">
        {activeTab === 'replay' && <TransactionReplay date={overview.date} symbol={symbolFilter} broker={brokerFilter} />}
        {activeTab === 'pairs' && <BrokerPairs date={overview.date} symbol={symbolFilter} broker={brokerFilter} />}
        {activeTab === 'rotation' && <RotationMap date={overview.date} />}
      </div>
    </div>
  );
}

function TransactionReplay({ date, symbol, broker }) {
  const [txns, setTxns] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const base = import.meta.env.BASE_URL === '/' ? '/NepseDataHome/' : (import.meta.env.BASE_URL || '/NepseDataHome/');
    let url = `${base}data/flow/transactions_${date}.json`;
    if (symbol) {
      const safeSymbol = symbol.replace("/", "-");
      url = `${base}data/flow/symbols/${safeSymbol}_flow.json`;
    }
    fetch(url)
      .then(r => r.json())
      .then(d => {
        if (symbol) {
          setTxns(d.timeline || []);
        } else {
          setTxns(d);
        }
        setLoading(false);
      });
  }, [date, symbol]);

  if (loading) return <LoadingState text="Loading Replay..." />;
  
  let displayTxns = txns;
  if (broker) {
    displayTxns = txns.filter(t => String(t.from) === String(broker) || String(t.to) === String(broker));
  }

  return (
    <Card noPadding>
      <div className="overflow-x-auto max-h-[600px] overflow-y-auto">
        <table className="w-full text-sm text-left">
          <thead className="sticky top-0 bg-[#060b19] z-10 border-b border-white/10 shadow-lg">
            <tr className="text-gray-400 text-[10px] uppercase tracking-wider">
              <th className="p-4 font-bold">Time / Seq</th>
              <th className="p-4 font-bold">Seller</th>
              <th className="p-4 font-bold text-center">Direction</th>
              <th className="p-4 font-bold">Buyer</th>
              <th className="p-4 font-bold">Symbol</th>
              <th className="p-4 font-bold text-right">Quantity</th>
              <th className="p-4 font-bold text-right">Rate</th>
              <th className="p-4 font-bold text-right">Amount</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {displayTxns.slice(0, 500).map((t, idx) => (
              <tr key={idx} className="hover:bg-white/5 transition-colors group">
                <td className="p-4 font-mono text-gray-500 text-xs">{t.transaction_no}</td>
                <td className="p-4">
                  <Link to={`/flow?broker=${t.from}`} className="flex items-center">
                    <div className={`w-6 h-6 rounded flex items-center justify-center font-bold text-[10px] mr-2 ${String(t.from) === broker ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30' : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'}`}>B{t.from}</div>
                  </Link>
                </td>
                <td className="p-4 text-center">
                  <div className="flex items-center justify-center text-gray-600 group-hover:text-blue-500 transition-colors">
                    <div className="w-8 h-px bg-current"></div>
                    <ArrowRight className="w-3 h-3 -ml-1" />
                  </div>
                </td>
                <td className="p-4">
                  <Link to={`/flow?broker=${t.to}`} className="flex items-center">
                    <div className={`w-6 h-6 rounded flex items-center justify-center font-bold text-[10px] mr-2 ${String(t.to) === broker ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30' : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'}`}>B{t.to}</div>
                  </Link>
                </td>
                <td className="p-4">
                  <Link to={`/flow?symbol=${t.symbol || symbol}`} className="font-bold text-white hover:text-blue-400 transition-colors">{t.symbol || symbol}</Link>
                </td>
                <td className="p-4 text-right font-mono text-gray-300">{t.quantity.toLocaleString()}</td>
                <td className="p-4 text-right font-mono text-gray-400">{t.rate}</td>
                <td className="p-4 text-right font-mono text-blue-400">Rs. {(t.amount / 1000).toFixed(1)}k</td>
              </tr>
            ))}
          </tbody>
        </table>
        {displayTxns.length > 500 && (
          <div className="p-4 text-center text-xs text-gray-500 border-t border-white/5 bg-white/2">
            Showing first 500 transactions of {displayTxns.length.toLocaleString()} total.
          </div>
        )}
      </div>
    </Card>
  );
}

function BrokerPairs({ date, symbol, broker }) {
  const [pairs, setPairs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const base = import.meta.env.BASE_URL === '/' ? '/NepseDataHome/' : (import.meta.env.BASE_URL || '/NepseDataHome/');
    let url = `${base}data/flow/broker_pairs.json`;
    if (symbol) {
      const safeSymbol = symbol.replace("/", "-");
      url = `${base}data/flow/symbols/${safeSymbol}_flow.json`;
    }
    fetch(url)
      .then(r => r.json())
      .then(d => {
        if (symbol) {
          setPairs(d.edges || []);
        } else {
          setPairs(d);
        }
        setLoading(false);
      });
  }, [symbol]);

  if (loading) return <LoadingState text="Loading Pairs..." />;

  let displayPairs = pairs;
  if (broker) {
    displayPairs = pairs.filter(p => String(p.buyer || p.target) === String(broker) || String(p.seller || p.source) === String(broker));
  }

  return (
    <Card noPadding>
      <div className="overflow-x-auto max-h-[600px] overflow-y-auto">
        <table className="w-full text-sm text-left">
          <thead className="sticky top-0 bg-[#060b19] z-10 border-b border-white/10 shadow-lg">
            <tr className="text-gray-400 text-[10px] uppercase tracking-wider">
              <th className="p-4 font-bold">Seller Broker</th>
              <th className="p-4 font-bold text-center">Flow Direction</th>
              <th className="p-4 font-bold">Buyer Broker</th>
              <th className="p-4 font-bold text-right">Total Quantity</th>
              <th className="p-4 font-bold text-right">Total Amount</th>
              <th className="p-4 font-bold text-right">Matched Trades</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {displayPairs.map((p, idx) => {
              const sellerId = p.seller || p.source;
              const buyerId = p.buyer || p.target;
              return (
              <tr key={idx} className={`hover:bg-white/5 transition-colors ${buyerId === sellerId ? 'bg-amber-500/5' : ''}`}>
                <td className="p-4">
                  <Link to={`/flow?broker=${sellerId}`} className={`font-bold transition-colors ${String(sellerId) === broker ? 'text-amber-400' : 'text-rose-400 hover:text-rose-300'}`}>Broker {sellerId}</Link>
                </td>
                <td className="p-4 text-center text-gray-600">
                  <ArrowRight className="w-4 h-4 mx-auto" />
                </td>
                <td className="p-4">
                  <Link to={`/flow?broker=${buyerId}`} className={`font-bold transition-colors ${String(buyerId) === broker ? 'text-amber-400' : 'text-emerald-400 hover:text-emerald-300'}`}>Broker {buyerId}</Link>
                  {buyerId === sellerId && <span className="ml-2 text-[9px] bg-amber-500 text-black px-1.5 py-0.5 rounded uppercase font-bold">Cross</span>}
                </td>
                <td className="p-4 text-right font-mono text-gray-300">{(p.quantity / 1000).toFixed(1)}k</td>
                <td className="p-4 text-right font-mono text-blue-400">Rs. {(p.amount / 1000000).toFixed(2)}M</td>
                <td className="p-4 text-right font-mono text-gray-500">{p.trade_count}</td>
              </tr>
            )})}
          </tbody>
        </table>
      </div>
    </Card>
  );
}

function RotationMap() {
  const [rotations, setRotations] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const base = import.meta.env.BASE_URL === '/' ? '/NepseDataHome/' : (import.meta.env.BASE_URL || '/NepseDataHome/');
    fetch(`${base}data/flow/rotation_map.json`)
      .then(r => r.json())
      .then(d => {
        setRotations(d);
        setLoading(false);
      });
  }, []);

  if (loading) return <LoadingState text="Loading Rotation Patterns..." />;

  return (
    <Card noPadding>
      <div className="overflow-x-auto max-h-[600px] overflow-y-auto">
        <table className="w-full text-sm text-left">
          <thead className="sticky top-0 bg-[#060b19] z-10 border-b border-white/10 shadow-lg">
            <tr className="text-gray-400 text-[10px] uppercase tracking-wider">
              <th className="p-4 font-bold">Broker</th>
              <th className="p-4 font-bold text-right">Symbols Net Bought</th>
              <th className="p-4 font-bold text-right">Symbols Net Sold</th>
              <th className="p-4 font-bold text-right">Rotation Score</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {rotations.map((r, idx) => (
              <tr key={idx} className="hover:bg-white/5 transition-colors">
                <td className="p-4">
                  <Link to={`/broker/${r.broker}`} className="font-bold text-white hover:text-blue-400">Broker {r.broker}</Link>
                </td>
                <td className="p-4 text-right font-mono text-emerald-400">{r.net_buy_symbols}</td>
                <td className="p-4 text-right font-mono text-rose-400">{r.net_sell_symbols}</td>
                <td className="p-4 text-right">
                  <div className="inline-flex items-center">
                    <span className="font-mono text-gray-300 mr-3">{r.rotation_score.toFixed(1)}</span>
                    <div className="w-16 h-1.5 bg-gray-800 rounded-full overflow-hidden">
                      <div className="h-full bg-purple-500" style={{ width: `${Math.min(100, (r.rotation_score / rotations[0].rotation_score) * 100)}%` }}></div>
                    </div>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}
