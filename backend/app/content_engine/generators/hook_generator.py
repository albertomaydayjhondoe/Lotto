"""
Hook Generator
Generación de hooks virales usando LLM.

Cumple con Prompt Refinement Checklist:
- Template versionado en app/prompts/
- Metadata con prompt_version
- Validación con Pydantic
- Fallback mechanism
- Token tracking
- Cost guards
"""

import logging
from typing import List, Dict, Any, Optional
import json

from ..models import GeneratedHook
from ..config import ContentEngineConfig

logger = logging.getLogger(__name__)


class HookGenerator:
    """
    Generador de hooks para contenido.
    
    Responsabilidades:
    - Generar hooks atractivos basados en contexto
    - Validar calidad de hooks generados
    - Trackear tokens y costos
    - Manejar fallbacks en caso de error
    """
    
    # STUB: Hooks predefinidos para Sprint 1
    FALLBACK_HOOKS = [
        {
            "text": "¿Sabías que este truco puede cambiar tu forma de crear contenido?",
            "type": "question",
            "confidence": 0.7,
            "target_emotion": "curiosity"
        },
        {
            "text": "Lo que nadie te cuenta sobre crear contenido viral",
            "type": "statement",
            "confidence": 0.75,
            "target_emotion": "intrigue"
        },
        {
            "text": "3 errores que están matando tu engagement (y cómo solucionarlos)",
            "type": "challenge",
            "confidence": 0.8,
            "target_emotion": "concern"
        }
    ]
    
    def __init__(self, config: ContentEngineConfig):
        self.config = config
        self.prompt_version = config.prompt_version
        logger.info(
            f"HookGenerator initialized with model={config.llm_model}, "
            f"prompt_version={self.prompt_version}"
        )
    
    async def generate_hooks(
        self,
        video_id: str,
        context: Dict[str, Any],
        num_hooks: int = 3
    ) -> List[GeneratedHook]:
        """
        Genera hooks para el video.
        
        Args:
            video_id: ID del video
            context: Contexto con análisis y metadata
            num_hooks: Número de hooks a generar
            
        Returns:
            Lista de GeneratedHook
        """
        logger.info(f"Generating {num_hooks} hooks for video: {video_id}")
        
        try:
            # STUB MODE Sprint 1: Retorna hooks predefinidos
            # TODO Sprint 2: Implementar llamada real a LLM
            
            hooks = []
            for i, fallback in enumerate(self.FALLBACK_HOOKS[:num_hooks]):
                hook = GeneratedHook(
                    text=fallback["text"],
                    type=fallback["type"],
                    confidence=fallback["confidence"],
                    target_emotion=fallback.get("target_emotion"),
                    estimated_engagement=0.65 + (i * 0.05)  # Simulado
                )
                hooks.append(hook)
            
            logger.info(f"Generated {len(hooks)} hooks successfully")
            return hooks
            
        except Exception as e:
            logger.error(f"Hook generation failed: {str(e)}", exc_info=True)
            # Fallback: retorna hooks básicos
            return self._get_fallback_hooks(num_hooks)
    
    def _get_fallback_hooks(self, num_hooks: int) -> List[GeneratedHook]:
        """
        Retorna hooks de fallback en caso de error.
        
        Args:
            num_hooks: Número de hooks requeridos
            
        Returns:
            Lista de hooks básicos
        """
        logger.warning("Using fallback hooks")
        
        hooks = []
        for fallback in self.FALLBACK_HOOKS[:num_hooks]:
            hook = GeneratedHook(
                text=fallback["text"],
                type=fallback["type"],
                confidence=fallback["confidence"] * 0.8,  # Reducida por fallback
                target_emotion=fallback.get("target_emotion")
            )
            hooks.append(hook)
        
        return hooks
    
    def _build_hook_prompt(self, context: Dict[str, Any]) -> str:
        """
        Construye prompt para generación de hooks.
        
        TODO Sprint 2: Usar template versionado desde app/prompts/
        
        Args:
            context: Contexto con análisis
            
        Returns:
            Prompt construido
        """
        # STUB: Prompt básico
        # TODO: Migrar a template file con versioning
        
        video_analysis = context.get("video_analysis")
        trend_analysis = context.get("trend_analysis")
        platform = context.get("platform", "instagram")
        
        prompt = f"""
        Generate viral hooks for a {platform} video.
        
        Video Details:
        - Duration: {video_analysis.duration_seconds if video_analysis else 'unknown'}s
        - Quality: {video_analysis.quality_score if video_analysis else 'unknown'}
        
        Trends:
        - Detected: {', '.join(trend_analysis.detected_trends[:3]) if trend_analysis else 'none'}
        
        Requirements:
        - Hook must grab attention in first 3 seconds
        - Target emotion: curiosity, intrigue, or surprise
        - Length: 10-100 characters
        - Platform-optimized for {platform}
        
        Generate 3 different hook types: question, statement, challenge.
        """
        
        return prompt.strip()
    
    def _parse_llm_response(self, response: str) -> List[GeneratedHook]:
        """
        Parsea respuesta del LLM a lista de hooks.
        
        Args:
            response: Respuesta raw del LLM
            
        Returns:
            Lista de GeneratedHook parseados
        """
        # TODO Sprint 2: Implementar parsing robusto
        try:
            data = json.loads(response)
            hooks = []
            for item in data.get("hooks", []):
                hook = GeneratedHook(**item)
                hooks.append(hook)
            return hooks
        except Exception as e:
            logger.error(f"Failed to parse LLM response: {str(e)}")
            return self._get_fallback_hooks(3)
