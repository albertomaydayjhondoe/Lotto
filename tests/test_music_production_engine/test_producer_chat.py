"""Tests for Producer Chat module."""
import pytest
from backend.app.music_production_engine.producer_chat import ProducerChatStub
from backend.app.music_production_engine.producer_chat.session_manager import create_session
from backend.app.music_production_engine.producer_chat.prompts import get_prompt

@pytest.mark.asyncio
async def test_producer_chat_send_message():
    chat = ProducerChatStub()
    response = await chat.send_message("Let's make a trap beat")
    assert "session_id" in response
    assert "message" in response
    assert response["message"]["role"] == "assistant"
    assert len(response["message"]["content"]) > 0

def test_session_creation():
    session = create_session({"genre": "hip-hop"})
    assert session.session_id is not None
    assert session.context["genre"] == "hip-hop"

def test_prompt_templates():
    system_prompt = get_prompt("system")
    assert "producer" in system_prompt.lower()
    assert len(system_prompt) > 100
