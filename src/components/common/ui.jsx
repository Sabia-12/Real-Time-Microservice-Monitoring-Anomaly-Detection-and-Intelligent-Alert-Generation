import { useMemo, useState } from 'react';
import { AlertCircle, ArrowUpDown, Inbox, Loader2, RefreshCw, Search } from 'lucide-react';

const tones = {
  healthy: 'bg-emerald-500/10 text-emerald-300 ring-emerald-500/30', warning: 'bg-amber-500/10 text-amber-300 ring-amber-500/30',
  critical: 'bg-red-500/10 text-red-300 ring-red-500/30', info: 'bg-sky-500/10 text-sky-300 ring-sky-500/30', muted: 'bg-slate-500/10 text-slate-400 ring-slate-500/30',
};
const map = { healthy: 'healthy', resolved: 'healthy', closed: 'healthy', warning: 'warning', active: 'warning', open: 'warning', ongoing: 'warning',
  critical: 'critical', info: 'info', acknowledged: 'info', 'under review': 'info', dismissed: 'muted' };
export const Badge = ({ value }) => (
  <span className={`inline-flex items-center gap-1.5 whitespace-nowrap rounded-full px-2 py-0.5 text-xs font-medium ring-1 ${tones[map[value.toLowerCase()] || 'muted']}`}>
    <span aria-hidden className="h-1.5 w-1.5 rounded-full bg-current" />{value}
  </span>
);
export const Card = ({ title, children, className = '' }) => (
  <section className={`rounded-xl border border-slate-800 bg-[#111a2e] p-4 ${className}`}>
    {title && <h2 className="mb-3 text-sm font-medium text-slate-300">{title}</h2>}{children}
  </section>
);
export const PageHeader = ({ title, subtitle, children }) => (
  <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
    <div><h1 className="text-xl font-semibold text-slate-100">{title}</h1>{subtitle && <p className="text-sm text-slate-400">{subtitle}</p>}</div>
    <div className="flex flex-wrap items-center gap-2">{children}</div>
  </div>
);
export const Stat = ({ label, value, hint, tone }) => (
  <div className="rounded-xl border border-slate-800 bg-[#111a2e] p-4">
    <p className="text-xs text-slate-400">{label}</p>
    <p className={`mt-1 text-2xl font-semibold ${tone || 'text-slate-100'}`}>{value}</p>
    {hint && <p className="mt-0.5 text-xs text-slate-500">{hint}</p>}
  </div>
);
export const Loading = () => <div role="status" className="flex items-center gap-2 p-8 text-slate-400"><Loader2 className="animate-spin" size={18} />Loading…</div>;
export const ErrorMsg = ({ error, onRetry }) => (
  <div role="alert" className="flex items-center gap-3 rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-200">
    <AlertCircle size={18} /><span className="flex-1">{error?.message || 'Something went wrong.'}</span>
    {onRetry && <button onClick={onRetry} className="rounded-md border border-red-400/40 px-2 py-1 hover:bg-red-500/20">Retry</button>}
  </div>
);
export const Empty = ({ text = 'Nothing to show.' }) => <div className="flex flex-col items-center gap-2 p-8 text-sm text-slate-500"><Inbox size={22} />{text}</div>;
// Renders loading / error / data for a useAsync result.
export const Async = ({ state, children }) => state.loading && !state.data ? <Loading /> : state.error ? <ErrorMsg error={state.error} onRetry={state.reload} /> : state.data ? children(state.data) : null;

export const SearchBox = ({ value, onChange, placeholder }) => (
  <label className="relative block"><span className="sr-only">{placeholder}</span>
    <Search size={15} className="absolute left-2.5 top-2.5 text-slate-500" />
    <input value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder}
      className="w-56 rounded-lg border border-slate-700 bg-[#0b1220] py-2 pl-8 pr-3 text-sm placeholder:text-slate-500" /></label>
);
export const Select = ({ label, value, onChange, options }) => (
  <label className="text-sm"><span className="sr-only">{label}</span>
    <select value={value} onChange={(e) => onChange(e.target.value)} className="rounded-lg border border-slate-700 bg-[#0b1220] px-3 py-2 text-sm">
      <option value="">{label}: All</option>{options.map((o) => <option key={o}>{o}</option>)}
    </select></label>
);
export const RangeTabs = ({ value, onChange }) => (
  <div role="group" aria-label="Time range" className="flex rounded-lg border border-slate-700 p-0.5 text-sm">
    {['15m', '1h', '24h'].map((r) => (
      <button key={r} aria-pressed={value === r} onClick={() => onChange(r)} className={`rounded-md px-3 py-1.5 ${value === r ? 'bg-cyan-500/20 text-cyan-300' : 'text-slate-400 hover:text-slate-200'}`}>{r}</button>))}
  </div>
);
export const RefreshButton = ({ onClick }) => (
  <button onClick={onClick} className="flex items-center gap-2 rounded-lg border border-slate-700 px-3 py-2 text-sm text-slate-300 hover:bg-slate-800"><RefreshCw size={15} />Refresh</button>
);
export function DataTable({ columns, rows, rowKey, onRowClick, empty }) {
  const [sort, setSort] = useState(null);
  const sorted = useMemo(() => {
    const c = columns.find((x) => x.key === sort?.key);
    if (!c) return rows;
    const g = c.sortValue || ((r) => r[c.key]);
    return [...rows].sort((a, b) => (g(a) > g(b) ? 1 : g(a) < g(b) ? -1 : 0) * (sort.dir === 'asc' ? 1 : -1));
  }, [rows, sort, columns]);
  if (!rows.length) return <Empty text={empty || 'No results match your filters.'} />;
  return (
    <div className="overflow-x-auto"><table className="w-full text-left text-sm">
      <thead><tr className="border-b border-slate-800 text-xs text-slate-400">
        {columns.map((c) => (
          <th key={c.key} scope="col" className="px-3 py-2 font-medium" aria-sort={sort?.key === c.key ? (sort.dir === 'asc' ? 'ascending' : 'descending') : undefined}>
            {c.sortable ? <button className="inline-flex items-center gap-1 hover:text-slate-200" onClick={() => setSort((s) => ({ key: c.key, dir: s?.key === c.key && s.dir === 'asc' ? 'desc' : 'asc' }))}>{c.label}<ArrowUpDown size={12} /></button> : c.label}
          </th>))}
      </tr></thead>
      <tbody>{sorted.map((r) => (
        <tr key={r[rowKey]} tabIndex={onRowClick ? 0 : undefined} onClick={() => onRowClick?.(r)} onKeyDown={(e) => e.key === 'Enter' && onRowClick?.(r)}
          className={`border-b border-slate-800/60 ${onRowClick ? 'cursor-pointer hover:bg-slate-800/40' : ''}`}>
          {columns.map((c) => <td key={c.key} className="px-3 py-2.5">{c.render ? c.render(r) : r[c.key]}</td>)}
        </tr>))}</tbody>
    </table></div>
  );
}
