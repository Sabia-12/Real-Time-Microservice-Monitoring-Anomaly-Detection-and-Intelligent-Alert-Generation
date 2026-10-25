import { Link, useNavigate } from 'react-router-dom';
import { Badge, DataTable } from '../common/ui';
import { fmtClock, ms, pct } from '../../utils/format';

export default function ServiceTable({ services }) {
  const nav = useNavigate();
  const order = { Critical: 2, Warning: 1, Healthy: 0 };
  const columns = [
    { key: 'name', label: 'Service', sortable: true, render: (s) => <Link className="font-medium text-cyan-300 hover:underline" to={`/services/${s.id}`} onClick={(e) => e.stopPropagation()}>{s.name}</Link> },
    { key: 'status', label: 'Health', sortable: true, sortValue: (s) => order[s.status], render: (s) => <Badge value={s.status} /> },
    { key: 'cpu', label: 'CPU (%)', sortable: true, render: (s) => pct(s.cpu) },
    { key: 'memory', label: 'Memory (%)', sortable: true, render: (s) => pct(s.memory) },
    { key: 'latency', label: 'Latency (ms)', sortable: true, render: (s) => ms(s.latency) },
    { key: 'errorRate', label: 'Error rate (%)', sortable: true, render: (s) => (s.errorRate == null ? 'n/a' : pct(s.errorRate)) },
    { key: 'updatedAt', label: 'Updated', sortable: true, render: (s) => fmtClock(s.updatedAt) },
  ];
  return <DataTable columns={columns} rows={services} rowKey="id" onRowClick={(s) => nav(`/services/${s.id}`)} empty="No services match your filters." />;
}
