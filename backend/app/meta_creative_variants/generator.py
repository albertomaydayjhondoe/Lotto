"""
Generator de variantes creativas para Meta Creative Variants Engine (PASO 10.10)

Genera combinaciones de video, texto y thumbnails.
"""
import logging
import random
import uuid
from datetime import datetime
from typing import List, Dict, Any
from itertools import product

from app.meta_creative_variants.schemas import (
    VideoVariant,
    TextVariant,
    ThumbnailVariant,
    CreativeVariant,
    CropRatio,
    VideoSpeed,
    CTAType,
    VariantStatus,
)
from app.meta_creative_variants.extractor import CreativeMaterialExtractor

logger = logging.getLogger(__name__)


class CreativeVariantsGenerator:
    """
    Genera variantes creativas combinando video, texto y thumbnails.
    """
    
    def __init__(self, extractor: CreativeMaterialExtractor):
        self.extractor = extractor
    
    async def generate_video_variants(
        self,
        clip_id: str,
        count: int = 5,
        crop_ratios: List[CropRatio] = None
    ) -> List[VideoVariant]:
        """
        Genera variantes de video.
        
        Args:
            clip_id: ID del clip base
            count: Número de variantes a generar (3-7)
            crop_ratios: Ratios de crop a usar
            
        Returns:
            Lista de VideoVariant
        """
        logger.info(f"Generating {count} video variants for clip {clip_id}")
        
        if crop_ratios is None:
            crop_ratios = [CropRatio.SQUARE, CropRatio.VERTICAL, CropRatio.PORTRAIT]
        
        # Extraer fragmentos
        fragments = await self.extractor.extract_video_fragments(clip_id, num_fragments=count)
        
        variants = []
        for i, fragment in enumerate(fragments[:count]):
            variant_id = f"video_{clip_id}_{uuid.uuid4().hex[:8]}"
            
            # Seleccionar parámetros
            crop_ratio = crop_ratios[i % len(crop_ratios)]
            speed = random.choice([VideoSpeed.SLOW, VideoSpeed.NORMAL, VideoSpeed.FAST])
            muted = i % 3 == 0  # Cada 3er video silenciado
            subtitles = i % 2 == 0  # Alternar subtítulos
            
            variant = VideoVariant(
                variant_id=variant_id,
                clip_id=clip_id,
                start_time=fragment["start_time"],
                end_time=fragment["end_time"],
                duration=fragment["duration"],
                crop_ratio=crop_ratio,
                speed=speed,
                muted=muted,
                subtitles_enabled=subtitles,
                scene_description=fragment.get("description"),
                thumbnail_timestamp=fragment["start_time"] + (fragment["duration"] / 2),
                created_at=datetime.utcnow(),
            )
            
            variants.append(variant)
            logger.debug(f"Generated video variant: {variant_id} ({crop_ratio}, {speed})")
        
        return variants
    
    async def generate_text_variants(
        self,
        clip_id: str,
        count: int = 5,
        cta_types: List[CTAType] = None,
        language: str = "es"
    ) -> List[TextVariant]:
        """
        Genera variantes de texto.
        
        Args:
            clip_id: ID del clip base
            count: Número de variantes a generar (3-10)
            cta_types: Tipos de CTA a usar
            language: Idioma de los textos
            
        Returns:
            Lista de TextVariant
        """
        logger.info(f"Generating {count} text variants for clip {clip_id}")
        
        if cta_types is None:
            cta_types = [CTAType.LEARN_MORE, CTAType.SHOP_NOW, CTAType.SIGN_UP]
        
        # Extraer plantillas base
        templates = await self.extractor.extract_text_templates(clip_id, num_templates=count)
        material = await self.extractor.extract_from_clip(clip_id)
        
        keywords = material.get("keywords", [])
        hashtags = material.get("hashtags", [])
        
        variants = []
        for i, template in enumerate(templates[:count]):
            variant_id = f"text_{clip_id}_{uuid.uuid4().hex[:8]}"
            
            # Seleccionar CTA
            cta_type = cta_types[i % len(cta_types)]
            cta_text = self._get_cta_text(cta_type, language)
            
            variant = TextVariant(
                variant_id=variant_id,
                headline=template["headline"],
                primary_text=template["primary_text"],
                description=template.get("description"),
                cta_type=cta_type,
                cta_text=cta_text,
                language=language,
                keywords=keywords[:5],
                hashtags=hashtags[:3],
                created_at=datetime.utcnow(),
            )
            
            variants.append(variant)
            logger.debug(f"Generated text variant: {variant_id} (CTA: {cta_type})")
        
        return variants
    
    async def generate_thumbnail_variants(
        self,
        clip_id: str,
        count: int = 4,
        crop_ratios: List[CropRatio] = None
    ) -> List[ThumbnailVariant]:
        """
        Genera variantes de thumbnail.
        
        Args:
            clip_id: ID del clip base
            count: Número de variantes a generar (3-6)
            crop_ratios: Ratios de crop a usar
            
        Returns:
            Lista de ThumbnailVariant
        """
        logger.info(f"Generating {count} thumbnail variants for clip {clip_id}")
        
        if crop_ratios is None:
            crop_ratios = [CropRatio.SQUARE, CropRatio.VERTICAL]
        
        # Extraer puntos óptimos para thumbnails
        thumbnail_points = await self.extractor.extract_thumbnail_points(clip_id, num_points=count)
        
        variants = []
        for i, point in enumerate(thumbnail_points[:count]):
            variant_id = f"thumb_{clip_id}_{uuid.uuid4().hex[:8]}"
            
            # Seleccionar tipo y parámetros
            source_type = point["source_type"]
            crop_ratio = crop_ratios[i % len(crop_ratios)]
            has_overlay = i % 2 == 0  # Cada 2do con texto
            
            overlay_text = None
            if has_overlay:
                overlay_text = "🔥 NUEVO"
            
            variant = ThumbnailVariant(
                variant_id=variant_id,
                source_type=source_type,
                timestamp=point["timestamp"],
                has_text_overlay=has_overlay,
                overlay_text=overlay_text,
                crop_ratio=crop_ratio,
                created_at=datetime.utcnow(),
            )
            
            variants.append(variant)
            logger.debug(f"Generated thumbnail variant: {variant_id} ({source_type}, overlay={has_overlay})")
        
        return variants
    
    async def generate_creative_combinations(
        self,
        video_variants: List[VideoVariant],
        text_variants: List[TextVariant],
        thumbnail_variants: List[ThumbnailVariant],
        target_count: int = 10,
        campaign_id: str = None,
        adset_id: str = None
    ) -> List[CreativeVariant]:
        """
        Genera combinaciones completas de variantes creativas.
        
        Strategy:
        - Combina todas las variantes usando product()
        - Limita a target_count variantes
        - Prioriza combinaciones con crop_ratio matching
        
        Args:
            video_variants: Lista de variantes de video
            text_variants: Lista de variantes de texto
            thumbnail_variants: Lista de variantes de thumbnail
            target_count: Número objetivo de variantes (5-20)
            campaign_id: ID de campaña de Meta Ads
            adset_id: ID de adset de Meta Ads
            
        Returns:
            Lista de CreativeVariant (combinaciones completas)
        """
        logger.info(f"Generating {target_count} creative combinations")
        
        # Generar todas las combinaciones posibles
        all_combinations = list(product(video_variants, text_variants, thumbnail_variants))
        
        logger.info(f"Total possible combinations: {len(all_combinations)}")
        
        # Si hay más combinaciones que el target, seleccionar las mejores
        if len(all_combinations) > target_count:
            # Estrategia: priorizar crop_ratio matching entre video y thumbnail
            scored_combinations = []
            for video, text, thumbnail in all_combinations:
                score = 0
                
                # +10 puntos si video y thumbnail tienen mismo crop_ratio
                if video.crop_ratio == thumbnail.crop_ratio:
                    score += 10
                
                # +5 puntos si es formato vertical (mejor para móvil)
                if video.crop_ratio in [CropRatio.VERTICAL, CropRatio.PORTRAIT]:
                    score += 5
                
                # +3 puntos si tiene subtítulos
                if video.subtitles_enabled:
                    score += 3
                
                # +2 puntos si thumbnail tiene overlay
                if thumbnail.has_text_overlay:
                    score += 2
                
                scored_combinations.append((score, video, text, thumbnail))
            
            # Ordenar por score y tomar top target_count
            scored_combinations.sort(key=lambda x: x[0], reverse=True)
            selected = scored_combinations[:target_count]
        else:
            selected = [(0, v, t, th) for v, t, th in all_combinations]
        
        # Crear CreativeVariant para cada combinación
        creative_variants = []
        for i, (score, video, text, thumbnail) in enumerate(selected):
            variant_id = f"creative_{video.clip_id}_{uuid.uuid4().hex[:8]}"
            
            creative_variant = CreativeVariant(
                variant_id=variant_id,
                campaign_id=campaign_id,
                adset_id=adset_id,
                video_variant=video,
                text_variant=text,
                thumbnail_variant=thumbnail,
                status=VariantStatus.GENERATED,
                generated_by="auto",
                generation_timestamp=datetime.utcnow(),
            )
            
            creative_variants.append(creative_variant)
            logger.debug(f"Created creative variant: {variant_id} (score={score})")
        
        logger.info(f"Generated {len(creative_variants)} creative variants")
        return creative_variants
    
    def _get_cta_text(self, cta_type: CTAType, language: str) -> str:
        """Obtiene texto de CTA según tipo e idioma."""
        cta_texts = {
            "es": {
                CTAType.LEARN_MORE: "Más información",
                CTAType.SHOP_NOW: "Comprar ahora",
                CTAType.SIGN_UP: "Registrarse",
                CTAType.DOWNLOAD: "Descargar",
                CTAType.WATCH_MORE: "Ver más",
                CTAType.GET_OFFER: "Obtener oferta",
                CTAType.APPLY_NOW: "Aplicar ahora",
                CTAType.BOOK_NOW: "Reservar ahora",
            },
            "en": {
                CTAType.LEARN_MORE: "Learn More",
                CTAType.SHOP_NOW: "Shop Now",
                CTAType.SIGN_UP: "Sign Up",
                CTAType.DOWNLOAD: "Download",
                CTAType.WATCH_MORE: "Watch More",
                CTAType.GET_OFFER: "Get Offer",
                CTAType.APPLY_NOW: "Apply Now",
                CTAType.BOOK_NOW: "Book Now",
            },
        }
        
        return cta_texts.get(language, cta_texts["es"]).get(cta_type, "Más información")
