"""
SPRINT 12 - Account BirthFlow & Lifecycle Management
Module: Account Profile Manager

Gestor de identidades narrativas para cuentas satélite.
Cada cuenta tiene un perfil único (tema, tono, ritmo, preferencias).
"""

import logging
import random
from dataclasses import dataclass
from typing import Dict, List, Optional

from .account_models import AccountProfileNarrative, PlatformType

logger = logging.getLogger(__name__)


# ============================================================================
# PROFILE TEMPLATES
# ============================================================================

PROFILE_THEMES = [
    "fitness_motivation", "gaming_highlights", "cooking_quick", "travel_beauty",
    "tech_reviews", "comedy_sketches", "fashion_trends", "music_covers",
    "art_process", "dance_choreography", "pet_content", "diy_crafts",
    "book_reviews", "life_hacks", "meditation_wellness", "sports_analysis"
]

UNIVERSES = [
    "universe_gen_z", "universe_millennial", "universe_wellness",
    "universe_gaming", "universe_fashion", "universe_foodie",
    "universe_tech_early_adopters", "universe_creative"
]

PACE_OPTIONS = ["slow_deliberate", "medium_conversational", "fast_energetic"]

POSTING_STYLES = [
    "casual_authentic", "polished_professional", "raw_unfiltered",
    "educational_helpful", "humorous_entertaining", "inspirational_motivational"
]

LANGUAGE_BIASES = ["en", "es", "pt", "fr", "de", "it", "ja", "ko"]


# ============================================================================
# ACCOUNT PROFILE MANAGER
# ============================================================================

