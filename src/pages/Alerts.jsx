import { useMemo, useState } from 'react';
import { Async, Badge, Card, DataTable, PageHeader, SearchBox, Select } from '../components/common/ui';
import AlertModal from '../components/alerts/AlertModal';
import useAsync from '../hooks/useAsync';
import { acknowledgeAlert, getAlerts, resolveAlert } from '../services/api';
import { fmtTime } from '../utils/format';

export default function Alerts() {
  const state = useAsync(getAlerts, []);
  const [q, setQ] = useState(''), [sev, setSev] = useState(''), [st, setSt] = useState('');
  const [selId, setSelId] = useState(null), [busy, setBusy] = useState(false), [err, setErr] = useState(null);
  const rows = useMemo(() => (state.data || []).filter((a) => `${a.title} ${a.service}`.toLowerCase().includes(q.toLowerCase()) && (!sev || a.severity === sev) && (!st || a.status === st)), [state.data, q, sev, st]);
  const selected = state.data?.find((a) => a.id === selId);
  const act = async (fn) => { setBusy(true); setErr(null); try { await fn(selId); await state.reload(); } catch (e) { setErr(e); } finally { setBusy(false); } };
  const columns = [
    { key: 'title', label: 'Alert', render: (a) => <span className="font-medium text-slate-100">{a.title}</span> },
    { key: 'severity', label: 'Severity', sortable: true, render: (a) => <Badge value={a.severity} /> },
    { key: 'service', label: 'Service', sortable: true }, { key: 'metric', label: 'Metric' },
    { key: 'timestamp', label: 'Time', sortable: true, render: (a) => fmtTime(a.timestamp) },
    { key: 'status', label: 'Status', sortable: true, render: (a) => <Badge value={a.status} /> },
  ];
  return (
    <>
      <PageHeader title="Alerts" subtitle="Select an alert for details, then acknowledge or resolve it">
        <SearchBox value={q} onChange={setQ} placeholder="Search alerts" />
        <Select label="Severity" value={sev} onChange={setSev} options={['Critical', 'Warning', 'Info']} />
        <Select label="Status" value={st} onChange={setSt} options={['Active', 'Acknowledged', 'Resolved']} />
      </PageHeader>
      {err && <p role="alert" className="mb-3 text-sm text-red-300">{err.message}</p>}
      <Async state={state}>{() => <Card><DataTable columns={columns} rows={rows} rowKey="id" onRowClick={(a) => setSelId(a.id)} /></Card>}</Async>
      {selected && <AlertModal alert={selected} busy={busy} onClose={() => setSelId(null)} onAck={() => act(acknowledgeAlert)} onResolve={() => act(resolveAlert)} />}
    </>
  );
}
