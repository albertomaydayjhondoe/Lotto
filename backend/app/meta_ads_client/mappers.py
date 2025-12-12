"""
Meta Ads API Response Mappers

Functions to convert Meta API responses to model dictionaries
that can be used to create database model instances.
"""

from datetime import datetime, timezone
from typing import Any

from .types import (
    CampaignResponse,
    AdSetResponse,
    AdResponse,
    InsightsResponse,
)


def map_campaign_response_to_model_dict(
    response: CampaignResponse,
    social_account_id: int,
) -> dict[str, Any]:
    """
    Map Meta Campaign API response to MetaCampaign model dictionary.
    
    Args:
        response: Campaign response from Meta API
        social_account_id: Social account ID from our database
        
    Returns:
        Dictionary that can be used to create MetaCampaign model
    """
    return {
        "social_account_id": social_account_id,
        "campaign_id": response["id"],
        "name": response["name"],
        "status": response["status"],
        "objective": response["objective"],
        "daily_budget": int(response["daily_budget"]) if response.get("daily_budget") else None,
        "lifetime_budget": int(response["lifetime_budget"]) if response.get("lifetime_budget") else None,
        "bid_strategy": response.get("bid_strategy"),
        "effective_status": response.get("effective_status", response["status"]),
        "created_at": _parse_meta_timestamp(response.get("created_time")),
        "updated_at": _parse_meta_timestamp(response.get("updated_time")),
    }


def map_adset_response_to_model_dict(
    response: AdSetResponse,
    campaign_db_id: int,
    social_account_id: int,
) -> dict[str, Any]:
    """
    Map Meta AdSet API response to MetaAdSet model dictionary.
    
    Args:
        response: AdSet response from Meta API
        campaign_db_id: Campaign database ID (from MetaCampaign.id)
        social_account_id: Social account ID from our database
        
    Returns:
        Dictionary that can be used to create MetaAdSet model
    """
    return {
        "campaign_id": campaign_db_id,
        "social_account_id": social_account_id,
        "adset_id": response["id"],
        "name": response["name"],
        "status": response["status"],
        "optimization_goal": response["optimization_goal"],
        "billing_event": response.get("billing_event"),
        "daily_budget": int(response["daily_budget"]) if response.get("daily_budget") else None,
        "lifetime_budget": int(response["lifetime_budget"]) if response.get("lifetime_budget") else None,
        "bid_amount": int(response["bid_amount"]) if response.get("bid_amount") else None,
        "targeting": response.get("targeting"),
        "effective_status": response.get("effective_status", response["status"]),
        "created_at": _parse_meta_timestamp(response.get("created_time")),
        "updated_at": _parse_meta_timestamp(response.get("updated_time")),
    }


def map_ad_response_to_model_dict(
    response: AdResponse,
    adset_db_id: int,
    social_account_id: int,
    creative_id: str | None = None,
) -> dict[str, Any]:
    """
    Map Meta Ad API response to MetaAd model dictionary.
    
    Args:
        response: Ad response from Meta API
        adset_db_id: AdSet database ID (from MetaAdSet.id)
        social_account_id: Social account ID from our database
        creative_id: Creative ID if available
        
    Returns:
        Dictionary that can be used to create MetaAd model
    """
    # Extract creative ID from response if not provided
    if creative_id is None and response.get("creative"):
        creative_data = response["creative"]
        if isinstance(creative_data, dict):
            creative_id = creative_data.get("id")
    
    return {
        "adset_id": adset_db_id,
        "social_account_id": social_account_id,
        "ad_id": response["id"],
        "name": response["name"],
        "status": response["status"],
        "creative_id": creative_id,
        "effective_status": response.get("effective_status", response["status"]),
        "created_at": _parse_meta_timestamp(response.get("created_time")),
        "updated_at": _parse_meta_timestamp(response.get("updated_time")),
    }


def map_insights_response_to_model_dict(
    response: InsightsResponse,
    campaign_db_id: int | None = None,
    adset_db_id: int | None = None,
    ad_db_id: int | None = None,
) -> dict[str, Any]:
    """
    Map Meta Insights API response to MetaInsights model dictionary.
    
    Args:
        response: Insights response from Meta API
        campaign_db_id: Campaign database ID (optional)
        adset_db_id: AdSet database ID (optional)
        ad_db_id: Ad database ID (optional)
        
    Returns:
        Dictionary that can be used to create MetaInsights model
    """
    # Parse actions to extract specific metrics
    actions = response.get("actions", [])
    link_clicks = _extract_action_value(actions, "link_click")
    page_engagement = _extract_action_value(actions, "page_engagement")
    post_engagement = _extract_action_value(actions, "post_engagement")
    video_view = _extract_action_value(actions, "video_view")
    
    return {
        "campaign_id": campaign_db_id,
        "adset_id": adset_db_id,
        "ad_id": ad_db_id,
        "date_start": response["date_start"],
        "date_stop": response["date_stop"],
        "impressions": int(response["impressions"]) if response.get("impressions") else 0,
        "clicks": int(response["clicks"]) if response.get("clicks") else 0,
        "spend": float(response["spend"]) if response.get("spend") else 0.0,
        "reach": int(response["reach"]) if response.get("reach") else None,
        "frequency": float(response["frequency"]) if response.get("frequency") else None,
        "cpm": float(response["cpm"]) if response.get("cpm") else None,
        "cpc": float(response["cpc"]) if response.get("cpc") else None,
        "ctr": float(response["ctr"]) if response.get("ctr") else None,
        "link_clicks": link_clicks,
        "page_engagement": page_engagement,
        "post_engagement": post_engagement,
        "video_views": video_view,
        "raw_actions": actions,  # Store full actions array for reference
    }


def _parse_meta_timestamp(timestamp: str | None) -> datetime | None:
    """
    Parse Meta API timestamp to Python datetime.
    
    Meta timestamps are in ISO 8601 format.
    
    Args:
        timestamp: Timestamp string from Meta API
        
    Returns:
        Datetime object or None
    """
    if not timestamp:
        return None
    
    try:
        # Try parsing with timezone info
        if "+" in timestamp or timestamp.endswith("Z"):
            return datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        # Assume UTC if no timezone
        return datetime.fromisoformat(timestamp).replace(tzinfo=timezone.utc)
    except (ValueError, AttributeError):
        return None


def _extract_action_value(actions: list[dict], action_type: str) -> int | None:
    """
    Extract value for a specific action type from actions array.
    
    Args:
        actions: List of action dictionaries from Meta API
        action_type: Action type to extract (e.g., "link_click")
        
    Returns:
        Action value as integer or None if not found
    """
    for action in actions:
        if action.get("action_type") == action_type:
            try:
                return int(action.get("value", 0))
            except (ValueError, TypeError):
                return None
    return None
