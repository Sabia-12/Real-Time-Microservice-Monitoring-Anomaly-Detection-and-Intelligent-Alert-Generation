"""
Database seeding for Online Boutique initial services and baseline topology.
"""

import logging
import time
from sqlalchemy.orm import Session

from .models import ServiceModel, AnomalyModel, AlertModel, IncidentModel
from .session import engine, Base, SessionLocal

logger = logging.getLogger(__name__)

INITIAL_SERVICES = [
    {
        "id": "frontend",
        "name": "frontend",
        "description": "Web UI & ingress gateway (Go)",
        "cpu": 15.2,
        "memory": 32.4,
        "latency": 38.5,
        "error_rate": 0.001,
        "rx_bytes": 1240.0,
        "tx_bytes": 2890.0,
    },
    {
        "id": "cartservice",
        "name": "cartservice",
        "description": "Shopping cart service (C# / Redis)",
        "cpu": 12.0,
        "memory": 48.1,
        "latency": 14.2,
        "error_rate": 0.0,
        "rx_bytes": 850.0,
        "tx_bytes": 910.0,
    },
    {
        "id": "productcatalogservice",
        "name": "productcatalogservice",
        "description": "Product catalog gRPC service (Go)",
        "cpu": 18.4,
        "memory": 22.8,
        "latency": 24.1,
        "error_rate": 0.0,
        "rx_bytes": 1450.0,
        "tx_bytes": 3100.0,
    },
    {
        "id": "currencyservice",
        "name": "currencyservice",
        "description": "Currency conversion service (Node.js)",
        "cpu": 8.5,
        "memory": 41.2,
        "latency": 11.0,
        "error_rate": 0.0,
        "rx_bytes": 620.0,
        "tx_bytes": 640.0,
    },
    {
        "id": "paymentservice",
        "name": "paymentservice",
        "description": "Payment processor (Node.js)",
        "cpu": 9.1,
        "memory": 39.5,
        "latency": 45.0,
        "error_rate": 0.0,
        "rx_bytes": 480.0,
        "tx_bytes": 510.0,
    },
    {
        "id": "shippingservice",
        "name": "shippingservice",
        "description": "Shipping cost & tracking (Go)",
        "cpu": 7.3,
        "memory": 19.4,
        "latency": 18.2,
        "error_rate": 0.0,
        "rx_bytes": 410.0,
        "tx_bytes": 430.0,
    },
    {
        "id": "emailservice",
        "name": "emailservice",
        "description": "Order confirmation emails (Python)",
        "cpu": 11.0,
        "memory": 52.3,
        "latency": 32.0,
        "error_rate": 0.0,
        "rx_bytes": 310.0,
        "tx_bytes": 350.0,
    },
    {
        "id": "checkoutservice",
        "name": "checkoutservice",
        "description": "Order checkout orchestrator (Go)",
        "cpu": 14.5,
        "memory": 35.6,
        "latency": 62.4,
        "error_rate": 0.002,
        "rx_bytes": 1890.0,
        "tx_bytes": 2100.0,
    },
    {
        "id": "recommendationservice",
        "name": "recommendationservice",
        "description": "Product recommendation engine (Python)",
        "cpu": 16.8,
        "memory": 68.4,
        "latency": 41.0,
        "error_rate": 0.0,
        "rx_bytes": 980.0,
        "tx_bytes": 1050.0,
    },
    {
        "id": "adservice",
        "name": "adservice",
        "description": "Advertisement banners (Java)",
        "cpu": 21.0,
        "memory": 82.5,
        "latency": 22.0,
        "error_rate": 0.0,
        "rx_bytes": 550.0,
        "tx_bytes": 580.0,
    },
]


def init_db(db: Session = None):
    """Create all tables and seed services if not already present."""
    Base.metadata.create_all(bind=engine)

    close_after = False
    if db is None:
        db = SessionLocal()
        close_after = True

    try:
        existing = db.query(ServiceModel).count()
        if existing == 0:
            now_ms = int(time.time() * 1000)
            for item in INITIAL_SERVICES:
                svc = ServiceModel(
                    id=item["id"],
                    name=item["name"],
                    description=item["description"],
                    status="Healthy",
                    cpu=item["cpu"],
                    memory=item["memory"],
                    latency=item["latency"],
                    error_rate=item["error_rate"],
                    rx_bytes=item["rx_bytes"],
                    tx_bytes=item["tx_bytes"],
                    fault_type=None,
                    updated_at=now_ms,
                )
                db.add(svc)
            db.commit()
            logger.info("Database seeded with %d Online Boutique services.", len(INITIAL_SERVICES))
    finally:
        if close_after:
            db.close()


if __name__ == "__main__":
    init_db()
    print("Database tables created and initialized.")
