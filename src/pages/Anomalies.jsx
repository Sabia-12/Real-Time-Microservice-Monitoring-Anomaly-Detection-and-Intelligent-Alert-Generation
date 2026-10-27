/**
 * Anomalies — Detected metric deviations for Online Boutique.
 * Includes RE2-OB fault type labels for demo cases.
 */
import { useMemo, useState } from 'react';
import { Info } from 'lucide-react';
import { Async, Badge, Card, DataTable, PageHeader, Select } from '../components/common/ui';
import useAsync from '../hooks/useAsync';
import { getAnomalies } from '../services/api';
import { FAULT_TYPE_LABELS } from '../data/mock';
import { fmtTime } from '../utils/format';

export default function Anomalies() {
  const state = useAsync(getAnomalies, []);
  const [f, setF] = useState({ severity: '', service: '', status: '' });
  const set = (k) => (v) => setF((p) => ({ ...p, [k]: v }));
  const uniq = (k) => [...new Set((state.data || []).map((a) => a[k]))];
  const rows = useMemo(() => (state.data || []).filter((a) => Object.entries(f).every(([k, v]) => !v || a[k] === v)), [state.data, f]);

  const columns = [
    { key: 'id', label: 'ID', sortable: true, render: (a) => <span className="font-mono text-xs">{a.id}</span> },
    { key: 'service', label: 'Service', sortable: true },
    { key: 'metric', label: 'Metric' },
    { key: 'observed', label: 'Observed', sortable: true, render: (a) => `${a.observed} ${a.unit}` },
    { key: 'baseline', label: 'Baseline', render: (a) => (a.baseline == null ? '—' : `${a.baseline} ${a.unit}`) },
    {
      key: 'faultType', label: 'Fault type',
      render: (a) => a.faultType
        ? <span className="rounded bg-red-500/10 px-1.5 py-0.5 text-xs text-red-300 ring-1 ring-red-500/20">{FAULT_TYPE_LABELS[a.faultType] || a.faultType}</span>
        : <span className="text-slate-600">—</span>,
    },
    { key: 'severity', label: 'Severity', sortable: true, render: (a) => <Badge value={a.severity} /> },
    { key: 'detectedAt', label: 'Detected', sortable: true, render: (a) => fmtTime(a.detectedAt) },
    {
      key: 'score', label: 'Score', sortable: true,
      render: (a) => {
        if (a.score == null) return '—';
        const raw = Number(a.score);
        const pct = Math.min(100, Math.max(0, raw <= 1.0 ? raw * 100 : (raw / 15.0) * 100));
        return (
          <span className="flex items-center gap-2">
            <span className="w-16 h-1.5 rounded-full bg-slate-800 inline-block overflow-hidden ring-1 ring-slate-700/50">
              <span className="block h-full rounded-full bg-gradient-to-r from-sky-500 to-red-500" style={{ width: `${pct}%` }} />
            </span>
            <span className="text-xs font-mono">{raw > 1.0 ? `${raw.toFixed(2)}σ` : raw.toFixed(2)}</span>
          </span>
        );
      },
    },
    { key: 'status', label: 'Status', render: (a) => <Badge value={a.status} /> },
  ];

  return (
    <>
      <PageHeader title="Anomalies" subtitle="Metric deviations detected per service — observational, not root-cause determinations">
        <Select label="Severity" value={f.severity} onChange={set('severity')} options={['Critical', 'Warning', 'Info']} />
        <Select label="Service" value={f.service} onChange={set('service')} options={uniq('service')} />
        <Select label="Status" value={f.status} onChange={set('status')} options={uniq('status')} />
      </PageHeader>
      <div className="mb-4 flex gap-2 rounded-lg border border-sky-500/20 bg-sky-500/8 p-3 text-sm text-sky-200">
        <Info size={16} className="mt-0.5 shrink-0" />
        <p>
          An anomaly means a metric deviated from expected behavior. Scores shown are illustrative demo values
          from synthetic data — not real model output. Fault types are ground-truth labels from the RE2-OB dataset.
        </p>
      </div>
      <Async state={state}>
        {() => <Card><DataTable columns={columns} rows={rows} rowKey="id" /></Card>}
      </Async>
    </>
  );
}
