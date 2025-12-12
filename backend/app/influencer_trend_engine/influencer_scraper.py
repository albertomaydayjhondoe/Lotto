"""
Sprint 16: Influencer Trend Engine - Influencer Scraper

Multi-source intelligent scraper for extracting influencer data from URLs.

Supports:
- TikTok profiles
- Instagram profiles
- YouTube channels

Features:
- Metadata extraction
- Engagement metrics calculation
- Narrative/topic analysis
- Caching to avoid repeated scraping
- Rate limiting
- Robust error handling

Author: STAKAZO Project
Date: 2025-12-12
"""

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Any
from enum import Enum
import hashlib


class Platform(Enum):
    """Supported platforms"""
    TIKTOK = "tiktok"
    INSTAGRAM = "instagram"
    YOUTUBE = "youtube"
    UNKNOWN = "unknown"


class PostingFrequency(Enum):
    """Creator posting frequency"""
    VERY_HIGH = "very_high"  # >7 posts/week
    HIGH = "high"  # 4-7 posts/week
    MEDIUM = "medium"  # 2-3 posts/week
    LOW = "low"  # 1 post/week
    VERY_LOW = "very_low"  # <1 post/week


@dataclass
class InfluencerMetrics:
    """Raw metrics extracted from platform"""
    followers: int
    avg_views: float
    avg_likes: float
    avg_comments: float
    avg_shares: float
    total_posts: int
    posting_frequency: PostingFrequency
    engagement_rate: float  # (likes + comments) / followers
    view_to_follower_ratio: float  # avg_views / followers
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'followers': self.followers,
            'avg_views': self.avg_views,
            'avg_likes': self.avg_likes,
            'avg_comments': self.avg_comments,
            'avg_shares': self.avg_shares,
            'total_posts': self.total_posts,
            'posting_frequency': self.posting_frequency.value,
            'engagement_rate': self.engagement_rate,
            'view_to_follower_ratio': self.view_to_follower_ratio
        }


@dataclass
class InfluencerRawData:
    """Raw data scraped from influencer profile"""
    username: str
    platform: Platform
    profile_url: str
    metrics: InfluencerMetrics
    narrative_topics: List[str]
    video_styles: List[str]
    language: str
    verified: bool
    bio: str
    last_post_date: Optional[datetime]
    cultural_markers: List[str]
    scraped_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'username': self.username,
            'platform': self.platform.value,
            'profile_url': self.profile_url,
            'metrics': self.metrics.to_dict(),
            'narrative_topics': self.narrative_topics,
            'video_styles': self.video_styles,
            'language': self.language,
            'verified': self.verified,
            'bio': self.bio,
            'last_post_date': self.last_post_date.isoformat() if self.last_post_date else None,
            'cultural_markers': self.cultural_markers,
            'scraped_at': self.scraped_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'InfluencerRawData':
        metrics_data = data['metrics']
        metrics = InfluencerMetrics(
            followers=metrics_data['followers'],
            avg_views=metrics_data['avg_views'],
            avg_likes=metrics_data['avg_likes'],
            avg_comments=metrics_data['avg_comments'],
            avg_shares=metrics_data['avg_shares'],
            total_posts=metrics_data['total_posts'],
            posting_frequency=PostingFrequency(metrics_data['posting_frequency']),
            engagement_rate=metrics_data['engagement_rate'],
            view_to_follower_ratio=metrics_data['view_to_follower_ratio']
        )
        
        return cls(
            username=data['username'],
            platform=Platform(data['platform']),
            profile_url=data['profile_url'],
            metrics=metrics,
            narrative_topics=data['narrative_topics'],
            video_styles=data['video_styles'],
            language=data['language'],
            verified=data['verified'],
            bio=data['bio'],
            last_post_date=datetime.fromisoformat(data['last_post_date']) if data.get('last_post_date') else None,
            cultural_markers=data['cultural_markers'],
            scraped_at=datetime.fromisoformat(data['scraped_at'])
        )


