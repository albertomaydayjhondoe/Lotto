"""
Playlist Intelligence — Post-Release Engine

Handles playlist strategy after track release.
STUB MODE: Returns mock recommendations with Spotify URL.
"""

from typing import Dict, List, Any
from datetime import datetime

from .analyzer_stub import PlaylistAnalyzerStub, TrackAnalysis
from .matcher_stub import PlaylistMatcherStub, PlaylistMatch
from .trend_map_stub import TrendMapStub
from .playlist_database_stub import PlaylistDatabaseStub


class PostReleaseEngine:
    """
    STUB: Manages playlist strategy for released tracks.
    
    Uses Spotify track URL/ID to find optimal playlists and
    create comprehensive outreach strategy.
    
    In LIVE mode, this would use:
    - Spotify API for real track data
    - Streaming analytics
    - Playlist add/remove monitoring
    - Curator engagement tracking
    
    Phase 3: Returns mock strategy with Spotify URL stub.
    """
    
    def __init__(self):
        self.stub_mode = True
        self.analyzer = PlaylistAnalyzerStub()
        self.matcher = PlaylistMatcherStub()
        self.trend_map = TrendMapStub()
        self.playlist_db = PlaylistDatabaseStub()
        
    def create_post_release_strategy(
        self,
        track_metadata: Dict[str, Any],
        spotify_url: str = None
    ) -> Dict[str, Any]:
        """
        STUB: Create complete post-release playlist strategy.
        
        Args:
            track_metadata: Track information
            spotify_url: Spotify track URL (STUB in Phase 3)
            
        Returns:
            Post-release strategy dict
        """
        # Analyze track
        track_analysis = self.analyzer.analyze_track(track_metadata)
        
        # Find all matching playlists (released tracks can target all)
        matches = self.matcher.match_track(track_analysis, is_released=True)
        
        # Get trend analysis
        trend_data = self.trend_map.predict_playlist_demand(
            track_analysis.genre,
            track_analysis.mood,
            track_analysis.bpm
        )
        
        # Get saturation analysis
        saturation = self.trend_map.get_playlist_saturation(track_analysis.genre)
        
        # Prioritize matches
        high_priority = [m for m in matches if m.priority == "high"]
        medium_priority = [m for m in matches if m.priority == "medium"]
        low_priority = [m for m in matches if m.priority == "low"]
        
        strategy = {
            "status": "post_release",
            "track_id": track_analysis.track_id,
            "spotify_url": spotify_url or f"https://open.spotify.com/track/stub_{track_analysis.track_id}",
            "analysis": {
                "genre": track_analysis.genre,
                "subgenre": track_analysis.subgenre,
                "bpm": track_analysis.bpm,
                "key": track_analysis.key,
                "mood": track_analysis.mood,
                "energy": track_analysis.energy,
                "a_and_r_score": track_analysis.a_and_r_score,
                "production_quality": track_analysis.production_quality
            },
            "trend_analysis": trend_data,
            "saturation_analysis": saturation,
            "total_matching_playlists": len(matches),
            "priority_breakdown": {
                "high": len(high_priority),
                "medium": len(medium_priority),
                "low": len(low_priority)
            },
            "campaign_tiers": self._create_campaign_tiers(
                high_priority,
                medium_priority,
                low_priority
            ),
            "recommended_actions": self._generate_post_release_actions(
                track_analysis,
                matches,
                trend_data,
                saturation
            ),
            "outreach_schedule": self._create_post_release_schedule(
                high_priority,
                medium_priority,
                low_priority
            )
        }
        
        return strategy
    
    def _create_campaign_tiers(
        self,
        high_priority: List[PlaylistMatch],
        medium_priority: List[PlaylistMatch],
        low_priority: List[PlaylistMatch]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Organize playlists into campaign tiers"""
        
        return {
            "tier_1_premium": [
                {
                    "playlist_name": m.playlist.name,
                    "playlist_id": m.playlist.playlist_id,
                    "playlist_size": m.playlist.size,
                    "curator_email": m.playlist.curator_email,
                    "curator_name": m.playlist.curator_name,
                    "compatibility_score": m.compatibility_score,
                    "match_reasons": m.match_reasons,
                    "timing": "immediate",
                    "personalization_level": "high",
                    "follow_up_days": 7
                }
                for m in high_priority[:20]
            ],
            "tier_2_core": [
                {
                    "playlist_name": m.playlist.name,
                    "playlist_id": m.playlist.playlist_id,
                    "playlist_size": m.playlist.size,
                    "curator_email": m.playlist.curator_email,
                    "curator_name": m.playlist.curator_name,
                    "compatibility_score": m.compatibility_score,
                    "match_reasons": m.match_reasons,
                    "timing": "week 1-2",
                    "personalization_level": "medium",
                    "follow_up_days": 14
                }
                for m in high_priority[20:] + medium_priority[:30]
            ],
            "tier_3_volume": [
                {
                    "playlist_name": m.playlist.name,
                    "playlist_id": m.playlist.playlist_id,
                    "playlist_size": m.playlist.size,
                    "curator_email": m.playlist.curator_email,
                    "curator_name": m.playlist.curator_name,
                    "compatibility_score": m.compatibility_score,
                    "timing": "week 3-4",
                    "personalization_level": "low",
                    "follow_up_days": 21
                }
                for m in medium_priority[30:] + low_priority[:50]
            ]
        }
    
    def _generate_post_release_actions(
        self,
        track_analysis: TrackAnalysis,
        matches: List[PlaylistMatch],
        trend_data: Dict[str, Any],
        saturation: Dict[str, Any]
    ) -> List[str]:
        """Generate actionable recommendations for post-release"""
        actions = []
        
        # Match quality
        high_quality_matches = len([m for m in matches if m.compatibility_score >= 0.75])
        if high_quality_matches >= 30:
            actions.append(f"🎯 {high_quality_matches} high-quality matches - strong playlist potential")
        elif high_quality_matches >= 15:
            actions.append(f"✅ {high_quality_matches} quality matches - good opportunities")
        else:
            actions.append(f"⚠️ Limited high-quality matches - focus on niche positioning")
        
        # Saturation strategy
        if saturation["competition"] == "high":
            actions.append("🔥 High competition - emphasize unique angle and quality in pitches")
        elif saturation["competition"] == "medium":
            actions.append("📊 Moderate competition - focus on best-fit playlists first")
        else:
            actions.append("🌟 Low competition - good opportunity for wide reach")
        
        # Trend alignment
        if trend_data["demand_score"] >= 0.80:
            actions.append(f"📈 High demand for {track_analysis.genre} - move quickly")
        
        # Size distribution
        large_playlists = len([m for m in matches if m.playlist.size >= 50000])
        if large_playlists >= 10:
            actions.append(f"🎵 {large_playlists} large playlists matched - potential for significant reach")
        
        # BPM versatility
        compatible_genres = self.trend_map.get_genres_by_bpm(track_analysis.bpm)
        if len(compatible_genres) > 2:
            genres_str = ", ".join([g.genre for g in compatible_genres[:3]])
            actions.append(f"🔄 Cross-genre potential: {genres_str}")
        
        return actions
    
    def _create_post_release_schedule(
        self,
        high_priority: List[PlaylistMatch],
        medium_priority: List[PlaylistMatch],
        low_priority: List[PlaylistMatch]
    ) -> List[Dict[str, Any]]:
        """Create outreach schedule for post-release campaign"""
        
        schedule = []
        
        # Day 1-3: Premium curators
        if high_priority:
            schedule.append({
                "phase": "Premium Launch",
                "day_range": "1-3",
                "target_count": min(20, len(high_priority)),
                "playlists": "Tier 1 - High compatibility, large playlists",
                "message_type": "personalized_pitch",
                "goal": "Secure key playlist adds"
            })
        
        # Week 1: Core outreach
        if len(high_priority) > 20 or medium_priority:
            schedule.append({
                "phase": "Core Campaign",
                "day_range": "4-7",
                "target_count": min(50, len(high_priority[20:]) + len(medium_priority[:30])),
                "playlists": "Tier 1 overflow + Tier 2 core",
                "message_type": "semi_personalized",
                "goal": "Build momentum and coverage"
            })
        
        # Week 2: Volume push
        if len(medium_priority) > 30 or low_priority:
            schedule.append({
                "phase": "Volume Push",
                "day_range": "8-14",
                "target_count": min(100, len(medium_priority[30:]) + len(low_priority[:50])),
                "playlists": "Tier 2 extended + Tier 3",
                "message_type": "template_based",
                "goal": "Maximize reach and exposure"
            })
        
        # Week 3-4: Follow-ups and long-tail
        schedule.append({
            "phase": "Follow-up & Long-tail",
            "day_range": "15-30",
            "target_count": "remaining matches",
            "playlists": "All tiers - follow-ups and new opportunities",
            "message_type": "follow_up + fresh_pitches",
            "goal": "Convert pending responses, reach remaining curators"
        })
        
        return schedule
    
    def track_playlist_performance(
        self,
        track_id: str,
        playlist_ids: List[str]
    ) -> Dict[str, Any]:
        """
        STUB: Track performance metrics for playlists.
        
        In LIVE mode: Pull real Spotify streaming data.
        
        Args:
            track_id: Track identifier
            playlist_ids: List of playlist IDs to track
            
        Returns:
            Performance metrics dict
        """
        # STUB: Return mock performance data
        return {
            "track_id": track_id,
            "tracked_playlists": len(playlist_ids),
            "metrics": {
                "total_playlist_adds": len(playlist_ids) * 0.3,  # 30% conversion stub
                "avg_streams_per_playlist": 1250,
                "estimated_total_reach": len(playlist_ids) * 15000,
                "estimated_monthly_listeners_gain": len(playlist_ids) * 85
            },
            "top_performing_playlists": [
                {
                    "playlist_id": pid,
                    "estimated_streams": 3500,
                    "estimated_saves": 120,
                    "engagement_rate": 0.034
                }
                for pid in playlist_ids[:5]
            ],
            "stub_note": "STUB MODE - Replace with real Spotify analytics in Phase 4"
        }
