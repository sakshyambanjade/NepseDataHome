import React, { useState, useEffect } from 'react';
import { Briefcase, TrendingUp, BarChart3, AlertTriangle } from 'lucide-react';
import { PageHeader, LoadingState, EmptyState, Card } from '../components/ui';
import { Link } from 'react-router-dom';

export function HoldingIntelligence() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchHoldings = async () => {
      try {
        const base = import.meta.env.BASE_URL === '/' ? '/NepseDataHome/' : (import.meta.env.BASE_URL || '/NepseDataHome/');
        const response = await fetch(`${base}data/flowsheet_table.json`);
        const flowsheet = await response.json();
        
        // Map flowsheet to approximate institutional holdings
        const holdings = flowsheet
          .filter(f => f.accumulation_score > 60 && f.net_buy_strength > 20)
          .sort((a, b) => b.accumulation_score - a.accumulation_score)
          .map(f => ({
            symbol: f.symbol,
            accScore: f.accumulation_score,
            netStrength: f.net_buy_strength,
            topBuyer: f.top_net_buyers?.[0] || null,
            volume: f.total_qty
          }));

        setData(holdings);
      } catch (err) {
        console.error("Error loading holding data", err);
      } finally {
        setLoading(false);
      }
    };
    fetchHoldings();
  }, []);

  if (loading) return <LoadingState text="Calculating Institutional Holding Proxies..." />;
  if (data.length === 0) return <EmptyState icon={<Briefcase />} title="No Significant Holdings Detected" description="There is not enough strong accumulation data to project holdings today." />;

  return (
    <div className="space-y-8 animate-in fade-in duration-700">
      <PageHeader 
        title="Holding Intelligence"
        subtitle="Estimated institutional positioning based on intense, sustained accumulation patterns. While exact ownership requires BOID data, this model highlights high-conviction broker channels."
        icon={<Briefcase />}
      />

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {data.map((item, idx) => (
          <Card key={idx} className="group relative overflow-hidden hover:border-emerald-500/30 transition-all">
            <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-500/10 blur-3xl -mr-16 -mt-16 rounded-full pointer-events-none" />
            
            <div className="flex justify-between items-start mb-6 relative z-10">
              <Link to={`/flowsheet/${item.symbol}`} className="text-3xl font-black text-white group-hover:text-emerald-400 transition-colors">
                {item.symbol}
              </Link>
              <div className="text-right">
                <div className="text-2xl font-black text-emerald-500">{item.accScore}</div>
                <div className="text-[9px] font-bold text-gray-500 uppercase tracking-widest">Acc. Score</div>
              </div>
            </div>

            <div className="space-y-4 relative z-10">
              <div className="bg-white/5 rounded-2xl p-4 border border-white/5 flex justify-between items-center">
                <div className="flex items-center text-[10px] font-bold text-gray-500 uppercase">
                  <TrendingUp className="w-3 h-3 mr-2" /> Buy Strength
                </div>
                <span className="text-sm font-black text-white">{item.netStrength}</span>
              </div>

              {item.topBuyer && (
                <div className="bg-emerald-500/5 rounded-2xl p-4 border border-emerald-500/10">
                  <div className="text-[10px] font-bold text-emerald-600/70 uppercase mb-2">Dominant Buyer</div>
                  <div className="flex justify-between items-center">
                    <Link to={`/broker/${item.topBuyer.broker}`} className="text-lg font-black text-emerald-400 hover:underline">
                      Broker {item.topBuyer.broker}
                    </Link>
                    <span className="text-xs font-mono text-emerald-200/60">{(item.topBuyer.net_qty / 1000).toFixed(1)}k Net</span>
                  </div>
                </div>
              )}
            </div>
            
            <div className="mt-6 flex justify-between items-center pt-4 border-t border-white/5 relative z-10">
              <span className="text-[10px] font-bold text-gray-600 uppercase">Vol: {(item.volume / 1000).toFixed(1)}k</span>
              <Link to={`/flowsheet/${item.symbol}`} className="text-[10px] font-black text-blue-400 uppercase tracking-widest hover:text-blue-300 transition-colors">
                View Detail →
              </Link>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
