"""
ARES — AI-Powered Incident Response Copilot

FastAPI application entry point.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import API_TITLE, API_VERSION, API_DESCRIPTION, MAPS_DIR
from app.ml import load_models
from app.database import init_db, init_other_db
from app.routes import health, analyze, risk, recommendation, similar, hotspots, diversion, report, station_portal, route


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: load models and init DB. Shutdown: nothing to clean up."""
    print("=" * 50)
    print(f"Starting {API_TITLE} v{API_VERSION}")
    print("=" * 50)

    # Load ML models and dataset into memory
    load_models()

    # Initialize SQLite database
    init_db()

    # Initialize secondary SQLite database for custom descriptions
    init_other_db()

    print("ARES is ready.")
    print("=" * 50)

    yield  # App runs here

    print("ARES shutting down.")


# Create the FastAPI app
app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    description=API_DESCRIPTION,
    lifespan=lifespan,
)

# CORS — allow all origins for hackathon simplicity
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve generated maps as static files
app.mount("/maps", StaticFiles(directory=str(MAPS_DIR)), name="maps")

# Register routes
app.include_router(health.router)
app.include_router(analyze.router)
app.include_router(risk.router)
app.include_router(recommendation.router)
app.include_router(similar.router)
app.include_router(hotspots.router)
app.include_router(diversion.router)
app.include_router(report.router)
app.include_router(station_portal.router)
app.include_router(route.router)


@app.get("/", tags=["System"])
def root():
    """Root endpoint — API info."""
    return {
        "name": API_TITLE,
        "version": API_VERSION,
        "docs": "/docs",
        "endpoints": [
            "POST /report",
            "POST /analyze",
            "POST /risk",
            "POST /recommendation",
            "POST /similar-incidents",
            "POST /diversion",
            "GET /hotspots",
            "GET /health",
            "POST /api/portal/login",
            "GET /api/portal/incidents/{station_id}",
            "POST /api/portal/incidents/{incident_id}/feedback",
            "POST /route",
        ],
    }
