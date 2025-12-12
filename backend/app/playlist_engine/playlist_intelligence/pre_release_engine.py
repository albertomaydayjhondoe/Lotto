"""
Playlist Intelligence — Pre-Release Engine

Handles playlist strategy before track release.
STUB MODE: Returns mock recommendations.
"""

from typing import Dict, List, Any
from datetime import datetime, timedelta

from .analyzer_stub import PlaylistAnalyzerStub, TrackAnalysis
from .matcher_stub import PlaylistMatcherStub, PlaylistMatch
from .trend_map_stub import TrendMapStub
from .playlist_database_stub import PlaylistDatabaseStub


class PreReleaseEngine:
    """
    STUB: Manages playlist strategy for unreleased tracks.
    
    Predicts playlist fit before release and identifies curators
    who accept unreleased music for early positioning.
    
    In LIVE mode, this would use:
    - Historical A&R data
    - Curator relationship history
    - Pre-save campaign data
    - Artist growth metrics
    
    Phase 3: Returns mock strategy recommendations.
    """
    
    def __init__(self):
        self.stub_mode = True
        self.analyzer = PlaylistAnalyzerStub()
        self.matcher = PlaylistMatcherStub()
        self.trend_map = TrendMapStub()
        self.playlist_db = PlaylistDatabaseStub()
        
    def create_pre_release_strategy(
        self,
        track_metadata: Dict[str, Any],
        release_date: str = None
    ) -> Dict[str, Any]:
        """
        STUB: Create complete pre-release playlist strategy.
        
        Args:
            track_metadata: Track information (no Spotify URL yet)
            release_date: Planned release date (ISO format)
            
        Returns:
            Pre-release strategy dict
        """
        # Analyze track
        track_analysis = self.analyzer.analyze_track(track_metadata)
        
        # Find matching playlists that accept unreleased
        matches = self.matcher.match_track(track_analysis, is_released=False)
        
        # Get trend analysis
        trend_data = self.trend_map.predict_playlist_demand(
            track_analysis.genre,
            track_analysis.mood,
            track_analysis.bpm
        )
        
        # Filter for high-priority unreleased opportunities
        unreleased_opportunities = [
            m for m in matches
            if m.playlist.accepts_unreleased and m.compatibility_score >= 0.65
        ]
        
        # Create strategy phases
        strategy = {
            "status": "pre_release",
            "track_id": track_analysis.track_id,
            "release_date": release_date,
            "analysis": {
                "genre": track_analysis.genre,
                "subgenre": track_analysis.subgenre,
                "bpm": track_analysis.bpm,
                "mood": track_analysis.mood,
                "a_and_r_score": track_analysis.a_and_r_score,
                "production_quality": track_analysis.production_quality
            },
            "trend_analysis": trend_data,
            "total_matching_playlists": len(matches),
            "unreleased_opportunities": len(unreleased_opportunities),
            "phases": self._create_strategy_phases(
                unreleased_opportunities,
                release_date
            ),
            "recommended_actions": self._generate_pre_release_actions(
                track_analysis,
                unreleased_opportunities,
                trend_data
            ),
            "curator_outreach_timeline": self._create_outreach_timeline(
                unreleased_opportunities,
                release_date
            )
        }
        
        return strategy
    
    def _create_strategy_phases(
        self,
        opportunities: List[PlaylistMatch],
        release_date: str
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Create phased approach for pre-release outreach"""
        
        # Sort by priority and size
        high_priority = [o for o in opportunities if o.priority == "high"]
        medium_priority = [o for o in opportunities if o.priority == "medium"]
        low_priority = [o for o in opportunities if o.priority == "low"]
        
        return {
            "phase_1_early_positioning": [
                {
                    "playlist_name": m.playlist.name,
                    "playlist_id": m.playlist.playlist_id,
                    "curator_email": m.playlist.curator_email,
                    "compatibility_score": m.compatibility_score,
                    "timing": "4-6 weeks before release",
                    "approach": "exclusive premiere pitch"
                }
                for m in high_priority[:5]
            ],
            "phase_2_core_outreach": [
                {
                    "playlist_name": m.playlist.name,
                    "playlist_id": m.playlist.playlist_id,
                    "curator_email": m.playlist.curator_email,
                    "compatibility_score": m.compatibility_score,
                    "timing": "2-3 weeks before release",
                    "approach": "pre-release access pitch"
                }
                for m in high_priority[5:] + medium_priority[:10]
            ],
            "phase_3_final_push": [
                {
                    "playlist_name": m.playlist.name,
                    "playlist_id": m.playlist.playlist_id,
                    "curator_email": m.playlist.curator_email,
                    "compatibility_score": m.compatibility_score,
                    "timing": "1 week before release",
                    "approach": "release week notification"
                }
                for m in medium_priority[10:] + low_priority[:15]
            ]
        }
    
    def _generate_pre_release_actions(
        self,
        track_analysis: TrackAnalysis,
        opportunities: List[PlaylistMatch],
        trend_data: Dict[str, Any]
    ) -> List[str]:
        """Generate actionable recommendations for pre-release"""
        actions = []
        
        # Quality check
        if track_analysis.a_and_r_score >= 8.0:
            actions.append("🎯 High A&R score - target premium curators")
        elif track_analysis.a_and_r_score >= 7.0:
            actions.append("✅ Good A&R score - target mid-tier curators")
        else:
            actions.append("⚠️ Consider refinement before pitching to top curators")
        
        # Trend alignment
        if trend_data["trend_direction"] == "up":
            actions.append(f"📈 Genre trending up - capitalize on {track_analysis.genre} momentum")
        
        # Opportunity count
        if len(opportunities) >= 50:
            actions.append(f"🎵 {len(opportunities)} curators accept unreleased - strong pre-release potential")
        elif len(opportunities) >= 20:
            actions.append(f"✨ {len(opportunities)} curators accept unreleased - good opportunities")
        else:
            actions.append(f"⏳ Limited pre-release options - focus on post-release strategy")
        
        # BPM strategy
        compatible_genres = self.trend_map.get_genres_by_bpm(track_analysis.bpm)
        if len(compatible_genres) > 1:
            actions.append(f"🔄 BPM {track_analysis.bpm} fits multiple genres - consider cross-genre pitching")
        
        return actions
    
    def _create_outreach_timeline(
        self,
        opportunities: List[PlaylistMatch],
        release_date: str
    ) -> List[Dict[str, Any]]:
        """Create timeline for curator outreach"""
        
        if not release_date:
            return []
        
        try:
            release_dt = datetime.fromisoformat(release_date.replace('Z', '+00:00'))
        except:
            return []
        
        timeline = []
        
        # 6 weeks before
        if len(opportunities) > 0:
            timeline.append({
                "date": (release_dt - timedelta(weeks=6)).isoformat(),
                "action": "Begin premium curator outreach",
                "target_count": min(5, len([o for o in opportunities if o.priority == "high"])),
                "message_type": "exclusive_premiere"
            })
        
        # 3 weeks before
        if len(opportunities) > 5:
            timeline.append({
                "date": (release_dt - timedelta(weeks=3)).isoformat(),
                "action": "Core curator campaign",
                "target_count": min(20, len(opportunities)),
                "message_type": "pre_release_access"
            })
        
        # 1 week before
        if len(opportunities) > 15:
            timeline.append({
                "date": (release_dt - timedelta(weeks=1)).isoformat(),
                "action": "Final pre-release push",
                "target_count": min(50, len(opportunities)),
                "message_type": "release_week_notification"
            })
        
        # Release day
        timeline.append({
            "date": release_dt.isoformat(),
            "action": "Activate post-release strategy",
            "target_count": "all remaining matches",
            "message_type": "now_available"
        })
        
        return timeline
    
    def get_unreleased_playlists_only(self, genre: str = None) -> List[Dict[str, Any]]:
        """
        STUB: Get playlists that specifically accept unreleased tracks.
        
        Args:
            genre: Optional genre filter
            
        Returns:
            List of unreleased-accepting playlists
        """
        if genre:
            playlists = self.playlist_db.filter_by_genre(genre)
        else:
            playlists = self.playlist_db.get_all_playlists()
        
        unreleased_playlists = [
            p for p in playlists
            if p.accepts_unreleased
        ]
        
        return [
            {
                "playlist_id": p.playlist_id,
                "name": p.name,
                "size": p.size,
                "curator_email": p.curator_email,
                "accepted_genres": p.accepted_genres,
                "mood": p.mood,
                "engagement_rate": p.engagement_rate
            }
            for p in unreleased_playlists
        ]