class InfluencerScraper:
    """
    Multi-source intelligent scraper for influencer data.
    
    Features:
    - Platform detection from URL
    - Metadata extraction (followers, engagement, etc.)
    - Topic/style analysis
    - Caching (avoids repeated scraping)
    - Rate limiting
    - Fallback strategies
    
    Note: This is a simulated scraper for demo purposes.
    In production, integrate with actual APIs or scraping libraries.
    """
    
    def __init__(
        self,
        cache_dir: str = "storage/influencer_cache",
        cache_ttl_hours: int = 24
    ):
        """
        Initialize scraper.
        
        Args:
            cache_dir: Directory for caching scraped data
            cache_ttl_hours: Cache time-to-live in hours
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_ttl = timedelta(hours=cache_ttl_hours)
        
        # Rate limiting tracking
        self._request_timestamps: Dict[str, List[datetime]] = {}
        self._rate_limit_per_minute = 10
    
    def scrape_influencer(
        self,
        url: str,
        force_refresh: bool = False
    ) -> Optional[InfluencerRawData]:
        """
        Scrape influencer data from URL.
        
        Args:
            url: Profile URL
            force_refresh: Force re-scraping even if cached
        
        Returns:
            InfluencerRawData or None if failed
        """
        # Check cache first
        if not force_refresh:
            cached = self._get_from_cache(url)
            if cached:
                return cached
        
        # Detect platform
        platform = self._detect_platform(url)
        if platform == Platform.UNKNOWN:
            print(f"Warning: Unknown platform for URL {url}")
            return None
        
        # Check rate limit
        if not self._check_rate_limit(platform.value):
            print(f"Warning: Rate limit exceeded for {platform.value}")
            return None
        
        # Scrape based on platform
        try:
            if platform == Platform.TIKTOK:
                data = self._scrape_tiktok(url)
            elif platform == Platform.INSTAGRAM:
                data = self._scrape_instagram(url)
            elif platform == Platform.YOUTUBE:
                data = self._scrape_youtube(url)
            else:
                return None
            
            # Cache result
            if data:
                self._save_to_cache(url, data)
            
            return data
        
        except Exception as e:
            print(f"Error scraping {url}: {e}")
            return None
    
    def scrape_multiple(
        self,
        urls: List[str],
        force_refresh: bool = False
    ) -> List[InfluencerRawData]:
        """
        Scrape multiple influencers.
        
        Args:
            urls: List of profile URLs
            force_refresh: Force re-scraping
        
        Returns:
            List of InfluencerRawData (skips failures)
        """
        results = []
        
        for url in urls:
            data = self.scrape_influencer(url, force_refresh=force_refresh)
            if data:
                results.append(data)
        
        return results
    
    def _detect_platform(self, url: str) -> Platform:
        """Detect platform from URL"""
        url_lower = url.lower()
        
        if 'tiktok.com' in url_lower:
            return Platform.TIKTOK
        elif 'instagram.com' in url_lower:
            return Platform.INSTAGRAM
        elif 'youtube.com' in url_lower or 'youtu.be' in url_lower:
            return Platform.YOUTUBE
        else:
            return Platform.UNKNOWN
    
    def _scrape_tiktok(self, url: str) -> Optional[InfluencerRawData]:
        """
        Scrape TikTok profile.
        
        Note: This is simulated. In production, use TikTok API or scraping library.
        """
        # Extract username from URL
        username = self._extract_username_tiktok(url)
        
        # Simulate scraping (in production, call actual API/scraper)
        # For demo, generate realistic-looking data
        followers = 128000
        avg_views = 54000
        avg_likes = 4200
        avg_comments = 180
        total_posts = 245
        
        metrics = InfluencerMetrics(
            followers=followers,
            avg_views=avg_views,
            avg_likes=avg_likes,
            avg_comments=avg_comments,
            avg_shares=avg_likes * 0.05,  # Estimate
            total_posts=total_posts,
            posting_frequency=self._calculate_posting_frequency(total_posts, 180),  # 180 days
            engagement_rate=(avg_likes + avg_comments) / followers,
            view_to_follower_ratio=avg_views / followers
        )
        
        return InfluencerRawData(
            username=username,
            platform=Platform.TIKTOK,
            profile_url=url,
            metrics=metrics,
            narrative_topics=["belleza", "lifestyle", "humor"],
            video_styles=["fast-cut", "trends", "mirror-shots"],
            language="es",
            verified=False,
            bio="Content creator | Beauty & Lifestyle 💄",
            last_post_date=datetime.now() - timedelta(days=2),
            cultural_markers=["latam", "gen-z", "urban"],
            scraped_at=datetime.now()
        )
    
    def _scrape_instagram(self, url: str) -> Optional[InfluencerRawData]:
        """Scrape Instagram profile (simulated)"""
        username = self._extract_username_instagram(url)
        
        followers = 85000
        avg_likes = 3200
        avg_comments = 95
        total_posts = 312
        
        metrics = InfluencerMetrics(
            followers=followers,
            avg_views=avg_likes * 10,  # Estimate for reels
            avg_likes=avg_likes,
            avg_comments=avg_comments,
            avg_shares=avg_likes * 0.03,
            total_posts=total_posts,
            posting_frequency=self._calculate_posting_frequency(total_posts, 365),
            engagement_rate=(avg_likes + avg_comments) / followers,
            view_to_follower_ratio=(avg_likes * 10) / followers
        )
        
        return InfluencerRawData(
            username=username,
            platform=Platform.INSTAGRAM,
            profile_url=url,
            metrics=metrics,
            narrative_topics=["fashion", "travel", "photography"],
            video_styles=["aesthetic", "cinematic", "carousel"],
            language="es",
            verified=True,
            bio="Photographer 📸 | Storyteller",
            last_post_date=datetime.now() - timedelta(days=1),
            cultural_markers=["latam", "millennial", "creative"],
            scraped_at=datetime.now()
        )
    
    def _scrape_youtube(self, url: str) -> Optional[InfluencerRawData]:
        """Scrape YouTube channel (simulated)"""
        username = self._extract_username_youtube(url)
        
        subscribers = 250000
        avg_views = 45000
        avg_likes = 2100
        avg_comments = 320
        total_videos = 156
        
        metrics = InfluencerMetrics(
            followers=subscribers,
            avg_views=avg_views,
            avg_likes=avg_likes,
            avg_comments=avg_comments,
            avg_shares=avg_likes * 0.08,
            total_posts=total_videos,
            posting_frequency=self._calculate_posting_frequency(total_videos, 730),  # 2 years
            engagement_rate=(avg_likes + avg_comments) / subscribers,
            view_to_follower_ratio=avg_views / subscribers
        )
        
        return InfluencerRawData(
            username=username,
            platform=Platform.YOUTUBE,
            profile_url=url,
            metrics=metrics,
            narrative_topics=["tech", "reviews", "tutorials"],
            video_styles=["talking-head", "screen-recording", "b-roll"],
            language="es",
            verified=True,
            bio="Tech reviews & tutorials",
            last_post_date=datetime.now() - timedelta(days=5),
            cultural_markers=["latam", "tech-savvy", "educator"],
            scraped_at=datetime.now()
        )
    
    def _calculate_posting_frequency(
        self,
        total_posts: int,
        days_active: int
    ) -> PostingFrequency:
        """Calculate posting frequency from total posts and days active"""
        posts_per_week = (total_posts / days_active) * 7
        
        if posts_per_week > 7:
            return PostingFrequency.VERY_HIGH
        elif posts_per_week >= 4:
            return PostingFrequency.HIGH
        elif posts_per_week >= 2:
            return PostingFrequency.MEDIUM
        elif posts_per_week >= 1:
            return PostingFrequency.LOW
        else:
            return PostingFrequency.VERY_LOW
    
    def _extract_username_tiktok(self, url: str) -> str:
        """Extract TikTok username from URL"""
        match = re.search(r'tiktok\.com/@([a-zA-Z0-9_\.]+)', url)
        return match.group(1) if match else "unknown_tiktok"
    
    def _extract_username_instagram(self, url: str) -> str:
        """Extract Instagram username from URL"""
        match = re.search(r'instagram\.com/([a-zA-Z0-9_\.]+)', url)
        return match.group(1) if match else "unknown_instagram"
    
    def _extract_username_youtube(self, url: str) -> str:
        """Extract YouTube channel name from URL"""
        match = re.search(r'youtube\.com/(@?[a-zA-Z0-9_-]+)', url)
        return match.group(1) if match else "unknown_youtube"
    
    def _check_rate_limit(self, platform: str) -> bool:
        """Check if rate limit allows request"""
        now = datetime.now()
        
        # Clean old timestamps
        if platform in self._request_timestamps:
            self._request_timestamps[platform] = [
                ts for ts in self._request_timestamps[platform]
                if now - ts < timedelta(minutes=1)
            ]
        else:
            self._request_timestamps[platform] = []
        
        # Check limit
        if len(self._request_timestamps[platform]) >= self._rate_limit_per_minute:
            return False
        
        # Record request
        self._request_timestamps[platform].append(now)
        return True
    
    def _get_cache_key(self, url: str) -> str:
        """Generate cache key from URL"""
        return hashlib.md5(url.encode()).hexdigest()
    
    def _get_from_cache(self, url: str) -> Optional[InfluencerRawData]:
        """Retrieve from cache if not expired"""
        cache_key = self._get_cache_key(url)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Check expiry
            scraped_at = datetime.fromisoformat(data['scraped_at'])
            if datetime.now() - scraped_at > self.cache_ttl:
                return None
            
            return InfluencerRawData.from_dict(data)
        
        except Exception as e:
            print(f"Warning: Failed to load cache: {e}")
            return None
    
    def _save_to_cache(self, url: str, data: InfluencerRawData):
        """Save to cache"""
        cache_key = self._get_cache_key(url)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data.to_dict(), f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to save cache: {e}")


if __name__ == "__main__":
    # Example usage
    scraper = InfluencerScraper()
    
    # Scrape single influencer
    url = "https://www.tiktok.com/@example_creator"
    data = scraper.scrape_influencer(url)
    
    if data:
        print("✓ Influencer scraped successfully")
        print(f"  Username: {data.username}")
        print(f"  Platform: {data.platform.value}")
        print(f"  Followers: {data.metrics.followers:,}")
        print(f"  Engagement rate: {data.metrics.engagement_rate:.2%}")
        print(f"  Topics: {', '.join(data.narrative_topics)}")
    
    # Scrape multiple
    urls = [
        "https://www.tiktok.com/@creator1",
        "https://www.instagram.com/creator2",
        "https://www.youtube.com/@creator3"
    ]
    
    results = scraper.scrape_multiple(urls)
    print(f"\n✓ Scraped {len(results)} influencers")
