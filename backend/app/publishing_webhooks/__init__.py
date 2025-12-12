"""
Publishing Webhooks module.

Simulated webhook handlers for social media platform callbacks.
"""

from app.publishing_webhooks.instagram import handle_instagram_webhook
from app.publishing_webhooks.tiktok import handle_tiktok_webhook
from app.publishing_webhooks.youtube import handle_youtube_webhook

__all__ = [
    "handle_instagram_webhook",
    "handle_tiktok_webhook",
    "handle_youtube_webhook",
]
