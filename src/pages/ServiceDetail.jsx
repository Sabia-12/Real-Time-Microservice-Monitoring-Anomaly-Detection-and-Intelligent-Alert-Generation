import { useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { Async, Badge, Card, Empty, PageHeader, RangeTabs, Stat } from '../components/common/ui';
import MetricChart from '../components/charts/MetricChart';
import useAsync from '../hooks/useAsync';
import { getPrefs, getServiceDetails } from '../services/api';
import { fmtTime, ms, pct } from '../utils/format';

export default function ServiceDetail() {
  const { id } = useParams();
  const [range, setRange] = useState(getPrefs().defaultRange);
  const state = useAsync(() => getServiceDetails(id, range), [id, range]);
  return (
    <>
      <Link to="/services" className="mb-3 inline-flex items-center gap-1 text-sm text-slate-400 hover:text-slate-200"><ArrowLeft size={14} />Services</Link>
      <PageHeader title={id}><RangeTabs value={range} onChange={setRange} /></PageHeader>
      <Async state={state}>{({ service: s, series, alerts }) => (
        <div className="space-y-5">
          <div className="grid grid-cols-2 gap-3 lg:grid-cols-5">
            <Stat label="Health" value={<Badge value={s.status} />} />
            <Stat label="CPU" value={pct(s.cpu)} /><Stat label="Memory" value={pct(s.memory)} />
            <Stat label="Latency" value={ms(s.latency)} /><Stat label="Error rate" value={pct(s.errorRate)} />
          </div>
          <div className="grid gap-4 lg:grid-cols-2">
            <MetricChart title="CPU & memory" unit="%" data={series} domain={[0, 100]} series={[{ key: 'cpu', name: 'CPU', color: '#22d3ee' }, { key: 'memory', name: 'Memory', color: '#60a5fa' }]} />
            <MetricChart title="Latency" unit="ms" data={series} series={[{ key: 'latency', name: 'Latency', color: '#f59e0b' }]} />
          </div>
          <Card title="Recent alerts">{!alerts.length ? <Empty text="No alerts for this service." /> : (
            <ul className="divide-y divide-slate-800">{alerts.map((a) => (
              <li key={a.id} className="flex flex-wrap items-center justify-between gap-2 py-2 text-sm"><span>{a.title}</span>
                <span className="flex items-center gap-2"><Badge value={a.severity} /><Badge value={a.status} /><span className="text-xs text-slate-500">{fmtTime(a.timestamp)}</span></span></li>))}</ul>)}</Card>
        </div>)}</Async>
    </>
  );
}