class AccountProfileManager:
    """
    Gestor de perfiles de identidad para cuentas.
    
    Responsabilidades:
    - Generar perfiles únicos por cuenta
    - CRUD de perfiles
    - Asegurar diversidad (no 2 cuentas idénticas)
    - Proveer recomendaciones basadas en perfil
    """
    
    def __init__(self):
        # Profile storage (account_id -> profile)
        self._profiles: Dict[str, AccountProfileNarrative] = {}
        
        # Track used combinations to ensure uniqueness
        self._used_combinations: set = set()
        
        logger.info("AccountProfileManager initialized")
    
    # ========================================================================
    # PUBLIC API - PROFILE CREATION
    # ========================================================================
    
    def create_profile(
        self,
        account_id: str,
        platform: PlatformType,
        theme: Optional[str] = None,
        universe: Optional[str] = None,
        **kwargs
    ) -> AccountProfileNarrative:
        """
        Crea un perfil único para una cuenta.
        
        Si no se especifican parámetros, genera aleatorios únicos.
        """
        # Generate unique combination
        if not theme or not universe:
            theme, universe = self._generate_unique_combination()
        
        # Generate other attributes
        pace = kwargs.get("pace", random.choice(PACE_OPTIONS))
        posting_style = kwargs.get("posting_style", random.choice(POSTING_STYLES))
        language_bias = kwargs.get("language_bias", random.choice(LANGUAGE_BIASES))
        
        # Risk tolerance (0.0-1.0)
        risk_tolerance = kwargs.get("risk_tolerance", random.uniform(0.3, 0.7))
        
        # Automation level (0.0-1.0)
        # Lower = más humano/supervisado
        automation_level = kwargs.get("automation_level", random.uniform(0.4, 0.8))
        
        # Content themes (pick 2-4)
        num_themes = random.randint(2, 4)
        content_themes = random.sample(self._get_content_themes_for(theme), num_themes)
        
        # Preferred hours (pick 3-5 hours)
        num_hours = random.randint(3, 5)
        preferred_hours = sorted(random.sample(range(8, 23), num_hours))
        
        # Preferred days (pick 4-6 days)
        num_days = random.randint(4, 6)
        all_days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        preferred_days = random.sample(all_days, num_days)
        
        profile = AccountProfileNarrative(
            account_id=account_id,
            theme=theme,
            universe=universe,
            pace=pace,
            posting_style=posting_style,
            risk_tolerance=risk_tolerance,
            automation_level=automation_level,
            language_bias=language_bias,
            content_themes=content_themes,
            preferred_hours=preferred_hours,
            preferred_days=preferred_days,
            platform=platform
        )
        
        self._profiles[account_id] = profile
        self._used_combinations.add((theme, universe))
        
        logger.info(f"✅ Created profile for {account_id}: {theme} in {universe}")
        return profile
    
    def get_profile(self, account_id: str) -> Optional[AccountProfileNarrative]:
        """Obtiene el perfil de una cuenta"""
        return self._profiles.get(account_id)
    
    def update_profile(
        self,
        account_id: str,
        **kwargs
    ) -> bool:
        """
        Actualiza campos del perfil.
        
        Args:
            **kwargs: Campos a actualizar
        
        Returns:
            True si se actualizó
        """
        profile = self._profiles.get(account_id)
        if not profile:
            logger.warning(f"Profile not found: {account_id}")
            return False
        
        # Update fields
        for key, value in kwargs.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
        
        logger.info(f"Updated profile for {account_id}")
        return True
    
    def delete_profile(self, account_id: str) -> bool:
        """Elimina un perfil"""
        if account_id in self._profiles:
            profile = self._profiles[account_id]
            
            # Free combination
            combo = (profile.theme, profile.universe)
            self._used_combinations.discard(combo)
            
            del self._profiles[account_id]
            logger.info(f"Deleted profile for {account_id}")
            return True
        
        return False
    
    # ========================================================================
    # PUBLIC API - RECOMMENDATIONS
    # ========================================================================
    
    def get_content_recommendations(
        self,
        account_id: str,
        count: int = 5
    ) -> List[str]:
        """
        Retorna recomendaciones de contenido basadas en perfil.
        
        Returns:
            Lista de tags/keywords recomendados
        """
        profile = self._profiles.get(account_id)
        if not profile:
            return []
        
        # Get content themes
        recommendations = list(profile.content_themes)
        
        # Add theme-specific keywords
        theme_keywords = self._get_keywords_for_theme(profile.theme)
        recommendations.extend(theme_keywords)
        
        # Shuffle and limit
        random.shuffle(recommendations)
        return recommendations[:count]
    
    def should_post_now(
        self,
        account_id: str,
        current_hour: int,
        current_day: str
    ) -> bool:
        """
        Indica si es un buen momento para postear basado en perfil.
        
        Args:
            current_hour: Hora actual (0-23)
            current_day: Día actual (monday, tuesday, etc.)
        
        Returns:
            True si es buen momento
        """
        profile = self._profiles.get(account_id)
        if not profile:
            return True  # Default: always OK
        
        # Check preferred hours
        if current_hour not in profile.preferred_hours:
            return False
        
        # Check preferred days
        if current_day.lower() not in [d.lower() for d in profile.preferred_days]:
            return False
        
        return True
    
    def get_automation_level(self, account_id: str) -> float:
        """
        Retorna el nivel de automatización permitido.
        
        Returns:
            0.0-1.0 (0 = totalmente manual, 1 = totalmente automatizado)
        """
        profile = self._profiles.get(account_id)
        if not profile:
            return 0.5  # Default: medium automation
        
        return profile.automation_level
    
    # ========================================================================
    # INTERNAL HELPERS
    # ========================================================================
    
    def _generate_unique_combination(self) -> tuple[str, str]:
        """Genera una combinación única de (theme, universe)"""
        
        # Try up to 100 times
        for _ in range(100):
            theme = random.choice(PROFILE_THEMES)
            universe = random.choice(UNIVERSES)
            
            combo = (theme, universe)
            if combo not in self._used_combinations:
                return theme, universe
        
        # If can't find unique, just return random
        logger.warning("Could not find unique combination, using random")
        return random.choice(PROFILE_THEMES), random.choice(UNIVERSES)
    
    def _get_content_themes_for(self, theme: str) -> List[str]:
        """Get related content themes"""
        
        theme_map = {
            "fitness_motivation": ["workout", "health", "gym", "running", "strength", "cardio"],
            "gaming_highlights": ["gameplay", "esports", "console", "pc_gaming", "mobile_games"],
            "cooking_quick": ["recipe", "food", "kitchen", "baking", "meal_prep"],
            "travel_beauty": ["destination", "adventure", "landscape", "city", "nature"],
            "tech_reviews": ["gadgets", "software", "apps", "tech_news", "unboxing"],
            "comedy_sketches": ["humor", "jokes", "parody", "funny", "memes"],
            "fashion_trends": ["outfit", "style", "clothing", "accessories", "runway"],
            "music_covers": ["singing", "instruments", "acoustic", "performance"],
            "art_process": ["drawing", "painting", "digital_art", "illustration", "creative"],
            "dance_choreography": ["movement", "choreography", "performance", "dance_style"],
            "pet_content": ["dogs", "cats", "cute_pets", "animal_care", "funny_animals"],
            "diy_crafts": ["handmade", "crafting", "projects", "creative", "tutorial"],
            "book_reviews": ["reading", "literature", "bookish", "recommendations"],
            "life_hacks": ["tips", "tricks", "productivity", "organization"],
            "meditation_wellness": ["mindfulness", "relaxation", "self_care", "mental_health"],
            "sports_analysis": ["sports", "athletes", "training", "competition", "highlights"]
        }
        
        return theme_map.get(theme, ["general"])
    
    def _get_keywords_for_theme(self, theme: str) -> List[str]:
        """Get SEO keywords for theme"""
        
        keyword_map = {
            "fitness_motivation": ["fitspo", "transformation", "goals"],
            "gaming_highlights": ["pro_player", "clutch", "epic_win"],
            "cooking_quick": ["easy_recipe", "quick_meal", "delicious"],
            "travel_beauty": ["wanderlust", "bucket_list", "hidden_gem"],
            "tech_reviews": ["review", "comparison", "worth_it"],
            "comedy_sketches": ["laugh", "relatable", "viral"],
            "fashion_trends": ["trending", "fashion_week", "style_inspo"],
            "music_covers": ["cover", "acoustic_version", "tribute"],
            "art_process": ["timelapse", "process_video", "art_challenge"],
            "dance_choreography": ["challenge", "trend", "viral_dance"],
            "pet_content": ["adorable", "funny_pet", "pet_life"],
            "diy_crafts": ["diy", "homemade", "craft_tutorial"],
            "book_reviews": ["book_rec", "must_read", "book_lover"],
            "life_hacks": ["life_hack", "genius", "game_changer"],
            "meditation_wellness": ["calm", "peaceful", "self_care"],
            "sports_analysis": ["breakdown", "analysis", "highlight_reel"]
        }
        
        return keyword_map.get(theme, [])


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def create_profile_manager() -> AccountProfileManager:
    """Helper para crear profile manager"""
    return AccountProfileManager()


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "PROFILE_THEMES",
    "UNIVERSES",
    "PACE_OPTIONS",
    "POSTING_STYLES",
    "LANGUAGE_BIASES",
    "AccountProfileManager",
    "create_profile_manager",
]
