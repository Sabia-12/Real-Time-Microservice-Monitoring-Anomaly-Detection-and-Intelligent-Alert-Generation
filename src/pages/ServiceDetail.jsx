/**
 * ServiceDetail — Per-service metric charts + alerts + fault evidence.
 * Shows anomaly marker lines on charts when fault data is available.
 */
import { useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ArrowLeft, AlertTriangle, Info } from 'lucide-react';
import { Async, Badge, Card, Empty, PageHeader, RangeTabs, Stat } from '../components/common/ui';
import MetricChart from '../components/charts/MetricChart';
import useAsync from '../hooks/useAsync';
import { getPrefs, getServiceDetails } from '../services/api';
import { FAULT_TYPE_LABELS } from '../data/mock';
import { fmtTime, ms, pct } from '../utils/format';

export default function ServiceDetail() {
  const { id } = useParams();
  const [range, setRange] = useState(getPrefs().defaultRange);
  const state = useAsync(() => getServiceDetails(id, range), [id, range]);

  return (
    <>
      <Link to="/services" className="mb-3 inline-flex items-center gap-1 text-sm text-slate-400 hover:text-slate-200 transition-colors">
        <ArrowLeft size={14} />Services
      </Link>
      <PageHeader title={id}>
        <RangeTabs value={range} onChange={setRange} />
      </PageHeader>
      <Async state={state}>
        {({ service: s, series, alerts, anomalyMarkers = [] }) => {
          // Build markers per chart from anomalyMarkers
          const markersFor = (metricKey) =>
            anomalyMarkers
              .filter((m) => m.metric === metricKey || m.metric === null)
              .map((m) => ({ t: m.t, label: `⚠ ${FAULT_TYPE_LABELS[m.faultType] || ''}` }));

          return (
            <div className="space-y-5">
              {/* Fault type banner */}
              {s.faultType && (
                <div className="flex items-center gap-3 rounded-lg border border-red-500/20 bg-red-500/8 px-4 py-3 text-sm text-red-300">
                  <AlertTriangle size={16} className="shrink-0" />
                  <span>
                    <strong>Active fault detected:</strong>{' '}
                    {FAULT_TYPE_LABELS[s.faultType] || s.faultType} (RE2-OB fault type:{' '}
                    <code className="rounded bg-red-500/10 px-1 font-mono text-xs">{s.faultType}</code>)
                  </span>
                </div>
              )}

              {/* Stat row */}
              <div className="grid grid-cols-2 gap-3 lg:grid-cols-5">
                <Stat label="Health" value={<Badge value={s.status} />} />
                <Stat label="CPU" value={pct(s.cpu)} tone={s.cpu >= 85 ? 'text-red-300' : s.cpu >= 65 ? 'text-amber-300' : undefined} />
                <Stat label="Memory" value={pct(s.memory)} tone={s.memory >= 88 ? 'text-red-300' : s.memory >= 78 ? 'text-amber-300' : undefined} />
                <Stat label="Latency" value={ms(s.latency)} tone={s.latency >= 800 ? 'text-red-300' : s.latency >= 400 ? 'text-amber-300' : undefined} />
                <Stat label="Error rate" value={pct(s.errorRate)} tone={s.errorRate >= 3 ? 'text-red-300' : s.errorRate >= 1.5 ? 'text-amber-300' : undefined} />
              </div>

              {/* Charts with anomaly markers */}
              <div className="grid gap-4 lg:grid-cols-2">
                <MetricChart
                  title="CPU & memory"
                  unit="%"
                  data={series}
                  domain={[0, 100]}
                  series={[
                    { key: 'cpu', name: 'CPU', color: '#22d3ee' },
                    { key: 'memory', name: 'Memory', color: '#60a5fa' },
                  ]}
                  markers={[...markersFor('cpu'), ...markersFor('memory')]}
                />
                <MetricChart
                  title="Latency (P50)"
                  unit="ms"
                  data={series}
                  series={[{ key: 'latency', name: 'Latency', color: '#f59e0b' }]}
                  markers={markersFor('latency')}
                />
                <MetricChart
                  title="Error rate"
                  unit="%"
                  data={series}
                  series={[{ key: 'errorRate', name: 'Error rate', color: '#f87171' }]}
                  markers={markersFor('errorRate')}
                />
                <MetricChart
                  title="Network throughput"
                  unit="B/s"
                  data={series}
                  series={[
                    { key: 'rxBytes', name: 'Rx', color: '#a78bfa' },
                    { key: 'txBytes', name: 'Tx', color: '#34d399' },
                  ]}
                  markers={[...markersFor('rxBytes'), ...markersFor('txBytes')]}
                />
              </div>

              {/* Anomaly markers legend */}
              {anomalyMarkers.length > 0 && (
                <div className="flex items-start gap-2 rounded-lg border border-red-500/20 bg-red-500/8 p-3 text-sm text-red-300">
                  <Info size={15} className="mt-0.5 shrink-0" />
                  <p>
                    Red dashed lines mark detected anomaly timestamps (demo data — not model output).
                    Fault type(s):{' '}
                    {[...new Set(anomalyMarkers.map((m) => FAULT_TYPE_LABELS[m.faultType]).filter(Boolean))].join(', ')}.
                  </p>
                </div>
              )}

              {/* Recent alerts */}
              <Card title="Recent alerts for this service">
                {!alerts.length ? (
                  <Empty text="No alerts for this service." />
                ) : (
                  <ul className="divide-y divide-slate-800">
                    {alerts.map((a) => (
                      <li key={a.id} className="py-3 text-sm">
                        <div className="flex flex-wrap items-center justify-between gap-2">
                          <span className="font-medium text-slate-100">{a.title}</span>
                          <span className="flex items-center gap-2">
                            <Badge value={a.severity} />
                            <Badge value={a.status} />
                            <span className="text-xs text-slate-500">{fmtTime(a.timestamp)}</span>
                          </span>
                        </div>
                        {a.evidence && (
                          <p className="mt-1 text-xs text-slate-400">{a.evidence}</p>
                        )}
                      </li>
                    ))}
                  </ul>
                )}
              </Card>
            </div>
          );
        }}
      </Async>
    </>
  );
}
