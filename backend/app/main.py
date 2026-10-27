"""
Main FastAPI Application entrypoint for Online Boutique Monitoring & Alerting.
"""

from contextlib import asynccontextmanager
import logging
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.db.seed import init_db
from backend.app.api import (
    health,
    services,
    dashboard,
    anomalies,
    alerts,
    incidents,
    events,
    replay,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("msm.backend")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler: runs DB migrations and initial seeding on startup."""
    logger.info("Initializing database and service seed data...")
    init_db()
    logger.info("MSM Monitor Backend ready.")
    yield
    logger.info("Shutting down MSM Monitor Backend...")


app = FastAPI(
    title="MSM Microservice Monitor API",
    description="Real-Time Microservice Monitoring, Anomaly Detection and Alert Engine for Online Boutique",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration for Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*",  # Permissive in development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers under /api prefix
app.include_router(health.router, prefix="/api")
app.include_router(services.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(anomalies.router, prefix="/api")
app.include_router(alerts.router, prefix="/api")
app.include_router(incidents.router, prefix="/api")
app.include_router(events.router, prefix="/api")
app.include_router(replay.router, prefix="/api")


@app.get("/")
def root():
    return {
        "app": "MSM Monitor API",
        "status": "online",
        "docs": "/docs",
        "health": "/api/health",
    }
