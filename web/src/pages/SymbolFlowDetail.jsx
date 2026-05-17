import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { 
  ChevronLeft, BarChart3, Users, Activity, Zap, 
  ArrowRight, Table, Info, TrendingUp, TrendingDown, Repeat, AlertTriangle
} from 'lucide-react';
import { Card, MetricCard, ScoreBadge, PageHeader, LoadingState, EmptyState, InfoPill } from '../components/ui';

export function SymbolFlowDetail() {
  const { symbol } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const base = import.meta.env.BASE_URL === '/' ? '/NepseDataHome/' : (import.meta.env.BASE_URL || '/NepseDataHome/');
    const safeSymbol = String(symbol).replace("/", "-");
    fetch(`${base}data/symbols/${safeSymbol}_broker_flow.json`)
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

  if (loading) return <LoadingState text={`Analyzing deep flow data for ${symbol}...`} />;
  
  if (error || !data) {
    return (
      <div className="max-w-3xl mx-auto mt-12">
        <EmptyState 
          icon={<AlertTriangle />}
          title="Symbol Data Unavailable"
          description={error || "No flowsheet intelligence found for this symbol today."}
        />
        <div className="text-center mt-4">
          <Link to="/flowsheet" className="text-blue-400 hover:text-blue-300 font-bold transition-colors inline-flex items-center">
            <ChevronLeft className="w-4 h-4 mr-1" /> Back to Flowsheet Intelligence
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-in fade-in duration-700 pb-16">
      <Link to="/flowsheet" className="text-gray-500 hover:text-blue-400 text-sm font-medium transition-colors inline-flex items-center mb-[-1rem]">
        <ChevronLeft className="w-4 h-4 mr-1" /> Back to Flowsheet
      </Link>
      
      <PageHeader 
        title={data.symbol}
        subtitle={`Daily Broker-Flow Intelligence • Total Volume: ${(data.total_qty / 1000).toFixed(1)}k QTY • VWAP: Rs. ${data.vwap || "0.00"}`}
        icon={<Zap />}
        rightElement={
          <div className="flex items-center space-x-4">
            <Link to={`/flow?symbol=${data.symbol}`} className="flex items-center px-4 py-2 bg-blue-500/10 hover:bg-blue-500/20 text-blue-400 font-bold rounded-xl border border-blue-500/20 transition-colors shadow-[0_0_15px_rgba(59,130,246,0.1)]">
              <Zap className="w-4 h-4 mr-2" /> View Flow Map
            </Link>
            <div className="flex flex-col items-end">
              <span className="text-[10px] text-gray-500 font-bold uppercase tracking-widest">Trade Count</span>
              <span className="text-2xl font-black text-white">{data.trade_count}</span>
              <div className="mt-2 text-[10px] font-bold text-gray-400 uppercase">
                {data.date}
              </div>
            </div>
          </div>
        }
      />

      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
        <Card className="flex flex-col items-center justify-center p-4">
          <InfoPill text="Acc. Score" tooltip="Measures buying pressure, buyer concentration, and sliced buying patterns." />
          <div className="mt-3"><ScoreBadge score={data.accumulation_score} type="accumulation" /></div>
        </Card>
        <Card className="flex flex-col items-center justify-center p-4">
          <InfoPill text="Dist. Score" tooltip="Measures selling pressure, seller concentration, and structured offloading." />
          <div className="mt-3"><ScoreBadge score={data.distribution_score} type="distribution" /></div>
        </Card>
        <Card className="flex flex-col items-center justify-center p-4">
          <InfoPill text="Pattern Score" tooltip="Detects coordinated trading, wash-like patterns, and high broker churn." />
          <div className="mt-3"><ScoreBadge score={data.operator_like_score} type="pattern" /></div>
        </Card>
        <Card className="flex flex-col items-center justify-center p-4 text-center">
          <div className="text-[10px] font-bold text-gray-500 uppercase">Buy Strength</div>
          <div className="mt-2 text-2xl font-black text-emerald-400">{data.net_buy_strength || 0}</div>
        </Card>
        <Card className="flex flex-col items-center justify-center p-4 text-center">
          <div className="text-[10px] font-bold text-gray-500 uppercase">Sell Strength</div>
          <div className="mt-2 text-2xl font-black text-rose-400">{data.net_sell_strength || 0}</div>
        </Card>
        <Card className="flex flex-col items-center justify-center p-4 text-center">
          <div className="text-[10px] font-bold text-gray-500 uppercase">Pair Score</div>
          <div className="mt-2 text-2xl font-black text-blue-400">{data.repeated_pair_score || 0}</div>
        </Card>
        <Card className="flex flex-col items-center justify-center p-4 text-center">
          <div className="text-[10px] font-bold text-gray-500 uppercase">Cross Trade</div>
          <div className="mt-2 text-2xl font-black text-purple-400">{(data.cross_trade_ratio * 100)?.toFixed(1)}%</div>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <Card noPadding>
          <div className="px-6 py-5 border-b border-white/5 bg-white/[0.02] flex items-center justify-between">
            <h3 className="text-lg font-bold text-white flex items-center">
              <Users className="w-5 h-5 mr-3 text-emerald-400" /> Top Net Buyers
            </h3>
            <span className="text-[10px] text-gray-500 font-bold uppercase tracking-widest">Market Share</span>
          </div>
          <div className="divide-y divide-white/5">
            {data.top_net_buyers?.length > 0 ? data.top_net_buyers.map((b, idx) => (
              <Link to={`/broker/${b.broker}`} key={idx} className="px-6 py-4 flex items-center justify-between hover:bg-white/5 transition-all group">
                <div className="flex items-center space-x-4">
                  <div className="w-8 h-8 bg-emerald-500/10 rounded border border-emerald-500/20 flex items-center justify-center font-bold text-emerald-400 text-xs transition-colors">
                    B{b.broker}
                  </div>
                  <div>
                    <div className="text-sm font-bold text-white group-hover:text-emerald-400 transition-colors">Broker {b.broker}</div>
                    <div className="text-[10px] text-gray-500 font-mono">{(b.net_qty / 1000).toFixed(1)}k Net</div>
                  </div>
                </div>
                <div className="text-right font-mono font-bold text-emerald-400 text-sm">
                  {(b.share * 100)?.toFixed(1)}%
                </div>
              </Link>
            )) : <div className="p-6 text-center text-sm text-gray-500">No significant buyers</div>}
          </div>
        </Card>

        <Card noPadding>
          <div className="px-6 py-5 border-b border-white/5 bg-white/[0.02] flex items-center justify-between">
            <h3 className="text-lg font-bold text-white flex items-center">
              <Users className="w-5 h-5 mr-3 text-rose-400" /> Top Net Sellers
            </h3>
            <span className="text-[10px] text-gray-500 font-bold uppercase tracking-widest">Market Share</span>
          </div>
          <div className="divide-y divide-white/5">
            {data.top_net_sellers?.length > 0 ? data.top_net_sellers.map((s, idx) => (
              <Link to={`/broker/${s.broker}`} key={idx} className="px-6 py-4 flex items-center justify-between hover:bg-white/5 transition-all group">
                <div className="flex items-center space-x-4">
                  <div className="w-8 h-8 bg-rose-500/10 rounded border border-rose-500/20 flex items-center justify-center font-bold text-rose-400 text-xs transition-colors">
                    B{s.broker}
                  </div>
                  <div>
                    <div className="text-sm font-bold text-white group-hover:text-rose-400 transition-colors">Broker {s.broker}</div>
                    <div className="text-[10px] text-gray-500 font-mono">{(s.net_qty / 1000).toFixed(1)}k Net</div>
                  </div>
                </div>
                <div className="text-right font-mono font-bold text-rose-400 text-sm">
                  {(s.share * 100)?.toFixed(1)}%
                </div>
              </Link>
            )) : <div className="p-6 text-center text-sm text-gray-500">No significant sellers</div>}
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <Card noPadding>
          <div className="px-6 py-5 border-b border-white/5 bg-white/[0.02] flex items-center">
            <Repeat className="w-5 h-5 mr-3 text-blue-400" />
            <h3 className="text-lg font-bold text-white">Repeating Broker Pairs</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-white/5">
                <tr className="text-gray-500 uppercase tracking-widest text-[10px] font-bold">
                  <th className="px-6 py-3">Pair (Buy → Sell)</th>
                  <th className="px-6 py-3 text-right">Volume</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {data.drilldown?.broker_pairs?.length > 0 ? data.drilldown.broker_pairs.map((pair, idx) => (
                  <tr key={idx} className="hover:bg-white/5 transition-colors">
                    <td className="px-6 py-4 font-bold text-gray-300 flex items-center">
                      <Link to={`/broker/${pair.buyer_broker}`} className="text-emerald-400 hover:underline">B{pair.buyer_broker}</Link> 
                      <ArrowRight className="w-4 h-4 mx-3 opacity-30" /> 
                      <Link to={`/broker/${pair.seller_broker}`} className="text-rose-400 hover:underline">B{pair.seller_broker}</Link>
                    </td>
                    <td className="px-6 py-4 text-right font-mono text-gray-400">{(pair.quantity / 1000)?.toFixed(1)}k</td>
                  </tr>
                )) : <tr><td colSpan="2" className="p-6 text-center text-sm text-gray-500">No repeating pairs detected.</td></tr>}
              </tbody>
            </table>
          </div>
        </Card>

        <Card noPadding>
          <div className="px-6 py-5 border-b border-white/5 bg-white/[0.02] flex items-center">
            <Table className="w-5 h-5 mr-3 text-amber-400" />
            <h3 className="text-lg font-bold text-white">Largest Transactions</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-white/5">
                <tr className="text-gray-500 uppercase tracking-widest text-[10px] font-bold">
                  <th className="px-6 py-3">Brokers</th>
                  <th className="px-6 py-3">Qty</th>
                  <th className="px-6 py-3">Rate</th>
                  <th className="px-6 py-3 text-right">Amount</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {data.drilldown?.largest_trades?.length > 0 ? data.drilldown.largest_trades.map((trade, idx) => (
                  <tr key={idx} className="hover:bg-white/5 transition-colors">
                    <td className="px-6 py-4">
                      <Link to={`/broker/${trade.buyer_broker}`} className="text-emerald-400 font-bold hover:underline">B{trade.buyer_broker}</Link>
                      <span className="mx-2 opacity-20">/</span>
                      <Link to={`/broker/${trade.seller_broker}`} className="text-rose-400 font-bold hover:underline">B{trade.seller_broker}</Link>
                    </td>
                    <td className="px-6 py-4 font-mono font-bold text-gray-300">{trade.quantity.toLocaleString()}</td>
                    <td className="px-6 py-4 font-mono text-gray-500">{trade.rate}</td>
                    <td className="px-6 py-4 text-right font-mono text-gray-300">Rs. {(trade.amount / 1000000)?.toFixed(2)}M</td>
                  </tr>
                )) : <tr><td colSpan="4" className="p-6 text-center text-sm text-gray-500">No large trades recorded.</td></tr>}
              </tbody>
            </table>
          </div>
        </Card>
      </div>

      <Card className="text-center bg-blue-500/5 border-blue-500/10">
        <Info className="w-6 h-6 text-blue-400 mx-auto mb-3" />
        <h4 className="text-sm font-bold text-white mb-2 uppercase">Flow Explanation</h4>
        <p className="text-xs text-gray-400 max-w-3xl mx-auto leading-relaxed">
          The flow analysis measures institutional routing behavior. High Accumulation Scores imply coordinated buying through a small network of brokers, while high Pattern Scores highlight structured anomalies (e.g., sliced trades or unusual matching sequences). These signals reflect broker-channel order routing, not specific investor identities.
        </p>
      </Card>

    </div>
  );
}
