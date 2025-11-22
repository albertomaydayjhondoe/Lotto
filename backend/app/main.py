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
from app.publishing_integrations.router import router as providers_router
from app.publishing_worker.controller import router as worker_router
from app.publishing_webhooks.router import router as webhooks_router
from app.publishing_reconciliation.router import router as reconciliation_router
from app.publishing_scheduler.router import router as scheduler_router
from app.publishing_intelligence.router import router as intelligence_router
from app.orchestrator import orchestrator_router
from app.dashboard_api import dashboard_router
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

# Publishing Integrations endpoints (Step 3)
app.include_router(providers_router, prefix="/publishing", tags=["providers"])

# Publishing Worker endpoints (Step 4.2)
app.include_router(worker_router, prefix="/publishing", tags=["worker"])

# Publishing Webhooks endpoints (Step 4.3)
app.include_router(webhooks_router, prefix="/publishing", tags=["webhooks"])

# Publishing Reconciliation endpoints (Step 4.3)
app.include_router(reconciliation_router, prefix="/publishing", tags=["reconciliation"])

# Publishing Scheduler endpoints (Step 4.4)
app.include_router(scheduler_router, prefix="/publishing", tags=["scheduler"])

# Publishing Intelligence endpoints (Step 4.5)
app.include_router(intelligence_router, prefix="/publishing/intelligence", tags=["intelligence"])

# Orchestrator endpoints (Step 4.6)
app.include_router(orchestrator_router, tags=["orchestrator"])

# Dashboard API endpoints (PASO 6.1)
app.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])

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
