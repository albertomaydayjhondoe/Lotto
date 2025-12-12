"""
Meta Ads API Client Module

Provides a client for interacting with Meta Marketing API (Facebook Ads).
Supports STUB mode (no real API calls) and LIVE mode (prepared for production).
"""

from .client import MetaAdsClient
from .exceptions import MetaAPIError, MetaAuthError, MetaRateLimitError
from .factory import get_meta_client_for_account

__all__ = [
    "MetaAdsClient",
    "MetaAPIError",
    "MetaAuthError",
    "MetaRateLimitError",
    "get_meta_client_for_account",
]
