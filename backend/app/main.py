"""
FastAPI main application entry point.
Implements the Orquestador OpenAPI specification.
"""
import asyncio
import logging
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
from app.visual_analytics import router as visual_analytics_router
from app.core.config import settings
from app.core.database import init_db, get_db

# Meta Ads modules (PASO 10.5, 10.6, 10.7, 10.8, 10.9, 10.10, 10.11, 10.12, 10.13, 10.15)
from app.meta_ads_orchestrator.roas_router import router as roas_router
from app.meta_optimization.routes import router as optimization_router
from app.meta_autonomous.routes import router as autonomous_router
from app.meta_insights_collector.router import router as insights_router
from app.meta_insights_collector.scheduler import get_scheduler, start_meta_insights_scheduler
from app.meta_autopublisher.router import router as autopublisher_router
from app.meta_budget_spike.router import router as budget_spike_router
from app.meta_creative_variants.router import router as creative_variants_router
from app.meta_full_cycle.router import router as full_cycle_router
from app.meta_full_cycle.scheduler import start_meta_cycle_scheduler, stop_meta_cycle_scheduler
from app.meta_targeting_optimizer.router import router as targeting_optimizer_router
from app.meta_targeting_optimizer.scheduler import start_targeting_optimizer_scheduler, stop_targeting_optimizer_scheduler
from app.meta_creative_intelligence.router import router as creative_intelligence_router
from app.meta_creative_intelligence.scheduler import start_creative_intelligence_scheduler, stop_creative_intelligence_scheduler
from app.meta_creative_analyzer.router import router as creative_analyzer_router
from app.meta_creative_analyzer.scheduler import start_creative_analyzer_scheduler, stop_creative_analyzer_scheduler


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
    
    # Start Meta Autonomous Worker if enabled (PASO 10.7)
    meta_auto_worker_task = None
    if settings.META_AUTO_ENABLED:
        from app.meta_autonomous.auto_worker import MetaAutoWorker
        from app.meta_autonomous.routes import set_worker
        from app.core.database import AsyncSessionLocal
        
        meta_auto_worker = MetaAutoWorker(AsyncSessionLocal)
        set_worker(meta_auto_worker)
        meta_auto_worker.start()
        meta_auto_worker_task = meta_auto_worker._task
    
    # Start Meta Insights Scheduler if enabled (PASO 10.7)
    meta_insights_task = None
    try:
        meta_insights_task = await start_meta_insights_scheduler(
            mode=settings.META_INSIGHTS_MODE,
            interval_minutes=settings.META_INSIGHTS_SYNC_INTERVAL_MINUTES
        )
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.warning(f"Meta Insights Scheduler not started: {e}")
    
    # Start Meta Full Cycle Scheduler if enabled (PASO 10.11)
    meta_cycle_task = None
    if getattr(settings, 'META_CYCLE_ENABLED', False):
        try:
            meta_cycle_task = await start_meta_cycle_scheduler()
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.warning(f"Meta Full Cycle Scheduler not started: {e}")
    
    # Start Meta Targeting Optimizer Scheduler if enabled (PASO 10.12)
    targeting_optimizer_task = None
    if getattr(settings, 'META_TARGETING_ENABLED', False):
        try:
            targeting_optimizer_task = await start_targeting_optimizer_scheduler()
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.warning(f"Meta Targeting Optimizer Scheduler not started: {e}")
    
    # Start Meta Creative Intelligence Scheduler if enabled (PASO 10.13)
    creative_intelligence_task = None
    if getattr(settings, 'CREATIVE_INTELLIGENCE_ENABLED', False):
        try:
            creative_intelligence_task = await start_creative_intelligence_scheduler(
                interval_hours=getattr(settings, 'CREATIVE_INTELLIGENCE_INTERVAL_HOURS', 12),
                mode=getattr(settings, 'CREATIVE_INTELLIGENCE_MODE', 'stub')
            )
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.warning(f"Meta Creative Intelligence Scheduler not started: {e}")
    
    # Start Meta Creative Analyzer Scheduler if enabled (PASO 10.15)
    creative_analyzer_task = None
    if getattr(settings, 'CREATIVE_ANALYZER_ENABLED', False):
        try:
            creative_analyzer_task = await start_creative_analyzer_scheduler(
                interval_hours=getattr(settings, 'CREATIVE_ANALYZER_INTERVAL_HOURS', 24),
                mode=getattr(settings, 'CREATIVE_ANALYZER_MODE', 'stub')
            )
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.warning(f"Meta Creative Analyzer Scheduler not started: {e}")
    
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
    
    # Stop Meta Autonomous Worker
    if meta_auto_worker_task:
        try:
            meta_auto_worker_task.cancel()
            await meta_auto_worker_task
        except asyncio.CancelledError:
            pass
    
    # Stop Meta Insights Scheduler
    # Stop Meta Full Cycle Scheduler
    if meta_cycle_task:
        try:
            await stop_meta_cycle_scheduler(meta_cycle_task)
        except asyncio.CancelledError:
            pass
    
    # Stop Meta Targeting Optimizer Scheduler
    if targeting_optimizer_task:
        try:
            await stop_targeting_optimizer_scheduler(targeting_optimizer_task)
        except asyncio.CancelledError:
            pass
    
    # Stop Meta Creative Intelligence Scheduler
    if creative_intelligence_task:
        try:
            await stop_creative_intelligence_scheduler(creative_intelligence_task)
        except asyncio.CancelledError:
            pass
    
    # Stop Meta Creative Analyzer Scheduler
    if creative_analyzer_task:
        try:
            await stop_creative_analyzer_scheduler(creative_analyzer_task)
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

