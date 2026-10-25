import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Async, Badge, Card, Empty, PageHeader, RangeTabs, RefreshButton, Stat } from '../components/common/ui';
import MetricChart from '../components/charts/MetricChart';
import ServiceTable from '../components/services/ServiceTable';
import useAsync from '../hooks/useAsync';
import { getAlerts, getAnomalies, getDashboardSummary, getPrefs, getServices } from '../services/api';
import { avg, fmtTime, ms, pct } from '../utils/format';

export default function Overview() {
  const prefs = getPrefs();
  const [range, setRange] = useState(prefs.defaultRange);
  const state = useAsync(async () => {
    const [services, alerts, anomalies, summary] = await Promise.all([getServices(), getAlerts(), getAnomalies(), getDashboardSummary(range)]);
    return { services, alerts, anomalies, summary };
  }, [range], prefs.refreshSec);
  return (
    <>
      <PageHeader title="Overview" subtitle={state.data ? `Last updated ${fmtTime(state.data.summary.updatedAt)}` : 'Loading…'}>
        <RangeTabs value={range} onChange={setRange} /><RefreshButton onClick={state.reload} />
      </PageHeader>
      <Async state={state}>{({ services, alerts, anomalies, summary }) => {
        const total = services.length, healthy = services.filter((s) => s.status === 'Healthy').length;
        const active = alerts.filter((a) => a.status === 'Active').length;
        const score = total ? Math.round((healthy / total) * 100) : 0;
        const activity = [...alerts.map((a) => ({ id: a.id, kind: 'Alert', text: a.title, sev: a.severity, t: a.timestamp })),
          ...anomalies.map((a) => ({ id: a.id, kind: 'Anomaly', text: `${a.metric} deviation on ${a.service}`, sev: a.severity, t: a.detectedAt }))].sort((a, b) => b.t - a.t).slice(0, 7);
        return (
          <div className="space-y-5">
            <div className="grid grid-cols-2 gap-3 lg:grid-cols-5">
              <Stat label="Monitored services" value={total} />
              <Stat label="Healthy services" value={healthy} tone="text-emerald-300" />
              <Stat label="Services with anomalies" value={total - healthy} tone="text-amber-300" />
              <Stat label="Active alerts" value={active} tone="text-red-300" />
              <Stat label="System health" value={`${score}%`} hint="Share of services healthy" />
            </div>
            <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
              <Stat label="Avg CPU" value={pct(avg(services, 'cpu'))} hint="Across services" />
              <Stat label="Avg memory" value={pct(avg(services, 'memory'))} hint="Across services" />
              <Stat label="Avg latency" value={ms(avg(services, 'latency'))} hint="Across services" />
              <Stat label="Avg error rate" value={pct(avg(services, 'errorRate'))} hint="Across services" />
            </div>
            <div className="grid gap-4 xl:grid-cols-3">
              <MetricChart title="CPU utilization (avg)" unit="%" data={summary.series} domain={[0, 100]} series={[{ key: 'cpu', name: 'CPU', color: '#22d3ee' }]} />
              <MetricChart title="Memory utilization (avg)" unit="%" data={summary.series} domain={[0, 100]} series={[{ key: 'memory', name: 'Memory', color: '#60a5fa' }]} />
              <MetricChart title="Latency (avg)" unit="ms" data={summary.series} series={[{ key: 'latency', name: 'Latency', color: '#f59e0b' }]} />
            </div>
            <div className="grid gap-4 xl:grid-cols-3">
              <Card title="Service health" className="xl:col-span-2"><ServiceTable services={services} /></Card>
              <Card title="Recent anomaly & alert activity">
                {!activity.length ? <Empty text="No recent activity." /> : (
                  <ul className="space-y-3">{activity.map((a) => (
                    <li key={a.id} className="text-sm"><div className="flex items-center justify-between gap-2"><Badge value={a.sev} /><span className="text-xs text-slate-500">{fmtTime(a.t)}</span></div>
                      <p className="mt-1 text-slate-300">{a.text}</p><p className="text-xs text-slate-500">{a.kind} {a.id}</p></li>))}</ul>)}
                <Link to="/alerts" className="mt-3 inline-block text-sm text-cyan-300 hover:underline">View all alerts</Link>
              </Card>
            </div>
          </div>);
      }}</Async>
    </>
  );
}
