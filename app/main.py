from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.config import ALLOWED_ORIGINS
from app.database import init_db
from app.routers import (
    debts,
    dependencies,
    reviews,
    release_gates,
    analytics,
    export,
    simulations,
    recommendations,
)

BASE_DIR = Path(__file__).resolve().parent

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB tables and non-destructive migrations on application startup
    init_db()
    yield

app = FastAPI(
    title="Requirement Debt Ledger (RDL) API",
    description="Design and Implementation of a Risk-Aware, Time-Bound Requirement Debt Ledger for Software Requirements Management",
    version="1.1.0",
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

# CORS middleware restricted to explicitly configured trusted origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Mount API routers
app.include_router(debts.router)
app.include_router(dependencies.router)
app.include_router(reviews.router)
app.include_router(release_gates.router)
app.include_router(analytics.router)
app.include_router(export.router)
app.include_router(simulations.router)
app.include_router(recommendations.router)

# Mount Static assets
static_dir = BASE_DIR / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

@app.get("/")
def serve_index():
    """Serve the single page application frontend."""
    return FileResponse(str(static_dir / "index.html"))

@app.get("/api/health")
def health_check():
    """System health check endpoint."""
    return {
        "status": "online",
        "service": "Requirement Debt Ledger (RDL)",
        "version": "1.1.0",
        "cors_origins": ALLOWED_ORIGINS,
    }
