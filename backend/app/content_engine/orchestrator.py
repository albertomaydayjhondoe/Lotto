"""
Content Engine Orchestrator
Coordinador principal del módulo de generación de contenido.
"""

import time
import logging
from typing import Optional
from datetime import datetime

from .models import (
    ContentAnalysisRequest,
    ContentAnalysisResponse,
    VideoAnalysisResult,
    TrendAnalysisResult,
    GeneratedContent,
    ContentMetrics
)
from .config import ContentEngineConfig
from .analyzers.video_analyzer import VideoAnalyzer
from .analyzers.trend_analyzer import TrendAnalyzer
from .generators.hook_generator import HookGenerator
from .generators.caption_generator import CaptionGenerator
from .validators.content_validator import ContentValidator
from .telemetry.metrics import MetricsCollector

logger = logging.getLogger(__name__)


class ContentEngineOrchestrator:
    """
    Orquestador principal del Content Engine.
    
    Coordina:
    - Análisis de video (técnico)
    - Análisis de tendencias
    - Generación de hooks y captions
    - Validación de outputs
    - Telemetría y cost tracking
    """
    
    def __init__(self, config: Optional[ContentEngineConfig] = None):
        """
        Inicializa el orchestrator con configuración.
        
        Args:
            config: Configuración del engine. Si None, usa config por defecto.
        """
        self.config = config or ContentEngineConfig.from_env()
        
        # Initialize subsystems
        self.video_analyzer = VideoAnalyzer(self.config)
        self.trend_analyzer = TrendAnalyzer(self.config)
        self.hook_generator = HookGenerator(self.config)
        self.caption_generator = CaptionGenerator(self.config)
        self.validator = ContentValidator(self.config)
        self.metrics = MetricsCollector(self.config)
        
        logger.info(
            f"ContentEngineOrchestrator initialized with model={self.config.llm_model}, "
            f"cost_limit={self.config.max_cost_per_request}€"
        )
    
    async def analyze_and_generate(
        self,
        request: ContentAnalysisRequest
    ) -> ContentAnalysisResponse:
        """
        Ejecuta análisis completo y generación de contenido.
        
        Args:
            request: Request con parámetros de análisis
            
        Returns:
            Response con todos los resultados
            
        Raises:
            ValueError: Si el request es inválido
            RuntimeError: Si se excede el límite de coste
        """
        start_time = time.time()
        request_id = f"req_{datetime.utcnow().timestamp()}"
        
        logger.info(f"[{request_id}] Starting content analysis for video_id={request.video_id}")
        
        response = ContentAnalysisResponse(
            video_id=request.video_id,
            request_id=request_id
        )
        
        try:
            # 1. Video Analysis (opcional)
            if self.config.enable_video_analysis:
                response.video_analysis = await self._analyze_video(request)
            
            # 2. Trend Analysis (opcional)
            if self.config.enable_trend_analysis and request.analyze_trends:
                response.trend_analysis = await self._analyze_trends(request)
            
            # 3. Content Generation
            generated_content = GeneratedContent(
                video_id=request.video_id,
                prompt_version=self.config.prompt_version,
                model_used=self.config.llm_model
            )
            
            # 3a. Generate Hooks
            if self.config.enable_hook_generation and request.generate_hooks:
                hooks = await self.hook_generator.generate_hooks(
                    video_id=request.video_id,
                    context={
                        "video_analysis": response.video_analysis,
                        "trend_analysis": response.trend_analysis,
                        "platform": request.target_platform
                    }
                )
                # Validate hooks
                validated_hooks = self.validator.validate_hooks(hooks)
                generated_content.hooks = validated_hooks
            
            # 3b. Generate Captions
            if self.config.enable_caption_generation and request.generate_captions:
                captions = await self.caption_generator.generate_captions(
                    video_id=request.video_id,
                    context={
                        "video_analysis": response.video_analysis,
                        "trend_analysis": response.trend_analysis,
                        "platform": request.target_platform,
                        "hooks": generated_content.hooks
                    }
                )
                # Validate captions
                validated_captions = self.validator.validate_captions(captions)
                generated_content.captions = validated_captions
            
            response.generated_content = generated_content
            
            # 4. Calculate metrics
            execution_time_ms = (time.time() - start_time) * 1000
            response.execution_time_ms = execution_time_ms
            
            # Cost tracking
            total_cost = generated_content.estimated_cost_eur
            response.total_cost_eur = total_cost
            
            # Cost guard
            if total_cost > self.config.max_cost_per_request:
                raise RuntimeError(
                    f"Cost limit exceeded: {total_cost}€ > {self.config.max_cost_per_request}€"
                )
            
            # 5. Telemetry
            if self.config.enable_telemetry:
                metrics = ContentMetrics(
                    request_id=request_id,
                    video_id=request.video_id,
                    execution_time_ms=execution_time_ms,
                    tokens_used=generated_content.total_tokens,
                    cost_eur=total_cost,
                    model_used=self.config.llm_model,
                    success=True
                )
                response.metrics = metrics
                await self.metrics.record(metrics)
            
            response.success = True
            logger.info(
                f"[{request_id}] Content analysis completed successfully. "
                f"Time={execution_time_ms:.2f}ms, Cost={total_cost:.4f}€"
            )
            
        except Exception as e:
            logger.error(f"[{request_id}] Content analysis failed: {str(e)}", exc_info=True)
            response.success = False
            response.error_message = str(e)
            
            # Record failure metrics
            if self.config.enable_telemetry:
                execution_time_ms = (time.time() - start_time) * 1000
                metrics = ContentMetrics(
                    request_id=request_id,
                    video_id=request.video_id,
                    execution_time_ms=execution_time_ms,
                    tokens_used=0,
                    cost_eur=0.0,
                    model_used=self.config.llm_model,
                    success=False,
                    error_message=str(e)
                )
                response.metrics = metrics
                await self.metrics.record(metrics)
        
        return response
    
    async def _analyze_video(
        self,
        request: ContentAnalysisRequest
    ) -> VideoAnalysisResult:
        """Ejecuta análisis técnico de video."""
        logger.debug(f"Analyzing video: {request.video_id}")
        return await self.video_analyzer.analyze(
            video_id=request.video_id,
            video_url=request.video_url,
            metadata=request.video_metadata
        )
    
    async def _analyze_trends(
        self,
        request: ContentAnalysisRequest
    ) -> TrendAnalysisResult:
        """Ejecuta análisis de tendencias."""
        logger.debug(f"Analyzing trends for: {request.video_id}")
        return await self.trend_analyzer.analyze(
            video_id=request.video_id,
            platform=request.target_platform
        )
    
    async def get_metrics_summary(self) -> dict:
        """Retorna resumen de métricas agregadas."""
        return await self.metrics.get_summary()
    
    async def check_cost_limits(self) -> dict:
        """Verifica estado de límites de coste."""
        return await self.metrics.check_cost_limits()
