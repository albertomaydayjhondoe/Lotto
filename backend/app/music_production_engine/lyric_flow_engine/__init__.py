"""Lyric Flow Engine Module

Analyzes lyrics, flow, and provides correction/improvement suggestions.
Combines Whisper transcription with NLP analysis.
"""

from .whisper_stub import WhisperStub, TranscriptionResult
from .lyric_analyzer import LyricAnalyzer, LyricAnalysisResult
from .flow_analyzer import FlowAnalyzer, FlowAnalysisResult
from .correction_engine import CorrectionEngine, CorrectionSuggestion

__all__ = [
    "WhisperStub",
    "TranscriptionResult",
    "LyricAnalyzer",
    "LyricAnalysisResult",
    "FlowAnalyzer",
    "FlowAnalysisResult",
    "CorrectionEngine",
    "CorrectionSuggestion",
]


def get_lyric_flow_status() -> dict:
    """Get status of lyric flow engine module."""
    return {
        "module": "lyric_flow_engine",
        "status": "STUB",
        "features": [
            "transcription (Whisper)",
            "lyric quality analysis",
            "flow complexity analysis",
            "rhyme scheme detection",
            "correction suggestions"
        ],
        "note": "All analysis uses mock data - no real transcription or NLP"
    }
