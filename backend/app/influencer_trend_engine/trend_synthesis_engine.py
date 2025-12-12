"""
Sprint 16: Influencer Trend Engine - Trend Synthesis Engine

Generates optimal trends for songs based on musical/aesthetic analysis.

Features:
- Trend Blueprint generation (movement, style, rhythm, caption, challenge)
- Multiple variants for different audiences (influencers, satellites, organic, ads)
- Integration with Satellite Engine universes
- STAKAZO/Lendas Daría aesthetic alignment
- Risk scoring

Author: STAKAZO Project
Date: 2025-12-12
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
from datetime import datetime
import random


class TrendVariantType(Enum):
    """Types of trend variants"""
    INFLUENCER = "influencer"  # For primary/support influencers
    SATELLITE = "satellite"  # For satellite accounts
    ORGANIC = "organic"  # For organic spread
    ADS = "ads"  # For paid ads


class VisualStyle(Enum):
    """Visual style options"""
    FAST_CUT = "fast_cut"
    CINEMATIC = "cinematic"
    RAW_AUTHENTIC = "raw_authentic"
    AESTHETIC_GRID = "aesthetic_grid"
    STORY_MODE = "story_mode"
    MIRROR_SHOTS = "mirror_shots"
    URBAN_STREET = "urban_street"


class CutRhythm(Enum):
    """Video cut rhythm"""
    HYPER_FAST = "hyper_fast"  # <1s per cut
    FAST = "fast"  # 1-2s per cut
    MEDIUM = "medium"  # 2-4s per cut
    SLOW = "slow"  # 4-8s per cut
    CINEMATIC_SLOW = "cinematic_slow"  # >8s per cut


@dataclass
class TrendBlueprint:
    """
    Core trend blueprint for a song.
    
    Defines the optimal viral formula.
    """
    trend_id: str
    song_name: str
    core_movement: str  # Main dance/action (e.g., "transition reveal", "lip sync + walk")
    visual_style: VisualStyle
    cut_rhythm: CutRhythm
    recommended_caption_template: str  # Template with placeholders
    challenge_element: Optional[str]  # Optional challenge component
    sound_cut_timestamp: Optional[str]  # Optimal cut (e.g., "0:15-0:30")
    hashtags: List[str]
    risk_score: float  # 0-1: how risky/edgy is this trend?
    virality_potential: float  # 0-1: estimated viral potential
    target_duration_seconds: int
    ideal_settings: List[str]  # Where to film (e.g., ["urban street", "bedroom", "studio"])
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'trend_id': self.trend_id,
            'song_name': self.song_name,
            'core_movement': self.core_movement,
            'visual_style': self.visual_style.value,
            'cut_rhythm': self.cut_rhythm.value,
            'recommended_caption_template': self.recommended_caption_template,
            'challenge_element': self.challenge_element,
            'sound_cut_timestamp': self.sound_cut_timestamp,
            'hashtags': self.hashtags,
            'risk_score': self.risk_score,
            'virality_potential': self.virality_potential,
            'target_duration_seconds': self.target_duration_seconds,
            'ideal_settings': self.ideal_settings,
            'created_at': self.created_at.isoformat()
        }


@dataclass
class TrendVariant:
    """
    Specific variant of a trend for a target audience.
    """
    variant_id: str
    blueprint_id: str
    variant_type: TrendVariantType
    customization: str  # How this variant differs from blueprint
    specific_caption: str  # Actual caption (not template)
    specific_hashtags: List[str]
    tone: str  # "playful", "serious", "aspirational", etc.
    target_audience: str  # Who this variant targets
    difficulty_level: str  # "easy", "medium", "hard"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'variant_id': self.variant_id,
            'blueprint_id': self.blueprint_id,
            'variant_type': self.variant_type.value,
            'customization': self.customization,
            'specific_caption': self.specific_caption,
            'specific_hashtags': self.specific_hashtags,
            'tone': self.tone,
            'target_audience': self.target_audience,
            'difficulty_level': self.difficulty_level
        }


class TrendSynthesisEngine:
    """
    Generates optimal trends for songs.
    
    Process:
    1. Analyze song characteristics (tempo, mood, genre)
    2. Consider visual aesthetic (STAKAZO/Lendas Daría)
    3. Generate Trend Blueprint (core formula)
    4. Create 3-5 variants for different audiences
    5. Integrate with Satellite Engine universes
    """
    
    def __init__(
        self,
        brand_aesthetic: List[str] = None,
        satellite_universes: Optional[List[str]] = None
    ):
        """
        Initialize trend synthesis engine.
        
        Args:
            brand_aesthetic: Target brand aesthetic keywords
            satellite_universes: Available satellite universes (from Sprint 11)
        """
        if brand_aesthetic is None:
            self.brand_aesthetic = [
                "urban", "authentic", "bold", "diverse", "raw",
                "gen-z", "latam", "music-first", "creative"
            ]
        else:
            self.brand_aesthetic = brand_aesthetic
        
        if satellite_universes is None:
            # Default universes from Satellite Engine (Sprint 11)
            self.satellite_universes = [
                "latam_music_lovers",
                "urban_youth",
                "party_lifestyle",
                "fashion_forward",
                "fitness_enthusiasts"
            ]
        else:
            self.satellite_universes = satellite_universes
    
    def synthesize_trend(
        self,
        song_name: str,
        song_tempo: int,  # BPM
        song_mood: str,  # "energetic", "melancholic", "romantic", etc.
        visual_aesthetic: str,  # "urban", "cinematic", "raw", etc.
        artist_language: str = "es"
    ) -> tuple[TrendBlueprint, List[TrendVariant]]:
        """
        Generate optimal trend blueprint + variants.
        
        Args:
            song_name: Name of the song
            song_tempo: Tempo in BPM
            song_mood: Mood/vibe
            visual_aesthetic: Target visual aesthetic
            artist_language: Language code
        
        Returns:
            (TrendBlueprint, List of TrendVariants)
        """
        # Generate blueprint
        blueprint = self._generate_blueprint(
            song_name=song_name,
            tempo=song_tempo,
            mood=song_mood,
            aesthetic=visual_aesthetic,
            language=artist_language
        )
        
        # Generate variants
        variants = self._generate_variants(blueprint, artist_language)
        
        return blueprint, variants
    
    def _generate_blueprint(
        self,
        song_name: str,
        tempo: int,
        mood: str,
        aesthetic: str,
        language: str
    ) -> TrendBlueprint:
        """Generate core trend blueprint"""
        
        # Determine visual style based on aesthetic
        if "urban" in aesthetic.lower():
            visual_style = VisualStyle.URBAN_STREET
        elif "raw" in aesthetic.lower() or "authentic" in aesthetic.lower():
            visual_style = VisualStyle.RAW_AUTHENTIC
        elif "cinematic" in aesthetic.lower():
            visual_style = VisualStyle.CINEMATIC
        elif "aesthetic" in aesthetic.lower():
            visual_style = VisualStyle.AESTHETIC_GRID
        else:
            visual_style = VisualStyle.FAST_CUT
        
        # Determine cut rhythm based on tempo
        if tempo > 140:
            cut_rhythm = CutRhythm.HYPER_FAST
        elif tempo > 120:
            cut_rhythm = CutRhythm.FAST
        elif tempo > 90:
            cut_rhythm = CutRhythm.MEDIUM
        elif tempo > 70:
            cut_rhythm = CutRhythm.SLOW
        else:
            cut_rhythm = CutRhythm.CINEMATIC_SLOW
        
        # Determine core movement based on mood
        if mood.lower() in ["energetic", "party", "hype"]:
            core_movement = "Transition reveal + mini dance"
        elif mood.lower() in ["romantic", "emotional"]:
            core_movement = "Lip sync + slow reveal"
        elif mood.lower() in ["melancholic", "sad"]:
            core_movement = "Walking shot + emotional moment"
        elif mood.lower() in ["confident", "boss", "power"]:
            core_movement = "Confident walk + pose"
        else:
            core_movement = "Lip sync + gesture"
        
        # Generate caption template
        if language == "es":
            caption_templates = [
                "Cuando suena {song_name} 🔥 #SoyEso",
                "{song_name} es mi vibe 💫",
                "Así me siento con {song_name} 🎵",
                "Mood: {song_name} forever 🌟",
                "{song_name} + yo = 💯"
            ]
        else:
            caption_templates = [
                "When {song_name} hits different 🔥",
                "{song_name} is my vibe 💫",
                "POV: {song_name} is playing 🎵",
                "Mood: {song_name} on repeat 🌟"
            ]
        
        caption_template = random.choice(caption_templates)
        
        # Generate challenge element (50% chance)
        challenge_element = None
        if random.random() > 0.5:
            if language == "es":
                challenge_element = f"Muéstrame tu versión de {song_name}"
            else:
                challenge_element = f"Show me your {song_name} version"
        
        # Generate hashtags
        base_hashtags = ["STAKAZO", "LendasDaría"]
        mood_hashtags = {
            "energetic": ["Energy", "Vibes", "Party"],
            "romantic": ["Love", "Romance", "Feelings"],
            "melancholic": ["Mood", "Feels", "Emotional"],
            "confident": ["Boss", "Confidence", "Power"]
        }
        
        hashtags = base_hashtags + mood_hashtags.get(mood.lower(), ["Vibe", "Music"])
        
        # Determine sound cut (optimal 15s section)
        sound_cut = self._determine_optimal_cut(tempo, mood)
        
        # Risk score (how edgy/controversial)
        risk_score = 0.15  # Conservative baseline
        if "raw" in aesthetic.lower():
            risk_score += 0.1
        if tempo > 140:
            risk_score += 0.05  # Very fast = higher energy = slight risk
        
        # Virality potential (estimated)
        virality = 0.6  # Base
        if tempo > 110 and tempo < 140:
            virality += 0.15  # Sweet spot for virality
        if visual_style in [VisualStyle.FAST_CUT, VisualStyle.RAW_AUTHENTIC]:
            virality += 0.1
        if challenge_element:
            virality += 0.15
        
        virality = min(1.0, virality)
        
        # Target duration
        if tempo > 130:
            duration = 15  # Fast songs = short content
        elif tempo > 90:
            duration = 20
        else:
            duration = 30
        
        # Ideal settings
        if visual_style == VisualStyle.URBAN_STREET:
            settings = ["urban street", "rooftop", "parking lot"]
        elif visual_style == VisualStyle.CINEMATIC:
            settings = ["studio", "minimalist room", "outdoor golden hour"]
        elif visual_style == VisualStyle.RAW_AUTHENTIC:
            settings = ["bedroom", "bathroom mirror", "car"]
        else:
            settings = ["any location", "indoors", "outdoors"]
        
        # Generate unique trend ID
        trend_id = f"trend_{song_name.replace(' ', '_').lower()}_{int(datetime.now().timestamp())}"
        
        return TrendBlueprint(
            trend_id=trend_id,
            song_name=song_name,
            core_movement=core_movement,
            visual_style=visual_style,
            cut_rhythm=cut_rhythm,
            recommended_caption_template=caption_template,
            challenge_element=challenge_element,
            sound_cut_timestamp=sound_cut,
            hashtags=hashtags,
            risk_score=risk_score,
            virality_potential=virality,
            target_duration_seconds=duration,
            ideal_settings=settings
        )
    
    def _generate_variants(
        self,
        blueprint: TrendBlueprint,
        language: str
    ) -> List[TrendVariant]:
        """Generate 3-5 trend variants for different audiences"""
        variants = []
        
        # Variant 1: INFLUENCER - Premium, high-effort
        variants.append(TrendVariant(
            variant_id=f"{blueprint.trend_id}_influencer",
            blueprint_id=blueprint.trend_id,
            variant_type=TrendVariantType.INFLUENCER,
            customization="Premium production: professional lighting, multiple angles, polished editing",
            specific_caption=self._fill_caption_template(
                blueprint.recommended_caption_template,
                blueprint.song_name,
                language,
                tone="aspirational"
            ),
            specific_hashtags=blueprint.hashtags + ["Creator", "ContentCreator"],
            tone="aspirational",
            target_audience="Content creators, verified accounts, influencers",
            difficulty_level="hard"
        ))
        
        # Variant 2: SATELLITE - Authentic, relatable
        variants.append(TrendVariant(
            variant_id=f"{blueprint.trend_id}_satellite",
            blueprint_id=blueprint.trend_id,
            variant_type=TrendVariantType.SATELLITE,
            customization="Authentic feel: phone-shot, natural lighting, minimal editing",
            specific_caption=self._fill_caption_template(
                blueprint.recommended_caption_template,
                blueprint.song_name,
                language,
                tone="relatable"
            ),
            specific_hashtags=blueprint.hashtags + ["Mood", "Vibe"],
            tone="relatable",
            target_audience="Regular users, satellite accounts, micro-creators",
            difficulty_level="easy"
        ))
        
        # Variant 3: ORGANIC - Simple, accessible
        variants.append(TrendVariant(
            variant_id=f"{blueprint.trend_id}_organic",
            blueprint_id=blueprint.trend_id,
            variant_type=TrendVariantType.ORGANIC,
            customization="Ultra-simple: minimal movement, easy to replicate, low barrier",
            specific_caption=self._fill_caption_template(
                blueprint.recommended_caption_template,
                blueprint.song_name,
                language,
                tone="casual"
            ),
            specific_hashtags=blueprint.hashtags[:3],  # Fewer hashtags
            tone="casual",
            target_audience="General audience, first-time trend participants",
            difficulty_level="easy"
        ))
        
        # Variant 4: ADS - Clear CTA, brand-focused
        variants.append(TrendVariant(
            variant_id=f"{blueprint.trend_id}_ads",
            blueprint_id=blueprint.trend_id,
            variant_type=TrendVariantType.ADS,
            customization="Brand-forward: clear product/artist showcase, polished, CTA-driven",
            specific_caption=self._generate_ad_caption(blueprint.song_name, language),
            specific_hashtags=blueprint.hashtags + ["NewMusic", "MusicPromotion"],
            tone="promotional",
            target_audience="Potential listeners, music discovery audience",
            difficulty_level="medium"
        ))
        
        # Optional Variant 5: CHALLENGE (if blueprint has challenge element)
        if blueprint.challenge_element:
            variants.append(TrendVariant(
                variant_id=f"{blueprint.trend_id}_challenge",
                blueprint_id=blueprint.trend_id,
                variant_type=TrendVariantType.ORGANIC,
                customization="Challenge-focused: emphasize participation, duets/stitches enabled",
                specific_caption=f"{blueprint.challenge_element} 🎵 {blueprint.song_name}",
                specific_hashtags=blueprint.hashtags + ["Challenge", "DuetThis"],
                tone="playful",
                target_audience="Challenge enthusiasts, community builders",
                difficulty_level="medium"
            ))
        
        return variants
    
    def _determine_optimal_cut(self, tempo: int, mood: str) -> str:
        """Determine optimal 15s cut of song"""
        # For most viral content, the hook/chorus is best
        # Typically appears 0:30-0:45 in songs
        if mood.lower() in ["energetic", "party"]:
            return "0:30-0:45"  # Hit the energy peak
        elif mood.lower() in ["romantic", "emotional"]:
            return "0:45-1:00"  # Emotional climax
        else:
            return "0:15-0:30"  # Safe default: intro to hook
    
    def _fill_caption_template(
        self,
        template: str,
        song_name: str,
        language: str,
        tone: str
    ) -> str:
        """Fill caption template with actual song name and adjust tone"""
        caption = template.replace("{song_name}", song_name)
        
        # Add tone-specific suffix
        if tone == "aspirational":
            suffix = " ✨" if language == "es" else " ✨"
        elif tone == "relatable":
            suffix = " 😌" if language == "es" else " 😌"
        elif tone == "casual":
            suffix = ""
        elif tone == "playful":
            suffix = " 🎉" if language == "es" else " 🎉"
        else:
            suffix = ""
        
        return caption + suffix
    
    def _generate_ad_caption(self, song_name: str, language: str) -> str:
        """Generate ad-specific caption with CTA"""
        if language == "es":
            templates = [
                f"Descubre {song_name} — Ya disponible 🎵 #NuevaMúsica",
                f"{song_name} está cambiando el juego 🔥 Escúchalo ahora",
                f"¿Ya escuchaste {song_name}? Link en bio 🎧"
            ]
        else:
            templates = [
                f"Discover {song_name} — Out now 🎵 #NewMusic",
                f"{song_name} is changing the game 🔥 Listen now",
                f"Have you heard {song_name} yet? Link in bio 🎧"
            ]
        
        return random.choice(templates)


if __name__ == "__main__":
    # Example usage
    engine = TrendSynthesisEngine()
    
    # Synthesize trend for a song
    blueprint, variants = engine.synthesize_trend(
        song_name="Bailando en la Noche",
        song_tempo=128,
        song_mood="energetic",
        visual_aesthetic="urban raw",
        artist_language="es"
    )
    
    print("✓ Trend synthesized successfully")
    print(f"\nBlueprint: {blueprint.trend_id}")
    print(f"  Movement: {blueprint.core_movement}")
    print(f"  Style: {blueprint.visual_style.value}")
    print(f"  Rhythm: {blueprint.cut_rhythm.value}")
    print(f"  Virality: {blueprint.virality_potential:.2f}")
    print(f"  Risk: {blueprint.risk_score:.2f}")
    print(f"  Hashtags: {', '.join(blueprint.hashtags)}")
    
    print(f"\nVariants ({len(variants)}):")
    for variant in variants:
        print(f"  - {variant.variant_type.value}: {variant.tone} ({variant.difficulty_level})")
        print(f"    Caption: {variant.specific_caption}")
