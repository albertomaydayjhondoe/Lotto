"""
Content Recommender - Creative Recommendations for Community Manager AI

Generates creative recommendations for videoclips, wardrobe, narrative, aesthetics.
"""

import logging
from datetime import datetime
from typing import List, Dict, Optional, Any
import json

from .models import (
    CreativeRecommendation,
    VideoclipRecommendation
)

logger = logging.getLogger(__name__)


class ContentRecommender:
    """
    Creative content recommender.
    
    Generates recommendations for:
    - Videoclip concepts
    - Wardrobe/vestuario
    - Narrative/storytelling
    - Visual aesthetics
    - Content ideas
    """
    
    def __init__(
        self,
        brand_rules_path: Optional[str] = None,
        mode: str = "live"
    ):
        """
        Initialize recommender.
        
        Args:
            brand_rules_path: Path to BRAND_STATIC_RULES.json
            mode: "live" or "stub"
        """
        self.mode = mode
        self.brand_rules_path = brand_rules_path
        self.brand_rules: Optional[Dict[str, Any]] = None
        
        if brand_rules_path and mode == "live":
            self._load_brand_rules()
    
    def _load_brand_rules(self) -> None:
        """Load brand rules."""
        try:
            with open(self.brand_rules_path, 'r', encoding='utf-8') as f:
                self.brand_rules = json.load(f)
            logger.info(f"✅ Loaded brand rules for recommender")
        except Exception as e:
            logger.error(f"❌ Failed to load brand rules: {e}")
            self.brand_rules = None
    
    def recommend_official_content(
        self,
        user_id: str,
        vision_metadata: Optional[List[Dict[str, Any]]] = None,
        trend_data: Optional[Dict[str, Any]] = None,
        performance_data: Optional[Dict[str, Any]] = None
    ) -> List[CreativeRecommendation]:
        """
        Recommend content for official channel.
        
        Args:
            user_id: Artist user ID
            vision_metadata: Visual metadata from Vision Engine
            trend_data: Trend analysis data
            performance_data: Historical performance
        
        Returns:
            List of creative recommendations
        """
        logger.info(f"🎨 Generating content recommendations for {user_id}")
        
        recommendations = []
        
        # Recommend based on best-performing aesthetics
        if performance_data and "top_aesthetics" in performance_data:
            for aesthetic in performance_data["top_aesthetics"][:3]:
                rec = self._recommend_from_aesthetic(aesthetic)
                recommendations.append(rec)
        
        # Recommend based on trends (brand-aligned only)
        if trend_data and self.brand_rules:
            trend_recs = self._recommend_from_trends(trend_data)
            recommendations.extend(trend_recs)
        
        # Stub mode fallback
        if self.mode == "stub" and not recommendations:
            recommendations = self._stub_recommendations(user_id)
        
        logger.info(f"✅ Generated {len(recommendations)} recommendations")
        return recommendations
    
    def recommend_satellite_experiments(
        self,
        user_id: str,
        trend_data: Optional[Dict[str, Any]] = None
    ) -> List[CreativeRecommendation]:
        """
        Recommend experiments for satellite channels.
        
        No brand restrictions - pure ML testing.
        """
        logger.info(f"🧪 Generating satellite experiments for {user_id}")
        
        experiments = []
        
        if trend_data and "trending_formats" in trend_data:
            for trend in trend_data["trending_formats"][:5]:
                exp = CreativeRecommendation(
                    recommendation_id=f"sat_exp_{user_id}_{trend['name']}",
                    category="satellite_experiment",
                    title=f"Test: {trend['name']}",
                    description=f"Experiment with {trend['description']}",
                    details=trend,
                    color_palette=[],
                    scene_types=[],
                    objects=[],
                    references=[],
                    brand_aligned=False,
                    brand_score=0.0,
                    confidence=0.80,
                    created_at=datetime.utcnow()
                )
                experiments.append(exp)
        
        if self.mode == "stub" and not experiments:
            experiments = self._stub_satellite_experiments(user_id)
        
        return experiments
    
    def recommend_video_aesthetic(
        self,
        track_name: str,
        track_mood: str,
        vision_metadata: Optional[List[Dict[str, Any]]] = None
    ) -> CreativeRecommendation:
        """
        Recommend aesthetic for a specific track/video.
        
        Args:
            track_name: Name of the track
            track_mood: Emotional mood (e.g., "dark", "energetic", "melancholic")
            vision_metadata: Past visual success data
        
        Returns:
            Aesthetic recommendation
        """
        logger.info(f"🎬 Recommending aesthetic for '{track_name}' (mood: {track_mood})")
        
        # Map mood to visual elements
        mood_aesthetics = {
            "dark": {
                "colors": ["#0A0A0A", "#1C1C1C", "#8B44FF"],
                "scenes": ["noche", "club", "calle"],
                "lighting": "Low-key, shadows, neon accents"
            },
            "energetic": {
                "colors": ["#FF0000", "#FFD700", "#8B44FF"],
                "scenes": ["coche", "calle", "urbano"],
                "lighting": "High contrast, fast cuts, strobe effects"
            },
            "melancholic": {
                "colors": ["#4A4A4A", "#6A5ACD", "#2E2E4F"],
                "scenes": ["costa", "interior", "noche"],
                "lighting": "Soft, blue hour, atmospheric"
            }
        }
        
        aesthetic_data = mood_aesthetics.get(track_mood, mood_aesthetics["dark"])
        
        return CreativeRecommendation(
            recommendation_id=f"aesthetic_{track_name}_{track_mood}",
            category="aesthetic",
            title=f"Visual Aesthetic for '{track_name}'",
            description=f"Recommended aesthetic based on {track_mood} mood",
            details={
                "track_name": track_name,
                "mood": track_mood,
                "lighting": aesthetic_data["lighting"]
            },
            color_palette=aesthetic_data["colors"],
            scene_types=aesthetic_data["scenes"],
            objects=[],
            references=[],
            brand_aligned=True,
            brand_score=0.90,
            confidence=0.85,
            created_at=datetime.utcnow()
        )
    
    def recommend_clip_styles(
        self,
        content_type: str,
        target_platform: str
    ) -> List[str]:
        """
        Recommend editing styles for clips.
        
        Args:
            content_type: Type of content (e.g., "music_video", "snippet", "story")
            target_platform: Target platform (e.g., "instagram", "tiktok")
        
        Returns:
            List of editing style recommendations
        """
        styles = {
            "instagram_reel": [
                "Fast cuts every 0.8s",
                "Vertical 9:16 format",
                "Text overlays with trending fonts",
                "Hook in first 0.5s",
                "Purple color grading"
            ],
            "tiktok_video": [
                "Aggressive transitions",
                "On-beat cuts",
                "Trending audio integration",
                "Captions on every phrase",
                "High saturation"
            ],
            "youtube_short": [
                "Story arc: hook → tension → payoff",
                "Clear focal point",
                "Vertical format",
                "30-45s duration",
                "End screen CTA"
            ]
        }
        
        key = f"{target_platform}_{content_type}"
        return styles.get(key, styles.get("instagram_reel", []))
    
    def creative_brainstorm(
        self,
        topic: str,
        constraints: Optional[List[str]] = None
    ) -> List[str]:
        """
        Generate creative ideas for a topic.
        
        Args:
            topic: Topic to brainstorm (e.g., "videoclip", "vestuario", "narrative")
            constraints: Optional constraints (e.g., ["low budget", "urban locations"])
        
        Returns:
            List of creative ideas
        """
        logger.info(f"💡 Brainstorming ideas for: {topic}")
        
        ideas = {
            "videoclip": [
                "Concepto: Ascenso desde la calle hacia el éxito (simbolizado con altura física)",
                "Secuencia: Sótano trap house → Coche en movimiento → Terraza skyline",
                "Paleta: Morado dominante con neones azules y rojos",
                "Narrativa: Sin diálogos, pura imagen y música",
                "Referencia: 'Drive' meets Bad Bunny 'Yo Perreo Sola'"
            ],
            "vestuario": [
                "Look 1: Chandal negro con detalles morados fosforescentes",
                "Look 2: Chaqueta de cuero + cadenas minimalistas",
                "Look 3: Oversized hoodie con capucha + gafas oscuras",
                "Accesorios: Reloj statement, anillos silver",
                "Evitar: Logos grandes, colores pasteles"
            ],
            "narrative": [
                "Storytelling: Del barrio al mainstream sin perder autenticidad",
                "Tono: Confiado pero no arrogante",
                "Mensaje: El éxito viene del trabajo, no del chance",
                "Emotion: Ambición + Nostalgia por los inicios",
                "Arc: Struggle → Grind → Victory"
            ]
        }
        
        return ideas.get(topic, ["Generate custom ideas based on brand rules"])
    
    def recommend_videoclip_concept(
        self,
        track_name: str,
        track_lyrics_theme: str,
        budget: str = "medium"
    ) -> VideoclipRecommendation:
        """
        Recommend complete videoclip concept.
        
        Args:
            track_name: Track name
            track_lyrics_theme: Main theme of lyrics
            budget: "low", "medium", "high"
        
        Returns:
            Complete videoclip recommendation
        """
        logger.info(f"🎬 Creating videoclip concept for '{track_name}'")
        
        if self.mode == "stub":
            return VideoclipRecommendation(
                concept_id=f"concept_{track_name}",
                title=f"Videoclip Concept: {track_name}",
                narrative="Ascenso visual desde trap house hasta skyline urbano",
                aesthetic="Dark purple trap meets cyberpunk",
                color_palette=["#8B44FF", "#0A0A0A", "#FF0066"],
                scene_sequence=[
                    "INT. Trap House - Oscuro, humo, morado",
                    "EXT. Calle noche - Coche deportivo, neones",
                    "EXT. Terraza - Skyline, éxito visual"
                ],
                wardrobe="Chandal negro + chaqueta cuero + cadenas silver",
                props=["Coche deportivo", "Teléfono luxury", "Chains"],
                lighting="Low-key con acentos neon purple",
                locations=["Parking urbano", "Calle noche", "Rooftop"],
                emotional_tone="Confianza, ambición, autenticidad",
                target_emotion="Motivación + Hype",
                brand_score=0.94,
                references=[
                    "Bad Bunny - 'Yo Perreo Sola' (aesthetic)",
                    "Drive (2011) - night driving scenes",
                    "Blade Runner - neon cityscape"
                ],
                created_at=datetime.utcnow()
            )
        
        # LIVE mode: generate from brand rules + performance data
        return self._generate_videoclip_from_brand(track_name, track_lyrics_theme, budget)
    
    def _recommend_from_aesthetic(self, aesthetic: Dict[str, Any]) -> CreativeRecommendation:
        """Create recommendation from aesthetic data."""
        return CreativeRecommendation(
            recommendation_id=f"rec_aesthetic_{aesthetic['name']}",
            category="aesthetic",
            title=f"Replicate: {aesthetic['name']}",
            description=f"Aesthetic with {aesthetic.get('avg_retention', 0)*100:.1f}% retention",
            details=aesthetic,
            color_palette=aesthetic.get("colors", []),
            scene_types=aesthetic.get("scenes", []),
            objects=[],
            references=[],
            brand_aligned=True,
            brand_score=aesthetic.get("brand_score", 0.85),
            confidence=0.88,
            created_at=datetime.utcnow()
        )
    
    def _recommend_from_trends(self, trend_data: Dict[str, Any]) -> List[CreativeRecommendation]:
        """Generate recommendations from trend data."""
        recommendations = []
        
        if "applicable_trends" in trend_data:
            for trend in trend_data["applicable_trends"][:2]:
                if self._is_brand_aligned_trend(trend):
                    rec = CreativeRecommendation(
                        recommendation_id=f"rec_trend_{trend['name']}",
                        category="trend",
                        title=f"Apply Trend: {trend['name']}",
                        description=trend.get("description", ""),
                        details=trend,
                        color_palette=[],
                        scene_types=[],
                        objects=[],
                        references=[],
                        brand_aligned=True,
                        brand_score=trend.get("brand_fit_score", 0.7),
                        confidence=0.80,
                        created_at=datetime.utcnow()
                    )
                    recommendations.append(rec)
        
        return recommendations
    
    def _is_brand_aligned_trend(self, trend: Dict[str, Any]) -> bool:
        """Check if trend aligns with brand."""
        if not self.brand_rules:
            return True
        
        brand_fit = trend.get("brand_fit_score", 0.0)
        return brand_fit >= 0.7
    
    def _stub_recommendations(self, user_id: str) -> List[CreativeRecommendation]:
        """Generate stub recommendations."""
        return [
            CreativeRecommendation(
                recommendation_id=f"stub_rec_1_{user_id}",
                category="videoclip",
                title="Purple Night Drive Concept",
                description="Videoclip con estética morada, coche deportivo, noche urbana",
                details={"budget": "medium", "duration": "3min"},
                color_palette=["#8B44FF", "#0A0A0A", "#FF0066"],
                scene_types=["coche", "noche", "calle"],
                objects=["car", "phone", "chains"],
                references=["Drive (2011)", "Bad Bunny aesthetics"],
                brand_aligned=True,
                brand_score=0.92,
                confidence=0.85,
                created_at=datetime.utcnow()
            )
        ]
    
    def _stub_satellite_experiments(self, user_id: str) -> List[CreativeRecommendation]:
        """Generate stub satellite experiments."""
        return [
            CreativeRecommendation(
                recommendation_id=f"stub_sat_1_{user_id}",
                category="satellite_experiment",
                title="Test: Viral TikTok Format",
                description="Aggressive cuts, trending audio, high saturation",
                details={"platform": "tiktok", "type": "experiment"},
                color_palette=[],
                scene_types=[],
                objects=[],
                references=[],
                brand_aligned=False,
                brand_score=0.30,
                confidence=0.75,
                created_at=datetime.utcnow()
            )
        ]
    
    def _generate_videoclip_from_brand(
        self,
        track_name: str,
        theme: str,
        budget: str
    ) -> VideoclipRecommendation:
        """Generate videoclip from brand rules."""
        # TODO: Use LLM + brand rules to generate custom concept
        return self.recommend_videoclip_concept(track_name, theme, budget)
