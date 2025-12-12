"""Demucs Source Separation Stub

Mock implementation of Demucs for audio source separation.
Simulates splitting audio into vocals, drums, bass, and other.
"""

import asyncio
from typing import Dict, List
from pydantic import BaseModel


class SeparatedSources(BaseModel):
    """Separated audio sources."""
    vocals_url: str
    drums_url: str
    bass_url: str
    other_url: str  # Includes melody, synths, etc.
    
    # Quality metrics for each stem
    vocals_quality: float  # 0-100
    drums_quality: float
    bass_quality: float
    other_quality: float
    
    # Isolation scores (how clean the separation is)
    vocals_isolation: float  # 0-1
    drums_isolation: float
    bass_isolation: float
    other_isolation: float


class StemAnalysis(BaseModel):
    """Individual stem characteristics."""
    stem_type: str  # "vocals", "drums", "bass", "other"
    url: str
    duration_seconds: float
    rms_energy: float  # Root mean square energy
    peak_amplitude: float
    spectral_centroid: float
    presence_in_mix: float  # 0-1, how prominent this stem is


class DemucsResult(BaseModel):
    """Complete Demucs separation result."""
    original_url: str
    separated: SeparatedSources
    stem_analyses: List[StemAnalysis]
    separation_quality: float  # Overall quality score
    processing_time_ms: int
    metadata: Dict


class DemucsStub:
    """
    Mock Demucs source separator.
    
    Real Demucs usage:
    ```python
    from demucs import pretrained
    from demucs.apply import apply_model
    
    model = pretrained.get_model('htdemucs')
    sources = apply_model(model, audio_tensor)
    # sources: [vocals, drums, bass, other]
    ```
    """
    
    def __init__(self, model_name: str = "htdemucs"):
        """
        Initialize stub separator.
        
        Args:
            model_name: Model to use (ignored in STUB)
        """
        self.model_name = model_name
    
    async def separate(self, audio_url: str) -> DemucsResult:
        """
        Separate audio into stems.
        
        Args:
            audio_url: URL or path to audio file
            
        Returns:
            DemucsResult with mock separated stems
        """
        # Simulate processing time (50-80ms)
        await asyncio.sleep(0.065)
        
        # Generate deterministic results
        url_hash = hash(audio_url)
        
        # Generate stem URLs
        base_id = audio_url.split("/")[-1].replace(".mp3", "")
        
        separated = SeparatedSources(
            vocals_url=f"https://cdn1.suno.ai/stems/{base_id}_vocals.wav",
            drums_url=f"https://cdn1.suno.ai/stems/{base_id}_drums.wav",
            bass_url=f"https://cdn1.suno.ai/stems/{base_id}_bass.wav",
            other_url=f"https://cdn1.suno.ai/stems/{base_id}_other.wav",
            vocals_quality=85 + (url_hash % 15),
            drums_quality=82 + (url_hash % 18),
            bass_quality=80 + (url_hash % 20),
            other_quality=83 + (url_hash % 17),
            vocals_isolation=0.85 + (url_hash % 15) / 100,
            drums_isolation=0.80 + (url_hash % 20) / 100,
            bass_isolation=0.78 + (url_hash % 22) / 100,
            other_isolation=0.82 + (url_hash % 18) / 100
        )
        
        # Stem analyses
        stem_analyses = [
            StemAnalysis(
                stem_type="vocals",
                url=separated.vocals_url,
                duration_seconds=180.0,
                rms_energy=0.25 + (url_hash % 20) / 100,
                peak_amplitude=0.85 + (url_hash % 15) / 100,
                spectral_centroid=2500 + (url_hash % 1500),
                presence_in_mix=0.75 + (url_hash % 20) / 100
            ),
            StemAnalysis(
                stem_type="drums",
                url=separated.drums_url,
                duration_seconds=180.0,
                rms_energy=0.30 + (url_hash % 25) / 100,
                peak_amplitude=0.90 + (url_hash % 10) / 100,
                spectral_centroid=3500 + (url_hash % 2000),
                presence_in_mix=0.70 + (url_hash % 25) / 100
            ),
            StemAnalysis(
                stem_type="bass",
                url=separated.bass_url,
                duration_seconds=180.0,
                rms_energy=0.28 + (url_hash % 22) / 100,
                peak_amplitude=0.88 + (url_hash % 12) / 100,
                spectral_centroid=180 + (url_hash % 120),
                presence_in_mix=0.65 + (url_hash % 30) / 100
            ),
            StemAnalysis(
                stem_type="other",
                url=separated.other_url,
                duration_seconds=180.0,
                rms_energy=0.22 + (url_hash % 18) / 100,
                peak_amplitude=0.82 + (url_hash % 18) / 100,
                spectral_centroid=1800 + (url_hash % 1200),
                presence_in_mix=0.60 + (url_hash % 35) / 100
            )
        ]
        
        # Overall separation quality (weighted average of isolation scores)
        overall_quality = (
            separated.vocals_isolation * 0.35 +
            separated.drums_isolation * 0.25 +
            separated.bass_isolation * 0.25 +
            separated.other_isolation * 0.15
        ) * 100
        
        return DemucsResult(
            original_url=audio_url,
            separated=separated,
            stem_analyses=stem_analyses,
            separation_quality=round(overall_quality, 1),
            processing_time_ms=65,
            metadata={
                "model": self.model_name,
                "version": "4.0.0",
                "stub_mode": True
            }
        )
    
    async def separate_batch(self, audio_urls: List[str]) -> List[DemucsResult]:
        """Separate multiple files in parallel."""
        tasks = [self.separate(url) for url in audio_urls]
        return await asyncio.gather(*tasks)
    
    def get_vocals_only(self, audio_url: str) -> str:
        """Quick vocal extraction (returns URL immediately in STUB)."""
        base_id = audio_url.split("/")[-1].replace(".mp3", "")
        return f"https://cdn1.suno.ai/stems/{base_id}_vocals.wav"
    
    def estimate_processing_time(self, duration_seconds: float) -> float:
        """
        Estimate processing time for given duration.
        
        Args:
            duration_seconds: Audio duration
            
        Returns:
            Estimated processing time in seconds
        """
        # Real Demucs: ~0.5-1.0x realtime on GPU
        # STUB: instant
        return 0.065  # Fixed 65ms in STUB mode


# Factory function
def get_demucs_separator(model_name: str = "htdemucs") -> DemucsStub:
    """
    Get Demucs separator instance.
    
    Args:
        model_name: Model to use
        
    Returns:
        DemucsStub instance
    """
    return DemucsStub(model_name=model_name)
