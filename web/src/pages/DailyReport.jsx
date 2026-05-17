import React, { useState, useEffect } from 'react';
import { FileText, Printer, Calendar, TrendingUp, AlertTriangle } from 'lucide-react';
import { PageHeader, LoadingState, EmptyState } from '../components/ui';

export function DailyReport() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const base = import.meta.env.BASE_URL === '/' ? '/NepseDataHome/' : (import.meta.env.BASE_URL || '/NepseDataHome/');
        const [market, report] = await Promise.all([
          fetch(`${base}data/market_overview.json`).then(r => r.json()),
          fetch(`${base}data/reports/latest.json`).then(r => r.json())
        ]);
        setData({ market, report });
      } catch (err) {
        console.error("Error loading report data", err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) return <LoadingState text="Generating End of Day Intelligence Report..." />;
  if (!data) return <EmptyState icon={<AlertTriangle />} title="Report Unavailable" description="Unable to generate the daily report." />;

  const topAccumulated = data.report.top_accumulation || [];
  const topDistributed = data.report.top_distribution || [];

  return (
    <div className="space-y-8 animate-in fade-in duration-700 max-w-4xl mx-auto">
      <div className="flex justify-between items-center mb-8">
        <h2 className="text-3xl font-black text-white flex items-center">
          <FileText className="w-8 h-8 mr-3 text-blue-500" /> End of Day Report
        </h2>
        <button onClick={() => window.print()} className="flex items-center px-4 py-2 bg-white/5 hover:bg-white/10 rounded-xl text-sm font-bold text-gray-300 transition-colors border border-white/10">
          <Printer className="w-4 h-4 mr-2" /> Print PDF
        </button>
      </div>

      <div className="bg-white text-black p-8 md:p-12 rounded-lg print:p-0 print:bg-transparent print:text-black shadow-2xl">
        <div className="border-b-4 border-blue-600 pb-6 mb-8 flex justify-between items-end">
          <div>
            <h1 className="text-4xl font-black tracking-tighter">NepSense Intelligence</h1>
            <p className="text-gray-500 font-bold uppercase tracking-widest mt-1 text-sm">Confidential Market Report</p>
          </div>
          <div className="text-right">
            <div className="text-2xl font-black">{data.market.date}</div>
            <div className="text-gray-500 font-bold uppercase tracking-widest text-xs flex items-center justify-end">
              <Calendar className="w-3 h-3 mr-1" /> EOD Summary
            </div>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-6 mb-12">
          <div className="p-4 bg-gray-50 rounded-xl border border-gray-200">
            <div className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-1">Turnover</div>
            <div className="text-2xl font-black text-gray-900">Rs. {(data.market.total_turnover / 1e7).toFixed(2)} Cr</div>
          </div>
          <div className="p-4 bg-gray-50 rounded-xl border border-gray-200">
            <div className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-1">Market Breadth</div>
            <div className="text-2xl font-black text-green-600">{data.market.advancers} <span className="text-sm text-gray-400">Adv</span> / <span className="text-red-500">{data.market.decliners}</span> <span className="text-sm text-gray-400">Dec</span></div>
          </div>
          <div className="p-4 bg-gray-50 rounded-xl border border-gray-200">
            <div className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-1">Total Volume</div>
            <div className="text-2xl font-black text-blue-600">{(data.report.summary.total_volume / 1e6).toFixed(2)}M</div>
          </div>
        </div>

        <div className="mb-12">
          <h3 className="text-xl font-black border-b-2 border-gray-200 pb-2 mb-4 flex items-center text-gray-900">
            <TrendingUp className="w-5 h-5 mr-2 text-green-500" /> Top Accumulation Targets
          </h3>
          <table className="w-full text-left text-sm border-collapse">
            <thead>
              <tr className="bg-gray-100 text-gray-600 uppercase tracking-wider text-[10px]">
                <th className="p-3 font-bold">Symbol</th>
                <th className="p-3 font-bold">Acc. Score</th>
                <th className="p-3 font-bold text-right">Volume</th>
              </tr>
            </thead>
            <tbody>
              {topAccumulated.map((row, idx) => (
                <tr key={idx} className="border-b border-gray-100">
                  <td className="p-3 font-black text-gray-900">{row.symbol}</td>
                  <td className="p-3 font-bold text-green-600">{row.score.toFixed(1)}</td>
                  <td className="p-3 text-right font-black text-gray-900">{row.volume.toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div>
          <h3 className="text-xl font-black border-b-2 border-gray-200 pb-2 mb-4 flex items-center text-gray-900">
            <TrendingDown className="w-5 h-5 mr-2 text-rose-500" /> Top Distribution Targets
          </h3>
          {topDistributed.length > 0 ? (
            <table className="w-full text-left text-sm border-collapse">
              <thead>
                <tr className="bg-gray-100 text-gray-600 uppercase tracking-wider text-[10px]">
                  <th className="p-3 font-bold">Symbol</th>
                  <th className="p-3 font-bold">Dist. Score</th>
                  <th className="p-3 font-bold text-right">Volume</th>
                </tr>
              </thead>
              <tbody>
                {topDistributed.map((row, idx) => (
                  <tr key={idx} className="border-b border-gray-100">
                    <td className="p-3 font-black text-gray-900">{row.symbol}</td>
                    <td className="p-3 font-bold text-rose-600">{row.score.toFixed(1)}</td>
                    <td className="p-3 text-right font-black text-gray-900">{row.volume.toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p className="text-gray-500 italic">No distribution patterns detected today.</p>
          )}
        </div>

        <div className="mt-8">
          <h3 className="text-xl font-black border-b-2 border-gray-200 pb-2 mb-4 flex items-center text-gray-900">
            <Info className="w-5 h-5 mr-2 text-blue-500" /> Data Quality Notes
          </h3>
          <ul className="list-disc pl-5 text-gray-600 text-sm">
            {data.report.data_quality_notes?.map((note, idx) => (
              <li key={idx}>{note}</li>
            ))}
          </ul>
        </div>

        <div className="mt-16 text-center text-[10px] text-gray-400 font-bold uppercase tracking-widest border-t border-gray-200 pt-8">
          End of Report • Generated automatically by NepSense Intelligence Engine
        </div>
      </div>
    </div>
  );
}
