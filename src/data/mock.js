// Deterministic DEMO data. Synthetic values only: not live telemetry, not ML output.
export const ANCHOR = Date.UTC(2026, 9, 25, 10, 0, 0); // fixed "now" of the demo snapshot
export const RANGES = { '15m': { n: 15, step: 60e3 }, '1h': { n: 12, step: 300e3 }, '24h': { n: 96, step: 900e3 } };
const MIN = 60e3, H = 3600e3;
const FAULT_START = ANCHOR - 3 * H;
const noise = (s, i) => { const x = Math.sin(s * 12.9898 + i * 78.233) * 43758.5453; return x - Math.floor(x) - 0.5; };

const defs = [
  { id: 'api-gateway', base: { cpu: 38, memory: 52, latency: 120, errorRate: 0.4 } },
  { id: 'auth-service', base: { cpu: 31, memory: 44, latency: 85, errorRate: 0.2 } },
  { id: 'cart-service', base: { cpu: 42, memory: 58, latency: 140, errorRate: 0.5 }, fault: { m: 'cpu', f: 2.4 } },
  { id: 'catalog-service', base: { cpu: 35, memory: 55, latency: 160, errorRate: 0.3 } },
  { id: 'order-service', base: { cpu: 48, memory: 62, latency: 210, errorRate: 0.8 }, fault: { m: 'latency', f: 5 } },
  { id: 'payment-service', base: { cpu: 40, memory: 60, latency: 180, errorRate: 0.6 }, fault: { m: 'errorRate', f: 6 } },
  { id: 'recommendation-service', base: { cpu: 55, memory: 70, latency: 240, errorRate: 0.5 }, fault: { m: 'memory', f: 1.2 } },
  { id: 'user-service', base: { cpu: 33, memory: 49, latency: 95, errorRate: 0.2 } },
];

export const statusOf = (s) =>
  s.cpu >= 90 || s.memory >= 90 || s.latency >= 900 || s.errorRate >= 5 ? 'Critical'
  : s.cpu >= 75 || s.memory >= 80 || s.latency >= 500 || s.errorRate >= 2 ? 'Warning' : 'Healthy';

function point(d, t) {
  const seed = d.id.length * 7 + d.id.charCodeAt(0), out = { t };
  for (const m of Object.keys(d.base)) {
    let v = d.base[m] * (1 + 0.06 * Math.sin(t / H * 2 + seed) + 0.05 * noise(seed + m.length, Math.round(t / MIN)));
    if (d.fault?.m === m && t >= FAULT_START) v *= 1 + (d.fault.f - 1) * Math.min(1, (t - FAULT_START) / H);
    if (m === 'cpu' || m === 'memory') v = Math.min(100, v);
    out[m] = Math.round(v * 10) / 10;
  }
  return out;
}
export const seriesFor = (id, range) => {
  const d = defs.find((x) => x.id === id), { n, step } = RANGES[range] || RANGES['1h'];
  return Array.from({ length: n }, (_, i) => point(d, ANCHOR - (n - 1 - i) * step));
};
export const dashboardSeries = (range) => {
  const all = defs.map((d) => seriesFor(d.id, range));
  return all[0].map((p, i) => {
    const avg = (k) => Math.round(all.reduce((a, s) => a + s[i][k], 0) / all.length * 10) / 10;
    return { t: p.t, cpu: avg('cpu'), memory: avg('memory'), latency: avg('latency'), errorRate: avg('errorRate') };
  });
};
export const getServices = () => defs.map((d, i) => {
  const p = point(d, ANCHOR);
  const s = { id: d.id, name: d.id, cpu: p.cpu, memory: p.memory, latency: p.latency, errorRate: p.errorRate, updatedAt: ANCHOR - (i % 4) * 15e3 };
  return { ...s, status: statusOf(s) };
});

