"""
FastAPI router for Publishing Integrations.

Provides endpoints to query available providers, their capabilities,
and validate post parameters without making actual API calls.
"""
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from app.publishing_integrations.instagram_client import InstagramPublishingClient
from app.publishing_integrations.tiktok_client import TikTokPublishingClient
from app.publishing_integrations.youtube_client import YouTubePublishingClient
from app.auth.permissions import require_role


router = APIRouter()


# Pydantic models for API
class ValidationRequest(BaseModel):
    """Request model for validating post parameters."""
    platform: str = Field(description="Platform: instagram, tiktok, youtube")
    params: Dict[str, Any] = Field(description="Platform-specific post parameters")


class ValidationResponse(BaseModel):
    """Response model for validation results."""
    platform: str
    valid: bool
    errors: List[str]


class ProviderInfo(BaseModel):
    """Response model for provider information."""
    platform: str
    authenticated: bool
    features: List[str]
    limits: Dict[str, Any]
    api_version: str
    documentation: str


# Provider registry
PROVIDERS = {
    "instagram": InstagramPublishingClient,
    "tiktok": TikTokPublishingClient,
    "youtube": YouTubePublishingClient
}


@router.get("/providers", response_model=List[str])
async def list_providers(
    _auth: dict = Depends(require_role("admin", "manager"))
):
    """
    Get list of available publishing providers.
    
    Returns:
        List of provider names (platforms)
    """
    return list(PROVIDERS.keys())


@router.get("/providers/{platform}", response_model=ProviderInfo)
async def get_provider_details(
    platform: str,
    _auth: dict = Depends(require_role("admin", "manager"))
):
    """
    Get detailed information about a specific provider.
    
    Args:
        platform: Platform name (instagram, tiktok, youtube)
        
    Returns:
        Provider capabilities, limits, and documentation
        
    Raises:
        HTTPException 404: Provider not found
    """
    if platform not in PROVIDERS:
        raise HTTPException(
            status_code=404,
            detail=f"Provider '{platform}' not found. Available: {', '.join(PROVIDERS.keys())}"
        )
    
    # Instantiate client (without authentication)
    client_class = PROVIDERS[platform]
    client = client_class()
    
    # Get capabilities
    capabilities = client.get_capabilities()
    
    return ProviderInfo(**capabilities)


@router.post("/validate", response_model=ValidationResponse)
async def validate_post_params(
    request: ValidationRequest,
    _auth: dict = Depends(require_role("admin", "manager"))
):
    """
    Validate post parameters for a specific platform.
    
    This endpoint validates parameters WITHOUT making actual API calls.
    Use it to check if your post data is valid before attempting to publish.
    
    Args:
        request: ValidationRequest with platform and params
        
    Returns:
        ValidationResponse with validation result
        
    Raises:
        HTTPException 404: Provider not found
    """
    if request.platform not in PROVIDERS:
        raise HTTPException(
            status_code=404,
            detail=f"Provider '{request.platform}' not found. Available: {', '.join(PROVIDERS.keys())}"
        )
    
    # Instantiate client
    client_class = PROVIDERS[request.platform]
    client = client_class()
    
    # Validate parameters
    validation_result = client.validate_post_params(**request.params)
    
    return ValidationResponse(
        platform=request.platform,
        valid=validation_result["valid"],
        errors=validation_result["errors"]
    )
