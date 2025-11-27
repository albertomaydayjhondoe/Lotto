"""
Creative Variants Engine (PASO 10.10)

Motor principal para generación de variantes creativas.
"""
import logging
import time
from datetime import datetime
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.meta_creative_variants.schemas import (
    GenerateVariantsRequest,
    GenerateVariantsResponse,
    CreativeVariant,
    CropRatio,
    CTAType,
)
from app.meta_creative_variants.extractor import CreativeMaterialExtractor
from app.meta_creative_variants.generator import CreativeVariantsGenerator
from app.meta_creative_variants.uploader import CreativeUploader
from app.meta_creative_variants.models import (
    MetaCreativeVariantModel,
    MetaCreativeVariantVideoModel,
    MetaCreativeVariantTextModel,
    MetaCreativeVariantThumbnailModel,
)

logger = logging.getLogger(__name__)


class CreativeVariantsEngine:
    """
    Motor completo para generación automática de variantes creativas.
    
    Workflow:
    1. Extraer material creativo del clip
    2. Generar variantes de video/texto/thumbnail
    3. Combinar en variantes completas
    4. (Opcional) Upload a Meta Ads
    5. Persistir en DB
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.extractor = CreativeMaterialExtractor(db)
        self.generator = CreativeVariantsGenerator(self.extractor)
        self.uploader = CreativeUploader()
    
    async def generate_variants(
        self,
        request: GenerateVariantsRequest
    ) -> GenerateVariantsResponse:
        """
        Genera variantes creativas completas.
        
        Args:
            request: GenerateVariantsRequest con parámetros
            
        Returns:
            GenerateVariantsResponse con variantes generadas
        """
        start_time = time.time()
        
        logger.info(
            f"Generating {request.num_variants} creative variants for clip {request.clip_id}"
        )
        
        if request.dry_run:
            logger.info("DRY RUN mode: no changes will be persisted")
        
        # 1. Generar variantes de video
        video_variants = await self.generator.generate_video_variants(
            clip_id=request.clip_id,
            count=request.video_variants_count,
            crop_ratios=request.crop_ratios,
        )
        
        # 2. Generar variantes de texto
        text_variants = await self.generator.generate_text_variants(
            clip_id=request.clip_id,
            count=request.text_variants_count,
            cta_types=request.cta_types,
            language=request.languages[0] if request.languages else "es",
        )
        
        # 3. Generar variantes de thumbnail
        thumbnail_variants = await self.generator.generate_thumbnail_variants(
            clip_id=request.clip_id,
            count=request.thumbnail_variants_count,
            crop_ratios=request.crop_ratios,
        )
        
        # 4. Combinar en variantes completas
        creative_variants = await self.generator.generate_creative_combinations(
            video_variants=video_variants,
            text_variants=text_variants,
            thumbnail_variants=thumbnail_variants,
            target_count=request.num_variants,
            campaign_id=request.campaign_id,
            adset_id=request.adset_id,
        )
        
        # 5. Persistir en DB (si no es dry_run)
        if not request.dry_run:
            await self._persist_variants(creative_variants)
        
        # 6. Upload a Meta Ads (si auto_upload=True)
        uploaded_count = 0
        upload_errors = []
        
        if request.auto_upload and request.campaign_id and request.adset_id:
            logger.info(f"Auto-uploading {len(creative_variants)} variants to Meta Ads")
            
            for variant in creative_variants:
                upload_response = await self.uploader.upload_creative(
                    variant=variant,
                    ad_account_id="act_stub",  # TODO: Get from config
                    campaign_id=request.campaign_id,
                    adset_id=request.adset_id,
                )
                
                if upload_response.success:
                    uploaded_count += 1
                    variant.meta_creative_id = upload_response.meta_creative_id
                    variant.meta_ad_id = upload_response.meta_ad_id
                    variant.uploaded_at = datetime.utcnow()
                else:
                    upload_errors.append(f"{variant.variant_id}: {upload_response.error}")
        
        generation_time = time.time() - start_time
        
        logger.info(
            f"Generation complete: {len(creative_variants)} variants in {generation_time:.2f}s"
        )
        
        return GenerateVariantsResponse(
            success=True,
            clip_id=request.clip_id,
            campaign_id=request.campaign_id,
            total_variants=len(creative_variants),
            variants=creative_variants,
            video_variants_generated=len(video_variants),
            text_variants_generated=len(text_variants),
            thumbnail_variants_generated=len(thumbnail_variants),
            uploaded_count=uploaded_count,
            upload_errors=upload_errors,
            generation_time_seconds=generation_time,
        )
    
    async def _persist_variants(self, variants: List[CreativeVariant]) -> None:
        """Persiste variantes en la base de datos."""
        logger.info(f"Persisting {len(variants)} variants to database")
        
        for variant in variants:
            # Crear video variant model
            video_model = MetaCreativeVariantVideoModel(
                variant_id=variant.video_variant.variant_id,
                clip_id=variant.video_variant.clip_id,
                start_time=variant.video_variant.start_time,
                end_time=variant.video_variant.end_time,
                duration=variant.video_variant.duration,
                crop_ratio=variant.video_variant.crop_ratio.value,
                speed=variant.video_variant.speed.value,
                muted=variant.video_variant.muted,
                subtitles_enabled=variant.video_variant.subtitles_enabled,
                scene_description=variant.video_variant.scene_description,
                thumbnail_timestamp=variant.video_variant.thumbnail_timestamp,
                file_url=variant.video_variant.file_url,
            )
            self.db.add(video_model)
            await self.db.flush()
            
            # Crear text variant model
            text_model = MetaCreativeVariantTextModel(
                variant_id=variant.text_variant.variant_id,
                headline=variant.text_variant.headline,
                primary_text=variant.text_variant.primary_text,
                description=variant.text_variant.description,
                cta_type=variant.text_variant.cta_type.value,
                cta_text=variant.text_variant.cta_text,
                language=variant.text_variant.language,
                keywords=variant.text_variant.keywords,
                hashtags=variant.text_variant.hashtags,
            )
            self.db.add(text_model)
            await self.db.flush()
            
            # Crear thumbnail variant model
            thumbnail_model = MetaCreativeVariantThumbnailModel(
                variant_id=variant.thumbnail_variant.variant_id,
                source_type=variant.thumbnail_variant.source_type,
                timestamp=variant.thumbnail_variant.timestamp,
                has_text_overlay=variant.thumbnail_variant.has_text_overlay,
                overlay_text=variant.thumbnail_variant.overlay_text,
                crop_ratio=variant.thumbnail_variant.crop_ratio.value,
                file_url=variant.thumbnail_variant.file_url,
                width=variant.thumbnail_variant.width,
                height=variant.thumbnail_variant.height,
            )
            self.db.add(thumbnail_model)
            await self.db.flush()
            
            # Crear creative variant model
            creative_model = MetaCreativeVariantModel(
                variant_id=variant.variant_id,
                campaign_id=variant.campaign_id,
                adset_id=variant.adset_id,
                video_variant_id=video_model.id,
                text_variant_id=text_model.id,
                thumbnail_variant_id=thumbnail_model.id,
                status=variant.status.value,
                meta_creative_id=variant.meta_creative_id,
                meta_ad_id=variant.meta_ad_id,
                generated_by=variant.generated_by,
                uploaded_at=variant.uploaded_at,
            )
            self.db.add(creative_model)
        
        await self.db.commit()
        logger.info("All variants persisted successfully")
