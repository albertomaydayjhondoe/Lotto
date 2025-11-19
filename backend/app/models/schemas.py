"""
Pydantic schemas matching the OpenAPI specification.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID


# Error Schema
class Error(BaseModel):
    """Error response schema."""
    code: int
    message: str


# Video Upload
class VideoUploadResponse(BaseModel):
    """Response for video upload."""
    video_asset_id: UUID
    job_id: UUID
    message: str


# Jobs
class JobParams(BaseModel):
    """Job parameters."""
    start_ms: Optional[int] = None
    end_ms: Optional[int] = None
    clip_id: Optional[str] = None
    n_variants: Optional[int] = None
    options: Optional[Dict[str, Any]] = None


class JobCreate(BaseModel):
    """Schema for creating a job."""
    job_type: str
    clip_id: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    dedup_key: Optional[str] = None


class Job(BaseModel):
    """Job schema."""
    id: UUID
    job_type: str
    status: str
    params: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Clips
class ClipCreate(BaseModel):
    """Schema for creating a clip."""
    video_asset_id: UUID
    start_ms: int
    end_ms: int
    params: Optional[Dict[str, Any]] = None


class ClipVariant(BaseModel):
    """Clip variant schema."""
    id: UUID
    clip_id: UUID
    variant_number: int
    platform: Optional[str] = None
    url: Optional[str] = None
    status: str
    
    class Config:
        from_attributes = True


class Clip(BaseModel):
    """Clip schema."""
    id: UUID
    start_ms: int
    end_ms: int
    duration_ms: int
    visual_score: Optional[float] = None
    status: Optional[str] = "pending"
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Clip Variants Request
class ClipVariantsRequest(BaseModel):
    """Request to create clip variants."""
    n_variants: int = Field(default=5, ge=1, le=20)
    options: Optional[Dict[str, Any]] = None
    dedup_key: Optional[str] = None


# Confirm Publish
class ConfirmPublishRequest(BaseModel):
    """Request to confirm clip publishing."""
    clip_id: UUID
    platform: str = "instagram"
    post_url: str
    post_id: str
    published_at: Optional[datetime] = None
    confirmed_by: UUID
    trace_id: Optional[str] = None


class ConfirmPublishResponse(BaseModel):
    """Response for confirm publish."""
    message: str
    trace_id: Optional[str] = None


# Campaigns
class CampaignTargeting(BaseModel):
    """Campaign targeting parameters."""
    countries: Optional[List[str]] = None
    age_range: Optional[List[int]] = None
    interests: Optional[List[str]] = None


class CampaignCreate(BaseModel):
    """Schema for creating a campaign."""
    name: str
    clip_id: UUID
    budget_cents: int
    targeting: Optional[CampaignTargeting] = None


class Campaign(BaseModel):
    """Campaign schema."""
    id: UUID
    name: str
    clip_id: UUID
    budget_cents: int
    status: str = "draft"
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Platform Rules
class PlatformRulesData(BaseModel):
    """Platform rules data."""
    min_retention: Optional[float] = None
    max_duration_seconds: Optional[int] = None
    aspect_ratio: Optional[str] = None
    min_visual_score: Optional[float] = None


class PlatformRulesCreate(BaseModel):
    """Schema for creating platform rules."""
    name: str
    rules: Dict[str, Any]


class PlatformRules(BaseModel):
    """Platform-specific rules schema."""
    id: UUID
    name: str
    rules: Dict[str, Any]
    status: str = "candidate"
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Webhook Instagram
class WebhookInstagramPayload(BaseModel):
    """Instagram webhook payload."""
    object: str
    entry: List[Dict[str, Any]]
