import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { ArrowLeft, TrendingUp, TrendingDown, Users, AlertTriangle, Activity } from "lucide-react";
import { Card, MetricCard, PageHeader, LoadingState, EmptyState } from '../components/ui';

export function BrokerDetail() {
  const { brokerId } = useParams();
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    const base = import.meta.env.BASE_URL === '/' ? '/NepseDataHome/' : (import.meta.env.BASE_URL || '/NepseDataHome/');
    fetch(`${base}data/brokers/${brokerId}.json`)
      .then((res) => {
        if (!res.ok) throw new Error("Broker data not found");
        return res.json();
      })
      .then(setData)
      .catch((err) => {
        console.error("Error loading broker detail:", err);
        setError(err.message);
      });
  }, [brokerId]);

  if (error) {
    return (
      <div className="max-w-3xl mx-auto mt-12">
        <EmptyState 
          icon={<AlertTriangle />}
          title="Data Unavailable"
          description={error || "Could not find intelligence for this broker today."}
        />
        <div className="text-center mt-4">
          <Link to="/brokers" className="text-blue-400 hover:text-blue-300 font-bold transition-colors inline-flex items-center">
            <ArrowLeft className="w-4 h-4 mr-1" /> Back to Broker Intelligence
          </Link>
        </div>
      </div>
    );
  }

  if (!data) return <LoadingState text="Loading broker detail..." />;

  const summary = data.summary || {};

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      <Link to="/brokers" className="text-blue-400 hover:text-blue-300 text-sm flex items-center w-fit transition-colors">
        <ArrowLeft className="w-4 h-4 mr-2" />
        Back to Broker Intelligence
      </Link>

      <PageHeader 
        title={`Broker ${data.broker}`}
        subtitle={`Broker Channel Position • ${data.date}`}
        rightElement={
          <div className="flex items-center space-x-4">
            <Link to={`/flow?broker=${data.broker}`} className="flex items-center px-4 py-2 bg-blue-500/10 hover:bg-blue-500/20 text-blue-400 font-bold rounded-xl border border-blue-500/20 transition-colors shadow-[0_0_15px_rgba(59,130,246,0.1)]">
              <Activity className="w-4 h-4 mr-2" /> View Flow Map
            </Link>
            <div className="flex flex-col items-end">
              <div className={`px-5 py-3 rounded-2xl border ${summary.total_net_qty >= 0 ? 'bg-emerald-500/5 border-emerald-500/10 text-emerald-400' : 'bg-rose-500/5 border-rose-500/10 text-rose-400'}`}>
                <span className="text-[10px] uppercase font-bold block opacity-60 leading-none mb-1">Total Net Flow</span>
                <span className="text-2xl font-black leading-none tracking-tight">
                {summary.total_net_qty > 0 ? '+' : ''}{Number(summary.total_net_qty).toLocaleString()} <span className="text-sm opacity-60">QTY</span>
              </span>
              </div>
            </div>
          </div>
        }
      />
      {data.flags && data.flags.length > 0 && (
        <div className="flex flex-wrap gap-2 mt-[-1rem] mb-4">
          {data.flags.map((flag, idx) => (
            <span key={idx} className="px-3 py-1 bg-amber-500/10 text-amber-500 border border-amber-500/20 rounded-full text-[10px] font-bold uppercase tracking-wider">
              {flag}
            </span>
          ))}
        </div>
      )}

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-8 relative z-10">
        <MetricCard title="Total Buy Qty" value={Number(summary.total_buy_qty || 0).toLocaleString()} colorClass="text-blue-400" />
        <MetricCard title="Total Sell Qty" value={Number(summary.total_sell_qty || 0).toLocaleString()} colorClass="text-rose-400" />
        <MetricCard title="Buy Amount" value={`Rs. ${(summary.total_buy_amt / 1000000).toFixed(2)}M`} colorClass="text-emerald-400" />
        <MetricCard title="Sell Amount" value={`Rs. ${(summary.total_sell_amt / 1000000).toFixed(2)}M`} colorClass="text-amber-400" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Section title="Net Buying Stocks" subtitle="Accumulation through this channel" icon={<TrendingUp />}>
          <BrokerStockTable rows={data.net_buy_stocks || []} positive />
        </Section>

        <Section title="Net Selling Stocks" subtitle="Distribution through this channel" icon={<TrendingDown />}>
          <BrokerStockTable rows={data.net_sell_stocks || []} />
        </Section>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1">
          <Section title="Top Counterparties" subtitle="Flow by matching broker" icon={<Users />}>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-gray-400 border-b border-white/10 text-[10px] uppercase tracking-wider">
                    <th className="text-left py-3 font-bold">Counterparty</th>
                    <th className="text-right py-3 font-bold">Matched Qty</th>
                  </tr>
                </thead>
                <tbody>
                  {(data.top_counterparties || []).length > 0 ? (
                    (data.top_counterparties || []).map((row) => (
                      <tr key={row.broker} className="border-b border-white/5 hover:bg-white/5 transition-colors group">
                        <td className="py-3">
                          <Link to={`/broker/${row.broker}`} className="flex items-center space-x-2">
                            <span className="w-6 h-6 rounded bg-gray-800 text-gray-400 flex items-center justify-center text-[10px] font-bold group-hover:bg-purple-500/20 group-hover:text-purple-400 transition-colors">
                              B{row.broker}
                            </span>
                            <span className="font-bold text-gray-300 group-hover:text-white transition-colors">Broker {row.broker}</span>
                          </Link>
                        </td>
                        <td className="text-right py-3 font-mono text-gray-300">{Number(row.quantity).toLocaleString()}</td>
                      </tr>
                    ))
                  ) : (
                    <tr><td colSpan="2" className="text-center py-6 text-gray-500 text-xs">No counterparty data</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </Section>
        </div>

        <div className="lg:col-span-2">
          <Section title="Largest Trades" subtitle="Major single-ticket executions">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-gray-400 border-b border-white/10 text-[10px] uppercase tracking-wider">
                    <th className="text-left py-3 font-bold">Txn</th>
                    <th className="text-left py-3 font-bold">Symbol</th>
                    <th className="text-left py-3 font-bold">Side</th>
                    <th className="text-left py-3 font-bold">Counterparty</th>
                    <th className="text-right py-3 font-bold">Qty</th>
                    <th className="text-right py-3 font-bold">Rate</th>
                    <th className="text-right py-3 font-bold">Amount</th>
                  </tr>
                </thead>
                <tbody>
                  {(data.largest_trades || []).length > 0 ? (
                    (data.largest_trades || []).map((row, idx) => (
                      <tr key={idx} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                        <td className="py-3 font-mono text-xs text-gray-500">{row.transaction_no}</td>
                        <td className="py-3">
                          <Link to={`/flowsheet/${row.symbol}`} className="font-bold text-white hover:text-blue-400 transition-colors">
                            {row.symbol}
                          </Link>
                        </td>
                        <td className="py-3">
                          <span className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase ${row.side === 'BUY' ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20' : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'}`}>
                            {row.side}
                          </span>
                        </td>
                        <td className="py-3">
                          <Link to={`/broker/${row.counterparty_broker}`} className="text-purple-400 hover:text-purple-300 font-bold transition-colors">
                            B{row.counterparty_broker}
                          </Link>
                        </td>
                        <td className="text-right py-3 font-mono text-gray-300">{Number(row.quantity).toLocaleString()}</td>
                        <td className="text-right py-3 font-mono text-gray-400">{row.rate}</td>
                        <td className="text-right py-3 font-mono text-gray-400 text-xs">Rs. {(Number(row.amount)/1000).toLocaleString()}k</td>
                      </tr>
                    ))
                  ) : (
                    <tr><td colSpan="7" className="text-center py-6 text-gray-500 text-xs">No large trades recorded</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </Section>
        </div>
      </div>
    </div>
  );
}

function Section({ title, subtitle, children, icon }) {
  return (
    <Card noPadding className="flex flex-col h-full">
      <div className="px-6 py-5 border-b border-white/5 bg-white/[0.02]">
        <div className="flex items-center gap-3">
          {icon && React.cloneElement(icon, { className: "w-5 h-5 text-blue-400" })}
          <div>
            <h3 className="text-lg font-bold text-white">{title}</h3>
            {subtitle && <div className="text-xs text-gray-400 mt-0.5">{subtitle}</div>}
          </div>
        </div>
      </div>
      <div className="p-6 flex-grow">
        {children}
      </div>
    </Card>
  );
}

function BrokerStockTable({ rows, positive }) {
  if (!rows || rows.length === 0) {
    return <div className="text-center py-8 text-gray-500 text-sm">No significant flows.</div>;
  }
  
  return (
    <div className="overflow-x-auto -mx-2 px-2">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-gray-400 border-b border-white/10 text-[10px] uppercase tracking-wider">
            <th className="text-left py-3 font-bold">Symbol</th>
            <th className="text-right py-3 font-bold">Buy Qty</th>
            <th className="text-right py-3 font-bold">Sell Qty</th>
            <th className="text-right py-3 font-bold">Net Qty</th>
            <th className="text-right py-3 font-bold">Weight</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.symbol} className="border-b border-white/5 hover:bg-white/5 transition-colors">
              <td className="py-3">
                <Link to={`/flowsheet/${row.symbol}`} className="font-black text-white hover:text-blue-400 transition-colors">
                  {row.symbol}
                </Link>
                <div className="text-[10px] text-gray-500 mt-0.5">{row.direction}</div>
              </td>
              <td className="text-right py-3 font-mono text-gray-400">{Number(row.buy_qty || 0).toLocaleString()}</td>
              <td className="text-right py-3 font-mono text-gray-400">{Number(row.sell_qty || 0).toLocaleString()}</td>
              <td className={`text-right py-3 font-mono font-bold ${positive ? "text-emerald-400" : "text-rose-400"}`}>
                {positive ? '+' : ''}{Number(row.net_qty || 0).toLocaleString()}
              </td>
              <td className="text-right py-3">
                <div className="inline-flex items-center">
                  <span className="font-mono text-xs text-gray-300 mr-2">{Number(row.broker_participation_pct || 0).toFixed(1)}%</span>
                  <div className="w-8 h-1.5 bg-gray-800 rounded-full overflow-hidden">
                    <div 
                      className={`h-full ${positive ? 'bg-emerald-500' : 'bg-rose-500'}`} 
                      style={{ width: `${Math.min(100, Number(row.broker_participation_pct || 0))}%` }}
                    />
                  </div>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
