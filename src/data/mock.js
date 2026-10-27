// ─── Online Boutique demo snapshot ───────────────────────────────────────────
// Service names match Google Online Boutique (RE2-OB dataset, 90 cases).
// Fault types match RE2-OB: cpu | delay | disk | loss | memory | socket.
// Values are SYNTHETIC and deterministic — not live telemetry or ML output.
// ─────────────────────────────────────────────────────────────────────────────
export const ANCHOR = Date.UTC(2026, 9, 25, 10, 0, 0); // fixed "now" of demo snapshot
export const RANGES = { '15m': { n: 15, step: 60e3 }, '1h': { n: 12, step: 300e3 }, '24h': { n: 96, step: 900e3 } };
const MIN = 60e3, H = 3600e3;
const FAULT_START = ANCHOR - 3 * H;

// Deterministic pseudo-random noise
const noise = (s, i) => { const x = Math.sin(s * 12.9898 + i * 78.233) * 43758.5453; return x - Math.floor(x) - 0.5; };

// Real Online Boutique services (from RE2-OB docs and source)
// fault.type mirrors RE2-OB fault categories: cpu | delay | disk | loss | memory | socket
const OB_SERVICES = [
  {
    id: 'frontend',
    displayName: 'frontend',
    description: 'Web UI (Go), entry point for all user requests',
    base: { cpu: 22, memory: 38, latency: 95, errorRate: 0.3, rxBytes: 4200, txBytes: 3800 },
  },
  {
    id: 'productcatalogservice',
    displayName: 'productcatalogservice',
    description: 'Product catalog gRPC service (Go)',
    base: { cpu: 18, memory: 45, latency: 42, errorRate: 0.1, rxBytes: 1800, txBytes: 2100 },
    fault: { type: 'cpu', metric: 'cpu', factor: 3.1 },
  },
  {
    id: 'cartservice',
    displayName: 'cartservice',
    description: 'Shopping cart (C#), backed by Redis',
    base: { cpu: 31, memory: 55, latency: 68, errorRate: 0.4, rxBytes: 2400, txBytes: 2200 },
    fault: { type: 'memory', metric: 'memory', factor: 1.45 },
  },
  {
    id: 'recommendationservice',
    displayName: 'recommendationservice',
    description: 'Product recommendations (Python)',
    base: { cpu: 48, memory: 62, latency: 185, errorRate: 0.5, rxBytes: 900, txBytes: 1100 },
    fault: { type: 'delay', metric: 'latency', factor: 6.2 },
  },
  {
    id: 'checkoutservice',
    displayName: 'checkoutservice',
    description: 'Order checkout orchestrator (Go)',
    base: { cpu: 25, memory: 42, latency: 310, errorRate: 0.6, rxBytes: 1600, txBytes: 1400 },
    fault: { type: 'loss', metric: 'errorRate', factor: 8.5 },
  },
  {
    id: 'paymentservice',
    displayName: 'paymentservice',
    description: 'Payment processing (Node.js)',
    base: { cpu: 20, memory: 36, latency: 140, errorRate: 0.2, rxBytes: 1200, txBytes: 1100 },
  },
  {
    id: 'shippingservice',
    displayName: 'shippingservice',
    description: 'Shipping cost estimation (Go)',
    base: { cpu: 15, memory: 30, latency: 55, errorRate: 0.1, rxBytes: 800, txBytes: 900 },
    fault: { type: 'disk', metric: 'rxBytes', factor: 0.1 },
  },
  {
    id: 'emailservice',
    displayName: 'emailservice',
    description: 'Order confirmation emails (Python)',
    base: { cpu: 12, memory: 28, latency: 75, errorRate: 0.2, rxBytes: 600, txBytes: 550 },
    fault: { type: 'socket', metric: 'errorRate', factor: 5.0 },
  },
  {
    id: 'currencyservice',
    displayName: 'currencyservice',
    description: 'Currency conversion (Node.js)',
    base: { cpu: 10, memory: 24, latency: 32, errorRate: 0.1, rxBytes: 700, txBytes: 650 },
  },
  {
    id: 'adservice',
    displayName: 'adservice',
    description: 'Advertisement banner service (Java)',
    base: { cpu: 35, memory: 58, latency: 48, errorRate: 0.3, rxBytes: 1100, txBytes: 1000 },
  },
  {
    id: 'redis-cart',
    displayName: 'redis-cart',
    description: 'Redis cache for cart state',
    base: { cpu: 8, memory: 70, latency: 5, errorRate: 0.05, rxBytes: 3500, txBytes: 3400 },
  },
];

