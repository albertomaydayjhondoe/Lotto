"""
Alerting Router

REST and WebSocket endpoints for alert management.
"""

from uuid import UUID
from fastapi import APIRouter, Depends, WebSocketDisconnect, WebSocket
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.core.database import get_db
from .models import AlertsListResponse, AlertResponse
from .service import get_alerts, get_recent_alerts, mark_alert_read, get_unread_count
from .engine import analyze_system_state
from .websocket import alert_manager

router = APIRouter(prefix="/alerting")
logger = logging.getLogger(__name__)


@router.get("/alerts", response_model=AlertsListResponse)
async def get_all_alerts(
    unread_only: bool = False,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """
    Get alerts from system.
    
    Args:
        unread_only: Only return unread alerts
        limit: Maximum number of alerts to return
        db: Database session
        
    Returns:
        List of alerts with metadata
    """
    alerts = await get_alerts(db, unread_only=unread_only, limit=limit)
    unread_count = await get_unread_count(db)
    
    return AlertsListResponse(
        alerts=[AlertResponse(**alert.model_dump()) for alert in alerts],
        total=len(alerts),
        unread_count=unread_count
    )


@router.get("/alerts/unread", response_model=AlertsListResponse)
async def get_unread_alerts(
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """
    Get only unread alerts.
    
    Args:
        limit: Maximum number of alerts to return
        db: Database session
        
    Returns:
        List of unread alerts
    """
    alerts = await get_alerts(db, unread_only=True, limit=limit)
    unread_count = len(alerts)
    
    return AlertsListResponse(
        alerts=[AlertResponse(**alert.model_dump()) for alert in alerts],
        total=unread_count,
        unread_count=unread_count
    )


@router.post("/alerts/{alert_id}/read")
async def mark_as_read(
    alert_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Mark an alert as read.
    
    Args:
        alert_id: Alert ID to mark as read
        db: Database session
        
    Returns:
        Success status
    """
    success = await mark_alert_read(db, alert_id)
    
    if not success:
        return {"success": False, "message": "Alert not found"}
    
    return {"success": True, "message": "Alert marked as read"}


@router.post("/run-analysis")
async def run_analysis(
    db: AsyncSession = Depends(get_db)
):
    """
    Manually trigger system analysis and generate alerts.
    
    Args:
        db: Database session
        
    Returns:
        List of generated alerts
    """
    alerts = await analyze_system_state(db)
    
    # Broadcast new alerts via WebSocket
    for alert in alerts:
        await alert_manager.broadcast_alert(alert)
    
    return {
        "success": True,
        "alerts_generated": len(alerts),
        "alerts": [AlertResponse(**alert.model_dump()) for alert in alerts]
    }


@router.get("/stats")
async def get_alert_stats(
    db: AsyncSession = Depends(get_db)
):
    """
    Get alert statistics.
    
    Args:
        db: Database session
        
    Returns:
        Alert statistics
    """
    unread_count = await get_unread_count(db)
    
    return {
        "unread_count": unread_count,
        "active_connections": alert_manager.get_connection_count(),
        "has_subscribers": alert_manager.has_subscribers()
    }


@router.websocket("/ws/alerts")
async def alerts_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for real-time alert notifications.
    
    Clients connect to this endpoint and receive Alert objects
    whenever new alerts are generated.
    
    Protocol:
    - Client connects
    - Server sends alerts as they are generated
    - Client can send ping messages to keep connection alive
    - Connection closes on disconnect
    
    Args:
        websocket: WebSocket connection
    """
    client_id = f"{websocket.client.host}:{websocket.client.port}"
    logger.info(f"Alert client connecting: {client_id}")
    
    try:
        # Register connection
        await alert_manager.connect(websocket)
        logger.info(f"Alert client connected: {client_id} (total: {alert_manager.get_connection_count()})")
        
        # Keep connection alive and handle ping/pong
        while True:
            try:
                # Wait for client messages (ping, etc.)
                data = await websocket.receive_text()
                
                # Handle ping
                if data == "ping":
                    await websocket.send_text("pong")
                    
            except WebSocketDisconnect:
                raise  # Propagate disconnect to outer handler
            except Exception as e:
                logger.error(f"Error in alert WebSocket loop for {client_id}: {e}")
                break
                
    except WebSocketDisconnect:
        logger.info(f"Alert client disconnected: {client_id}")
    except Exception as e:
        logger.error(f"Unexpected error in alert WebSocket for {client_id}: {e}")
    finally:
        # Unregister connection
        await alert_manager.disconnect(websocket)
        logger.info(f"Alert client cleaned up: {client_id} (remaining: {alert_manager.get_connection_count()})")
