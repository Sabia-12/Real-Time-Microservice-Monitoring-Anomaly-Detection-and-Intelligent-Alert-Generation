# Real-Time Microservice Monitoring: Frontend

React + Vite + Tailwind + React Router + Recharts + Lucide. Frontend only; runs in **demo mode** without a backend.

## Prerequisites
Node.js 18+ and npm.

## Run
```bash
npm install
npm run dev       # http://localhost:5173
npm run build     # production build in dist/
npm run preview   # serve the build
```

## Environment
Copy `.env.example` to `.env`. `VITE_API_BASE_URL` (e.g. `http://localhost:8000`) points at the Python backend. If empty, the app uses demo data.

## Demo mode
All data comes from `src/data/mock.js` (deterministic, frozen at a fixed demo timestamp). A banner shows when it is active. Values are synthetic: they are **not** live telemetry or ML detections, and no accuracy/precision/recall figures are shown. Anomaly scores are illustrative. Alert acknowledge/resolve change in-memory state only (reset on reload). Services page status is derived from simple thresholds in `statusOf` (demo only).

## Structure
```
src/components/{layout,charts,common,services,alerts}  src/pages  src/services/api.js  src/data/mock.js  src/hooks  src/utils
```
Components only call functions in `src/services/api.js`; swapping demo for live needs no UI changes.

## Proposed backend contracts (to be agreed; none exist yet)
| Function | Request | Response |
|---|---|---|
| getDashboardSummary | `GET /api/dashboard/summary?range=15m\|1h\|24h` | `{updatedAt, series:[{t,cpu,memory,latency,errorRate}]}` (t = epoch ms; cpu/memory %, latency ms, errorRate %) |
| getServices | `GET /api/services` | `[{id,name,status,cpu,memory,latency,errorRate,updatedAt}]` |
| getServiceDetails | `GET /api/services/{id}?range=` | `{service, series:[...], alerts:[...]}` |
| getAnomalies | `GET /api/anomalies` | `[{id,service,metric,unit,observed,baseline,severity,detectedAt,score,status}]` |
| getAlerts | `GET /api/alerts` | `[{id,title,severity,service,metric,timestamp,description,status}]` |
| acknowledgeAlert / resolveAlert | `POST /api/alerts/{id}/acknowledge` / `/resolve` | updated alert |
| getIncidents | `GET /api/incidents` | `[{id,start,end,ongoing,durationMin,services,severity,alerts,status,category}]` |
| getConnectionStatus | `GET /api/health` | any 2xx |

Severity: Critical/Warning/Info. Alert status: Active/Acknowledged/Resolved. Timestamps: epoch ms.

## Limitations / next steps
- No backend, ML detector or live telemetry yet; endpoint shapes are proposals.
- Live mode has no authentication, retries or CORS handling (configure CORS on the backend).
- No ESLint or test setup is included yet.
- Incident "category" describes observed behavior only; no root-cause diagnosis is shown.
