import { useState } from 'react';
import { API_BASE, getConnectionStatus, getPrefs, savePrefs } from '../services/api';
import { Async, Badge, Card, PageHeader } from '../components/common/ui';
import useAsync from '../hooks/useAsync';

export default function Settings() {
  const [prefs, setPrefs] = useState(getPrefs());
  const status = useAsync(getConnectionStatus, [prefs.demo]);
  const update = (k, v) => { const n = { ...prefs, [k]: v }; setPrefs(n); savePrefs(n); };
  const field = 'rounded-lg border border-slate-700 bg-[#0b1220] px-3 py-2 text-sm';
  return (
    <>
      <PageHeader title="Settings" subtitle="Preferences are stored in this browser only" />
      <div className="grid gap-4 lg:grid-cols-2">
        <Card title="Backend connection">
          <dl className="space-y-3 text-sm">
            <div><dt className="text-slate-400">API base URL (VITE_API_BASE_URL)</dt><dd className="break-all">{API_BASE || 'Not configured'}</dd></div>
            <div><dt className="text-slate-400">Connection status</dt><dd className="mt-1"><Async state={status}>{(s) => <span className="flex items-center gap-2"><Badge value={s.mode === 'demo' ? 'Info' : s.ok ? 'Healthy' : 'Critical'} />{s.message}</span>}</Async></dd></div>
          </dl>
          <label className="mt-4 flex items-center gap-2 text-sm"><input type="checkbox" checked={prefs.demo || !API_BASE} disabled={!API_BASE} onChange={(e) => update('demo', e.target.checked)} />Use demo data{!API_BASE && ' (live mode requires VITE_API_BASE_URL)'}</label>
          <p className="mt-2 text-xs text-slate-500">Reload the app after changing this setting.</p>
        </Card>
        <Card title="Display preferences">
          <div className="space-y-4 text-sm">
            <label className="block"><span className="mb-1 block text-slate-400">Auto-refresh interval</span>
              <select className={field} value={prefs.refreshSec} onChange={(e) => update('refreshSec', Number(e.target.value))}>
                <option value={0}>Off</option><option value={15}>15 seconds</option><option value={30}>30 seconds</option><option value={60}>60 seconds</option></select></label>
            <label className="block"><span className="mb-1 block text-slate-400">Default time range</span>
              <select className={field} value={prefs.defaultRange} onChange={(e) => update('defaultRange', e.target.value)}>
                <option value="15m">15 minutes</option><option value="1h">1 hour</option><option value="24h">24 hours</option></select></label>
          </div>
        </Card>
      </div>
    </>
  );
}
