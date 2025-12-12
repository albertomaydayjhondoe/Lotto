"""CREPE Pitch Detection Stub

Mock implementation of CREPE monophonic pitch tracker.
Provides pitch tracking and analysis for vocals/melody.
"""

import asyncio
from typing import Dict, List, Optional
from pydantic import BaseModel
import numpy as np


class PitchFrame(BaseModel):
    """Single frame of pitch analysis."""
    time: float  # Seconds
    frequency: float  # Hz
    confidence: float  # 0-1
    note: Optional[str] = None  # E.g., "C#4"


class PitchContour(BaseModel):
    """Pitch trajectory analysis."""
    mean_frequency: float
    std_frequency: float
    frequency_range: float  # Max - min
    vibrato_rate: Optional[float] = None  # Hz
    vibrato_extent: Optional[float] = None  # Cents
    pitch_stability: float  # 0-1


class CrepeResult(BaseModel):
    """Complete CREPE analysis."""
    frames: List[PitchFrame]
    contour: PitchContour
    voiced_percentage: float  # Percentage of frames with voice detected
    mean_confidence: float
    key_detected: str
    vocal_range: str  # E.g., "C3 - G5"
    metadata: Dict


class CrepeStub:
    """
    Mock CREPE pitch detector.
    
    Real CREPE usage:
    ```python
    import crepe
    
    time, frequency, confidence, activation = crepe.predict(
        audio, sr=44100, model_capacity='full'
    )
    ```
    """
    
    def __init__(self, model_capacity: str = "full"):
        """
        Initialize stub detector.
        
        Args:
            model_capacity: Model size (tiny/small/medium/large/full) - ignored in STUB
        """
        self.model_capacity = model_capacity
    
    async def analyze(
        self,
        audio_url: str,
        step_size: int = 10  # ms between frames
    ) -> CrepeResult:
        """
        Analyze pitch trajectory.
        
        Args:
            audio_url: URL or path to audio file
            step_size: Milliseconds between analysis frames
            
        Returns:
            CrepeResult with mock pitch data
        """
        # Simulate processing time
        await asyncio.sleep(0.05)
        
        # Generate deterministic results
        url_hash = hash(audio_url)
        
        # Generate pitch frames (180 seconds / 0.01 = 18000 frames, but we'll sample)
        num_frames = 100  # Reduced for performance
        frames = []
        
        base_freq = 220 + (url_hash % 200)  # A3 to G#4 range
        
        for i in range(num_frames):
            time = i * 1.8  # Spread across 180 seconds
            
            # Add some pitch variation (vibrato simulation)
            freq_variation = np.sin(i * 0.3) * 10
            frequency = base_freq + freq_variation + (i % 20)
            
            # Confidence varies
            confidence = 0.75 + (hash(f"{url_hash}_{i}") % 25) / 100
            
            # Convert frequency to note
            note = self._frequency_to_note(frequency)
            
            frames.append(PitchFrame(
                time=round(time, 2),
                frequency=round(frequency, 2),
                confidence=round(confidence, 3),
                note=note
            ))
        
        # Calculate contour statistics
        frequencies = [f.frequency for f in frames]
        confidences = [f.confidence for f in frames]
        
        contour = PitchContour(
            mean_frequency=round(np.mean(frequencies), 2),
            std_frequency=round(np.std(frequencies), 2),
            frequency_range=round(max(frequencies) - min(frequencies), 2),
            vibrato_rate=5.5 + (url_hash % 15) / 10,
            vibrato_extent=20 + (url_hash % 30),
            pitch_stability=0.75 + (url_hash % 20) / 100
        )
        
        # Detect key (simplified)
        keys = ["C major", "C# minor", "D major", "E minor", "F major", "G major"]
        key_detected = keys[url_hash % len(keys)]
        
        # Vocal range
        min_note = self._frequency_to_note(min(frequencies))
        max_note = self._frequency_to_note(max(frequencies))
        vocal_range = f"{min_note} - {max_note}"
        
        return CrepeResult(
            frames=frames,
            contour=contour,
            voiced_percentage=85 + (url_hash % 15),
            mean_confidence=round(np.mean(confidences), 3),
            key_detected=key_detected,
            vocal_range=vocal_range,
            metadata={
                "model": f"crepe_{self.model_capacity}",
                "step_size_ms": step_size,
                "stub_mode": True
            }
        )
    
    def _frequency_to_note(self, frequency: float) -> str:
        """
        Convert frequency to note name.
        
        Args:
            frequency: Frequency in Hz
            
        Returns:
            Note name (e.g., "C#4")
        """
        if frequency <= 0:
            return "N/A"
        
        # A4 = 440 Hz
        a4 = 440.0
        notes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        
        # Calculate semitones from A4
        semitones_from_a4 = 12 * np.log2(frequency / a4)
        semitone = int(round(semitones_from_a4))
        
        # A4 is note 9 (A) in octave 4
        note_index = (9 + semitone) % 12
        octave = 4 + (9 + semitone) // 12
        
        return f"{notes[note_index]}{octave}"
    
    async def analyze_vocals_only(
        self,
        vocals_url: str,
        detailed: bool = True
    ) -> CrepeResult:
        """
        Analyze isolated vocals (optimized for vocal pitch tracking).
        
        Args:
            vocals_url: URL to vocals stem
            detailed: If True, return full frame data
            
        Returns:
            CrepeResult
        """
        result = await self.analyze(vocals_url, step_size=10 if detailed else 50)
        
        if not detailed:
            # Reduce frame count for quick analysis
            result.frames = result.frames[::5]
        
        return result
    
    def get_pitch_summary(self, audio_url: str) -> Dict:
        """
        Quick pitch summary (synchronous STUB).
        
        Args:
            audio_url: Audio file URL
            
        Returns:
            Summary dict
        """
        url_hash = hash(audio_url)
        base_freq = 220 + (url_hash % 200)
        
        return {
            "mean_pitch_hz": base_freq,
            "pitch_range_hz": 150 + (url_hash % 100),
            "confidence": 0.85 + (url_hash % 15) / 100,
            "key": ["C major", "D minor", "F major"][url_hash % 3]
        }


# Factory function
def get_crepe_detector(model_capacity: str = "full") -> CrepeStub:
    """
    Get CREPE detector instance.
    
    Args:
        model_capacity: Model size
        
    Returns:
        CrepeStub instance
    """
    return CrepeStub(model_capacity=model_capacity)
