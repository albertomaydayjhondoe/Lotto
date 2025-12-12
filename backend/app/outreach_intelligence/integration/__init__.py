"""
Integration subsystem initialization

Exports integration hooks for connecting to other phases.
"""

from .hooks_music_engine import MusicEngineHook
from .hooks_content_engine import ContentEngineHook
from .hooks_community_manager import CommunityManagerHook
from .hooks_master_orchestrator import MasterOrchestratorHook

__all__ = [
    "MusicEngineHook",
    "ContentEngineHook",
    "CommunityManagerHook",
    "MasterOrchestratorHook"
]
