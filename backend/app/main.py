"""
FastAPI main application entry point.
Implements the Orquestador OpenAPI specification.
"""
import asyncio
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
from app.dashboard_ai import router as dashboard_ai_router
from app.dashboard_actions import router as dashboard_actions_router
from app.dashboard_ai_integration import dashboard_ai_integration_router
from app.live_telemetry.router import router as telemetry_router
from app.live_telemetry.telemetry_manager import telemetry_manager
from app.live_telemetry.collector import gather_metrics
from app.alerting_engine import router as alerting_router
from app.alerting_engine.websocket import alert_manager
from app.alerting_engine.engine import analyze_system_state
from app.auth import auth_router
from app.ai_global_worker import ai_global_router, start_ai_worker_loop, stop_ai_worker_loop
from app.core.config import settings
from app.core.database import init_db, get_db


async def telemetry_broadcast_loop():
    """
    Background task that broadcasts telemetry data to all connected clients.
    
    Runs every TELEMETRY_INTERVAL_SECONDS and only collects metrics if there
    are active WebSocket subscribers to optimize database load.
    """
    while True:
        try:
            # Only collect and broadcast if there are subscribers
            if telemetry_manager.has_subscribers():
                # Get database session
                async for db in get_db():
                    # Collect metrics
                    payload = await gather_metrics(db)
                    
                    # Broadcast to all connected clients
                    await telemetry_manager.broadcast(payload)
                    
                    break  # Exit the async for loop after one iteration
            
            # Wait for next interval
            await asyncio.sleep(settings.TELEMETRY_INTERVAL_SECONDS)
            
        except Exception as e:
            # Log error but keep loop running
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in telemetry broadcast loop: {e}")
            await asyncio.sleep(settings.TELEMETRY_INTERVAL_SECONDS)


async def alert_analysis_loop():
    """
    Background task that periodically analyzes system state and generates alerts.
    
    Runs every 60 seconds and broadcasts alerts via WebSocket.
    """
    while True:
        try:
            # Get database session
            async for db in get_db():
                # Analyze system state and generate alerts
                alerts = await analyze_system_state(db)
                
                # Broadcast new alerts via WebSocket
                for alert in alerts:
                    await alert_manager.broadcast_alert(alert)
                
                break  # Exit the async for loop after one iteration
            
            # Wait for next interval (60 seconds)
            await asyncio.sleep(60)
            
        except Exception as e:
            # Log error but keep loop running
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in alert analysis loop: {e}")
            await asyncio.sleep(60)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    await init_db()
    
    # Start telemetry broadcast background task
    telemetry_task = asyncio.create_task(telemetry_broadcast_loop())
    
    # Start alert analysis background task
    alert_task = asyncio.create_task(alert_analysis_loop())
    
    # Start AI Global Worker if enabled
    ai_worker_task = None
    if settings.AI_WORKER_ENABLED:
        ai_worker_task = await start_ai_worker_loop(
            db_factory=get_db,
            interval_seconds=settings.AI_WORKER_INTERVAL_SECONDS
        )
    
    yield
    
    # Shutdown
    # Cancel telemetry task
    telemetry_task.cancel()
    try:
        await telemetry_task
    except asyncio.CancelledError:
        pass
    
    # Cancel alert task
    alert_task.cancel()
    try:
        await alert_task
    except asyncio.CancelledError:
        pass
    
    # Stop AI Worker
    if ai_worker_task:
        await stop_ai_worker_loop()
        try:
            await ai_worker_task
        except asyncio.CancelledError:
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

# Dashboard AI endpoints (PASO 6.3)
app.include_router(dashboard_ai_router, prefix="/dashboard", tags=["dashboard_ai"])

# Dashboard Actions endpoints (PASO 6.3)
app.include_router(dashboard_actions_router, prefix="/dashboard", tags=["dashboard_actions"])

# Dashboard AI Integration endpoints (PASO 8.0)
app.include_router(dashboard_ai_integration_router, prefix="/dashboard", tags=["dashboard_ai_integration"])

# Live Telemetry WebSocket endpoint (PASO 6.4)
app.include_router(telemetry_router, prefix="/telemetry", tags=["telemetry"])

# Alerting Engine endpoints (PASO 6.5)
app.include_router(alerting_router, tags=["alerting"])

# Auth endpoints (PASO 6.6)
app.include_router(auth_router, tags=["auth"])

# AI Global Worker endpoints (PASO 7.0)
app.include_router(ai_global_router, tags=["ai_global_worker"])

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
