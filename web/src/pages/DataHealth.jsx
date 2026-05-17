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
        const res = await fetch(`${base}data/reports/latest.json`);
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
        <MetricCard title="Latest Floorsheet" value={data.date} icon={<CheckCircle2 className="w-5 h-5 text-emerald-400" />} />
        <MetricCard title="Active Symbols" value={data.summary.active_symbols} icon={<Activity className="w-5 h-5 text-blue-400" />} />
        <MetricCard title="Total Volume Processed" value={(data.summary.total_volume / 1000000).toFixed(2) + "M"} />
        <MetricCard title="Pipeline Status" value="Healthy" colorClass="text-emerald-400" />
      </div>

      <Card title="Data Quality Notes">
        <ul className="space-y-3">
          {data.data_quality_notes?.map((note, idx) => (
            <li key={idx} className="flex items-start bg-white/5 p-4 rounded-xl border border-white/10">
              <Check className="w-5 h-5 text-emerald-400 mr-3 mt-0.5 shrink-0" />
              <span className="text-gray-300">{note}</span>
            </li>
          ))}
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
