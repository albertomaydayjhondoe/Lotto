"""
Alert WebSocket Manager

Manages WebSocket connections for real-time alert notifications.
"""

import asyncio
import json
from typing import Set
from fastapi import WebSocket
from datetime import datetime

from .models import Alert


class AlertManager:
    """
    Manages WebSocket subscribers for alert notifications.
    
    Similar to TelemetryManager but specialized for alerts.
    """
    
    def __init__(self):
        """Initialize alert manager."""
        self.active_connections: Set[WebSocket] = set()
        self._lock = asyncio.Lock()
    
    async def connect(self, websocket: WebSocket):
        """
        Register a new WebSocket connection.
        
        Args:
            websocket: WebSocket connection to register
        """
        await websocket.accept()
        async with self._lock:
            self.active_connections.add(websocket)
    
    async def disconnect(self, websocket: WebSocket):
        """
        Unregister a WebSocket connection.
        
        Args:
            websocket: WebSocket connection to unregister
        """
        async with self._lock:
            self.active_connections.discard(websocket)
    
    async def broadcast_alert(self, alert: Alert):
        """
        Broadcast alert to all connected clients.
        
        Args:
            alert: Alert to broadcast
        """
        # Convert to JSON once
        json_data = alert.model_dump(mode='json')
        
        # Track dead connections
        dead_connections = set()
        
        # Broadcast to all connections
        async with self._lock:
            for connection in self.active_connections.copy():
                try:
                    await connection.send_json(json_data)
                except Exception:
                    # Connection is dead, mark for removal
                    dead_connections.add(connection)
        
        # Clean up dead connections
        if dead_connections:
            async with self._lock:
                self.active_connections -= dead_connections
    
    def get_connection_count(self) -> int:
        """
        Get number of active connections.
        
        Returns:
            Number of active WebSocket connections
        """
        return len(self.active_connections)
    
    def has_subscribers(self) -> bool:
        """
        Check if there are any active subscribers.
        
        Returns:
            True if there are active connections
        """
        return len(self.active_connections) > 0


# Global singleton instance
alert_manager = AlertManager()
