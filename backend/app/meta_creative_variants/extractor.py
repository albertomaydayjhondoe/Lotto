"""
Extractor de material creativo para Meta Creative Variants Engine (PASO 10.10)

Extrae fragmentos, clips, textos, metadata desde VideoAsset y ClipManager.
"""
import logging
from typing import Dict, List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.database import Clip, Job
from app.core.config import settings

logger = logging.getLogger(__name__)


class CreativeMaterialExtractor:
    """
    Extrae material creativo (video, texto, metadata) desde clips existentes.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.mode = settings.META_API_MODE or "stub"
    
    async def extract_from_clip(self, clip_id: str) -> Dict[str, Any]:
        """
        Extrae todo el material creativo desde un clip.
        
        Args:
            clip_id: ID del clip
            
        Returns:
            Dict con:
                - clip_metadata
                - video_asset
                - text_content
                - keywords
                - hashtags
                - scenes (placeholder)
        """
        logger.info(f"Extracting creative material from clip: {clip_id}")
        
        if self.mode == "stub":
            return self._extract_stub_data(clip_id)
        
        # Obtener clip de la base de datos
        result = await self.db.execute(
            select(Clip).where(Clip.id == clip_id)
        )
        clip = result.scalar_one_or_none()
        
        if not clip:
            logger.error(f"Clip not found: {clip_id}")
            return self._extract_stub_data(clip_id)
        
        # Extraer datos reales
        return {
            "clip_id": clip.id,
            "clip_metadata": {
                "title": clip.title or "Untitled",
                "description": clip.description or "",
                "duration": clip.duration or 30.0,
                "status": clip.status,
                "video_url": clip.video_url or "",
                "thumbnail_url": clip.thumbnail_url or "",
            },
            "video_asset": {
                "url": clip.video_url or "",
                "duration": clip.duration or 30.0,
                "format": "mp4",
                "resolution": "1080p",
            },
            "text_content": {
                "title": clip.title or "Producto increíble",
                "description": clip.description or "Descubre nuestro producto",
                "caption": self._extract_caption(clip),
                "language": "es",
            },
            "keywords": self._extract_keywords(clip),
            "hashtags": self._extract_hashtags(clip),
            "scenes": await self._detect_scenes(clip),
        }
    
    def _extract_stub_data(self, clip_id: str) -> Dict[str, Any]:
        """
        Genera datos stub para testing.
        """
        return {
            "clip_id": clip_id,
            "clip_metadata": {
                "title": "Producto Innovador 2025",
                "description": "Descubre la mejor tecnología del mercado",
                "duration": 30.0,
                "status": "ready",
                "video_url": f"https://stub.example.com/videos/{clip_id}.mp4",
                "thumbnail_url": f"https://stub.example.com/thumbnails/{clip_id}.jpg",
            },
            "video_asset": {
                "url": f"https://stub.example.com/videos/{clip_id}.mp4",
                "duration": 30.0,
                "format": "mp4",
                "resolution": "1080p",
            },
            "text_content": {
                "title": "Producto Innovador 2025",
                "description": "Descubre la mejor tecnología del mercado",
                "caption": "🚀 Innovación que transforma tu vida ✨",
                "language": "es",
            },
            "keywords": [
                "tecnología",
                "innovación",
                "calidad",
                "oferta",
                "descuento",
                "nuevo",
                "premium",
                "exclusivo",
            ],
            "hashtags": [
                "#tecnología",
                "#innovación",
                "#ofertas",
                "#nuevo2025",
                "#calidad",
            ],
            "scenes": [
                {
                    "start": 0.0,
                    "end": 10.0,
                    "description": "Intro impactante con producto",
                    "timestamp": 5.0,
                },
                {
                    "start": 10.0,
                    "end": 20.0,
                    "description": "Demostración de características",
                    "timestamp": 15.0,
                },
                {
                    "start": 20.0,
                    "end": 30.0,
                    "description": "Call to action final",
                    "timestamp": 25.0,
                },
            ],
        }
    
    def _extract_caption(self, clip: Clip) -> str:
        """Extrae o genera caption del clip."""
        if clip.description:
            return clip.description[:100]
        return "Descubre más sobre este increíble producto"
    
    def _extract_keywords(self, clip: Clip) -> List[str]:
        """Extrae keywords relevantes del clip."""
        # TODO: Integrar con NLP/AI para extracción real
        default_keywords = [
            "producto", "oferta", "nuevo", "calidad",
            "descuento", "innovación", "premium", "exclusivo"
        ]
        
        # Extraer de título/descripción
        text = f"{clip.title or ''} {clip.description or ''}".lower()
        extracted = []
        for keyword in default_keywords:
            if keyword in text:
                extracted.append(keyword)
        
        return extracted if extracted else default_keywords[:5]
    
    def _extract_hashtags(self, clip: Clip) -> List[str]:
        """Extrae o genera hashtags del clip."""
        keywords = self._extract_keywords(clip)
        return [f"#{kw.replace(' ', '')}" for kw in keywords[:5]]
    
    async def _detect_scenes(self, clip: Clip) -> List[Dict[str, Any]]:
        """
        Detecta escenas importantes en el video.
        TODO: Integrar con AI para scene detection real.
        """
        duration = clip.duration or 30.0
        
        # Stub: dividir en 3 escenas iguales
        scene_duration = duration / 3
        
        return [
            {
                "start": 0.0,
                "end": scene_duration,
                "description": "Escena introductoria",
                "timestamp": scene_duration / 2,
            },
            {
                "start": scene_duration,
                "end": scene_duration * 2,
                "description": "Escena principal",
                "timestamp": scene_duration * 1.5,
            },
            {
                "start": scene_duration * 2,
                "end": duration,
                "description": "Escena de cierre",
                "timestamp": scene_duration * 2.5,
            },
        ]
    
    async def extract_video_fragments(
        self,
        clip_id: str,
        num_fragments: int = 5
    ) -> List[Dict[str, float]]:
        """
        Extrae fragmentos temporales del video para variantes.
        
        Args:
            clip_id: ID del clip
            num_fragments: Número de fragmentos a generar
            
        Returns:
            Lista de fragmentos con start_time, end_time, duration
        """
        material = await self.extract_from_clip(clip_id)
        duration = material["video_asset"]["duration"]
        
        fragments = []
        
        # Estrategia 1: Video completo
        fragments.append({
            "start_time": 0.0,
            "end_time": duration,
            "duration": duration,
            "description": "Video completo",
        })
        
        # Estrategia 2: Primeros N segundos (6, 10, 15)
        for cut_duration in [6.0, 10.0, 15.0]:
            if cut_duration < duration:
                fragments.append({
                    "start_time": 0.0,
                    "end_time": cut_duration,
                    "duration": cut_duration,
                    "description": f"Primeros {int(cut_duration)}s",
                })
        
        # Estrategia 3: Escenas específicas
        scenes = material.get("scenes", [])
        for i, scene in enumerate(scenes[:2]):  # Top 2 escenas
            fragments.append({
                "start_time": scene["start"],
                "end_time": scene["end"],
                "duration": scene["end"] - scene["start"],
                "description": f"Escena {i+1}: {scene['description']}",
            })
        
        return fragments[:num_fragments]
    
    async def extract_text_templates(
        self,
        clip_id: str,
        num_templates: int = 5
    ) -> List[Dict[str, str]]:
        """
        Extrae y genera plantillas de texto.
        
        Returns:
            Lista de plantillas con headline, primary_text, description
        """
        material = await self.extract_from_clip(clip_id)
        text_content = material["text_content"]
        title = text_content["title"]
        description = text_content["description"]
        
        templates = []
        
        # Template 1: Directo
        templates.append({
            "headline": title[:40],
            "primary_text": f"{description} Descubre más ahora"[:125],
            "description": "Ver más"[:30],
        })
        
        # Template 2: Con emoji
        templates.append({
            "headline": f"✨ {title[:37]}",
            "primary_text": f"🚀 {description} ¡No te lo pierdas!"[:125],
            "description": "Compra ahora"[:30],
        })
        
        # Template 3: Urgencia
        templates.append({
            "headline": f"🔥 {title[:37]}",
            "primary_text": f"⏰ Oferta por tiempo limitado: {description}"[:125],
            "description": "Solo hoy"[:30],
        })
        
        # Template 4: Beneficio
        templates.append({
            "headline": "Mejora tu vida hoy",
            "primary_text": f"💎 {description} | Calidad garantizada"[:125],
            "description": "Más info"[:30],
        })
        
        # Template 5: Social proof
        templates.append({
            "headline": "Miles lo prefieren",
            "primary_text": f"⭐ {description} | Recomendado por expertos"[:125],
            "description": "Únete ahora"[:30],
        })
        
        return templates[:num_templates]
    
    async def extract_thumbnail_points(
        self,
        clip_id: str,
        num_points: int = 4
    ) -> List[Dict[str, Any]]:
        """
        Extrae puntos temporales óptimos para thumbnails.
        
        Returns:
            Lista de timestamps con metadata
        """
        material = await self.extract_from_clip(clip_id)
        duration = material["video_asset"]["duration"]
        scenes = material.get("scenes", [])
        
        points = []
        
        # Punto 1: Frame del medio
        points.append({
            "timestamp": duration / 2,
            "description": "Frame central",
            "source_type": "freeze_frame",
        })
        
        # Punto 2: Primer segundo (hook)
        points.append({
            "timestamp": 1.0,
            "description": "Hook inicial",
            "source_type": "extract_frame",
        })
        
        # Puntos 3-4: Mid-points de escenas principales
        for i, scene in enumerate(scenes[:2]):
            mid_point = (scene["start"] + scene["end"]) / 2
            points.append({
                "timestamp": mid_point,
                "description": f"Punto clave escena {i+1}",
                "source_type": "extract_frame",
            })
        
        return points[:num_points]
