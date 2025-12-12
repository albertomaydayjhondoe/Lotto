"""
Pydantic Models for Brand Engine (Sprint 4)

All models are completely agnostic - no presets or assumptions.
Everything is learned from:
1. Artist interrogation
2. Real metrics
3. Real visual content
"""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


# ========================================
# Enums
# ========================================

class ContentCategory(str, Enum):
    """Content categories (learned from artist responses)."""
    OFFICIAL = "official"  # Canal principal
    SATELLITE = "satellite"  # Cuentas satélite


class QuestionType(str, Enum):
    """Types of interrogation questions."""
    OPEN_TEXT = "open_text"
    MULTIPLE_CHOICE = "multiple_choice"
    RATING_SCALE = "rating_scale"
    COLOR_PICKER = "color_picker"
    YES_NO = "yes_no"


# ========================================
# 1. Brand Interrogator Models
# ========================================

class InterrogationQuestion(BaseModel):
    """Single question in the brand interrogation."""
    question_id: str
    question_text: str
    question_type: QuestionType
    category: str = Field(..., description="Category: aesthetic, narrative, tone, restrictions, etc.")
    options: Optional[List[str]] = None  # For multiple choice
    required: bool = True
    follow_up_questions: Optional[List[str]] = None  # IDs of follow-up questions


class InterrogationResponse(BaseModel):
    """Artist's response to a question."""
    question_id: str
    response_text: Optional[str] = None
    response_options: Optional[List[str]] = None  # For multiple choice
    response_rating: Optional[int] = Field(None, ge=1, le=10)
    response_color: Optional[str] = None  # Hex color
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class BrandProfile(BaseModel):
    """
    Complete brand profile learned from interrogation.
    
    NO presets - everything comes from artist responses.
    """
    profile_id: str
    artist_name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Aesthetic (learned from artist)
    primary_colors: List[str] = Field(default_factory=list, description="Hex colors chosen by artist")
    secondary_colors: List[str] = Field(default_factory=list)
    aesthetic_keywords: List[str] = Field(default_factory=list, description="Artist-defined aesthetic")
    visual_references: List[str] = Field(default_factory=list, description="Referenced artists/brands")
    
    # Narrative & Tone (learned from artist)
    brand_narrative: str = Field("", description="Artist's story/narrative")
    tone_of_voice: List[str] = Field(default_factory=list, description="e.g., ['energetic', 'raw', 'poetic']")
    key_messages: List[str] = Field(default_factory=list, description="Core messages to communicate")
    
    # Cultural References (chosen by artist)
    cultural_context: List[str] = Field(default_factory=list, description="e.g., ['galician', 'trap', 'street']")
    musical_influences: List[str] = Field(default_factory=list)
    geographic_roots: List[str] = Field(default_factory=list)
    
    # Content Rules (defined by artist)
    allowed_content: List[str] = Field(default_factory=list, description="What IS allowed")
    prohibited_content: List[str] = Field(default_factory=list, description="What is NOT allowed")
    content_guidelines: Dict[str, str] = Field(default_factory=dict)
    
    # Visual Coherence (artist preferences)
    preferred_scenes: List[str] = Field(default_factory=list, description="Preferred scene types")
    prohibited_scenes: List[str] = Field(default_factory=list, description="Scenes to avoid")
    
    # Long-term Vision (artist goals)
    brand_vision: str = Field("", description="Long-term brand vision")
    target_audience: str = Field("", description="Who is the target audience")
    success_metrics: List[str] = Field(default_factory=list)
    
    # Raw responses (for reference)
    interrogation_responses: List[InterrogationResponse] = Field(default_factory=list)
    
    model_config = {"json_schema_extra": {
        "example": {
            "profile_id": "profile_001",
            "artist_name": "Artist Name",
            "primary_colors": ["#8B44FF", "#1A1A2E"],
            "aesthetic_keywords": ["urban", "nocturnal", "energetic"],
            "brand_narrative": "Artist-defined story...",
            "tone_of_voice": ["raw", "authentic", "bold"],
            "cultural_context": ["street", "underground"],
            "allowed_content": ["cars", "nightlife", "urban"],
            "prohibited_content": ["violence", "explicit"],
            "brand_vision": "Artist's long-term vision..."
        }
    }}


# ========================================
# 2. Brand Metrics Models
# ========================================

