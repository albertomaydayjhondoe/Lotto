"""
Tests for Industry Crawler subsystem
"""

import pytest
from backend.app.outreach_intelligence.industry_crawler import (
    CrawlerStub,
    PlatformType,
    ScoringModelStub,
    LegalCompliance,
    DiscoveryRules
)


def test_crawler_spotify_discovery():
    """Test Spotify playlist discovery"""
    crawler = CrawlerStub()
    
    playlists = crawler.discover_spotify_playlists(
        genre="Deep House",
        min_followers=1000,
        accepts_submissions=True
    )
    
    assert len(playlists) > 0
    assert playlists[0]["platform"] == PlatformType.SPOTIFY_PLAYLIST.value
    assert playlists[0]["follower_count"] >= 1000


def test_crawler_youtube_discovery():
    """Test YouTube channel discovery"""
    crawler = CrawlerStub()
    
    channels = crawler.discover_youtube_channels(
        content_type="music_review",
        min_subscribers=10000
    )
    
    assert len(channels) > 0
    assert channels[0]["platform"] == PlatformType.YOUTUBE_CHANNEL.value
    assert channels[0]["subscriber_count"] >= 10000


def test_crawler_comprehensive_crawl(sample_track_metadata):
    """Test comprehensive multi-platform crawl"""