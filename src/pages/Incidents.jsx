/**
 * Incidents — Incident history for Online Boutique.
 * Shows fault types, affected services, severity and duration.
 */
import { useMemo, useState } from 'react';
import { Async, Badge, Card, DataTable, PageHeader, SearchBox, Select } from '../components/common/ui';
import useAsync from '../hooks/useAsync';
import { getIncidents } from '../services/api';
import { FAULT_TYPE_LABELS } from '../data/mock';
import { dur, fmtTime } from '../utils/format';

export default function Incidents() {
  const state = useAsync(getIncidents, []);
  const [q, setQ] = useState('');
  const [sev, setSev] = useState('');
  const [st, setSt] = useState('');

  const rows = useMemo(() =>
    (state.data || []).filter((i) =>
      `${i.id} ${i.services.join(' ')}`.toLowerCase().includes(q.toLowerCase())
      && (!sev || i.severity === sev)
      && (!st || i.status === st)
    ), [state.data, q, sev, st]);

  const columns = [
    { key: 'id', label: 'Incident', sortable: true, render: (i) => <span className="font-mono font-medium text-slate-100">{i.id}</span> },
    { key: 'start', label: 'Start', sortable: true, render: (i) => fmtTime(i.start) },
    { key: 'end', label: 'End', render: (i) => (i.end ? fmtTime(i.end) : <span className="text-amber-300">Ongoing</span>) },
    { key: 'durationMin', label: 'Duration', sortable: true, render: (i) => dur(i.durationMin) },
    { key: 'services', label: 'Affected services', render: (i) => (
      <span className="flex flex-wrap gap-1">
        {i.services.map((s) => (
          <span key={s} className="rounded bg-slate-800 px-1.5 py-0.5 text-xs font-mono text-slate-300">{s}</span>
        ))}
      </span>
    )},
    { key: 'faultTypes', label: 'Fault types', render: (i) => (
      i.faultTypes?.length
        ? <span className="flex flex-wrap gap-1">
            {i.faultTypes.map((t) => (
              <span key={t} className="rounded bg-red-500/10 px-1.5 py-0.5 text-xs text-red-300 ring-1 ring-red-500/20">{FAULT_TYPE_LABELS[t] || t}</span>
            ))}
          </span>
        : <span className="text-slate-600">—</span>
    )},
    { key: 'severity', label: 'Severity', render: (i) => <Badge value={i.severity} /> },
    { key: 'alerts', label: 'Alerts', render: (i) => (i.alerts.length ? i.alerts.join(', ') : '—') },
    { key: 'status', label: 'Status', render: (i) => <Badge value={i.status} /> },
  ];

  return (
    <>
      <PageHeader title="Incident History" subtitle="Root causes are not determined by this interface — observational data only">
        <SearchBox value={q} onChange={setQ} placeholder="Search ID or service" />
        <Select label="Severity" value={sev} onChange={setSev} options={['Critical', 'Warning', 'Info']} />
        <Select label="Status" value={st} onChange={setSt} options={['Ongoing', 'Resolved', 'Closed']} />
      </PageHeader>
      <Async state={state}>
        {() => (
          <Card>
            <DataTable columns={columns} rows={rows} rowKey="id" />
          </Card>
        )}
      </Async>
    </>
  );
}
