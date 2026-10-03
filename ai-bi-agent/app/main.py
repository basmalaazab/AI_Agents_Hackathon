"""
FastAPI application entry point.

Mounts all API routers, configures logging, and starts the background scheduler.
"""
import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import health, sources, uploads, pipelines, data, analytics, agent
from app.config import get_settings
from app.database import Base, engine
from app.models import (  # noqa: F401 — register models before create_all
    Customer,
    DataQualityError,
    DataSource,
    IngestionRun,
    Order,
    OrderItem,
    Product,
    RawRecord,
)
from app.services.scheduler import start_scheduler, stop_scheduler


# ---------------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------------

settings = get_settings()

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifespan — startup / shutdown hooks
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting AI Business Intelligence Agent — Data Engineering Layer")
    Base.metadata.create_all(bind=engine)
    start_scheduler()
    yield
    stop_scheduler()
    logger.info("Shutdown complete.")


# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="AI BI Agent — Data Engineering API",
    description=(
        "Data ingestion, validation, transformation, and pipeline management API "
        "for the AI Business Intelligence Agent hackathon project.\n\n"
        "**Note:** All demo data is synthetic and clearly labelled."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
    ],
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

API_PREFIX = "/api/v1"

app.include_router(health.router, prefix=API_PREFIX)
app.include_router(sources.router, prefix=API_PREFIX)
app.include_router(uploads.router, prefix=API_PREFIX)
app.include_router(pipelines.router, prefix=API_PREFIX)
app.include_router(data.router, prefix=API_PREFIX)
app.include_router(analytics.router, prefix=API_PREFIX)
app.include_router(agent.router, prefix=API_PREFIX)




@app.get("/", tags=["root"])
def root():
    return {
        "service": "AI BI Agent — Data Engineering Layer",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/health",
    }
