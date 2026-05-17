import React, { useState, useEffect } from 'react';
import { Share2, ArrowRight, Activity } from 'lucide-react';
import { PageHeader, LoadingState, EmptyState, Card } from '../components/ui';
import { Link } from 'react-router-dom';

export function BrokerNetwork() {
  const [pairs, setPairs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchNetwork = async () => {
      try {
        const base = import.meta.env.BASE_URL === '/' ? '/NepseDataHome/' : (import.meta.env.BASE_URL || '/NepseDataHome/');
        const response = await fetch(`${base}data/flowsheet_table.json`);
        const flowsheet = await response.json();
        
        const allPairs = [];
        flowsheet.forEach(symbolData => {
          if (symbolData.drilldown?.broker_pairs) {
            symbolData.drilldown.broker_pairs.forEach(pair => {
              allPairs.push({
                symbol: symbolData.symbol,
                ...pair
              });
            });
          }
        });

        // Group by pair
        const pairMap = {};
        allPairs.forEach(p => {
          const key = `${p.buyer_broker}-${p.seller_broker}`;
          if (!pairMap[key]) {
            pairMap[key] = {
              buyer: p.buyer_broker,
              seller: p.seller_broker,
              total_qty: 0,
              total_amt: 0,
              symbols: new Set()
            };
          }
          pairMap[key].total_qty += p.quantity;
          pairMap[key].total_amt += p.amount;
          pairMap[key].symbols.add(p.symbol);
        });

        const sortedPairs = Object.values(pairMap)
          .map(p => ({ ...p, symbols: Array.from(p.symbols) }))
          .sort((a, b) => b.total_amt - a.total_amt)
          .slice(0, 30);

        setPairs(sortedPairs);
      } catch (err) {
        console.error("Error loading network", err);
      } finally {
        setLoading(false);
      }
    };
    fetchNetwork();
  }, []);

  if (loading) return <LoadingState text="Mapping Broker Counterparty Network..." />;
  if (pairs.length === 0) return <EmptyState icon={<Share2 />} title="No Network Data" description="Could not find sufficient broker pairing data." />;

  return (
    <div className="space-y-8 animate-in fade-in duration-700">
      <PageHeader 
        title="Broker Network"
        subtitle="Identifies the strongest repeating counterparty relationships across all symbols. High volume pairs may indicate coordinated routing or institutional matching."
        icon={<Share2 />}
      />

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {pairs.map((pair, idx) => (
          <Card key={idx} className="group hover:border-blue-500/30 transition-all">
            <div className="flex items-center justify-between mb-6 border-b border-white/5 pb-4">
              <Link to={`/broker/${pair.buyer}`} className="flex flex-col items-center group/broker">
                <div className="w-12 h-12 bg-blue-500/10 rounded-full flex items-center justify-center border border-blue-500/20 text-blue-400 font-black text-lg group-hover/broker:bg-blue-500 group-hover/broker:text-white transition-colors">
                  {pair.buyer}
                </div>
                <span className="text-[10px] font-bold text-gray-500 uppercase mt-2">Buyer</span>
              </Link>
              
              <div className="flex flex-col items-center px-4">
                <span className="text-xs font-bold text-gray-400 mb-1 font-mono">{(pair.total_qty / 1000).toFixed(1)}k QTY</span>
                <div className="w-16 h-px bg-white/10 relative">
                  <ArrowRight className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-4 h-4 text-gray-600 group-hover:text-blue-400 transition-colors" />
                </div>
                <span className="text-[10px] font-bold text-blue-400 mt-1 uppercase tracking-widest">
                  Rs. {(pair.total_amt / 1000000).toFixed(1)}M
                </span>
              </div>

              <Link to={`/broker/${pair.seller}`} className="flex flex-col items-center group/broker">
                <div className="w-12 h-12 bg-rose-500/10 rounded-full flex items-center justify-center border border-rose-500/20 text-rose-400 font-black text-lg group-hover/broker:bg-rose-500 group-hover/broker:text-white transition-colors">
                  {pair.seller}
                </div>
                <span className="text-[10px] font-bold text-gray-500 uppercase mt-2">Seller</span>
              </Link>
            </div>
            
            <div>
              <div className="flex items-center text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-3">
                <Activity className="w-3 h-3 mr-1" /> Active in {pair.symbols.length} Symbols
              </div>
              <div className="flex flex-wrap gap-1.5">
                {pair.symbols.slice(0, 6).map(s => (
                  <Link key={s} to={`/flowsheet/${s}`} className="px-2 py-1 bg-white/5 hover:bg-white/10 rounded text-[10px] font-bold text-gray-300 transition-colors">
                    {s}
                  </Link>
                ))}
                {pair.symbols.length > 6 && (
                  <span className="px-2 py-1 bg-white/5 rounded text-[10px] font-bold text-gray-500">
                    +{pair.symbols.length - 6} more
                  </span>
                )}
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
