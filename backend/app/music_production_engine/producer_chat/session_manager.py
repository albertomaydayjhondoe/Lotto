"""Session Manager for Producer Chat

Handles conversation persistence, context management, and session lifecycle.
STUB implementation uses in-memory storage with realistic session management.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from uuid import uuid4


class ChatMessage:
    """Individual message in conversation."""
    
    def __init__(
        self,
        role: str,
        content: str,
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict] = None
    ):
        self.id = str(uuid4())
        self.role = role  # "user" or "assistant"
        self.content = content
        self.timestamp = timestamp or datetime.utcnow()
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


class ChatSession:
    """Complete conversation session with context."""
    
    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id or str(uuid4())
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.messages: List[ChatMessage] = []
        self.context: Dict = {}
        self.metadata: Dict = {
            "iteration_count": 0,
            "current_version_id": None,
            "aesthetic_defined": False,
            "generation_started": False,
        }
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict] = None) -> ChatMessage:
        """Add message to session history."""
        message = ChatMessage(role, content, metadata=metadata)
        self.messages.append(message)
        self.updated_at = datetime.utcnow()
        return message
    
    def get_messages(self, limit: Optional[int] = None) -> List[ChatMessage]:
        """Retrieve messages, optionally limited to most recent."""
        if limit:
            return self.messages[-limit:]
        return self.messages
    
    def get_conversation_history(self) -> List[Dict]:
        """Format messages for ChatGPT API format."""
        return [msg.to_dict() for msg in self.messages]
    
    def update_context(self, updates: Dict) -> None:
        """Update session context with new information."""
        self.context.update(updates)
        self.updated_at = datetime.utcnow()
    
    def get_context(self) -> Dict:
        """Retrieve current session context."""
        return self.context.copy()
    
    def increment_iteration(self) -> int:
        """Increment iteration counter and return new value."""
        self.metadata["iteration_count"] += 1
        self.updated_at = datetime.utcnow()
        return self.metadata["iteration_count"]
    
    def to_dict(self) -> Dict:
        """Serialize session to dictionary."""
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "message_count": len(self.messages),
            "context": self.context,
            "metadata": self.metadata
        }


class SessionManagerStub:
    """
    In-memory session manager for STUB mode.
    
    In production, this would interface with Redis or database
    for persistent session storage with TTL management.
    """
    
    def __init__(self, session_ttl_hours: int = 24):
        self._sessions: Dict[str, ChatSession] = {}
        self.session_ttl = timedelta(hours=session_ttl_hours)
    
    def create_session(self, initial_context: Optional[Dict] = None) -> ChatSession:
        """
        Create new chat session.
        
        Args:
            initial_context: Optional context to initialize session
            
        Returns:
            New ChatSession instance
        """
        session = ChatSession()
        if initial_context:
            session.update_context(initial_context)
        
        self._sessions[session.session_id] = session
        return session
    
    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """
        Retrieve session by ID.
        
        Args:
            session_id: UUID of session
            
        Returns:
            ChatSession if found and not expired, None otherwise
        """
        session = self._sessions.get(session_id)
        
        if not session:
            return None
        
        # Check TTL
        if datetime.utcnow() - session.updated_at > self.session_ttl:
            del self._sessions[session_id]
            return None
        
        return session
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete session by ID.
        
        Args:
            session_id: UUID of session to delete
            
        Returns:
            True if deleted, False if not found
        """
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False
    
    def list_sessions(self, limit: int = 10) -> List[Dict]:
        """
        List recent sessions (most recently updated first).
        
        Args:
            limit: Maximum number of sessions to return
            
        Returns:
            List of session summaries
        """
        # Clean up expired sessions
        now = datetime.utcnow()
        expired = [
            sid for sid, session in self._sessions.items()
            if now - session.updated_at > self.session_ttl
        ]
        for sid in expired:
            del self._sessions[sid]
        
        # Sort by updated_at descending
        sorted_sessions = sorted(
            self._sessions.values(),
            key=lambda s: s.updated_at,
            reverse=True
        )
        
        return [session.to_dict() for session in sorted_sessions[:limit]]
    
    def cleanup_expired_sessions(self) -> int:
        """
        Remove all expired sessions.
        
        Returns:
            Number of sessions cleaned up
        """
        now = datetime.utcnow()
        expired = [
            sid for sid, session in self._sessions.items()
            if now - session.updated_at > self.session_ttl
        ]
        
        for sid in expired:
            del self._sessions[sid]
        
        return len(expired)
    
    def get_session_stats(self) -> Dict:
        """
        Get statistics about active sessions.
        
        Returns:
            Statistics dictionary
        """
        if not self._sessions:
            return {
                "total_sessions": 0,
                "total_messages": 0,
                "avg_messages_per_session": 0.0,
                "oldest_session_age_hours": 0.0,
            }
        
        total_messages = sum(len(s.messages) for s in self._sessions.values())
        oldest_session = min(self._sessions.values(), key=lambda s: s.created_at)
        oldest_age = (datetime.utcnow() - oldest_session.created_at).total_seconds() / 3600
        
        return {
            "total_sessions": len(self._sessions),
            "total_messages": total_messages,
            "avg_messages_per_session": total_messages / len(self._sessions),
            "oldest_session_age_hours": round(oldest_age, 2),
        }


# Global instance for STUB mode
_session_manager = SessionManagerStub(session_ttl_hours=24)


def get_session_manager() -> SessionManagerStub:
    """
    Retrieve global session manager instance.
    
    In production with dependency injection:
    ```python
    from fastapi import Depends
    
    async def get_session_manager(
        redis: Redis = Depends(get_redis)
    ) -> SessionManager:
        return SessionManager(redis)
    ```
    
    Returns:
        SessionManagerStub instance
    """
    return _session_manager


# Convenience functions for direct access
def create_session(initial_context: Optional[Dict] = None) -> ChatSession:
    """Create new session via global manager."""
    return get_session_manager().create_session(initial_context)


def get_session(session_id: str) -> Optional[ChatSession]:
    """Retrieve session via global manager."""
    return get_session_manager().get_session(session_id)


def delete_session(session_id: str) -> bool:
    """Delete session via global manager."""
    return get_session_manager().delete_session(session_id)


def list_sessions(limit: int = 10) -> List[Dict]:
    """List sessions via global manager."""
    return get_session_manager().list_sessions(limit)


def cleanup_expired_sessions() -> int:
    """Clean up expired sessions via global manager."""
    return get_session_manager().cleanup_expired_sessions()
