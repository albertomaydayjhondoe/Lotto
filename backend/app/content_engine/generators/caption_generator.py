"""
Caption Generator
Generación de captions optimizados usando LLM.

Cumple con Prompt Refinement Checklist.
"""

import logging
from typing import List, Dict, Any

from ..models import GeneratedCaption
from ..config import ContentEngineConfig

logger = logging.getLogger(__name__)


class CaptionGenerator:
    """Generador de captions para contenido."""
    
    FALLBACK_CAPTIONS = [
        {
            "text": "Descubre el secreto detrás de contenido que conecta. "
                   "¿Estás listo para el siguiente nivel? 🚀",
            "hashtags": ["#contenido", "#viral", "#tips"],
            "emojis": ["🚀", "💡", "✨"],
            "call_to_action": "Guarda este post para después",
            "confidence": 0.75
        }
    ]
    
    def __init__(self, config: ContentEngineConfig):
        self.config = config
        logger.info("CaptionGenerator initialized (STUB MODE)")
    
    async def generate_captions(
        self,
        video_id: str,
        context: Dict[str, Any],
        num_captions: int = 2
    ) -> List[GeneratedCaption]:
        """Genera captions para el video."""
        logger.info(f"Generating {num_captions} captions for video: {video_id}")
        
        # STUB MODE Sprint 1
        captions = []
        for fallback in self.FALLBACK_CAPTIONS[:num_captions]:
            caption = GeneratedCaption(
                text=fallback["text"],
                hashtags=fallback["hashtags"],
                emojis=fallback["emojis"],
                call_to_action=fallback.get("call_to_action"),
                confidence=fallback["confidence"]
            )
            captions.append(caption)
        
        return captions
