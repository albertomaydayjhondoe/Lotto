"""
Content Validator
Validación de outputs generados por LLM.
"""

import logging
from typing import List

from ..models import GeneratedHook, GeneratedCaption
from ..config import ContentEngineConfig

logger = logging.getLogger(__name__)


class ContentValidator:
    """Valida contenido generado contra criterios de calidad."""
    
    def __init__(self, config: ContentEngineConfig):
        self.config = config
        self.min_confidence = config.min_confidence_threshold
    
    def validate_hooks(self, hooks: List[GeneratedHook]) -> List[GeneratedHook]:
        """Valida y filtra hooks por confianza."""
        validated = [
            hook for hook in hooks 
            if hook.confidence >= self.min_confidence
        ]
        logger.info(f"Validated {len(validated)}/{len(hooks)} hooks")
        return validated
    
    def validate_captions(self, captions: List[GeneratedCaption]) -> List[GeneratedCaption]:
        """Valida y filtra captions por confianza."""
        validated = [
            caption for caption in captions
            if caption.confidence >= self.min_confidence
        ]
        logger.info(f"Validated {len(validated)}/{len(captions)} captions")
        return validated
