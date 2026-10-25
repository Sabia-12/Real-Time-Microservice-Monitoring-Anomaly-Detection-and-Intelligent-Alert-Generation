import { useMemo, useState } from 'react';
import { Async, Badge, Card, DataTable, PageHeader, SearchBox, Select } from '../components/common/ui';
import useAsync from '../hooks/useAsync';
import { getIncidents } from '../services/api';
import { dur, fmtTime } from '../utils/format';

export default function Incidents() {
  const state = useAsync(getIncidents, []);
  const [q, setQ] = useState(''), [sev, setSev] = useState(''), [st, setSt] = useState('');
  const rows = useMemo(() => (state.data || []).filter((i) => `${i.id} ${i.services.join(' ')}`.toLowerCase().includes(q.toLowerCase()) && (!sev || i.severity === sev) && (!st || i.status === st)), [state.data, q, sev, st]);
  const columns = [
    { key: 'id', label: 'Incident', sortable: true, render: (i) => <span className="font-medium text-slate-100">{i.id}</span> },
    { key: 'start', label: 'Start', sortable: true, render: (i) => fmtTime(i.start) },
    { key: 'end', label: 'End', render: (i) => (i.end ? fmtTime(i.end) : 'Ongoing') },
    { key: 'durationMin', label: 'Duration', sortable: true, render: (i) => dur(i.durationMin) },
    { key: 'services', label: 'Affected services', render: (i) => i.services.join(', ') },
    { key: 'severity', label: 'Severity', render: (i) => <Badge value={i.severity} /> },
    { key: 'alerts', label: 'Alerts', render: (i) => (i.alerts.length ? i.alerts.join(', ') : 'None') },
    { key: 'category', label: 'Observed behavior' },
    { key: 'status', label: 'Status', render: (i) => <Badge value={i.status} /> },
  ];
  return (
    <>
      <PageHeader title="Incident history" subtitle="Root causes are not determined by this interface.">
        <SearchBox value={q} onChange={setQ} placeholder="Search ID or service" />
        <Select label="Severity" value={sev} onChange={setSev} options={['Critical', 'Warning', 'Info']} />
        <Select label="Status" value={st} onChange={setSt} options={['Ongoing', 'Resolved', 'Closed']} />
      </PageHeader>
      <Async state={state}>{() => <Card><DataTable columns={columns} rows={rows} rowKey="id" /></Card>}</Async>
    </>
  );
}