# Visual Analytics endpoints (PASO 8.3)
app.include_router(visual_analytics_router, tags=["visual_analytics"])

# Meta Ads ROAS Engine endpoints (PASO 10.5)
app.include_router(roas_router, tags=["meta_roas"])

# Meta Optimization Loop endpoints (PASO 10.6)
app.include_router(optimization_router, tags=["meta_optimization"])
# Full Autonomous Cycle endpoints (PASO 10.11)
app.include_router(full_cycle_router, prefix="/meta/full-cycle", tags=["meta_full_cycle"])

# Targeting Optimizer endpoints (PASO 10.12)
app.include_router(targeting_optimizer_router, prefix="/meta/targeting", tags=["meta_targeting_optimizer"])

# Creative Intelligence endpoints (PASO 10.13)
app.include_router(creative_intelligence_router, prefix="/meta/creative-intelligence", tags=["meta_creative_intelligence"])

# Creative Analyzer endpoints (PASO 10.15)
app.include_router(creative_analyzer_router, prefix="/meta/creative-analyzer", tags=["meta_creative_analyzer"])

# Debug endpoints (DEVELOPMENT ONLY)
# Meta Insights Collector endpoints (PASO 10.7)
app.include_router(insights_router, tags=["meta_insights"])

# AutoPublisher endpoints (PASO 10.8)
app.include_router(autopublisher_router, prefix="/meta/autopilot", tags=["meta_autopublisher"])

# Budget SPIKE Manager endpoints (PASO 10.9)
app.include_router(budget_spike_router, prefix="/meta/budget-spikes", tags=["meta_budget_spike"])

# Creative Variants Engine endpoints (PASO 10.10)
app.include_router(creative_variants_router, prefix="/meta/creative-variants", tags=["meta_creative_variants"])

# Full Autonomous Cycle endpoints (PASO 10.11)
app.include_router(full_cycle_router, prefix="/meta/full-cycle", tags=["meta_full_cycle"])

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
    """
    Health check endpoint for production monitoring.
    Verifies backend is running and database is accessible.
    """
    from sqlalchemy import text
    
    health_status = {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
    }
    
    # Check database connectivity
    try:
        async for db in get_db():
            # Simple query to verify DB connection
            await db.execute(text("SELECT 1"))
            health_status["database"] = "connected"
            break
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["database"] = "disconnected"
        health_status["error"] = str(e)
    
    return health_status
