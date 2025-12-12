"""Producer Chat Router - FastAPI Endpoints (STUB)

Exposes producer conversation endpoints for frontend integration.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, List
from . import get_or_create_session, close_session

router = APIRouter()


class ChatMessage(BaseModel):
    """User message to producer."""

    message: str
    context: Optional[Dict] = None


class ContextUpdate(BaseModel):
    """Creative context update."""

    aesthetic: Optional[str] = None
    energy_level: Optional[int] = None
    tone: Optional[str] = None
    influences: Optional[List[str]] = None
    emotional_intent: Optional[str] = None


@router.post("/chat/send")
async def send_message_to_producer(
    session_id: Optional[str] = None, payload: ChatMessage = None
):
    """
    Send message to AI producer (ChatGPT-5 STUB).
    
    Returns producer response with suggestions and Suno prompt.
    """
    try:
        session = get_or_create_session(session_id)
        response = await session.send_message(payload.message, payload.context)
        return {"status": "success", "data": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Producer chat error: {str(e)}")


@router.post("/chat/context")
async def update_creative_context(session_id: str, updates: ContextUpdate):
    """Update creative context for session."""
    try:
        session = get_or_create_session(session_id)
        session.update_context(updates.dict(exclude_unset=True))
        return {
            "status": "success",
            "context": session.creative_context,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Context update error: {str(e)}")


@router.get("/chat/history/{session_id}")
async def get_conversation_history(session_id: str):
    """Retrieve full conversation history for session."""
    try:
        session = get_or_create_session(session_id)
        return {
            "status": "success",
            "session_id": session_id,
            "history": session.get_conversation_history(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"History retrieval error: {str(e)}")


@router.delete("/chat/session/{session_id}")
async def close_chat_session(session_id: str):
    """Close and cleanup chat session."""
    success = close_session(session_id)
    if success:
        return {"status": "success", "message": "Session closed"}
    raise HTTPException(status_code=404, detail="Session not found")


@router.get("/chat/export/{session_id}")
async def export_session_data(session_id: str):
    """Export full session data for persistence."""
    try:
        session = get_or_create_session(session_id)
        return {
            "status": "success",
            "export": session.export_session(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export error: {str(e)}")
