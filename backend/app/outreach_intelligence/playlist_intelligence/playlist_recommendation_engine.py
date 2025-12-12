"""
Playlist Intelligence — Recommendation Engine

Core recommendation engine that combines track analysis, playlist classification,
and GPT-5 insights to generate optimal outreach strategies.

Handles PRE-RELEASE (editorial only) and POST-RELEASE (automated) strategies.

STUB MODE: Returns mock recommendations.
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
from enum import Enum

from .analyzer_stub import PlaylistAnalyzerStub, TrackProfile
from .gpt_prompt_builder import GPTPromptBuilder
from .playlist_classifier import PlaylistClassifier, PlaylistTier


class ReleasePhase(Enum):
    """Release phase for outreach strategy"""
    PRE_RELEASE = "pre_release"  # Manual editorial only
    POST_RELEASE = "post_release"  # Automated independent playlists


class OutreachStrategy:
    """Complete outreach strategy"""
    
    def __init__(
        self,
        track_id: str,
        release_phase: ReleasePhase,
        editorial_targets: List[Dict[str, Any]],
        independent_targets: List[Dict[str, Any]],
        messaging_templates: List[Dict[str, Any]],
        timeline: List[Dict[str, Any]],
        estimated_reach: int,
        confidence_score: float
    ):
        self.track_id = track_id
        self.release_phase = release_phase
        self.editorial_targets = editorial_targets
        self.independent_targets = independent_targets
        self.messaging_templates = messaging_templates
        self.timeline = timeline
        self.estimated_reach = estimated_reach
        self.confidence_score = confidence_score


class PlaylistRecommendationEngine:
    """
    STUB: Main recommendation engine for playlist outreach.
    
    In LIVE mode:
    - Integrates real GPT-5 API
    - Uses trained ML models
    - Accesses live playlist database
    - Tracks historical success rates
    - Optimizes based on feedback
    
    Phase 4: Returns mock strategies.
    """
    
    def __init__(self):
        self.stub_mode = True
        self.analyzer = PlaylistAnalyzerStub()
        self.gpt_builder = GPTPromptBuilder()
        self.classifier = PlaylistClassifier()
        
    def generate_strategy(
        self,
        track_metadata: Dict[str, Any],
        release_phase: ReleasePhase,
        release_date: str = None
    ) -> OutreachStrategy:
        """
        STUB: Generate complete outreach strategy.
        
        Args:
            track_metadata: Track information
            release_phase: PRE_RELEASE or POST_RELEASE
            release_date: Expected release date (ISO format)
            
        Returns:
            Complete OutreachStrategy
        """
        track_id = track_metadata.get("track_id", "track_001")
        
        # Analyze track
        track_profile = self.analyzer.analyze_track(
            track_id=track_id,
            audio_file_path=track_metadata.get("audio_path"),
            lyrics=track_metadata.get("lyrics"),
            artist_metadata=track_metadata.get("artist_info")
        )
        
        if release_phase == ReleasePhase.PRE_RELEASE:
            return self._generate_pre_release_strategy(
                track_profile,
                track_metadata,
                release_date
            )
        else:
            return self._generate_post_release_strategy(
                track_profile,
                track_metadata
            )
    
    def _generate_pre_release_strategy(
        self,
        track_profile: TrackProfile,
        track_metadata: Dict[str, Any],
        release_date: str
    ) -> OutreachStrategy:
        """
        STUB: PRE-RELEASE strategy (editorial only, manual).
        
        Returns:
            Strategy with editorial targets and manual pitch templates
        """
        # Get editorial targets
        editorial_targets = self.classifier.get_editorial_targets(track_metadata)
        
        # Generate editorial pitch (for manual review)
        pitch_prompt = self.gpt_builder.build_editorial_pitch_prompt(
            track_info=track_metadata,
            artist_story=track_metadata.get("artist_story", "Emerging artist")
        )
        
        editorial_pitch = self.gpt_builder.execute_gpt_request(pitch_prompt)
        
        # Create timeline (manual actions)
        timeline = self._create_pre_release_timeline(release_date, editorial_targets)
        
        return OutreachStrategy(
            track_id=track_profile.track_id,
            release_phase=ReleasePhase.PRE_RELEASE,
            editorial_targets=editorial_targets,
            independent_targets=[],  # None for pre-release
            messaging_templates=[{
                "type": "spotify_editorial",
                "subject": f"Editorial Submission: {track_metadata.get('title')}",
                "body": editorial_pitch["response"],
                "manual_review": True,
                "submit_via": "Spotify for Artists dashboard",
                "stub_note": "MANUAL REVIEW REQUIRED - Do not auto-send"
            }],
            timeline=timeline,
            estimated_reach=0,  # Unknown for editorial
            confidence_score=0.0  # Manual submission, no prediction
        )
    
    def _generate_post_release_strategy(
        self,
        track_profile: TrackProfile,
        track_metadata: Dict[str, Any]
    ) -> OutreachStrategy:
        """
        STUB: POST-RELEASE strategy (independent playlists, automated).
        
        Returns:
            Strategy with independent targets and auto-send messages
        """
        # Get GPT playlist recommendations
        playlist_prompt = self.gpt_builder.build_playlist_analysis_prompt(
            track_metadata={
                "genre": track_profile.gpt_insights["primary_genre"],
                "mood": track_profile.lyric_analysis["sentiment"],
                "bpm": track_profile.audio_features["tempo"],
                "energy": track_profile.audio_features["energy"],
                "features": ["atmospheric", "melodic", "driving"],
                "themes": track_profile.lyric_analysis["themes"],
                "aesthetic": track_profile.aesthetic_profile["visual_style"]
            }
        )
        
        gpt_response = self.gpt_builder.execute_gpt_request(playlist_prompt)
        
        # STUB: Mock playlist database search
        independent_targets = self._find_independent_playlists(
            track_profile,
            gpt_response["response"]["playlist_types"]
        )
        
        # Rank opportunities
        ranked_targets = self.classifier.rank_by_opportunity(
            [t["classification"] for t in independent_targets],
            track_metadata
        )
        
        # Generate personalized messages
        messaging_templates = self._generate_curator_messages(
            ranked_targets[:50],  # Top 50 targets
            track_metadata
        )
        
        # Create automated timeline
        timeline = self._create_post_release_timeline(ranked_targets)
        
        # Calculate estimated reach
        estimated_reach = sum(
            t["estimated_reach"] for t in ranked_targets[:50]
        )
        
        return OutreachStrategy(
            track_id=track_profile.track_id,
            release_phase=ReleasePhase.POST_RELEASE,
            editorial_targets=[],  # No editorial post-release
            independent_targets=ranked_targets[:50],
            messaging_templates=messaging_templates,
            timeline=timeline,
            estimated_reach=estimated_reach,
            confidence_score=0.78  # STUB confidence
        )
    
    def _find_independent_playlists(
        self,
        track_profile: TrackProfile,
        playlist_types: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        STUB: Find independent playlists matching track.
        
        In LIVE mode: Queries playlist database with embeddings.
        """
        # STUB: Return mock playlist matches
        mock_playlists = []
        
        for i, ptype in enumerate(playlist_types[:10]):
            mock_playlists.append({
                "classification": self.classifier.classify_playlist({
                    "id": f"playlist_{i:03d}",
                    "name": f"{ptype['type']} Essentials",
                    "followers": 35000 + (i * 5000)
                }),
                "match_score": ptype.get("confidence", 0.85),
                "reasoning": f"Strong fit for {ptype['type']} category"
            })
        
        return mock_playlists
    
    def _generate_curator_messages(
        self,
        targets: List[Dict[str, Any]],
        track_metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        STUB: Generate personalized curator messages.
        
        POST-RELEASE: These are auto-sent.
        """
        messages = []
        
        for target in targets[:20]:  # Top 20 get personalized
            classification = target["classification"]
            
            message_prompt = self.gpt_builder.build_curator_message_prompt(
                curator_info={
                    "name": classification.playlist_name.split()[0],
                    "playlist_name": classification.playlist_name,
                    "style": classification.primary_genre
                },
                track_info=track_metadata,
                reasoning=target["reasoning"]
            )
            
            message_response = self.gpt_builder.execute_gpt_request(message_prompt)
            
            messages.append({
                "target_playlist": classification.playlist_name,
                "curator_email": f"curator_{classification.playlist_id}@stub.local",
                "subject": f"Track Submission: {track_metadata.get('title')}",
                "body": message_response["response"],
                "priority": target["priority"],
                "auto_send": True,  # POST-RELEASE auto-send
                "stub_note": "STUB MODE - Would send via email API"
            })
        
        return messages
    
    def _create_pre_release_timeline(
        self,
        release_date: str,
        editorial_targets: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Create manual action timeline for pre-release"""
        if not release_date:
            release_date = (datetime.now() + timedelta(days=30)).isoformat()
        
        release_dt = datetime.fromisoformat(release_date.split("T")[0])
        
        timeline = []
        
        for target in editorial_targets:
            submit_date = release_dt - timedelta(weeks=target["lead_time_weeks"])
            timeline.append({
                "date": submit_date.isoformat(),
                "action": f"Submit to {target['playlist_name']}",
                "platform": target["platform"],
                "method": target["submission_method"],
                "automated": False,
                "note": target["note"]
            })
        
        return sorted(timeline, key=lambda x: x["date"])
    
    def _create_post_release_timeline(
        self,
        ranked_targets: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Create automated outreach timeline for post-release"""
        now = datetime.now()
        timeline = []
        
        # Day 1: High priority (top 20)
        timeline.append({
            "date": now.isoformat(),
            "action": "Send to high-priority playlists",
            "target_count": min(20, len(ranked_targets)),
            "automated": True,
            "priority": "high"
        })
        
        # Day 3: Medium priority (21-50)
        timeline.append({
            "date": (now + timedelta(days=3)).isoformat(),
            "action": "Send to medium-priority playlists",
            "target_count": min(30, len(ranked_targets) - 20),
            "automated": True,
            "priority": "medium"
        })
        
        # Day 7: Follow-ups
        timeline.append({
            "date": (now + timedelta(days=7)).isoformat(),
            "action": "Send follow-up messages",
            "target_count": "responses pending",
            "automated": True,
            "priority": "follow_up"
        })
        
        return timeline
