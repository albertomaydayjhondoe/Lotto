"""Suno API Generator Stub

Mock implementation of Suno music generation API.
Returns realistic-looking responses without making actual API calls.
"""

import asyncio
import hashlib
from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel


class GenerationParams(BaseModel):
    """Parameters for Suno generation request."""
    prompt: str
    make_instrumental: bool = False
    model_version: str = "chirp-v3-5"
    wait_audio: bool = True
    
    # Creative parameters
    genre: Optional[str] = None
    mood: Optional[str] = None
    energy: Optional[int] = None  # 1-10
    bpm: Optional[int] = None
    key: Optional[str] = None


class GenerationResult(BaseModel):
    """Result from Suno generation."""
    id: str
    status: str  # "pending", "processing", "complete", "failed"
    audio_url: Optional[str] = None
    video_url: Optional[str] = None
    metadata: Dict
    duration_seconds: Optional[float] = None
    created_at: datetime


class SunoGeneratorStub:
    """
    Mock Suno API client for STUB mode.
    
    Simulates realistic generation behavior:
    - Async generation with realistic delays
    - Deterministic URLs based on prompt hash
    - Metadata extraction from parameters
    - Quality scoring simulation
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize stub generator.
        
        Args:
            api_key: Ignored in STUB mode (for API compatibility)
        """
        self.api_key = api_key  # Stored but unused in STUB
        self.base_url = "https://studio-api.suno.ai/api"  # Real Suno endpoint (not called)
    
    async def generate(self, params: GenerationParams) -> GenerationResult:
        """
        Generate music from text prompt.
        
        Args:
            params: Generation parameters
            
        Returns:
            GenerationResult with mock data
        """
        # Simulate API latency (20-40ms for STUB)
        await asyncio.sleep(0.03)
        
        # Generate deterministic ID from prompt
        prompt_hash = hashlib.md5(params.prompt.encode()).hexdigest()[:12]
        generation_id = f"suno_stub_{prompt_hash}"
        
        # Extract metadata
        metadata = {
            "prompt": params.prompt,
            "model": params.model_version,
            "instrumental": params.make_instrumental,
            "genre": params.genre or "auto-detected",
            "mood": params.mood or "neutral",
            "energy": params.energy or 7,
            "bpm": params.bpm or 140,
            "key": params.key or "C# minor",
            "generation_date": datetime.utcnow().isoformat(),
        }
        
        # Mock audio URL (realistic format)
        audio_url = f"https://cdn1.suno.ai/audio/{generation_id}.mp3"
        video_url = f"https://cdn1.suno.ai/video/{generation_id}.mp4"
        
        # Simulate duration (2:30 - 3:30 minutes)
        duration = 150 + (hash(params.prompt) % 60)
        
        return GenerationResult(
            id=generation_id,
            status="complete",
            audio_url=audio_url,
            video_url=video_url,
            metadata=metadata,
            duration_seconds=duration,
            created_at=datetime.utcnow()
        )
    
    async def get_generation_status(self, generation_id: str) -> str:
        """
        Check status of ongoing generation.
        
        Args:
            generation_id: ID from previous generate() call
            
        Returns:
            Status string
        """
        # STUB always returns "complete" immediately
        await asyncio.sleep(0.01)
        return "complete"
    
    async def get_generation(self, generation_id: str) -> Optional[GenerationResult]:
        """
        Retrieve completed generation by ID.
        
        Args:
            generation_id: ID from previous generate() call
            
        Returns:
            GenerationResult if found (STUB always returns mock data)
        """
        await asyncio.sleep(0.01)
        
        # In STUB mode, reconstruct from ID
        return GenerationResult(
            id=generation_id,
            status="complete",
            audio_url=f"https://cdn1.suno.ai/audio/{generation_id}.mp3",
            video_url=f"https://cdn1.suno.ai/video/{generation_id}.mp4",
            metadata={
                "stub_note": "Reconstructed from ID in STUB mode",
                "bpm": 140,
                "key": "C# minor",
            },
            duration_seconds=180,
            created_at=datetime.utcnow()
        )
    
    async def list_generations(self, limit: int = 10) -> List[GenerationResult]:
        """
        List recent generations.
        
        Args:
            limit: Maximum results to return
            
        Returns:
            List of GenerationResult (STUB returns empty list)
        """
        await asyncio.sleep(0.01)
        return []  # STUB has no persistent storage
    
    def get_credits_remaining(self) -> Dict:
        """
        Check API credit balance.
        
        Returns:
            Credit info dict (STUB returns unlimited)
        """
        return {
            "credits_total": 999999,
            "credits_used": 0,
            "credits_remaining": 999999,
            "billing_cycle_end": "2099-12-31",
            "note": "STUB mode - no real billing"
        }
    
    async def cancel_generation(self, generation_id: str) -> bool:
        """
        Cancel in-progress generation.
        
        Args:
            generation_id: ID to cancel
            
        Returns:
            True if cancelled (STUB always succeeds)
        """
        await asyncio.sleep(0.01)
        return True


# Factory function
def get_suno_generator(api_key: Optional[str] = None) -> SunoGeneratorStub:
    """
    Get Suno generator instance.
    
    In production with real API:
    ```python
    from suno import SunoClient
    
    def get_suno_generator(api_key: str) -> SunoClient:
        return SunoClient(api_key=api_key)
    ```
    
    Args:
        api_key: API key (ignored in STUB)
        
    Returns:
        SunoGeneratorStub instance
    """
    return SunoGeneratorStub(api_key=api_key)