class ContentPerformance(BaseModel):
    """Performance metrics for a single piece of content."""
    content_id: str
    content_type: str  # "clip", "post", "story"
    platform: str
    
    # Engagement metrics
    views: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    saves: int = 0
    
    # Retention metrics
    avg_watch_time_seconds: float = 0.0
    completion_rate: float = Field(0.0, ge=0.0, le=1.0)
    retention_rate: float = Field(0.0, ge=0.0, le=1.0)
    skip_rate: float = Field(0.0, ge=0.0, le=1.0)
    
    # Click-through metrics
    ctr: float = Field(0.0, ge=0.0, le=1.0, description="Click-through rate")
    link_clicks: int = 0
    
    # Visual characteristics (from Vision Engine)
    dominant_scene: Optional[str] = None
    dominant_colors: Optional[List[str]] = None
    aesthetic_score: Optional[float] = None
    
    published_at: datetime = Field(default_factory=datetime.utcnow)


class MetricInsights(BaseModel):
    """
    Insights learned from real content performance.
    
    NO assumptions - everything derived from actual data.
    """
    insights_id: str
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Performance patterns (learned from data)
    best_performing_scenes: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Scenes with highest engagement"
    )
    best_performing_colors: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Color palettes with highest engagement"
    )
    best_content_formats: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Formats with best retention"
    )
    
    # Correlations (data-driven)
    aesthetic_performance_correlation: Dict[str, float] = Field(
        default_factory=dict,
        description="Correlation between aesthetic features and performance"
    )
    scene_engagement_correlation: Dict[str, float] = Field(default_factory=dict)
    color_retention_correlation: Dict[str, float] = Field(default_factory=dict)
    
    # Averages (baseline metrics)
    avg_retention_rate: float = 0.0
    avg_completion_rate: float = 0.0
    avg_ctr: float = 0.0
    avg_engagement_rate: float = 0.0
    
    # Top performers
    top_performing_content: List[str] = Field(
        default_factory=list,
        description="IDs of top performing content"
    )
    
    # Statistical confidence
    sample_size: int = 0
    confidence_level: float = Field(0.0, ge=0.0, le=1.0)
    
    model_config = {"json_schema_extra": {
        "example": {
            "insights_id": "insights_001",
            "best_performing_scenes": [
                {"scene": "coche", "avg_retention": 0.75, "count": 15}
            ],
            "best_performing_colors": [
                {"color": "#8B44FF", "avg_engagement": 0.08, "count": 20}
            ],
            "avg_retention_rate": 0.65,
            "sample_size": 50
        }
    }}


# ========================================
# 3. Brand Aesthetic Extractor Models
# ========================================

class AestheticPattern(BaseModel):
    """A recurring aesthetic pattern detected in content."""
    pattern_name: str
    frequency: float = Field(..., ge=0.0, le=1.0, description="How often this appears")
    examples: List[str] = Field(..., description="Content IDs where this appears")
    confidence: float = Field(..., ge=0.0, le=1.0)


class AestheticDNA(BaseModel):
    """
    Visual DNA extracted from real content.
    
    NO presets - purely data-driven from artist's actual content.
    """
    dna_id: str
    extracted_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Dominant colors (extracted from real content)
    dominant_color_palette: List[str] = Field(
        default_factory=list,
        description="Most frequent colors across all content"
    )
    color_distribution: Dict[str, float] = Field(
        default_factory=dict,
        description="Percentage of each color family"
    )
    
    # Recurring scenes (from Vision Engine)
    recurring_scenes: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Most frequent scene types"
    )
    scene_distribution: Dict[str, float] = Field(default_factory=dict)
    
    # Recurring objects (from YOLO detections)
    recurring_objects: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Most frequent objects detected"
    )
    
    # Aesthetic patterns
    aesthetic_patterns: List[AestheticPattern] = Field(default_factory=list)
    
    # Visual consistency metrics
    color_consistency_score: float = Field(0.0, ge=0.0, le=1.0)
    scene_consistency_score: float = Field(0.0, ge=0.0, le=1.0)
    overall_coherence_score: float = Field(0.0, ge=0.0, le=1.0)
    
    # Sample size
    analyzed_content_count: int = 0
    
    model_config = {"json_schema_extra": {
        "example": {
            "dna_id": "dna_001",
            "dominant_color_palette": ["#8B44FF", "#1A1A2E", "#16213E"],
            "color_distribution": {"purple": 0.45, "dark_blue": 0.35, "black": 0.20},
            "recurring_scenes": [
                {"scene": "coche", "frequency": 0.35, "count": 18}
            ],
            "color_consistency_score": 0.82,
            "analyzed_content_count": 50
        }
    }}


