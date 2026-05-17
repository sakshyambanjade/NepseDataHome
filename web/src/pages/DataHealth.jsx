import React, { useState, useEffect } from 'react';
import { Database, Activity, CheckCircle2, AlertCircle, FileText, Check } from 'lucide-react';
import { PageHeader, LoadingState, EmptyState, MetricCard, Card } from '../components/ui';

export function DataHealth() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const base = import.meta.env.BASE_URL === '/' ? '/NepseDataHome/' : (import.meta.env.BASE_URL || '/NepseDataHome/');
        const res = await fetch(`${base}data/data_health.json`);
        const json = await res.json();
        setData(json);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) return <LoadingState text="Checking data health..." />;
  if (!data) return <EmptyState icon={<AlertCircle />} title="No Data Found" description="Data health metrics are unavailable." />;

  return (
    <div className="space-y-8 animate-in fade-in duration-700 max-w-5xl mx-auto">
      <PageHeader 
        title="Data Pipeline Health"
        subtitle="Live diagnostics of the daily data generation pipeline."
        icon={<Database />}
      />

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard title="Latest Floorsheet" value={data.latest_floorsheet_date} icon={<CheckCircle2 className="w-5 h-5 text-emerald-400" />} />
        <MetricCard title="Active Symbols" value={data.symbol_count} icon={<Activity className="w-5 h-5 text-blue-400" />} />
        <MetricCard title="Total Transactions" value={data.transaction_count.toLocaleString()} />
        <MetricCard title="Pipeline Status" value={data.invalid_row_count === 0 ? "Healthy" : "Warnings"} colorClass={data.invalid_row_count === 0 ? "text-emerald-400" : "text-amber-400"} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <Card title="Data Quality Metrics">
          <ul className="space-y-4">
            <li className="flex justify-between items-center bg-white/5 p-4 rounded-xl border border-white/10">
              <span className="text-gray-400 font-bold">Baseline Available</span>
              {data.baseline_available ? (
                <span className="flex items-center text-emerald-400 font-bold"><CheckCircle2 className="w-4 h-4 mr-2" /> Yes</span>
              ) : (
                <span className="flex items-center text-rose-400 font-bold"><AlertCircle className="w-4 h-4 mr-2" /> No</span>
              )}
            </li>
            <li className="flex justify-between items-center bg-white/5 p-4 rounded-xl border border-white/10">
              <span className="text-gray-400 font-bold">Invalid Rows</span>
              <span className={`font-mono font-bold ${data.invalid_row_count > 0 ? 'text-rose-400' : 'text-emerald-400'}`}>{data.invalid_row_count}</span>
            </li>
            <li className="flex justify-between items-center bg-white/5 p-4 rounded-xl border border-white/10">
              <span className="text-gray-400 font-bold">Duplicate Transactions</span>
              <span className={`font-mono font-bold ${data.duplicate_transaction_count > 0 ? 'text-amber-400' : 'text-emerald-400'}`}>{data.duplicate_transaction_count}</span>
            </li>
            <li className="flex justify-between items-center bg-white/5 p-4 rounded-xl border border-white/10">
              <span className="text-gray-400 font-bold">Brokers Detected</span>
              <span className="font-mono font-bold text-white">{data.broker_count}</span>
            </li>
            <li className="flex justify-between items-center bg-white/5 p-4 rounded-xl border border-white/10">
              <span className="text-gray-400 font-bold">Generated Artifacts</span>
              <span className="font-mono font-bold text-blue-400">{data.generated_files} Files</span>
            </li>
          </ul>
        </Card>

        <Card title="Generation Artifacts">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Artifact file="flow_overview.json" desc="Market flow summary" />
          <Artifact file="broker_pairs.json" desc="Broker-to-broker volume" />
          <Artifact file="rotation_map.json" desc="Broker rotation scores" />
          <Artifact file="alerts.json" desc="Flow and pattern alerts" />
          <Artifact file="reports/latest.json" desc="EOD intelligence report" />
          <Artifact file="flowsheet_table.json" desc="Full symbol metrics" />
        </div>
      </Card>
      </div>
    </div>
  );
}

function Artifact({ file, desc }) {
  return (
    <div className="flex items-center p-3 rounded-lg bg-white/5 border border-white/10">
      <FileText className="w-4 h-4 text-gray-500 mr-3" />
      <div>
        <div className="font-mono text-sm text-blue-400">{file}</div>
        <div className="text-xs text-gray-500">{desc}</div>
      </div>
      <CheckCircle2 className="w-4 h-4 text-emerald-500 ml-auto" />
    </div>
  );
}
