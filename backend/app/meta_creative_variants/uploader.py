"""
Uploader de creatives a Meta Ads API (PASO 10.10)
"""
import logging
from typing import Optional

from app.meta_creative_variants.schemas import CreativeVariant, UploadVariantResponse
from app.meta_ads_client.client import MetaAdsClient
from app.core.config import settings

logger = logging.getLogger(__name__)


class CreativeUploader:
    """
    Sube creatives generados a Meta Ads API.
    """
    
    def __init__(self):
        self.client = MetaAdsClient()
        self.mode = settings.META_API_MODE or "stub"
    
    async def upload_creative(
        self,
        variant: CreativeVariant,
        ad_account_id: str,
        campaign_id: str,
        adset_id: str
    ) -> UploadVariantResponse:
        """
        Sube un creative variant a Meta Ads.
        
        Args:
            variant: CreativeVariant a subir
            ad_account_id: ID de la cuenta de anuncios
            campaign_id: ID de la campaña
            adset_id: ID del adset
            
        Returns:
            UploadVariantResponse con resultado
        """
        try:
            logger.info(f"Uploading creative variant: {variant.variant_id}")
            
            if self.mode == "stub":
                return await self._upload_stub(variant, ad_account_id, campaign_id, adset_id)
            
            # Upload real a Meta Ads API
            # 1. Upload video
            video_response = await self.client.upload_video(
                ad_account_id=ad_account_id,
                video_url=variant.video_variant.file_url or "stub_url",
                title=variant.text_variant.headline,
            )
            
            # 2. Upload thumbnail
            thumbnail_response = await self.client.upload_image(
                ad_account_id=ad_account_id,
                image_url=variant.thumbnail_variant.file_url or "stub_url",
            )
            
            # 3. Create creative
            creative_response = await self.client.create_creative(
                ad_account_id=ad_account_id,
                name=f"Creative_{variant.variant_id}",
                video_id=video_response.get("id"),
                thumbnail_url=thumbnail_response.get("url"),
                headline=variant.text_variant.headline,
                body=variant.text_variant.primary_text,
                description=variant.text_variant.description,
                call_to_action_type=variant.text_variant.cta_type.value,
            )
            
            creative_id = creative_response.get("id")
            
            # 4. Create ad
            ad_response = await self.client.create_ad(
                ad_account_id=ad_account_id,
                adset_id=adset_id,
                creative_id=creative_id,
                name=f"Ad_{variant.variant_id}",
                status="PAUSED",  # Iniciar pausado
            )
            
            ad_id = ad_response.get("id")
            
            return UploadVariantResponse(
                success=True,
                variant_id=variant.variant_id,
                meta_creative_id=creative_id,
                meta_ad_id=ad_id,
            )
            
        except Exception as e:
            logger.error(f"Error uploading variant {variant.variant_id}: {e}")
            return UploadVariantResponse(
                success=False,
                variant_id=variant.variant_id,
                error=str(e),
            )
    
    async def _upload_stub(
        self,
        variant: CreativeVariant,
        ad_account_id: str,
        campaign_id: str,
        adset_id: str
    ) -> UploadVariantResponse:
        """Upload en modo stub (testing)."""
        import uuid
        
        creative_id = f"stub_creative_{uuid.uuid4().hex[:12]}"
        ad_id = f"stub_ad_{uuid.uuid4().hex[:12]}"
        
        logger.info(f"STUB: Uploaded variant {variant.variant_id} -> creative_id={creative_id}")
        
        return UploadVariantResponse(
            success=True,
            variant_id=variant.variant_id,
            meta_creative_id=creative_id,
            meta_ad_id=ad_id,
        )
