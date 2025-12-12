"""
Meta Ads API Types

TypedDict definitions for Meta Marketing API responses.
These types match the structure returned by Meta's Graph API.
"""

from typing import TypedDict, NotRequired, Literal


# Campaign Types
class CampaignResponse(TypedDict):
    """Response structure from Meta API for Campaign objects."""
    id: str
    name: str
    account_id: str
    status: Literal["ACTIVE", "PAUSED", "DELETED", "ARCHIVED"]
    objective: str
    daily_budget: NotRequired[str]
    lifetime_budget: NotRequired[str]
    bid_strategy: NotRequired[str]
    created_time: str
    updated_time: str
    start_time: NotRequired[str]
    stop_time: NotRequired[str]
    effective_status: NotRequired[str]
    can_use_spend_cap: NotRequired[bool]
    spend_cap: NotRequired[str]


class CampaignCreateRequest(TypedDict):
    """Request payload for creating a Meta campaign."""
    name: str
    objective: str
    status: str
    special_ad_categories: NotRequired[list[str]]
    daily_budget: NotRequired[int]
    lifetime_budget: NotRequired[int]
    bid_strategy: NotRequired[str]
    start_time: NotRequired[str]
    stop_time: NotRequired[str]


# AdSet Types
class AdSetTargeting(TypedDict):
    """Targeting specification for AdSets."""
    age_min: NotRequired[int]
    age_max: NotRequired[int]
    genders: NotRequired[list[int]]
    geo_locations: NotRequired[dict]
    interests: NotRequired[list[dict]]
    flexible_spec: NotRequired[list[dict]]
    targeting_optimization: NotRequired[str]


class AdSetResponse(TypedDict):
    """Response structure from Meta API for AdSet objects."""
    id: str
    name: str
    campaign_id: str
    account_id: str
    status: Literal["ACTIVE", "PAUSED", "DELETED", "ARCHIVED"]
    daily_budget: NotRequired[str]
    lifetime_budget: NotRequired[str]
    bid_amount: NotRequired[str]
    billing_event: NotRequired[str]
    optimization_goal: str
    targeting: NotRequired[AdSetTargeting]
    start_time: NotRequired[str]
    end_time: NotRequired[str]
    created_time: str
    updated_time: str
    effective_status: NotRequired[str]
    is_dynamic_creative: NotRequired[bool]


class AdSetCreateRequest(TypedDict):
    """Request payload for creating a Meta AdSet."""
    name: str
    campaign_id: str
    status: str
    optimization_goal: str
    billing_event: str
    bid_amount: NotRequired[int]
    daily_budget: NotRequired[int]
    lifetime_budget: NotRequired[int]
    start_time: NotRequired[str]
    end_time: NotRequired[str]
    targeting: NotRequired[AdSetTargeting]


# Ad Creative Types
class AdCreativeObjectStorySpec(TypedDict):
    """Object story spec for ad creative."""
    page_id: str
    video_data: NotRequired[dict]
    link_data: NotRequired[dict]
    photo_data: NotRequired[dict]


class AdCreativeResponse(TypedDict):
    """Response structure from Meta API for AdCreative objects."""
    id: str
    name: str
    object_story_spec: NotRequired[AdCreativeObjectStorySpec]
    object_type: NotRequired[str]
    status: NotRequired[str]
    thumbnail_url: NotRequired[str]
    video_id: NotRequired[str]


# Ad Types
class AdResponse(TypedDict):
    """Response structure from Meta API for Ad objects."""
    id: str
    name: str
    adset_id: str
    campaign_id: str
    account_id: str
    creative: NotRequired[dict]
    status: Literal["ACTIVE", "PAUSED", "DELETED", "ARCHIVED"]
    effective_status: NotRequired[str]
    created_time: str
    updated_time: str
    tracking_specs: NotRequired[list[dict]]
    conversion_specs: NotRequired[list[dict]]


class AdCreateRequest(TypedDict):
    """Request payload for creating a Meta Ad."""
    name: str
    adset_id: str
    creative: dict
    status: str
    tracking_specs: NotRequired[list[dict]]


# Video Upload Types
class VideoUploadResponse(TypedDict):
    """Response structure from Meta API for video uploads."""
    id: str
    title: NotRequired[str]
    description: NotRequired[str]
    source: NotRequired[str]
    status: NotRequired[dict]
    created_time: NotRequired[str]


class VideoUploadRequest(TypedDict):
    """Request payload for uploading video to Meta."""
    title: str
    description: NotRequired[str]
    file_url: NotRequired[str]
    file_size: NotRequired[int]


# Insights Types
class InsightsMetrics(TypedDict):
    """Metrics data from insights response."""
    impressions: NotRequired[str]
    clicks: NotRequired[str]
    spend: NotRequired[str]
    reach: NotRequired[str]
    frequency: NotRequired[str]
    cpm: NotRequired[str]
    cpc: NotRequired[str]
    ctr: NotRequired[str]
    cpp: NotRequired[str]
    cost_per_unique_click: NotRequired[str]
    actions: NotRequired[list[dict]]
    action_values: NotRequired[list[dict]]
    video_views: NotRequired[str]
    video_p25_watched_actions: NotRequired[list[dict]]
    video_p50_watched_actions: NotRequired[list[dict]]
    video_p75_watched_actions: NotRequired[list[dict]]
    video_p100_watched_actions: NotRequired[list[dict]]


class InsightsResponse(TypedDict):
    """Response structure from Meta API for Insights."""
    date_start: str
    date_stop: str
    account_id: NotRequired[str]
    campaign_id: NotRequired[str]
    adset_id: NotRequired[str]
    ad_id: NotRequired[str]
    impressions: NotRequired[str]
    clicks: NotRequired[str]
    spend: NotRequired[str]
    reach: NotRequired[str]
    frequency: NotRequired[str]
    cpm: NotRequired[str]
    cpc: NotRequired[str]
    ctr: NotRequired[str]
    actions: NotRequired[list[dict]]
    action_values: NotRequired[list[dict]]


class InsightsRequestParams(TypedDict):
    """Parameters for requesting insights from Meta API."""
    level: Literal["account", "campaign", "adset", "ad"]
    date_preset: NotRequired[str]
    time_range: NotRequired[dict]
    fields: list[str]
    filtering: NotRequired[list[dict]]
    breakdowns: NotRequired[list[str]]
    action_attribution_windows: NotRequired[list[str]]


# Error Types
class MetaErrorDetail(TypedDict):
    """Error detail structure from Meta API."""
    message: str
    type: str
    code: int
    error_subcode: NotRequired[int]
    error_user_title: NotRequired[str]
    error_user_msg: NotRequired[str]
    fbtrace_id: NotRequired[str]


class MetaErrorResponse(TypedDict):
    """Error response structure from Meta API."""
    error: MetaErrorDetail
