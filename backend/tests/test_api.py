"""
Integration tests for FastAPI REST endpoints using httpx.AsyncClient with anyio.
"""

import pytest
import httpx

from backend.app.main import app
from backend.app.db.seed import init_db
from backend.app.db.session import SessionLocal
from backend.app.db.models import AlertModel


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    init_db()


@pytest.fixture
async def client():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.anyio
async def test_health_endpoint(client):
    response = await client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


@pytest.mark.anyio
async def test_services_list(client):
    response = await client.get("/api/services")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 10
    svc = data[0]
    assert "id" in svc
    assert "name" in svc
    assert "cpu" in svc
    assert "memory" in svc


@pytest.mark.anyio
async def test_service_detail(client):
    response = await client.get("/api/services/frontend")
    assert response.status_code == 200
    data = response.json()
    assert "service" in data
    assert data["service"]["id"] == "frontend"
    assert "series" in data
    assert isinstance(data["series"], list)
    assert len(data["series"]) > 0
    assert "alerts" in data
    assert "anomalyMarkers" in data


@pytest.mark.anyio
async def test_service_detail_not_found(client):
    response = await client.get("/api/services/nonexistent_service")
    assert response.status_code == 404


@pytest.mark.anyio
async def test_dashboard_summary(client):
    response = await client.get("/api/dashboard/summary?range=1h")
    assert response.status_code == 200
    data = response.json()
    assert "updatedAt" in data
    assert "series" in data
    assert len(data["series"]) > 0


@pytest.mark.anyio
async def test_anomalies_list(client):
    response = await client.get("/api/anomalies?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.anyio
async def test_alerts_list_and_lifecycle(client):
    # Insert a test alert
    db = SessionLocal()
    alert = AlertModel(
        id="AL-TEST-99",
        title="Test Alert",
        severity="Warning",
        service="frontend",
        metric="cpu",
        timestamp=1700000000000,
        status="Active",
    )
    db.merge(alert)
    db.commit()
    db.close()

    # List alerts
    response = await client.get("/api/alerts")
    assert response.status_code == 200
    data = response.json()
    assert any(a["id"] == "AL-TEST-99" for a in data)

    # Acknowledge
    ack_res = await client.post("/api/alerts/AL-TEST-99/acknowledge")
    assert ack_res.status_code == 200
    assert ack_res.json()["status"] == "Acknowledged"

    # Resolve
    res_res = await client.post("/api/alerts/AL-TEST-99/resolve")
    assert res_res.status_code == 200
    assert res_res.json()["status"] == "Resolved"


@pytest.mark.anyio
async def test_incidents_list(client):
    response = await client.get("/api/incidents")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.anyio
async def test_replay_cases_and_status(client):
    cases_res = await client.get("/api/replay/cases")
    assert cases_res.status_code == 200
    cases_data = cases_res.json()
    assert "total" in cases_data
    assert "cases" in cases_data
    assert cases_data["total"] >= 10

    status_res = await client.get("/api/replay/status")
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert "running" in status_data
