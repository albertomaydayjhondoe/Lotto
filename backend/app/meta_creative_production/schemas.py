"""Pydantic schemas for Meta Creative Production Engine (PASO 10.17)"""
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum

# ==================== ENUMS ====================

class VariantType(str, Enum):
    """Type of creative variant"""
    FRAGMENT_REORDER = "fragment_reorder"
    TEXT_OVERLAY = "text_overlay"
    CAPTION_OPTIMIZED = "caption_optimized"
    HASHTAG_VARIANT = "hashtag_variant"
    COLOR_LUT = "color_lut"
    DURATION_SHORT = "duration_short"  # 5-7s
    DURATION_MEDIUM = "duration_medium"  # 8-12s
    DURATION_LONG = "duration_long"  # 13-18s
    RECOMBINED = "recombined"

class NarrativeStructure(str, Enum):
    """Narrative structure type"""
    HOOK_BODY_CTA = "hook_body_cta"  # Standard
    HOOK_INVERTED = "hook_inverted"  # CTA first
    CTA_FORWARD = "cta_forward"  # CTA at beginning

class VariantStatus(str, Enum):
    """Status of variant"""
    GENERATED = "generated"
    UPLOADED = "uploaded"
    TESTING = "testing"
    ACTIVE = "active"
    FATIGUED = "fatigued"
    ARCHIVED = "archived"

class FragmentType(str, Enum):
    """Type of creative fragment"""
    HOOK = "hook"
    BODY = "body"
    CTA = "cta"
    OUTRO = "outro"

# ==================== INPUT SCHEMAS ====================

class MasterCreativeInput(BaseModel):
    """User input for master creative"""
    video_url: str = Field(..., description="Master creative video URL")
    title: str = Field(..., max_length=200)
    description: Optional[str] = None
    duration_seconds: float = Field(..., gt=0)
    pixels: List[str] = Field(..., min_length=1, description="Authorized pixels")
    genre: str
    subgenres: List[str] = Field(..., min_length=1)
    
    model_config = ConfigDict(from_attributes=True)

class CreativeFragmentInput(BaseModel):
    """User-approved fragment input"""
    fragment_id: UUID
    fragment_type: FragmentType
    start_time: float = Field(..., ge=0)
    end_time: float = Field(..., gt=0)
    duration: float = Field(..., gt=0)
    video_url: str
    approved: bool = True
    performance_score: Optional[float] = Field(None, ge=0, le=100)
    
    model_config = ConfigDict(from_attributes=True)

class StyleGuideInput(BaseModel):
    """Style guide and vibe instructions"""
    vibes: List[str] = Field(..., min_length=1, description="Style vibes")
    aesthetic_reference: str = Field(..., description="Aesthetic reference")
    color_palette: Optional[List[str]] = None
    font_style: Optional[str] = None
    music_style: Optional[str] = None
    tone: str = Field(default="energetic", description="Content tone")
    
    model_config = ConfigDict(from_attributes=True)

class CreativeProductionRequest(BaseModel):
    """Full production request"""
    master_creative: MasterCreativeInput
    fragments: List[CreativeFragmentInput] = Field(..., min_length=1)
    style_guide: StyleGuideInput
    campaign_id: Optional[UUID] = None
    generate_variants: bool = True
    auto_upload: bool = False
    mode: str = "stub"
    
    model_config = ConfigDict(from_attributes=True)

# ==================== VARIANT GENERATION ====================

class VariantGenerationConfig(BaseModel):
    """Configuration for variant generation"""
    min_variants: int = Field(5, ge=1, le=50)
    max_variants: int = Field(15, ge=1, le=50)
    enable_short_duration: bool = True  # 5-7s
    enable_medium_duration: bool = True  # 8-12s
    enable_long_duration: bool = True  # 13-18s
    enable_fragment_reorder: bool = True
    enable_text_overlay: bool = True
    enable_caption_optimization: bool = True
    enable_hashtag_variants: bool = True
    enable_color_luts: bool = True
    
    model_config = ConfigDict(from_attributes=True)

class GeneratedVariant(BaseModel):
    """Generated creative variant"""
    variant_id: UUID
    parent_id: UUID
    variant_type: VariantType
    narrative_structure: NarrativeStructure
    
    # Content
    fragments_order: List[UUID]  # Fragment IDs in order
    caption: str = Field(..., max_length=2200)
    hashtags: List[str] = Field(..., max_length=30)
    text_overlay: Optional[str] = None
    
    # Technical
    duration_seconds: float
    color_lut: Optional[str] = None
    
    # Scores
    estimated_score: float = Field(..., ge=0, le=100)
    confidence: float = Field(..., ge=0, le=1)
    
    # Metadata
    generated_at: datetime
    mode: str = "stub"
    
    model_config = ConfigDict(from_attributes=True)

class VariantGenerationResult(BaseModel):
    """Result of variant generation"""
    master_creative_id: UUID
    variants_generated: int
    variants: List[GeneratedVariant]
    generation_time_ms: int
    summary: str
    
    model_config = ConfigDict(from_attributes=True)

