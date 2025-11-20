"""
FastAPI main application entry point.
Implements the Orquestador OpenAPI specification.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api import upload, jobs, clips, confirm_publish, webhooks, campaigns, rules, debug, rule_engine, campaigns_orchestrator
from app.e2b import api as e2b_api
from app.publishing_engine import router as publishing_router
from app.core.config import settings
from app.core.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    await init_db()
    yield
    # Shutdown
    pass


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(upload.router, tags=["upload"])
app.include_router(jobs.router, tags=["jobs"])
app.include_router(clips.router, tags=["clips"])
app.include_router(confirm_publish.router, tags=["confirm_publish"])
app.include_router(webhooks.router, prefix="/webhook", tags=["webhooks"])
app.include_router(campaigns.router, tags=["campaigns"])
app.include_router(rules.router, tags=["rules"])

# Rule Engine endpoints
app.include_router(rule_engine.router, prefix="/rules", tags=["rule_engine"])

# Campaigns Orchestrator endpoints
app.include_router(campaigns_orchestrator.router, tags=["campaigns_orchestrator"])

# E2B Sandbox Simulation endpoints
app.include_router(e2b_api.router, tags=["e2b_simulation"])

# Publishing Engine endpoints
app.include_router(publishing_router, prefix="/publishing", tags=["publishing"])

# Debug endpoints (DEVELOPMENT ONLY)
# WARNING: In production, these endpoints should be protected with authentication
# or disabled by setting DEBUG_ENDPOINTS_ENABLED=False in config
if settings.DEBUG_ENDPOINTS_ENABLED:
    app.include_router(debug.router, prefix="/debug", tags=["debug"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs_url": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