// Map RE2-OB fault type → human label
export const FAULT_TYPE_LABELS = {
  cpu: 'CPU stress',
  delay: 'Network delay',
  disk: 'Disk I/O pressure',
  loss: 'Packet loss',
  memory: 'Memory pressure',
  socket: 'Socket exhaustion',
};

// ─── Status derivation ────────────────────────────────────────────────────────
export const statusOf = (s) =>
  s.cpu >= 85 || s.memory >= 88 || s.latency >= 800 || s.errorRate >= 3 ? 'Critical'
  : s.cpu >= 65 || s.memory >= 78 || s.latency >= 400 || s.errorRate >= 1.5 ? 'Warning' : 'Healthy';

// ─── Time-series generation ───────────────────────────────────────────────────
function point(d, t) {
  const seed = d.id.length * 7 + d.id.charCodeAt(0);
  const out = { t };
  for (const m of Object.keys(d.base)) {
    let v = d.base[m] * (1 + 0.06 * Math.sin(t / H * 2 + seed) + 0.05 * noise(seed + m.length, Math.round(t / MIN)));
    if (d.fault?.metric === m && t >= FAULT_START) {
      v *= 1 + (d.fault.factor - 1) * Math.min(1, (t - FAULT_START) / (1.5 * H));
    }
    if (m === 'cpu' || m === 'memory') v = Math.min(100, v);
    if (m === 'errorRate') v = Math.max(0, v);
    out[m] = Math.round(v * 10) / 10;
  }
  return out;
}

// Anomaly marker timestamps per service (for chart annotations)
export const anomalyTimestamps = (id) => {
  const d = OB_SERVICES.find((x) => x.id === id);
  if (!d?.fault) return [];
  return [{ t: FAULT_START + H, metric: d.fault.metric, faultType: d.fault.type }];
};

export const seriesFor = (id, range) => {
  const d = OB_SERVICES.find((x) => x.id === id);
  if (!d) return [];
  const { n, step } = RANGES[range] || RANGES['1h'];
  return Array.from({ length: n }, (_, i) => point(d, ANCHOR - (n - 1 - i) * step));
};

export const dashboardSeries = (range) => {
  const all = OB_SERVICES.map((d) => seriesFor(d.id, range));
  return all[0].map((p, i) => {
    const avg = (k) => Math.round(all.reduce((a, s) => a + s[i][k], 0) / all.length * 10) / 10;
    return { t: p.t, cpu: avg('cpu'), memory: avg('memory'), latency: avg('latency'), errorRate: avg('errorRate') };
  });
};

export const getServices = () => OB_SERVICES.map((d, i) => {
  const p = point(d, ANCHOR);
  const s = {
    id: d.id,
    name: d.displayName,
    description: d.description,
    cpu: p.cpu,
    memory: p.memory,
    latency: p.latency,
    errorRate: p.errorRate,
    rxBytes: p.rxBytes,
    txBytes: p.txBytes,
    faultType: d.fault?.type || null,
    updatedAt: ANCHOR - (i % 5) * 12e3,
  };
  return { ...s, status: statusOf(s) };
});

// ─── Fixed timestamp helper ───────────────────────────────────────────────────
const at = (min) => ANCHOR - min * MIN;