# ==================== RECOMBINATION ====================

class RecombinationRequest(BaseModel):
    """Request for creative recombination"""
    master_creative_id: UUID
    use_best_fragments: bool = True
    narrative_structures: List[NarrativeStructure] = Field(
        default=[NarrativeStructure.HOOK_BODY_CTA]
    )
    min_recombinations: int = Field(3, ge=1)
    
    model_config = ConfigDict(from_attributes=True)

class RecombinedCreative(BaseModel):
    """Recombined creative result"""
    recombined_id: UUID
    parent_id: UUID
    narrative_structure: NarrativeStructure
    fragments_used: List[UUID]
    
    # Fragment details
    hook_fragment_id: Optional[UUID] = None
    body_fragments: List[UUID] = Field(default_factory=list)
    cta_fragment_id: Optional[UUID] = None
    
    # Performance
    estimated_improvement: float = Field(..., description="Expected % improvement")
    confidence: float = Field(..., ge=0, le=1)
    
    # Content
    caption: str
    hashtags: List[str]
    duration_seconds: float
    
    recombined_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class RecombinationResult(BaseModel):
    """Result of recombination process"""
    master_creative_id: UUID
    recombinations_created: int
    recombinations: List[RecombinedCreative]
    best_structure: NarrativeStructure
    processing_time_ms: int
    
    model_config = ConfigDict(from_attributes=True)

# ==================== PROMOTION ====================

class PromotionRequest(BaseModel):
    """Request to promote variant to Meta Ads"""
    variant_id: UUID
    campaign_id: UUID
    adset_id: Optional[UUID] = None
    budget: Optional[float] = Field(None, gt=0)
    force: bool = False
    
    model_config = ConfigDict(from_attributes=True)

class PromotionResult(BaseModel):
    """Result of promotion to Meta Ads"""
    success: bool
    variant_id: UUID
    meta_creative_id: Optional[str] = None
    meta_ad_id: Optional[str] = None
    campaign_id: UUID
    message: str
    uploaded_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class AutoPromotionResult(BaseModel):
    """Result of auto-promotion loop"""
    variants_uploaded: int
    promotions: List[PromotionResult]
    top_3_promoted: List[UUID]
    total_time_ms: int
    
    model_config = ConfigDict(from_attributes=True)

# ==================== FATIGUE MONITORING ====================

class FatigueDetectionResult(BaseModel):
    """Result of fatigue detection"""
    variant_id: UUID
    is_fatigued: bool
    fatigue_score: float = Field(..., ge=0, le=100)
    days_active: int
    performance_drop: float  # % drop
    recommendation: str  # "archive", "refresh", "continue"
    
    model_config = ConfigDict(from_attributes=True)

class RefreshSuggestion(BaseModel):
    """Suggestion for creative refresh"""
    variant_id: UUID
    suggestion_type: str  # "new_fragments", "new_caption", "new_structure"
    reason: str
    estimated_impact: float
    prompt_for_user: str  # AI-generated prompt
    
    model_config = ConfigDict(from_attributes=True)

class FatigueMonitoringResult(BaseModel):
    """Result of fatigue monitoring cycle"""
    variants_checked: int
    fatigued_detected: int
    archived_count: int
    refresh_suggestions: List[RefreshSuggestion]
    new_variants_created: int
    
    model_config = ConfigDict(from_attributes=True)

# ==================== API SCHEMAS ====================

class ProductionEngineStatus(BaseModel):
    """Status of production engine"""
    status: str
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    total_masters: int
    total_variants: int
    active_variants: int
    fatigued_variants: int
    mode: str
    
    model_config = ConfigDict(from_attributes=True)

class RunProductionRequest(BaseModel):
    """Request to run full production cycle"""
    master_creative_ids: Optional[List[UUID]] = None
    generate_variants: bool = True
    auto_upload: bool = False
    promote_top_3: bool = True
    mode: str = "stub"
    
    model_config = ConfigDict(from_attributes=True)

class RunProductionResponse(BaseModel):
    """Response from production run"""
    production_id: UUID
    masters_processed: int
    variants_generated: int
    variants_uploaded: int
    top_3_promoted: List[UUID]
    fatigued_archived: int
    processing_time_ms: int
    summary: str
    started_at: datetime
    completed_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class VariantListResponse(BaseModel):
    """List of variants for a master creative"""
    master_creative_id: UUID
    total_variants: int
    active: int
    testing: int
    fatigued: int
    archived: int
    variants: List[GeneratedVariant]
    
    model_config = ConfigDict(from_attributes=True)

class ProductionHistoryResponse(BaseModel):
    """Production history"""
    total_runs: int
    total_variants_generated: int
    total_uploads: int
    avg_variants_per_master: float
    best_performing_structure: NarrativeStructure
    history: List[Dict[str, Any]]
    
    model_config = ConfigDict(from_attributes=True)
