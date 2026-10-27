# API Contract — MSM Monitor (Online Boutique)

> **Status:** Live FastAPI Backend (`backend/app/main.py`) + Client (`src/services/api.js`).  
> Pointing the dashboard to the real backend requires setting `VITE_API_BASE_URL` in `.env`.

---

## Base URL

| Environment | URL |
|---|---|
| Development (mock) | `VITE_API_BASE_URL` not set → demo mode |
| Development (real) | `http://localhost:8000` |
| Production | `https://<your-domain>` |

All endpoints are prefixed with `/api`.

---

## Authentication

Phase 2: none (open).  
Phase 4+: Bearer token via `Authorization: Bearer <token>` header.

---

## Common conventions

- All timestamps are **Unix milliseconds** (integer).
- Severity values: `"Critical" | "Warning" | "Info"`.
- Status values differ per resource (documented below).
- `GET` requests that return lists support optional query params `?limit=N&offset=N`.

---

## Endpoints

### `GET /api/health`

Backend liveness probe.

**Response 200:**
```json
{ "status": "ok", "version": "0.1.0" }
```

---

### `GET /api/services`

List all monitored Online Boutique services with current metric snapshot.

**Response 200:**
```json
[
  {
    "id": "productcatalogservice",
    "name": "productcatalogservice",
    "description": "Product catalog gRPC service (Go)",
    "status": "Critical",
    "cpu": 94.2,
    "memory": 18.4,
    "latency": 42.0,
    "errorRate": 0.1,
    "rxBytes": 1800.0,
    "txBytes": 2100.0,
    "faultType": "cpu",
    "updatedAt": 1761379200000
  }
]
```

**Status values:** `"Healthy" | "Warning" | "Critical"`  
**faultType values (RE2-OB):** `"cpu" | "delay" | "disk" | "loss" | "memory" | "socket" | null`

---

### `GET /api/services/{id}`

Per-service detail: current snapshot + time-series + recent alerts + anomaly markers.

**Query params:** `range=15m|1h|24h` (default `1h`)

**Response 200:**
```json
{
  "service": { /* same shape as /api/services item */ },
  "series": [
    { "t": 1761375600000, "cpu": 18.2, "memory": 45.1, "latency": 41.8, "errorRate": 0.1, "rxBytes": 1820.0, "txBytes": 2090.0 }
  ],
  "alerts": [ /* Alert objects, see /api/alerts */ ],
  "anomalyMarkers": [
    { "t": 1761372000000, "metric": "cpu", "faultType": "cpu" }
  ]
}
```

---

### `GET /api/dashboard/summary`

Aggregated cluster-level time-series for the Overview page.

**Query params:** `range=15m|1h|24h`

**Response 200:**
```json
{
  "updatedAt": 1761379200000,
  "series": [
    { "t": 1761375600000, "cpu": 22.3, "memory": 47.1, "latency": 98.5, "errorRate": 0.28 }
  ]
}
```

---

### `GET /api/anomalies`

All detected anomalies.

**Response 200:**
```json
[
  {
    "id": "AN-1010",
    "service": "productcatalogservice",
    "metric": "CPU utilization",
    "unit": "%",
    "observed": 94.2,
    "baseline": 18.0,
    "severity": "Critical",
    "detectedAt": 1761374100000,
    "score": 0.96,
    "status": "Open",
    "faultType": "cpu",
    "anomalyScore": 0.96
  }
]
```

**status values:** `"Open" | "Under review" | "Closed" | "Dismissed"`

---

### `GET /api/alerts`

All alerts.

**Response 200:**
```json
[
  {
    "id": "AL-2008",
    "title": "CPU saturation on productcatalogservice",
    "severity": "Critical",
    "service": "productcatalogservice",
    "metric": "CPU utilization",
    "timestamp": 1761374040000,
    "status": "Active",
    "faultType": "cpu",
    "description": "CPU has sustained ~94% for over 80 minutes against a baseline of ~18%.",
    "evidence": "CPU spike began ~3h before now; correlated with productcatalogservice pod restarts.",
    "affectedMetrics": ["cpu", "latency"],
    "anomalyScore": 0.96
  }
]
```

**status values:** `"Active" | "Acknowledged" | "Resolved"`

---

### `POST /api/alerts/{id}/acknowledge`

Mark alert as acknowledged.

**Response 200:** Updated alert object.

---

### `POST /api/alerts/{id}/resolve`

Mark alert as resolved.

**Response 200:** Updated alert object.

---

### `GET /api/incidents`

All incidents (grouped alerts).

**Response 200:**
```json
[
  {
    "id": "INC-401",
    "start": 1761374100000,
    "end": null,
    "ongoing": true,
    "durationMin": 85,
    "services": ["productcatalogservice", "recommendationservice", "checkoutservice"],
    "severity": "Critical",
    "alerts": ["AL-2008", "AL-2007", "AL-2006"],
    "status": "Ongoing",
    "faultTypes": ["cpu", "delay", "loss"],
    "category": "Multi-service degradation: CPU stress, network delay, and packet loss"
  }
]
```

**status values:** `"Ongoing" | "Resolved" | "Closed"`

---

### `GET /api/events` (SSE — Phase 4)

Server-Sent Events stream for live anomaly/alert push.

**Content-Type:** `text/event-stream`

**Event types:**
```
event: anomaly
data: { "id": "AN-...", "service": "...", "severity": "...", "detectedAt": 0 }

event: alert
data: { "id": "AL-...", "title": "...", "severity": "...", "timestamp": 0 }

event: heartbeat
data: { "ts": 0 }
```

---

## Online Boutique service inventory (RE2-OB)

| Service ID | Language | Description |
|---|---|---|
| `frontend` | Go | Web UI, entry point |
| `productcatalogservice` | Go | Product catalog (gRPC) |
| `cartservice` | C# | Shopping cart, backed by Redis |
| `recommendationservice` | Python | Product recommendations |
| `checkoutservice` | Go | Order checkout orchestrator |
| `paymentservice` | Node.js | Payment processing |
| `shippingservice` | Go | Shipping cost estimation |
| `emailservice` | Python | Order confirmation emails |
| `currencyservice` | Node.js | Currency conversion |
| `adservice` | Java | Advertisement banners |
| `redis-cart` | Redis | Cart state cache |

## RE2-OB fault types

| Code | Label | Description |
|---|---|---|
| `cpu` | CPU stress | CPU throttle / stress injection |
| `delay` | Network delay | tc netem artificial latency |
| `disk` | Disk I/O pressure | fio disk saturation |
| `loss` | Packet loss | tc netem packet loss |
| `memory` | Memory pressure | memory allocation pressure |
| `socket` | Socket exhaustion | fd / socket limit exhaustion |

---

## Switching from mock to live backend

1. Set `VITE_API_BASE_URL=http://localhost:8000` in `.env`
2. Restart the Vite dev server (`npm run dev`)
3. In Settings, uncheck "Use demo data" (or leave it — it auto-detects the env var)
4. The app will call the real FastAPI backend at the endpoints above