const at = (min) => ANCHOR - min * MIN;
export const anomalies = [
  { id: 'AN-1008', service: 'cart-service', metric: 'CPU utilization', unit: '%', observed: 100, baseline: 42, severity: 'Critical', detectedAt: at(95), score: 0.97, status: 'Open' },
  { id: 'AN-1007', service: 'order-service', metric: 'Latency', unit: 'ms', observed: 1040, baseline: 210, severity: 'Critical', detectedAt: at(80), score: 0.94, status: 'Under review' },
  { id: 'AN-1006', service: 'payment-service', metric: 'Error rate', unit: '%', observed: 3.6, baseline: 0.6, severity: 'Warning', detectedAt: at(70), score: 0.88, status: 'Open' },
  { id: 'AN-1005', service: 'recommendation-service', metric: 'Memory utilization', unit: '%', observed: 84, baseline: 70, severity: 'Warning', detectedAt: at(55), score: 0.74, status: 'Open' },
  { id: 'AN-1004', service: 'api-gateway', metric: 'Latency', unit: 'ms', observed: 310, baseline: 120, severity: 'Info', detectedAt: at(600), score: 0.61, status: 'Dismissed' },
  { id: 'AN-1003', service: 'catalog-service', metric: 'CPU utilization', unit: '%', observed: 71, baseline: 35, severity: 'Warning', detectedAt: at(900), score: 0.79, status: 'Closed' },
  { id: 'AN-1002', service: 'order-service', metric: 'Error rate', unit: '%', observed: 2.9, baseline: 0.8, severity: 'Warning', detectedAt: at(1200), score: 0.81, status: 'Closed' },
];
export const alerts = [
  { id: 'AL-2006', title: 'CPU saturation on cart-service', severity: 'Critical', service: 'cart-service', metric: 'CPU utilization', timestamp: at(94), status: 'Active', description: 'CPU has stayed at or near 100% for over an hour, against a typical baseline of about 42%. Related anomaly: AN-1008. Cause not determined.' },
  { id: 'AL-2005', title: 'High latency on order-service', severity: 'Critical', service: 'order-service', metric: 'Latency', timestamp: at(79), status: 'Active', description: 'Latency is around 1,000 ms against a baseline of about 210 ms. Related anomaly: AN-1007. Cause not determined.' },
  { id: 'AL-2004', title: 'Elevated error rate on payment-service', severity: 'Warning', service: 'payment-service', metric: 'Error rate', timestamp: at(69), status: 'Acknowledged', description: 'Error rate is about 3.6% against a baseline of 0.6%. Related anomaly: AN-1006.' },
  { id: 'AL-2003', title: 'Memory growth on recommendation-service', severity: 'Warning', service: 'recommendation-service', metric: 'Memory utilization', timestamp: at(54), status: 'Active', description: 'Memory is at about 84% and rising against a 70% baseline. Related anomaly: AN-1005.' },
  { id: 'AL-2002', title: 'CPU spike on catalog-service', severity: 'Warning', service: 'catalog-service', metric: 'CPU utilization', timestamp: at(900), status: 'Resolved', description: 'Short CPU spike to about 71%; returned to baseline. Related anomaly: AN-1003.' },
  { id: 'AL-2001', title: 'Error spike on order-service', severity: 'Warning', service: 'order-service', metric: 'Error rate', timestamp: at(1200), status: 'Resolved', description: 'Error rate reached 2.9% briefly. Related anomaly: AN-1002.' },
];
export const incidents = [
  { id: 'INC-301', start: at(95), end: null, ongoing: true, durationMin: 95, services: ['cart-service', 'order-service', 'payment-service'], severity: 'Critical', alerts: ['AL-2006', 'AL-2005', 'AL-2004'], status: 'Ongoing', category: 'Resource saturation, latency and error-rate anomalies (cause not determined)' },
  { id: 'INC-300', start: at(1200), end: at(1130), durationMin: 70, services: ['order-service'], severity: 'Warning', alerts: ['AL-2001'], status: 'Resolved', category: 'Error-rate anomaly' },
  { id: 'INC-299', start: at(900), end: at(870), durationMin: 30, services: ['catalog-service'], severity: 'Warning', alerts: ['AL-2002'], status: 'Resolved', category: 'CPU anomaly' },
  { id: 'INC-298', start: at(2900), end: at(2840), durationMin: 60, services: ['api-gateway', 'auth-service'], severity: 'Info', alerts: [], status: 'Closed', category: 'Latency deviation (no alert raised)' },
];
