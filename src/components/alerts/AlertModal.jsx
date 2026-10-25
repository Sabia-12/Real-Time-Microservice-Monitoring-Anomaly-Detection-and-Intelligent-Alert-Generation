import { useEffect } from 'react';
import { X } from 'lucide-react';
import { Badge } from '../common/ui';
import { fmtTime } from '../../utils/format';

export default function AlertModal({ alert, onClose, onAck, onResolve, busy }) {
  useEffect(() => { const h = (e) => e.key === 'Escape' && onClose(); window.addEventListener('keydown', h); return () => window.removeEventListener('keydown', h); }, [onClose]);
  const btn = 'rounded-lg px-3 py-2 text-sm disabled:opacity-40';
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4" onClick={onClose}>
      <div role="dialog" aria-modal="true" aria-labelledby="alert-title" onClick={(e) => e.stopPropagation()} className="w-full max-w-lg rounded-xl border border-slate-700 bg-[#111a2e] p-5">
        <div className="flex items-start justify-between gap-3">
          <h2 id="alert-title" className="text-lg font-semibold text-slate-100">{alert.title}</h2>
          <button autoFocus aria-label="Close" onClick={onClose} className="rounded p-1 hover:bg-slate-800"><X size={18} /></button>
        </div>
        <div className="mt-3 flex gap-2"><Badge value={alert.severity} /><Badge value={alert.status} /></div>
        <dl className="mt-4 grid grid-cols-2 gap-3 text-sm">
          <div><dt className="text-slate-400">ID</dt><dd>{alert.id}</dd></div>
          <div><dt className="text-slate-400">Service</dt><dd>{alert.service}</dd></div>
          <div><dt className="text-slate-400">Triggering metric</dt><dd>{alert.metric}</dd></div>
          <div><dt className="text-slate-400">Raised</dt><dd>{fmtTime(alert.timestamp)}</dd></div>
        </dl>
        <p className="mt-4 text-sm text-slate-300">{alert.description}</p>
        <div className="mt-5 flex justify-end gap-2">
          <button className={`${btn} border border-slate-600 hover:bg-slate-800`} disabled={busy || alert.status !== 'Active'} onClick={onAck}>Acknowledge</button>
          <button className={`${btn} bg-cyan-600 text-white hover:bg-cyan-500`} disabled={busy || alert.status === 'Resolved'} onClick={onResolve}>Resolve</button>
        </div>
      </div>
    </div>
  );
}
