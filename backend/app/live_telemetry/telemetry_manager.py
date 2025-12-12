"""
Telemetry Manager

Manages WebSocket connections and broadcasts telemetry data.
"""

import asyncio
import json
from typing import Set
from fastapi import WebSocket
from datetime import datetime

from .models import TelemetryPayload


class TelemetryManager:
    """
    Manages WebSocket subscribers and broadcasts telemetry updates.
    
    Features:
    - Multiple concurrent subscribers
    - Automatic cleanup of dead connections
    - Efficient JSON broadcasting
    - Thread-safe operation
    """
    
    def __init__(self):
        """Initialize telemetry manager."""
        self.active_connections: Set[WebSocket] = set()
        self._lock = asyncio.Lock()
        self._last_payload: TelemetryPayload | None = None
    
    async def connect(self, websocket: WebSocket):
        """
        Register a new WebSocket connection.
        
        Args:
            websocket: WebSocket connection to register
        """
        await websocket.accept()
        async with self._lock:
            self.active_connections.add(websocket)
        
        # Send current state immediately if available
        if self._last_payload:
            try:
                await websocket.send_json(self._last_payload.model_dump(mode='json'))
            except Exception:
                pass  # Connection might be already closed
    
    async def disconnect(self, websocket: WebSocket):
        """
        Unregister a WebSocket connection.
        
        Args:
            websocket: WebSocket connection to unregister
        """
        async with self._lock:
            self.active_connections.discard(websocket)
    
    async def broadcast(self, payload: TelemetryPayload):
        """
        Broadcast telemetry payload to all connected clients.
        
        Args:
            payload: TelemetryPayload to broadcast
        """
        # Store last payload for new connections
        self._last_payload = payload
        
        # Convert to JSON once
        json_data = payload.model_dump(mode='json')
        
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
telemetry_manager = TelemetryManager()
