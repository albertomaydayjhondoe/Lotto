"""Orchestration Request/Response Models"""

from typing import Any, Literal
from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID


class OrchestrationRequest(BaseModel):
    """Request to orchestrate a complete Meta Ads campaign."""
    social_account_id: UUID
    clip_id: UUID
    campaign_name: str
    campaign_objective: Literal["OUTCOME_AWARENESS", "OUTCOME_TRAFFIC", "OUTCOME_ENGAGEMENT", "OUTCOME_LEADS", "OUTCOME_APP_PROMOTION", "OUTCOME_SALES"] = "OUTCOME_TRAFFIC"
    daily_budget_cents: int = Field(ge=100)
    targeting: dict[str, Any] = Field(default_factory=lambda: {"geo_locations": {"countries": ["US"]}})
    optimization_goal: Literal["LINK_CLICKS", "IMPRESSIONS", "REACH", "LANDING_PAGE_VIEWS"] = "LINK_CLICKS"
    creative_title: str
    creative_description: str
    landing_url: str
    auto_publish: bool = False


class CampaignCreationResult(BaseModel):
    """Result of campaign creation."""
    campaign_db_id: int
    campaign_meta_id: str
    adset_db_id: int
    adset_meta_id: str
    ad_db_id: int
    ad_meta_id: str
    creative_db_id: int
    creative_meta_id: str
    success: bool = True
    error: str | None = None


class InsightsSyncResult(BaseModel):
    """Result of insights synchronization."""
    insights_synced: int = 0
    date_range_start: str
    date_range_end: str
    success: bool = True
    error: str | None = None


class OrchestrationResult(BaseModel):
    """Complete orchestration result."""
    request_id: str
    social_account_id: UUID
    clip_id: UUID
    campaign_creation: CampaignCreationResult | None = None
    insights_sync: InsightsSyncResult | None = None
    overall_success: bool = True
    errors: list[str] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    duration_seconds: float | None = None
