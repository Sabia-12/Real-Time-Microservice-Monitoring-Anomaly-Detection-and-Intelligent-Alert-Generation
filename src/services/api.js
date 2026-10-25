import * as M from '../data/mock';
// All data access goes through here. Switch demo -> live by setting VITE_API_BASE_URL (see README).
const KEY = 'msm.prefs';
const defaults = { demo: true, refreshSec: 30, defaultRange: '1h' };
export const API_BASE = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '');
export const getPrefs = () => { try { return { ...defaults, ...JSON.parse(localStorage.getItem(KEY) || '{}') }; } catch { return defaults; } };
export const savePrefs = (p) => { try { localStorage.setItem(KEY, JSON.stringify(p)); } catch { /* ignore */ } };
export const isDemoMode = () => getPrefs().demo || !API_BASE;

const wait = (v) => new Promise((r) => setTimeout(() => r(structuredClone(v)), 250));
async function http(path, opts) {
  const res = await fetch(API_BASE + path, { headers: { 'Content-Type': 'application/json' }, ...opts });
  if (!res.ok) throw new Error(`Request failed: ${res.status} ${res.statusText}`);
  return res.json();
}
export const getDashboardSummary = (range) => isDemoMode() ? wait({ updatedAt: M.ANCHOR, series: M.dashboardSeries(range) }) : http(`/api/dashboard/summary?range=${range}`);
export const getServices = () => isDemoMode() ? wait(M.getServices()) : http('/api/services');
export const getServiceDetails = (id, range = '1h') => {
  if (!isDemoMode()) return http(`/api/services/${id}?range=${range}`);
  const service = M.getServices().find((s) => s.id === id);
  if (!service) return Promise.reject(new Error('Service not found'));
  return wait({ service, series: M.seriesFor(id, range), alerts: M.alerts.filter((a) => a.service === id) });
};
export const getAnomalies = () => isDemoMode() ? wait(M.anomalies) : http('/api/anomalies');
export const getAlerts = () => isDemoMode() ? wait(M.alerts) : http('/api/alerts');
const setAlert = (id, status, action) => {
  if (!isDemoMode()) return http(`/api/alerts/${id}/${action}`, { method: 'POST' });
  const a = M.alerts.find((x) => x.id === id);
  if (a) a.status = status; // local demo state only
  return wait(a);
};
export const acknowledgeAlert = (id) => setAlert(id, 'Acknowledged', 'acknowledge');
export const resolveAlert = (id) => setAlert(id, 'Resolved', 'resolve');
export const getIncidents = () => isDemoMode() ? wait(M.incidents) : http('/api/incidents');
export async function getConnectionStatus() {
  if (isDemoMode()) return { mode: 'demo', ok: true, message: 'Demo data mode. No backend is contacted.' };
  try { await http('/api/health'); return { mode: 'live', ok: true, message: 'Backend reachable.' }; }
  catch (e) { return { mode: 'live', ok: false, message: e.message }; }
}
