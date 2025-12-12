"""Tests for Suno Generation module."""
import pytest
from backend.app.music_production_engine.suno_generation import (
    SunoGeneratorStub, GenerationParams, SunoRefineStub, GenerationCycleManager
)

@pytest.mark.asyncio
async def test_suno_generation():
    generator = SunoGeneratorStub()
    params = GenerationParams(prompt="trap beat", bpm=140)
    result = await generator.generate(params)
    assert result.status == "complete"
    assert result.audio_url.startswith("https://")
    assert result.duration_seconds > 0

@pytest.mark.asyncio
async def test_suno_refinement():
    refiner = SunoRefineStub()
    from backend.app.music_production_engine.suno_generation.refine_stub import RefineParams
    params = RefineParams(base_generation_id="gen_123", improvements=["Better mix"], iteration_number=2)
    result = await refiner.refine(params)
    assert result.metadata["iteration_number"] == 2
    assert result.metadata["quality_score"] > 70

@pytest.mark.asyncio
async def test_cycle_manager():
    manager = GenerationCycleManager()
    result = await manager.run_cycle("Create energetic trap beat")
    assert result.status.value == "complete"
    assert result.iterations_completed > 0
    assert result.final_quality_score > 0
