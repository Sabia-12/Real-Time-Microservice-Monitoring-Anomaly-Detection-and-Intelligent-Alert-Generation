/**
 * Overview — System-level dashboard for Online Boutique monitoring.
 * Shows health grid, summary stats, metric trend charts, and recent activity.
 */
import { useState } from 'react';
import { Link } from 'react-router-dom';
import { AlertTriangle, CheckCircle2, XCircle } from 'lucide-react';
import { Async, Badge, Card, Empty, PageHeader, RangeTabs, RefreshButton, Stat } from '../components/common/ui';
import MetricChart from '../components/charts/MetricChart';
import ServiceTable from '../components/services/ServiceTable';
import useAsync from '../hooks/useAsync';
import { getAlerts, getAnomalies, getDashboardSummary, getPrefs, getServices } from '../services/api';
import { FAULT_TYPE_LABELS } from '../data/mock';
import { avg, fmtTime, ms, pct } from '../utils/format';

const STATUS_ICON = {
  Healthy: <CheckCircle2 size={12} className="text-emerald-400" />,
  Warning: <AlertTriangle size={12} className="text-amber-400" />,
  Critical: <XCircle size={12} className="text-red-400" />,
};
const STATUS_COLOR = {
  Healthy: 'border-emerald-500/20 bg-emerald-500/5',
  Warning: 'border-amber-500/20 bg-amber-500/5',
  Critical: 'border-red-500/20 bg-red-500/5 animate-pulse',
};

function MiniServiceGrid({ services }) {
  return (
    <div className="grid grid-cols-3 gap-2 sm:grid-cols-4 lg:grid-cols-6">
      {services.map((s) => (
        <Link
          key={s.id}
          to={`/services/${s.id}`}
          className={`group flex flex-col items-center gap-1 rounded-lg border p-2 text-center transition-all hover:scale-105 hover:shadow-md ${STATUS_COLOR[s.status] || STATUS_COLOR.Healthy}`}
        >
          <span className="flex items-center gap-1">{STATUS_ICON[s.status]}</span>
          <span className="w-full truncate text-[10px] font-medium text-slate-300 group-hover:text-white">{s.name}</span>
          {s.faultType && (
            <span className="rounded-full bg-red-500/10 px-1 py-0.5 text-[9px] text-red-400 ring-1 ring-red-500/20">
              {s.faultType}
            </span>
          )}
        </Link>
      ))}
    </div>
  );
}

export default function Overview() {
  const prefs = getPrefs();
  const [range, setRange] = useState(prefs.defaultRange);
  const state = useAsync(async () => {
    const [services, alerts, anomalies, summary] = await Promise.all([
      getServices(), getAlerts(), getAnomalies(), getDashboardSummary(range),
    ]);
    return { services, alerts, anomalies, summary };
  }, [range], prefs.refreshSec);

  return (
    <>
      <PageHeader
        title="Overview"
        subtitle={state.data ? `Last updated ${fmtTime(state.data.summary.updatedAt)}` : 'Loading…'}
      >
        <RangeTabs value={range} onChange={setRange} />
        <RefreshButton onClick={state.reload} />
      </PageHeader>
      <Async state={state}>
        {({ services, alerts, anomalies, summary }) => {
          const total = services.length;
          const healthy = services.filter((s) => s.status === 'Healthy').length;
          const warning = services.filter((s) => s.status === 'Warning').length;
          const critical = services.filter((s) => s.status === 'Critical').length;
          const active = alerts.filter((a) => a.status === 'Active').length;
          const score = total ? Math.round((healthy / total) * 100) : 0;

          // Recent activity feed (alerts + anomalies merged and sorted)
          const activity = [
            ...alerts.map((a) => ({ id: a.id, kind: 'Alert', text: a.title, sev: a.severity, t: a.timestamp, faultType: a.faultType })),
            ...anomalies.map((a) => ({ id: a.id, kind: 'Anomaly', text: `${a.metric} deviation on ${a.service}`, sev: a.severity, t: a.detectedAt, faultType: a.faultType })),
          ].sort((a, b) => b.t - a.t).slice(0, 8);

          return (
            <div className="space-y-5">
              {/* Summary stats */}
              <div className="grid grid-cols-2 gap-3 lg:grid-cols-5">
                <Stat label="Monitored services" value={total} />
                <Stat label="Healthy" value={healthy} tone="text-emerald-300" />
                <Stat label="Warning" value={warning} tone="text-amber-300" />
                <Stat label="Critical" value={critical} tone="text-red-300" />
                <Stat label="System health" value={`${score}%`} hint={`${active} active alert${active !== 1 ? 's' : ''}`} tone={score < 50 ? 'text-red-300' : score < 80 ? 'text-amber-300' : 'text-emerald-300'} />
              </div>

              {/* Aggregate metrics */}
              <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
                <Stat label="Avg CPU" value={pct(avg(services, 'cpu'))} hint="Across all services" />
                <Stat label="Avg memory" value={pct(avg(services, 'memory'))} hint="Across all services" />
                <Stat label="Avg latency" value={ms(avg(services, 'latency'))} hint="Across all services" />
                <Stat label="Avg error rate" value={pct(avg(services, 'errorRate'))} hint="Across all services" />
              </div>

              {/* Service health mini-grid */}
              <Card title="Service health — Online Boutique (11 services)">
                <MiniServiceGrid services={services} />
                <Link to="/services" className="mt-3 inline-block text-sm text-cyan-300 hover:underline">
                  View service details →
                </Link>
              </Card>

              {/* Trend charts */}
              <div className="grid gap-4 xl:grid-cols-3">
                <MetricChart
                  title="CPU utilization (avg)"
                  unit="%"
                  data={summary.series}
                  domain={[0, 100]}
                  series={[{ key: 'cpu', name: 'CPU', color: '#22d3ee' }]}
                />
                <MetricChart
                  title="Memory utilization (avg)"
                  unit="%"
                  data={summary.series}
                  domain={[0, 100]}
                  series={[{ key: 'memory', name: 'Memory', color: '#60a5fa' }]}
                />
                <MetricChart
                  title="Latency (avg)"
                  unit="ms"
                  data={summary.series}
                  series={[{ key: 'latency', name: 'Latency', color: '#f59e0b' }]}
                />
              </div>

              {/* Service table + activity feed */}
              <div className="grid gap-4 xl:grid-cols-3">
                <Card title="Service health (sortable)" className="xl:col-span-2">
                  <ServiceTable services={services} />
                </Card>
                <Card title="Recent anomaly & alert activity">
                  {!activity.length ? (
                    <Empty text="No recent activity." />
                  ) : (
                    <ul className="space-y-3">
                      {activity.map((a) => (
                        <li key={a.id} className="text-sm">
                          <div className="flex items-center justify-between gap-2">
                            <Badge value={a.sev} />
                            {a.faultType && (
                              <span className="rounded bg-slate-800 px-1.5 py-0.5 text-[10px] text-slate-400 font-mono">
                                {a.faultType}
                              </span>
                            )}
                            <span className="text-xs text-slate-500 ml-auto">{fmtTime(a.t)}</span>
                          </div>
                          <p className="mt-1 text-slate-300">{a.text}</p>
                          <p className="text-xs text-slate-500">{a.kind} {a.id}</p>
                        </li>
                      ))}
                    </ul>
                  )}
                  <Link to="/alerts" className="mt-3 inline-block text-sm text-cyan-300 hover:underline">
                    View all alerts →
                  </Link>
                </Card>
              </div>
            </div>
          );
        }}
      </Async>
    </>
  );
}
