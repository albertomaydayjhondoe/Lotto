"""
Playlist Intelligence — GPT Prompt Builder

Builds optimized prompts for GPT-5 to analyze tracks and generate
playlist recommendations, editorial pitches, and curator messaging.

STUB MODE: Returns mock prompts and responses.
"""

from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class GPTPromptTemplate:
    """Template for GPT-5 prompts"""
    name: str
    system_prompt: str
    user_prompt_template: str
    expected_output_format: str
    temperature: float = 0.7
    max_tokens: int = 1500


class GPTPromptBuilder:
    """
    STUB: Builds prompts for GPT-5 playlist intelligence.
    
    In LIVE mode:
    - Integrates OpenAI GPT-5 API
    - Optimizes prompts for cost/quality
    - Handles rate limiting
    - Caches common responses
    
    Phase 4: Returns mock prompts and responses.
    """
    
    def __init__(self):
        self.stub_mode = True
        self.templates = self._load_templates()
        
    def _load_templates(self) -> Dict[str, GPTPromptTemplate]:
        """Load prompt templates"""
        return {
            "playlist_analysis": GPTPromptTemplate(
                name="playlist_analysis",
                system_prompt=(
                    "You are an expert music curator and A&R professional "
                    "with deep knowledge of Spotify, Apple Music, and independent "
                    "playlist ecosystems. Analyze tracks and recommend optimal "
                    "playlist targets with strategic reasoning."
                ),
                user_prompt_template=(
                    "Track Analysis:\n"
                    "Genre: {genre}\n"
                    "Mood: {mood}\n"
                    "BPM: {bpm}\n"
                    "Energy: {energy}\n"
                    "Key Features: {features}\n"
                    "Lyrics Themes: {themes}\n"
                    "Artist Aesthetic: {aesthetic}\n\n"
                    "Task: Recommend 20 playlist types (NOT specific playlists) "
                    "that would be optimal for this track. Focus on playlist "
                    "categories, not curator names."
                ),
                expected_output_format="JSON array of playlist types with reasoning",
                temperature=0.7,
                max_tokens=1200
            ),
            "editorial_pitch": GPTPromptTemplate(
                name="editorial_pitch",
                system_prompt=(
                    "You are writing a pitch for Spotify Editorial team. "
                    "Be professional, concise, and highlight what makes the "
                    "track special for their curated playlists."
                ),
                user_prompt_template=(
                    "Track: {title} by {artist}\n"
                    "Genre: {genre}\n"
                    "Release Date: {release_date}\n"
                    "Key Story: {story}\n"
                    "Unique Angle: {angle}\n\n"
                    "Write a compelling 150-word pitch for Spotify Editorial."
                ),
                expected_output_format="Text pitch, 150 words max",
                temperature=0.8,
                max_tokens=300
            ),
            "curator_message": GPTPromptTemplate(
                name="curator_message",
                system_prompt=(
                    "You are writing personalized outreach messages to playlist "
                    "curators. Be genuine, professional, and respectful. Never "
                    "use generic templates."
                ),
                user_prompt_template=(
                    "Curator: {curator_name}\n"
                    "Playlist: {playlist_name}\n"
                    "Playlist Style: {playlist_style}\n"
                    "Track: {track_title} by {artist}\n"
                    "Why This Fits: {reasoning}\n\n"
                    "Write a personalized 80-word message."
                ),
                expected_output_format="Personalized email body, 80 words",
                temperature=0.9,
                max_tokens=200
            )
        }
    
    def build_playlist_analysis_prompt(
        self,
        track_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        STUB: Build prompt for playlist type recommendations.
        
        Args:
            track_metadata: Track information from analyzer
            
        Returns:
            Prompt ready for GPT-5 (STUB)
        """
        template = self.templates["playlist_analysis"]
        
        user_prompt = template.user_prompt_template.format(
            genre=track_metadata.get("genre", "Unknown"),
            mood=track_metadata.get("mood", "Unknown"),
            bpm=track_metadata.get("bpm", "Unknown"),
            energy=track_metadata.get("energy", "Unknown"),
            features=", ".join(track_metadata.get("features", [])),
            themes=", ".join(track_metadata.get("themes", [])),
            aesthetic=track_metadata.get("aesthetic", "Unknown")
        )
        
        return {
            "system": template.system_prompt,
            "user": user_prompt,
            "temperature": template.temperature,
            "max_tokens": template.max_tokens,
            "stub_mode": True
        }
    
    def build_editorial_pitch_prompt(
        self,
        track_info: Dict[str, Any],
        artist_story: str
    ) -> Dict[str, Any]:
        """
        STUB: Build Spotify Editorial pitch prompt.
        
        PRE-RELEASE ONLY: This generates manual message for user to review.
        
        Args:
            track_info: Track details
            artist_story: Artist narrative
            
        Returns:
            Prompt for editorial pitch (STUB)
        """
        template = self.templates["editorial_pitch"]
        
        user_prompt = template.user_prompt_template.format(
            title=track_info.get("title", "Untitled"),
            artist=track_info.get("artist", "Unknown Artist"),
            genre=track_info.get("genre", "Electronic"),
            release_date=track_info.get("release_date", "TBD"),
            story=artist_story,
            angle=track_info.get("unique_angle", "Fresh sound in the genre")
        )
        
        return {
            "system": template.system_prompt,
            "user": user_prompt,
            "temperature": template.temperature,
            "max_tokens": template.max_tokens,
            "manual_review_required": True,
            "stub_mode": True
        }
    
    def build_curator_message_prompt(
        self,
        curator_info: Dict[str, Any],
        track_info: Dict[str, Any],
        reasoning: str
    ) -> Dict[str, Any]:
        """
        STUB: Build personalized curator outreach prompt.
        
        POST-RELEASE: Auto-generated and sent.
        
        Args:
            curator_info: Curator details
            track_info: Track information
            reasoning: Why track fits playlist
            
        Returns:
            Prompt for curator message (STUB)
        """
        template = self.templates["curator_message"]
        
        user_prompt = template.user_prompt_template.format(
            curator_name=curator_info.get("name", "Curator"),
            playlist_name=curator_info.get("playlist_name", "Playlist"),
            playlist_style=curator_info.get("style", "Electronic"),
            track_title=track_info.get("title", "Track"),
            artist=track_info.get("artist", "Artist"),
            reasoning=reasoning
        )
        
        return {
            "system": template.system_prompt,
            "user": user_prompt,
            "temperature": template.temperature,
            "max_tokens": template.max_tokens,
            "auto_send": True,  # POST-RELEASE only
            "stub_mode": True
        }
    
    def execute_gpt_request(
        self,
        prompt: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        STUB: Execute GPT-5 request.
        
        In LIVE mode: Calls OpenAI API.
        
        Args:
            prompt: Prompt configuration
            
        Returns:
            GPT-5 response (STUB)
        """
        # STUB: Return mock GPT-5 response based on prompt type
        
        if "playlist_analysis" in prompt.get("system", ""):
            return {
                "response": {
                    "playlist_types": [
                        {"type": "Deep Electronic", "confidence": 0.92},
                        {"type": "Melodic Techno", "confidence": 0.89},
                        {"type": "Progressive House", "confidence": 0.85},
                        {"type": "Night Drive", "confidence": 0.88},
                        {"type": "Focus Flow", "confidence": 0.76}
                    ],
                    "reasoning": "Track combines atmospheric elements with driving rhythm"
                },
                "tokens_used": 450,
                "cost_usd": 0.0135,
                "model": "gpt-5-preview",
                "stub_note": "STUB MODE - Replace with real GPT-5 in Phase 5"
            }
        
        elif "editorial" in prompt.get("system", "").lower():
            return {
                "response": (
                    "This track represents a sophisticated evolution in melodic "
                    "house music. The artist masterfully blends organic textures "
                    "with electronic precision, creating an immersive sonic journey. "
                    "The emotional depth and production quality make it perfect for "
                    "curated playlists seeking contemporary electronic music with "
                    "artistic substance. Ideal for late-night listening and "
                    "atmospheric programming."
                ),
                "tokens_used": 95,
                "cost_usd": 0.0028,
                "model": "gpt-5-preview",
                "manual_review": True,
                "stub_note": "STUB MODE - Review before sending to Spotify Editorial"
            }
        
        else:  # Curator message
            return {
                "response": (
                    "Hi [Curator Name],\n\n"
                    "I discovered your [Playlist Name] and felt this track would "
                    "resonate with your curation style. The melodic progression and "
                    "atmospheric depth align perfectly with your playlist's vibe. "
                    "Would love to hear your thoughts.\n\n"
                    "Best regards"
                ),
                "tokens_used": 75,
                "cost_usd": 0.0022,
                "model": "gpt-5-preview",
                "stub_note": "STUB MODE - Personalize before sending"
            }