// ─── Anomalies (RE2-OB fault types labelled) ─────────────────────────────────
export const anomalies = [
  { id: 'AN-1010', service: 'productcatalogservice', metric: 'CPU utilization', unit: '%', observed: 94.2, baseline: 18, severity: 'Critical', detectedAt: at(85), score: 0.96, status: 'Open', faultType: 'cpu', anomalyScore: 0.96 },
  { id: 'AN-1009', service: 'recommendationservice', metric: 'Latency', unit: 'ms', observed: 1147, baseline: 185, severity: 'Critical', detectedAt: at(78), score: 0.93, status: 'Open', faultType: 'delay', anomalyScore: 0.93 },
  { id: 'AN-1008', service: 'checkoutservice', metric: 'Error rate', unit: '%', observed: 5.1, baseline: 0.6, severity: 'Critical', detectedAt: at(72), score: 0.91, status: 'Under review', faultType: 'loss', anomalyScore: 0.91 },
  { id: 'AN-1007', service: 'cartservice', metric: 'Memory utilization', unit: '%', observed: 88.4, baseline: 55, severity: 'Warning', detectedAt: at(60), score: 0.78, status: 'Open', faultType: 'memory', anomalyScore: 0.78 },
  { id: 'AN-1006', service: 'emailservice', metric: 'Error rate', unit: '%', observed: 2.8, baseline: 0.2, severity: 'Warning', detectedAt: at(50), score: 0.72, status: 'Open', faultType: 'socket', anomalyScore: 0.72 },
  { id: 'AN-1005', service: 'shippingservice', metric: 'Network Rx (bytes/s)', unit: 'B/s', observed: 82, baseline: 800, severity: 'Warning', detectedAt: at(600), score: 0.68, status: 'Closed', faultType: 'disk', anomalyScore: 0.68 },
  { id: 'AN-1004', service: 'frontend', metric: 'Latency', unit: 'ms', observed: 345, baseline: 95, severity: 'Info', detectedAt: at(900), score: 0.55, status: 'Dismissed', faultType: null, anomalyScore: 0.55 },
  { id: 'AN-1003', service: 'adservice', metric: 'CPU utilization', unit: '%', observed: 68, baseline: 35, severity: 'Warning', detectedAt: at(1100), score: 0.71, status: 'Closed', faultType: 'cpu', anomalyScore: 0.71 },
];

// ─── Alerts ───────────────────────────────────────────────────────────────────
export const alerts = [
  {
    id: 'AL-2008', title: 'CPU saturation on productcatalogservice', severity: 'Critical',
    service: 'productcatalogservice', metric: 'CPU utilization', timestamp: at(84), status: 'Active',
    faultType: 'cpu',
    description: 'CPU has sustained ~94% for over 80 minutes against a baseline of ~18%. Fault type: CPU stress injection. Related anomaly: AN-1010. Root cause not determined by this tool.',
    evidence: 'CPU spike began ~3h before now; correlated with productcatalogservice pod restarts (2 in window).',
    affectedMetrics: ['cpu', 'latency'],
    anomalyScore: 0.96,
  },
  {
    id: 'AL-2007', title: 'High latency on recommendationservice', severity: 'Critical',
    service: 'recommendationservice', metric: 'Latency', timestamp: at(77), status: 'Active',
    faultType: 'delay',
    description: 'gRPC latency is ~1,147 ms against a 185 ms baseline — 6.2× increase. Fault type: network delay. Related anomaly: AN-1009.',
    evidence: 'Latency growth co-incident with checkoutservice call volume. frontend → checkoutservice → recommendationservice call chain affected.',
    affectedMetrics: ['latency', 'errorRate'],
    anomalyScore: 0.93,
  },
  {
    id: 'AL-2006', title: 'Elevated error rate on checkoutservice', severity: 'Critical',
    service: 'checkoutservice', metric: 'Error rate', timestamp: at(71), status: 'Acknowledged',
    faultType: 'loss',
    description: 'Error rate is ~5.1% against a 0.6% baseline. Fault type: packet loss. Related anomaly: AN-1008.',
    evidence: 'Packet drops on the checkoutservice ↔ paymentservice link. paymentservice error rate also elevated.',
    affectedMetrics: ['errorRate', 'latency'],
    anomalyScore: 0.91,
  },
  {
    id: 'AL-2005', title: 'Memory pressure on cartservice', severity: 'Warning',
    service: 'cartservice', metric: 'Memory utilization', timestamp: at(59), status: 'Active',
    faultType: 'memory',
    description: 'Memory utilization is ~88% and still climbing against a 55% baseline. Fault type: memory pressure. Related anomaly: AN-1007.',
    evidence: 'redis-cart memory also elevated (cache spill-over suspected). OOM kill risk if not addressed.',
    affectedMetrics: ['memory'],
    anomalyScore: 0.78,
  },
  {
    id: 'AL-2004', title: 'Socket errors on emailservice', severity: 'Warning',
    service: 'emailservice', metric: 'Error rate', timestamp: at(49), status: 'Active',
    faultType: 'socket',
    description: 'Error rate ~2.8% against 0.2% baseline. Fault type: socket exhaustion. Related anomaly: AN-1006.',
    evidence: 'Socket file descriptor count near ulimit. SMTP connections timing out.',
    affectedMetrics: ['errorRate'],
    anomalyScore: 0.72,
  },
  {
    id: 'AL-2003', title: 'Network Rx drop on shippingservice', severity: 'Warning',
    service: 'shippingservice', metric: 'Network Rx (bytes/s)', timestamp: at(600), status: 'Resolved',
    faultType: 'disk',
    description: 'Rx throughput dropped to ~82 B/s from 800 B/s baseline. Fault type: disk I/O pressure (affecting network queue). Related anomaly: AN-1005.',
    evidence: 'Disk saturation caused network buffer drops. Resolved after disk pressure lifted.',
    affectedMetrics: ['rxBytes'],
    anomalyScore: 0.68,
  },
  {
    id: 'AL-2002', title: 'CPU spike on adservice', severity: 'Warning',
    service: 'adservice', metric: 'CPU utilization', timestamp: at(1100), status: 'Resolved',
    faultType: 'cpu',
    description: 'CPU spiked to ~68% from 35% baseline, returned to normal. Related anomaly: AN-1003.',
    evidence: 'Short-lived CPU stress. No downstream impact detected.',
    affectedMetrics: ['cpu'],
    anomalyScore: 0.71,
  },
  {
    id: 'AL-2001', title: 'Latency deviation on frontend', severity: 'Info',
    service: 'frontend', metric: 'Latency', timestamp: at(900), status: 'Resolved',
    faultType: null,
    description: 'Frontend latency reached ~345 ms from 95 ms baseline. Brief deviation; no fault injection detected. Related anomaly: AN-1004.',
    evidence: 'Latency returned to baseline within 15 minutes. No correlated service anomalies.',
    affectedMetrics: ['latency'],
    anomalyScore: 0.55,
  },
];

