/**
 * AlertModal — Alert detail dialog with evidence, anomaly score,
 * affected metrics, and fault type label.
 */
import { useEffect } from 'react';
import { AlertTriangle, X } from 'lucide-react';
import { Badge } from '../common/ui';
import { FAULT_TYPE_LABELS } from '../../data/mock';
import { fmtTime } from '../../utils/format';

export default function AlertModal({ alert, onClose, onAck, onResolve, busy }) {
  useEffect(() => {
    const h = (e) => e.key === 'Escape' && onClose();
    window.addEventListener('keydown', h);
    return () => window.removeEventListener('keydown', h);
  }, [onClose]);

  const btn = 'rounded-lg px-3 py-2 text-sm disabled:opacity-40';
  const rawScore = alert.anomalyScore != null ? Number(alert.anomalyScore) : null;
  const scorePercent = rawScore != null
    ? Math.min(100, Math.max(0, rawScore <= 1.0 ? rawScore * 100 : (rawScore / 15.0) * 100))
    : null;
  const faultLabel = alert.faultType ? FAULT_TYPE_LABELS[alert.faultType] : null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="alert-title"
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-lg rounded-xl border border-slate-700 bg-[#0d1626] shadow-2xl p-5 animate-in fade-in zoom-in-95 duration-150"
      >
        {/* Header */}
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-start gap-2 min-w-0">
            <AlertTriangle size={18} className="mt-0.5 shrink-0 text-amber-400" />
            <h2 id="alert-title" className="text-base font-semibold text-slate-100">{alert.title}</h2>
          </div>
          <button autoFocus aria-label="Close" onClick={onClose} className="rounded p-1 hover:bg-slate-800 text-slate-400 hover:text-slate-200">
            <X size={18} />
          </button>
        </div>

        {/* Badges */}
        <div className="mt-3 flex flex-wrap gap-2">
          <Badge value={alert.severity} />
          <Badge value={alert.status} />
          {faultLabel && (
            <span className="inline-flex items-center gap-1 rounded-full bg-red-500/10 px-2 py-0.5 text-xs text-red-300 ring-1 ring-red-500/20">
              {faultLabel}
            </span>
          )}
        </div>

        {/* Metadata grid */}
        <dl className="mt-4 grid grid-cols-2 gap-3 text-sm">
          <div><dt className="text-slate-400">ID</dt><dd className="font-mono text-slate-200">{alert.id}</dd></div>
          <div><dt className="text-slate-400">Service</dt><dd className="text-slate-200">{alert.service}</dd></div>
          <div><dt className="text-slate-400">Triggering metric</dt><dd className="text-slate-200">{alert.metric}</dd></div>
          <div><dt className="text-slate-400">Raised</dt><dd className="text-slate-200">{fmtTime(alert.timestamp)}</dd></div>
          {rawScore != null && (
            <div>
              <dt className="text-slate-400">Anomaly score</dt>
              <dd className="flex items-center gap-2 mt-1">
                <div className="h-2 flex-1 rounded-full bg-slate-800 overflow-hidden ring-1 ring-slate-700/50">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-amber-500 to-red-500 transition-all duration-300"
                    style={{ width: `${scorePercent}%` }}
                  />
                </div>
                <span className="text-xs font-mono font-medium text-slate-200 shrink-0">
                  {rawScore > 1.0 ? `${rawScore.toFixed(2)}σ` : rawScore.toFixed(2)}
                </span>
              </dd>
            </div>
          )}
          {alert.affectedMetrics?.length > 0 && (
            <div>
              <dt className="text-slate-400">Affected metrics</dt>
              <dd className="flex flex-wrap gap-1 mt-0.5">
                {alert.affectedMetrics.map((m) => (
                  <span key={m} className="rounded bg-slate-800 px-1.5 py-0.5 text-xs font-mono text-slate-300">{m}</span>
                ))}
              </dd>
            </div>
          )}
        </dl>

        {/* Description */}
        <p className="mt-4 text-sm text-slate-300">{alert.description}</p>

        {/* Evidence */}
        {alert.evidence && (
          <div className="mt-3 rounded-lg border border-sky-500/20 bg-sky-500/8 p-3 text-sm text-sky-200">
            <p className="mb-1 text-xs font-semibold text-sky-400 uppercase tracking-wide">Supporting evidence</p>
            <p>{alert.evidence}</p>
          </div>
        )}

        {/* Actions */}
        <div className="mt-5 flex justify-end gap-2">
          <button className={`${btn} border border-slate-600 hover:bg-slate-800 text-slate-200`} disabled={busy || alert.status !== 'Active'} onClick={onAck}>
            Acknowledge
          </button>
          <button className={`${btn} bg-cyan-600 text-white hover:bg-cyan-500`} disabled={busy || alert.status === 'Resolved'} onClick={onResolve}>
            Resolve
          </button>
        </div>
      </div>
    </div>
  );
}
