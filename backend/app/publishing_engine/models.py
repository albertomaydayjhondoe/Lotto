"""Pydantic models for Publishing Engine."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class PublishRequest(BaseModel):
    """Request to publish a clip to a social platform."""
    
    clip_id: UUID = Field(description="ID of the clip to publish")
    platform: str = Field(description="Target platform: instagram, tiktok, youtube, other")
    social_account_id: Optional[UUID] = Field(
        default=None,
        description="ID of the social account to publish to (optional)"
    )
    extra_metadata: Optional[dict] = Field(
        default=None,
        description="Additional metadata like caption, hashtags, etc."
    )


class PublishResult(BaseModel):
    """Result of a publish operation."""
    
    success: bool = Field(description="Whether the publish was successful")
    external_post_id: Optional[str] = Field(
        default=None,
        description="Platform-specific post ID"
    )
    external_url: Optional[str] = Field(
        default=None,
        description="URL of the published post"
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if publish failed"
    )
    platform: str = Field(description="Platform where publish was attempted")
    clip_id: UUID = Field(description="ID of the clip that was published")
    social_account_id: Optional[UUID] = Field(
        default=None,
        description="ID of the social account used"
    )


class PublishLogResponse(BaseModel):
    """Response model for publish log queries."""
    
    id: UUID
    clip_id: UUID
    platform: str
    social_account_id: Optional[UUID]
    status: str
    external_post_id: Optional[str]
    external_url: Optional[str]
    error_message: Optional[str]
    requested_at: datetime
    published_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
