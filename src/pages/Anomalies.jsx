import { useMemo, useState } from 'react';
import { Info } from 'lucide-react';
import { Async, Badge, Card, DataTable, PageHeader, Select } from '../components/common/ui';
import useAsync from '../hooks/useAsync';
import { getAnomalies } from '../services/api';
import { fmtTime } from '../utils/format';

export default function Anomalies() {
  const state = useAsync(getAnomalies, []);
  const [f, setF] = useState({ severity: '', service: '', status: '' });
  const set = (k) => (v) => setF((p) => ({ ...p, [k]: v }));
  const uniq = (k) => [...new Set((state.data || []).map((a) => a[k]))];
  const rows = useMemo(() => (state.data || []).filter((a) => Object.entries(f).every(([k, v]) => !v || a[k] === v)), [state.data, f]);
  const columns = [
    { key: 'id', label: 'ID', sortable: true }, { key: 'service', label: 'Service', sortable: true }, { key: 'metric', label: 'Metric' },
    { key: 'observed', label: 'Observed', sortable: true, render: (a) => `${a.observed} ${a.unit}` },
    { key: 'baseline', label: 'Baseline', render: (a) => (a.baseline == null ? 'n/a' : `${a.baseline} ${a.unit}`) },
    { key: 'severity', label: 'Severity', sortable: true, render: (a) => <Badge value={a.severity} /> },
    { key: 'detectedAt', label: 'Detected', sortable: true, render: (a) => fmtTime(a.detectedAt) },
    { key: 'score', label: 'Score (0–1)', sortable: true, render: (a) => (a.score == null ? 'n/a' : a.score.toFixed(2)) },
    { key: 'status', label: 'Status', render: (a) => <Badge value={a.status} /> },
  ];
  return (
    <>
      <PageHeader title="Anomalies" subtitle="Abnormal metric behavior detected per service">
        <Select label="Severity" value={f.severity} onChange={set('severity')} options={['Critical', 'Warning', 'Info']} />
        <Select label="Service" value={f.service} onChange={set('service')} options={uniq('service')} />
        <Select label="Status" value={f.status} onChange={set('status')} options={uniq('status')} />
      </PageHeader>
      <div className="mb-4 flex gap-2 rounded-lg border border-sky-500/20 bg-sky-500/10 p-3 text-sm text-sky-200"><Info size={16} className="mt-0.5 shrink-0" />
        <p>An anomaly means a metric deviated from its expected behavior. It is not a confirmed root cause. Scores here are illustrative demo values, not model output.</p></div>
      <Async state={state}>{() => <Card><DataTable columns={columns} rows={rows} rowKey="id" /></Card>}</Async>
    </>
  );
}
