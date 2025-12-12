"""Tests for Integration module."""
import pytest
from backend.app.music_production_engine.integration import (
    MetaIntegrationHooks, ContentEngineHooks, CommunityManagerHooks, OrchestratorHooks
)

@pytest.mark.asyncio
async def test_meta_hooks():
    hooks = MetaIntegrationHooks()
    result = await hooks.notify_generation_complete("gen_123", {})
    assert result is True
    
    prefs = await hooks.fetch_user_preferences("user_123")
    assert prefs is not None

@pytest.mark.asyncio
async def test_content_engine_hooks():
    hooks = ContentEngineHooks()
    asset_id = await hooks.register_music_asset("https://audio.mp3", {})
    assert len(asset_id) > 0
    
    similar = await hooks.get_similar_content(asset_id)
    assert len(similar) > 0

@pytest.mark.asyncio
async def test_community_manager_hooks():
    hooks = CommunityManagerHooks()
    post_id = await hooks.publish_music_to_feed("music_123", "Check this out")
    assert len(post_id) > 0

@pytest.mark.asyncio
async def test_orchestrator_hooks():
    hooks = OrchestratorHooks()
    job_id = await hooks.create_music_job({"prompt": "test"})
    assert len(job_id) > 0
    
    status = await hooks.get_job_status(job_id)
    assert status is not None
