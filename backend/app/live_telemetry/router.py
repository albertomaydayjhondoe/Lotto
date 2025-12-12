"""
Live Telemetry WebSocket Router

Provides WebSocket endpoint for real-time telemetry streaming.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import logging

from .telemetry_manager import telemetry_manager

router = APIRouter(prefix="/live")
logger = logging.getLogger(__name__)


@router.websocket("/ws/telemetry")
async def telemetry_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for streaming telemetry data.
    
    Clients connect to this endpoint and receive TelemetryPayload
    updates every TELEMETRY_INTERVAL_SECONDS.
    
    Protocol:
    - Client connects
    - Server immediately sends current state
    - Server broadcasts updates every N seconds
    - Client can send ping messages to keep connection alive
    - Connection closes on disconnect
    
    Args:
        websocket: WebSocket connection
    """
    client_id = f"{websocket.client.host}:{websocket.client.port}"
    logger.info(f"Telemetry client connecting: {client_id}")
    
    try:
        # Register connection and send current state
        await telemetry_manager.connect(websocket)
        logger.info(f"Telemetry client connected: {client_id} (total: {telemetry_manager.get_connection_count()})")
        
        # Keep connection alive and handle ping/pong
        while True:
            try:
                # Wait for client messages (ping, etc.)
                # This keeps the connection alive and allows client-side keepalive
                data = await websocket.receive_text()
                
                # Optional: handle specific client messages
                if data == "ping":
                    await websocket.send_text("pong")
                    
            except WebSocketDisconnect:
                raise  # Propagate disconnect to outer handler
            except Exception as e:
                logger.error(f"Error in telemetry WebSocket loop for {client_id}: {e}")
                break
                
    except WebSocketDisconnect:
        logger.info(f"Telemetry client disconnected: {client_id}")
    except Exception as e:
        logger.error(f"Unexpected error in telemetry WebSocket for {client_id}: {e}")
    finally:
        # Unregister connection
        await telemetry_manager.disconnect(websocket)
        logger.info(f"Telemetry client cleaned up: {client_id} (remaining: {telemetry_manager.get_connection_count()})")


@router.get("/stats")
async def telemetry_stats():
    """
    Get telemetry server statistics.
    
    Returns:
        Dictionary with connection stats
    """
    return {
        "active_connections": telemetry_manager.get_connection_count(),
        "has_subscribers": telemetry_manager.has_subscribers()
    }