# ========================================
# 4. Brand Static Rules (Generated Output)
# ========================================

class ColorRule(BaseModel):
    """Color rules for official content."""
    primary_palette: List[str] = Field(..., description="Primary hex colors")
    secondary_palette: List[str] = Field(default_factory=list)
    prohibited_colors: List[str] = Field(default_factory=list)
    min_consistency_score: float = Field(0.7, ge=0.0, le=1.0)


class SceneRule(BaseModel):
    """Scene rules for official content."""
    preferred_scenes: List[str] = Field(..., description="Scenes to prioritize")
    allowed_scenes: List[str] = Field(default_factory=list)
    prohibited_scenes: List[str] = Field(default_factory=list)
    min_scene_quality_score: float = Field(0.6, ge=0.0, le=1.0)


class ContentRule(BaseModel):
    """Content restrictions and guidelines."""
    allowed_themes: List[str] = Field(default_factory=list)
    prohibited_themes: List[str] = Field(default_factory=list)
    tone_requirements: List[str] = Field(default_factory=list)
    narrative_guidelines: List[str] = Field(default_factory=list)


class PerformanceThresholds(BaseModel):
    """Minimum performance thresholds for official content."""
    min_aesthetic_score: float = Field(0.6, ge=0.0, le=1.0)
    min_brand_affinity_score: float = Field(0.7, ge=0.0, le=1.0)
    min_virality_score: float = Field(0.5, ge=0.0, le=1.0)
    min_completion_rate: float = Field(0.5, ge=0.0, le=1.0)


class BrandStaticRules(BaseModel):
    """
    Auto-generated brand rules for OFFICIAL content only.
    
    Generated by Brand Rules Builder from:
    - BrandProfile (interrogation)
    - MetricInsights (real performance data)
    - AestheticDNA (visual analysis)
    
    SATELLITE accounts DO NOT follow these rules.
    """
    rules_id: str
    version: str = "1.0.0"
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Source components
    based_on_profile_id: str
    based_on_insights_id: str
    based_on_dna_id: str
    
    # Artist identity
    artist_name: str
    brand_narrative: str
    brand_vision: str
    
    # Visual rules
    color_rules: ColorRule
    scene_rules: SceneRule
    
    # Content rules
    content_rules: ContentRule
    
    # Performance thresholds
    performance_thresholds: PerformanceThresholds
    
    # Validation rules
    require_manual_approval: bool = True
    auto_reject_on_rule_violation: bool = False
    
    # Applicability
    applies_to_categories: List[ContentCategory] = Field(
        default=[ContentCategory.OFFICIAL],
        description="ONLY applies to official content, NOT satellites"
    )
    
    # Metadata
    approved_by_artist: bool = False
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = {"json_schema_extra": {
        "example": {
            "rules_id": "rules_001",
            "version": "1.0.0",
            "artist_name": "Artist Name",
            "brand_narrative": "Learned narrative...",
            "color_rules": {
                "primary_palette": ["#8B44FF", "#1A1A2E"],
                "min_consistency_score": 0.7
            },
            "scene_rules": {
                "preferred_scenes": ["coche", "urbano"],
                "prohibited_scenes": []
            },
            "applies_to_categories": ["official"]
        }
    }}


# ========================================
# 5. Validation Models
# ========================================

class ContentValidationResult(BaseModel):
    """Result of validating content against brand rules."""
    content_id: str
    is_valid: bool
    category: ContentCategory
    
    # Rule checks
    passes_color_rules: bool
    passes_scene_rules: bool
    passes_content_rules: bool
    passes_performance_thresholds: bool
    
    # Violations
    violations: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    
    # Scores
    aesthetic_score: float = 0.0
    brand_affinity_score: float = 0.0
    overall_compliance_score: float = 0.0
    
    # Decision
    recommendation: Literal["approve", "review", "reject"] = "review"
    reason: str = ""
    
    validated_at: datetime = Field(default_factory=datetime.utcnow)
