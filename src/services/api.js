/**
 * api.js — All data access goes through here.
 * Demo mode: returns mock data from src/data/mock.js.
 * Live mode: proxies to VITE_API_BASE_URL (one env-var change).
 *
 * REST contract: see docs/api_contract.md
 */
import * as M from '../data/mock';

const KEY = 'msm.prefs';
export const API_BASE = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '');
const defaults = { demo: !API_BASE, refreshSec: 30, defaultRange: '1h' };
export const getPrefs = () => { try { return { ...defaults, ...JSON.parse(localStorage.getItem(KEY) || '{}') }; } catch { return defaults; } };
export const savePrefs = (p) => { try { localStorage.setItem(KEY, JSON.stringify(p)); } catch { /* ignore */ } };
export const isDemoMode = () => getPrefs().demo || !API_BASE;

const wait = (v) => new Promise((r) => setTimeout(() => r(structuredClone(v)), 200));

async function http(path, opts) {
  const res = await fetch(API_BASE + path, { headers: { 'Content-Type': 'application/json' }, ...opts });
  if (!res.ok) throw new Error(`Request failed: ${res.status} ${res.statusText}`);
  return res.json();
}

// ── Dashboard ────────────────────────────────────────────────────────────────
export const getDashboardSummary = (range) =>
  isDemoMode() ? wait({ updatedAt: M.ANCHOR, series: M.dashboardSeries(range) }) : http(`/api/dashboard/summary?range=${range}`);

// ── Services ─────────────────────────────────────────────────────────────────
export const getServices = () =>
  isDemoMode() ? wait(M.getServices()) : http('/api/services');

export const getServiceDetails = (id, range = '1h') => {
  if (!isDemoMode()) return http(`/api/services/${id}?range=${range}`);
  const service = M.getServices().find((s) => s.id === id);
  if (!service) return Promise.reject(new Error('Service not found'));
  return wait({
    service,
    series: M.seriesFor(id, range),
    alerts: M.alerts.filter((a) => a.service === id),
    anomalyMarkers: M.anomalyTimestamps(id),
  });
};

// ── Anomalies ────────────────────────────────────────────────────────────────
export const getAnomalies = () =>
  isDemoMode() ? wait(M.anomalies) : http('/api/anomalies');

// ── Alerts ───────────────────────────────────────────────────────────────────
export const getAlerts = () =>
  isDemoMode() ? wait(M.alerts) : http('/api/alerts');

const setAlert = (id, status, action) => {
  if (!isDemoMode()) return http(`/api/alerts/${id}/${action}`, { method: 'POST' });
  const a = M.alerts.find((x) => x.id === id);
  if (a) a.status = status;
  return wait(a);
};
export const acknowledgeAlert = (id) => setAlert(id, 'Acknowledged', 'acknowledge');
export const resolveAlert = (id) => setAlert(id, 'Resolved', 'resolve');

// ── Incidents ────────────────────────────────────────────────────────────────
export const getIncidents = () =>
  isDemoMode() ? wait(M.incidents) : http('/api/incidents');

// ── Health / SSE / Replay ────────────────────────────────────────────────────
export async function getConnectionStatus() {
  if (isDemoMode()) return { mode: 'demo', ok: true, message: 'Demo data mode — no backend contacted.' };
  try { await http('/api/health'); return { mode: 'live', ok: true, message: 'Backend reachable.' }; }
  catch (e) { return { mode: 'live', ok: false, message: e.message }; }
}

export const getReplayCases = () => http('/api/replay/cases');
export const getReplayStatus = () => http('/api/replay/status');
export const startReplay = (caseId, speed = 5) =>
  http(`/api/replay/start?case_id=${encodeURIComponent(caseId)}&speed=${speed}`, { method: 'POST' });
export const stopReplay = () => http('/api/replay/stop', { method: 'POST' });

export function subscribeEvents(onMessage) {
  if (isDemoMode() || !API_BASE) return () => {};
  const eventSource = new EventSource(`${API_BASE}/api/events`);

  eventSource.addEventListener('anomaly', (e) => {
    try { onMessage({ type: 'anomaly', data: JSON.parse(e.data) }); } catch {}
  });
  eventSource.addEventListener('alert', (e) => {
    try { onMessage({ type: 'alert', data: JSON.parse(e.data) }); } catch {}
  });
  eventSource.addEventListener('incident', (e) => {
    try { onMessage({ type: 'incident', data: JSON.parse(e.data) }); } catch {}
  });
  eventSource.addEventListener('heartbeat', (e) => {
    try { onMessage({ type: 'heartbeat', data: JSON.parse(e.data) }); } catch {}
  });

  return () => eventSource.close();
}