// ─── Incidents ────────────────────────────────────────────────────────────────
// Online Boutique service dependency chain (simplified from RE2-OB docs):
//   frontend → checkoutservice → paymentservice
//                              → productcatalogservice
//                              → cartservice → redis-cart
//                              → shippingservice
//                              → recommendationservice
//                              → currencyservice
//                              → emailservice
export const incidents = [
  {
    id: 'INC-401',
    start: at(85), end: null, ongoing: true, durationMin: 85,
    services: ['productcatalogservice', 'recommendationservice', 'checkoutservice'],
    severity: 'Critical',
    alerts: ['AL-2008', 'AL-2007', 'AL-2006'],
    status: 'Ongoing',
    faultTypes: ['cpu', 'delay', 'loss'],
    category: 'Multi-service degradation: CPU stress, network delay, and packet loss across catalog/recommendation/checkout path',
  },
  {
    id: 'INC-400',
    start: at(59), end: null, ongoing: true, durationMin: 59,
    services: ['cartservice', 'redis-cart'],
    severity: 'Warning',
    alerts: ['AL-2005'],
    status: 'Ongoing',
    faultTypes: ['memory'],
    category: 'Memory pressure on cart service and its Redis backing store',
  },
  {
    id: 'INC-399',
    start: at(49), end: null, ongoing: true, durationMin: 49,
    services: ['emailservice'],
    severity: 'Warning',
    alerts: ['AL-2004'],
    status: 'Ongoing',
    faultTypes: ['socket'],
    category: 'Socket exhaustion on email service',
  },
  {
    id: 'INC-398',
    start: at(1100), end: at(1050), durationMin: 50,
    services: ['adservice'],
    severity: 'Warning',
    alerts: ['AL-2002'],
    status: 'Resolved',
    faultTypes: ['cpu'],
    category: 'CPU anomaly on adservice — short-lived, self-resolved',
  },
  {
    id: 'INC-397',
    start: at(600), end: at(555), durationMin: 45,
    services: ['shippingservice'],
    severity: 'Warning',
    alerts: ['AL-2003'],
    status: 'Resolved',
    faultTypes: ['disk'],
    category: 'Disk I/O pressure causing network throughput drop on shippingservice',
  },
  {
    id: 'INC-396',
    start: at(2900), end: at(2845), durationMin: 55,
    services: ['frontend'],
    severity: 'Info',
    alerts: ['AL-2001'],
    status: 'Closed',
    faultTypes: [],
    category: 'Latency deviation on frontend — no fault type identified, auto-resolved',
  },
];
