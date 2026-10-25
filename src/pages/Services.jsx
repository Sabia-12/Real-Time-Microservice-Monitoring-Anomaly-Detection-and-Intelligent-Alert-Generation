import { useMemo, useState } from 'react';
import { Async, Card, PageHeader, SearchBox, Select } from '../components/common/ui';
import ServiceTable from '../components/services/ServiceTable';
import useAsync from '../hooks/useAsync';
import { getServices } from '../services/api';

export default function Services() {
  const state = useAsync(getServices, []);
  const [q, setQ] = useState(''), [status, setStatus] = useState('');
  const rows = useMemo(() => (state.data || []).filter((s) => s.name.toLowerCase().includes(q.toLowerCase()) && (!status || s.status === status)), [state.data, q, status]);
  return (
    <>
      <PageHeader title="Services" subtitle="Monitored microservices and their current metrics">
        <SearchBox value={q} onChange={setQ} placeholder="Search services" />
        <Select label="Health" value={status} onChange={setStatus} options={['Healthy', 'Warning', 'Critical']} />
      </PageHeader>
      <Async state={state}>{() => <Card><ServiceTable services={rows} /></Card>}</Async>
    </>
  );
}
