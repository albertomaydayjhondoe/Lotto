"""Whisper Transcription Stub

Mock implementation of OpenAI Whisper for audio-to-text transcription.
Returns realistic lyrics with timestamps for flow analysis.
"""

import asyncio
from typing import Dict, List, Optional
from pydantic import BaseModel


class Word(BaseModel):
    """Individual word with timing."""
    word: str
    start: float  # Seconds
    end: float
    confidence: float


class Segment(BaseModel):
    """Transcription segment (typically one line/phrase)."""
    id: int
    start: float
    end: float
    text: str
    words: List[Word]
    avg_confidence: float


class TranscriptionResult(BaseModel):
    """Complete transcription result."""
    text: str  # Full lyrics
    segments: List[Segment]
    language: str
    duration: float
    metadata: Dict


class WhisperStub:
    """
    Mock Whisper transcription model.
    
    Real Whisper usage:
    ```python
    import whisper
    
    model = whisper.load_model("large-v3")
    result = model.transcribe(
        "audio.mp3",
        word_timestamps=True,
        language="en"
    )
    ```
    """
    
    # Mock lyrics database for STUB mode
    SAMPLE_LYRICS = [
        """Yeah I'm on my grind every day and night
Got the vision clear everything in sight
Moving through the city with my team so tight
Energy on high we gon reach the height

They been sleeping on me but I'm wide awake
Every move calculated never make mistake
Building up the empire brick by brick I take
Watch me rise to the top this is my fate

Running through the game like a champion
Money motivation I'm the one they banking on
Started from the bottom now my name is on
Every single playlist yeah I'm moving strong""",
        
        """Living life fast never looking back
Cash in my pocket got the whole stack
Enemies around me but I stay on track
Success is the mission that's a matter of fact

Pull up in the whip yeah it's all black
Confidence is high never showing slack
They can try to stop me but I counterattack
King of my domain put the crown on my back

Flow so sick need a remedy
Energy electric call it energy
Legacy I'm building for eternity
Making power moves that's the recipe"""
    ]
    
    def __init__(self, model_size: str = "large-v3"):
        """
        Initialize stub transcriber.
        
        Args:
            model_size: Model size (ignored in STUB)
        """
        self.model_size = model_size
    
    async def transcribe(
        self,
        audio_url: str,
        word_timestamps: bool = True,
        language: Optional[str] = None
    ) -> TranscriptionResult:
        """
        Transcribe audio to text.
        
        Args:
            audio_url: URL or path to audio file
            word_timestamps: Include word-level timestamps
            language: Language code (auto-detect if None)
            
        Returns:
            TranscriptionResult with mock lyrics
        """
        # Simulate processing time (70-100ms)
        await asyncio.sleep(0.085)
        
        # Select lyrics based on audio URL hash
        url_hash = hash(audio_url)
        lyrics_text = self.SAMPLE_LYRICS[url_hash % len(self.SAMPLE_LYRICS)]
        
        # Split into lines (segments)
        lines = [line.strip() for line in lyrics_text.strip().split('\n') if line.strip()]
        
        # Generate segments with timestamps
        segments = []
        current_time = 2.0  # Start after 2s intro
        
        for i, line in enumerate(lines):
            words_in_line = line.split()
            line_duration = len(words_in_line) * 0.35  # ~350ms per word
            
            # Generate words with timestamps
            words = []
            word_time = current_time
            
            if word_timestamps:
                for word_text in words_in_line:
                    word_duration = len(word_text) * 0.08  # Character-based duration
                    words.append(Word(
                        word=word_text,
                        start=round(word_time, 2),
                        end=round(word_time + word_duration, 2),
                        confidence=0.85 + (hash(f"{url_hash}_{i}_{word_text}") % 15) / 100
                    ))
                    word_time += word_duration + 0.1  # 100ms gap
            
            segment = Segment(
                id=i,
                start=round(current_time, 2),
                end=round(current_time + line_duration, 2),
                text=line,
                words=words,
                avg_confidence=0.88 + (hash(f"{url_hash}_{i}") % 10) / 100
            )
            
            segments.append(segment)
            current_time += line_duration + 0.5  # 500ms pause between lines
        
        return TranscriptionResult(
            text=lyrics_text.strip(),
            segments=segments,
            language=language or "en",
            duration=180.0,
            metadata={
                "model": f"whisper-{self.model_size}",
                "word_timestamps": word_timestamps,
                "stub_mode": True
            }
        )
    
    async def transcribe_vocals_only(
        self,
        vocals_url: str,
        language: Optional[str] = None
    ) -> TranscriptionResult:
        """
        Transcribe isolated vocals (more accurate than full mix).
        
        Args:
            vocals_url: URL to vocals stem
            language: Language code
            
        Returns:
            TranscriptionResult
        """
        # In STUB, same as regular transcribe but with higher confidence
        result = await self.transcribe(vocals_url, word_timestamps=True, language=language)
        
        # Boost confidence scores
        for segment in result.segments:
            segment.avg_confidence = min(0.98, segment.avg_confidence + 0.05)
            for word in segment.words:
                word.confidence = min(0.98, word.confidence + 0.05)
        
        return result
    
    def detect_language(self, audio_url: str) -> str:
        """
        Quick language detection (synchronous STUB).
        
        Args:
            audio_url: Audio file URL
            
        Returns:
            Language code
        """
        # STUB always returns English
        return "en"
    
    async def transcribe_batch(
        self,
        audio_urls: List[str],
        word_timestamps: bool = True
    ) -> List[TranscriptionResult]:
        """Transcribe multiple files in parallel."""
        tasks = [
            self.transcribe(url, word_timestamps=word_timestamps)
            for url in audio_urls
        ]
        return await asyncio.gather(*tasks)


# Factory function
def get_whisper_transcriber(model_size: str = "large-v3") -> WhisperStub:
    """
    Get Whisper transcriber instance.
    
    Args:
        model_size: Model size
        
    Returns:
        WhisperStub instance
    """
    return WhisperStub(model_size=model_size)
