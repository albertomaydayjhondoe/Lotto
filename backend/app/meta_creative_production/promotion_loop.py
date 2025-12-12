"""Auto-Promotion Loop (PASO 10.17)"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4
import random

from app.meta_creative_production.schemas import (
    PromotionRequest, PromotionResult, AutoPromotionResult, GeneratedVariant
)

class AutoPromotionLoop:
    """
    Handles automatic upload to Meta Ads and promotion.
    
    Flow:
    1. Upload variant via MetaAdsClient (10.2) + Orchestrator (10.3)
    2. Register in DB with parent_id, variant_type
    3. Associate with campaign/adset from 10.12, 10.5
    4. Track promotion status
    """
    
    def __init__(self, mode: str = "stub"):
        self.mode = mode
    
    async def upload_variant(
        self,
        request: PromotionRequest
    ) -> PromotionResult:
        """Upload single variant to Meta Ads"""
        
        if self.mode == "stub":
            # STUB: Simulate upload
            success = random.choice([True, True, True, False])  # 75% success rate
            
            return PromotionResult(
                success=success,
                variant_id=request.variant_id,
                meta_creative_id=f"stub_creative_{uuid4().hex[:8]}" if success else None,
                meta_ad_id=f"stub_ad_{uuid4().hex[:8]}" if success else None,
                campaign_id=request.campaign_id,
                message="Upload successful (STUB)" if success else "Upload failed (STUB)",
                uploaded_at=datetime.utcnow()
            )
        
        # LIVE: Upload via MetaAdsClient (10.2) + Orchestrator (10.3)
        # TODO: Implement real Meta Ads upload
        # 1. Call MetaAdsClient.upload_creative()
        # 2. Call MetaOrchestrator.associate_campaign()
        # 3. Store meta_creative_id and meta_ad_id in DB
        
        return PromotionResult(
            success=False,
            variant_id=request.variant_id,
            campaign_id=request.campaign_id,
            message="LIVE mode not implemented",
            uploaded_at=datetime.utcnow()
        )
    
    async def register_in_db(
        self,
        variant: GeneratedVariant,
        promotion_result: PromotionResult
    ) -> bool:
        """Register variant in database with Meta IDs"""
        
        if self.mode == "stub":
            # STUB: Simulate DB registration
            return True
        
        # LIVE: Store in MetaCreativeVariantModel
        # TODO: Update variant with meta_creative_id, meta_ad_id, upload_status
        return False
    
    async def associate_campaign(
        self,
        variant_id: UUID,
        campaign_id: UUID,
        adset_id: Optional[UUID] = None
    ) -> bool:
        """Associate variant with campaign/adset"""
        
        if self.mode == "stub":
            # STUB: Simulate association
            return True
        
        # LIVE: Query 10.12 (Targeting Optimizer) and 10.5 (ROAS Engine)
        # TODO: Get best campaign/adset for this variant
        return False
    
    async def promote_top_variants(
        self,
        variants: List[GeneratedVariant],
        campaign_id: UUID,
        top_n: int = 3
    ) -> AutoPromotionResult:
        """Promote top N variants automatically"""
        start_time = datetime.utcnow()
        
        # Sort by estimated score
        sorted_variants = sorted(variants, key=lambda v: v.estimated_score, reverse=True)
        top_variants = sorted_variants[:top_n]
        
        promotions: List[PromotionResult] = []
        
        for variant in top_variants:
            request = PromotionRequest(
                variant_id=variant.variant_id,
                campaign_id=campaign_id,
                force=False
            )
            
            result = await self.upload_variant(request)
            promotions.append(result)
            
            if result.success:
                await self.register_in_db(variant, result)
                await self.associate_campaign(variant.variant_id, campaign_id)
        
        elapsed = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        if elapsed == 0:
            elapsed = 1  # Ensure non-zero
        
        successful = [p for p in promotions if p.success]
        
        return AutoPromotionResult(
            variants_uploaded=len(successful),
            promotions=promotions,
            top_3_promoted=[v.variant_id for v in top_variants[:len(successful)]],
            total_time_ms=elapsed
        )
    
    async def track_promotion(
        self,
        variant_id: UUID
    ) -> Optional[PromotionResult]:
        """Track promotion status"""
        
        if self.mode == "stub":
            # STUB: Return synthetic status
            return None
        
        # LIVE: Query MetaCreativePromotionLogModel
        # TODO: Get latest promotion log for variant
        return None
