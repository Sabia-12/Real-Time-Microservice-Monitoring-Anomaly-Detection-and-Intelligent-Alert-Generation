/**
 * Services — Service health grid + detail table for Online Boutique.
 * Shows all 11 OB services as status cards, then a sortable table below.
 */
import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Activity, AlertTriangle, CheckCircle2, Clock,
  Cpu, Database, Server, XCircle, Zap,
} from 'lucide-react';
import { Async, Badge, Card, PageHeader, SearchBox, Select } from '../components/common/ui';
import ServiceTable from '../components/services/ServiceTable';
import useAsync from '../hooks/useAsync';
import { getServices } from '../services/api';
import { FAULT_TYPE_LABELS } from '../data/mock';
import { ms, pct } from '../utils/format';

const STATUS_META = {
  Healthy: { icon: CheckCircle2, ring: 'ring-emerald-500/30', bg: 'bg-emerald-500/8', text: 'text-emerald-300', dot: 'bg-emerald-400' },
  Warning: { icon: AlertTriangle, ring: 'ring-amber-500/30', bg: 'bg-amber-500/8', text: 'text-amber-300', dot: 'bg-amber-400' },
  Critical: { icon: XCircle, ring: 'ring-red-500/30', bg: 'bg-red-500/8', text: 'text-red-300', dot: 'bg-red-400 animate-pulse' },
};

function ServiceCard({ s }) {
  const m = STATUS_META[s.status] || STATUS_META.Healthy;
  const Icon = m.icon;
  return (
    <Link
      to={`/services/${s.id}`}
      className={`group relative flex flex-col gap-3 rounded-xl border p-4 transition-all duration-200 hover:scale-[1.02] hover:shadow-lg hover:shadow-black/30 ${m.ring} ${m.bg} border-slate-800 bg-[#111a2e]`}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          <p className={`truncate text-sm font-semibold ${m.text}`}>{s.name}</p>
          {s.faultType && (
            <span className="mt-0.5 inline-block rounded-full bg-red-500/15 px-2 py-0.5 text-[10px] text-red-300 ring-1 ring-red-500/30">
              {FAULT_TYPE_LABELS[s.faultType] || s.faultType}
            </span>
          )}
        </div>
        <span className={`flex items-center gap-1 rounded-full px-2 py-1 text-xs font-medium ring-1 ${m.ring} ${m.text}`}>
          <span className={`h-1.5 w-1.5 rounded-full ${m.dot}`} />
          {s.status}
        </span>
      </div>

      {/* Metric pills */}
      <dl className="grid grid-cols-2 gap-2">
        <Metric icon={Cpu} label="CPU" value={pct(s.cpu)} warn={s.cpu >= 65} crit={s.cpu >= 85} />
        <Metric icon={Database} label="Mem" value={pct(s.memory)} warn={s.memory >= 78} crit={s.memory >= 88} />
        <Metric icon={Clock} label="P50" value={ms(s.latency)} warn={s.latency >= 400} crit={s.latency >= 800} />
        <Metric icon={Activity} label="Err" value={pct(s.errorRate)} warn={s.errorRate >= 1.5} crit={s.errorRate >= 3} />
      </dl>

      {/* Hover arrow */}
      <span className="absolute right-3 top-3 opacity-0 transition-opacity group-hover:opacity-100 text-slate-500 text-xs">→</span>
    </Link>
  );
}

function Metric({ icon: Icon, label, value, warn, crit }) {
  const color = crit ? 'text-red-300' : warn ? 'text-amber-300' : 'text-slate-300';
  return (
    <div className="flex items-center gap-1.5">
      <Icon size={11} className="shrink-0 text-slate-500" />
      <span className="text-[10px] text-slate-500">{label}</span>
      <span className={`ml-auto text-xs font-mono font-medium ${color}`}>{value}</span>
    </div>
  );
}

function SummaryBar({ services }) {
  const healthy = services.filter((s) => s.status === 'Healthy').length;
  const warning = services.filter((s) => s.status === 'Warning').length;
  const critical = services.filter((s) => s.status === 'Critical').length;
  return (
    <div className="mb-5 flex flex-wrap gap-3">
      {[
        { label: 'Total', value: services.length, color: 'text-slate-300' },
        { label: 'Healthy', value: healthy, color: 'text-emerald-300' },
        { label: 'Warning', value: warning, color: 'text-amber-300' },
        { label: 'Critical', value: critical, color: 'text-red-300' },
      ].map(({ label, value, color }) => (
        <div key={label} className="flex items-center gap-2 rounded-lg border border-slate-800 bg-[#111a2e] px-4 py-2">
          <span className="text-xs text-slate-400">{label}</span>
          <span className={`text-lg font-semibold ${color}`}>{value}</span>
        </div>
      ))}
    </div>
  );
}

export default function Services() {
  const state = useAsync(getServices, []);
  const [q, setQ] = useState('');
  const [status, setStatus] = useState('');
  const [view, setView] = useState('grid'); // 'grid' | 'table'

  const filtered = useMemo(() =>
    (state.data || []).filter(
      (s) => `${s.name} ${s.description || ''}`.toLowerCase().includes(q.toLowerCase())
             && (!status || s.status === status)
    ), [state.data, q, status]);

  return (
    <>
      <PageHeader title="Services" subtitle="Online Boutique — monitored microservices">
        <SearchBox value={q} onChange={setQ} placeholder="Search services" />
        <Select label="Health" value={status} onChange={setStatus} options={['Healthy', 'Warning', 'Critical']} />
        {/* View toggle */}
        <div role="group" aria-label="View mode" className="flex rounded-lg border border-slate-700 p-0.5 text-sm">
          {[['grid', <Server size={14} />], ['table', <Zap size={14} />]].map(([v, icon]) => (
            <button
              key={v}
              aria-pressed={view === v}
              onClick={() => setView(v)}
              className={`flex items-center gap-1 rounded-md px-3 py-1.5 capitalize ${view === v ? 'bg-cyan-500/20 text-cyan-300' : 'text-slate-400 hover:text-slate-200'}`}
            >
              {icon}{v}
            </button>
          ))}
        </div>
      </PageHeader>

      <Async state={state}>
        {() => (
          <>
            <SummaryBar services={state.data || []} />
            {view === 'grid' ? (
              filtered.length === 0 ? (
                <p className="p-8 text-center text-slate-500">No services match your filters.</p>
              ) : (
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                  {filtered.map((s) => <ServiceCard key={s.id} s={s} />)}
                </div>
              )
            ) : (
              <Card>
                <ServiceTable services={filtered} />
              </Card>
            )}
          </>
        )}
      </Async>
    </>
  );
}
