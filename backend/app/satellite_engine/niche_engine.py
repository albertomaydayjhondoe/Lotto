"""
Satellite Niche Engine - Sprint 8
1 cuenta → 1 nicho con libros de estilo personalizados.

Nichos soportados:
- Shameless Edits
- Stranger Things Edits
- GTA 5 / GTA RP Cinematic
- EA Sports / FIFA Edits
- Anime Edits
- Corridos Aesthetic
- Lifestyle Neon Purple Aesthetic
"""
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class Niche(Enum):
    """Nichos disponibles para cuentas satélite."""
    SHAMELESS_EDITS = "shameless_edits"
    STRANGER_THINGS = "stranger_things_edits"
    GTA_CINEMATIC = "gta_cinematic"
    EA_SPORTS_FIFA = "ea_sports_fifa"
    ANIME_EDITS = "anime_edits"
    CORRIDOS_AESTHETIC = "corridos_aesthetic"
    LIFESTYLE_NEON = "lifestyle_neon_purple"


@dataclass
class VisualLibrary:
    """Librería visual del nicho."""
    frames: List[str] = field(default_factory=list)        # Paths a frames
    templates: List[str] = field(default_factory=list)     # Paths a templates
    scenes: List[Dict] = field(default_factory=list)       # Escenas clave
    color_palette: List[str] = field(default_factory=list) # Hex colors
    visual_style: str = "cinematic"
    
    def add_frame(self, frame_path: str):
        """Agrega frame a la librería."""
        self.frames.append(frame_path)
    
    def add_template(self, template_path: str):
        """Agrega template a la librería."""
        self.templates.append(template_path)
    
    def add_scene(self, scene: Dict):
        """
        Agrega escena clave.
        
        Args:
            scene: Dict con metadata de escena
                {
                    "name": "intro_dark",
                    "duration": 3.5,
                    "description": "Escena oscura inicial",
                    "tags": ["dark", "intro", "moody"]
                }
        """
        self.scenes.append(scene)


@dataclass
class StyleBook:
    """Libro de estilo del nicho."""
    visual_prompts: List[str] = field(default_factory=list)
    editing_style: Dict[str, any] = field(default_factory=dict)
    music_mapping_rules: List[Dict] = field(default_factory=list)
    hashtag_templates: List[str] = field(default_factory=list)
    title_templates: List[str] = field(default_factory=list)
    description_templates: List[str] = field(default_factory=list)
    
    def add_visual_prompt(self, prompt: str):
        """Agrega prompt visual."""
        self.visual_prompts.append(prompt)
    
    def set_editing_style(self, style: Dict[str, any]):
        """
        Define estilo de edición.
        
        Args:
            style: Dict con parámetros
                {
                    "transitions": "fast_cuts",
                    "color_grading": "dark_moody",
                    "effects": ["slow_motion", "glitch"],
                    "text_style": "bold_white",
                    "overlay": "purple_glow"
                }
        """
        self.editing_style = style
    
    def add_music_mapping_rule(self, rule: Dict):
        """
        Agrega regla de mapeo música → visual.
        
        Args:
            rule: Dict con regla
                {
                    "lyric_keyword": "barrio con oro",
                    "scene_to_use": "shameless_gold_scene",
                    "timing": "on_beat",
                    "duration": 2.5
                }
        """
        self.music_mapping_rules.append(rule)


@dataclass
class NicheProfile:
    """Perfil completo de un nicho."""
    niche: Niche
    name: str
    description: str
    visual_library: VisualLibrary
    style_book: StyleBook
    platforms_priority: List[str]  # ["tiktok", "instagram", "youtube"]
    content_sources: List[str]     # URLs o paths a fuentes
    target_audience: Dict[str, any]
    
    def get_visual_prompt_random(self) -> Optional[str]:
        """Obtiene prompt visual aleatorio."""
        import random
        if self.style_book.visual_prompts:
            return random.choice(self.style_book.visual_prompts)
        return None
    
    def get_hashtags_random(self, count: int = 5) -> List[str]:
        """Obtiene hashtags aleatorios."""
        import random
        if self.style_book.hashtag_templates:
            return random.sample(
                self.style_book.hashtag_templates,
                min(count, len(self.style_book.hashtag_templates))
            )
        return []


class SatelliteNicheEngine:
    """
    Motor de nichos para cuentas satélite.
    
    Features:
    - Asignación 1 cuenta → 1 nicho
    - Libros de estilo personalizados
    - Plantillas estéticas
    - Prompts por nicho
    """
    
    def __init__(self):
        self.niche_profiles: Dict[Niche, NicheProfile] = {}
        self.account_niche_mapping: Dict[str, Niche] = {}
        
        # Inicializar nichos predefinidos
        self._initialize_default_niches()
        
        logger.info("SatelliteNicheEngine initialized with default niches")
    
    def _initialize_default_niches(self):
        """Inicializa nichos predefinidos."""
        
        # 1. SHAMELESS EDITS
        shameless = self._create_shameless_profile()
        self.niche_profiles[Niche.SHAMELESS_EDITS] = shameless
        
        # 2. STRANGER THINGS
        stranger_things = self._create_stranger_things_profile()
        self.niche_profiles[Niche.STRANGER_THINGS] = stranger_things
        
        # 3. GTA CINEMATIC
        gta = self._create_gta_profile()
        self.niche_profiles[Niche.GTA_CINEMATIC] = gta
        
        # 4. EA SPORTS / FIFA
        fifa = self._create_fifa_profile()
        self.niche_profiles[Niche.EA_SPORTS_FIFA] = fifa
        
        # 5. ANIME EDITS
        anime = self._create_anime_profile()
        self.niche_profiles[Niche.ANIME_EDITS] = anime
        
        # 6. CORRIDOS AESTHETIC
        corridos = self._create_corridos_profile()
        self.niche_profiles[Niche.CORRIDOS_AESTHETIC] = corridos
        
        # 7. LIFESTYLE NEON
        lifestyle = self._create_lifestyle_neon_profile()
        self.niche_profiles[Niche.LIFESTYLE_NEON] = lifestyle
    
    def _create_shameless_profile(self) -> NicheProfile:
        """Crea perfil de Shameless Edits."""
        visual_lib = VisualLibrary(
            color_palette=["#1a1a2e", "#16213e", "#0f3460", "#e94560"],
            visual_style="gritty_urban"
        )
        
        style_book = StyleBook()
        style_book.set_editing_style({
            "transitions": "hard_cuts",
            "color_grading": "dark_contrast",
            "effects": ["slow_motion", "zoom_in"],
            "text_style": "bold_white_outline",
            "overlay": "none"
        })
        
        style_book.add_visual_prompt("Dark gritty urban scene from Shameless")
        style_book.add_visual_prompt("Character with money/gold from Shameless")
        style_book.add_visual_prompt("Street/barrio scene from Shameless")
        
        # Regla de mapeo ejemplo
        style_book.add_music_mapping_rule({
            "lyric_keyword": "barrio con oro",
            "scene_to_use": "shameless_gold_scene",
            "timing": "on_beat",
            "duration": 2.5
        })
        
        style_book.hashtag_templates = [
            "#Shameless", "#ShamelessEdits", "#ShamelessUS",
            "#Gallagher", "#FrankGallagher", "#Edits",
            "#TikTokEdits", "#ViralEdits"
        ]
        
        return NicheProfile(
            niche=Niche.SHAMELESS_EDITS,
            name="Shameless Edits",
            description="Edits urbanos de Shameless con música de Stakas",
            visual_library=visual_lib,
            style_book=style_book,
            platforms_priority=["tiktok", "instagram", "youtube"],
            content_sources=["shameless_clips_db", "shameless_episodes"],
            target_audience={
                "age_range": "16-30",
                "interests": ["urban_culture", "edits", "trap_music"]
            }
        )
    
    def _create_stranger_things_profile(self) -> NicheProfile:
        """Crea perfil de Stranger Things Edits."""
        visual_lib = VisualLibrary(
            color_palette=["#ff0000", "#000000", "#1a1a1a", "#ff6b6b"],
            visual_style="retro_horror"
        )
        
        style_book = StyleBook()
        style_book.set_editing_style({
            "transitions": "glitch_fade",
            "color_grading": "red_tint",
            "effects": ["vhs_effect", "chromatic_aberration"],
            "text_style": "retro_red",
            "overlay": "scanlines"
        })
        
        style_book.hashtag_templates = [
            "#StrangerThings", "#StrangerThingsEdits", "#ST5",
            "#Eleven", "#Demogorgon", "#UpsideDown",
            "#NetflixEdits", "#StrangerThings5"
        ]
        
        return NicheProfile(
            niche=Niche.STRANGER_THINGS,
            name="Stranger Things Edits",
            description="Edits retro-horror de Stranger Things",
            visual_library=visual_lib,
            style_book=style_book,
            platforms_priority=["tiktok", "instagram", "youtube"],
            content_sources=["stranger_things_clips_db"],
            target_audience={
                "age_range": "14-28",
                "interests": ["sci_fi", "horror", "netflix"]
            }
        )
    
    def _create_gta_profile(self) -> NicheProfile:
        """Crea perfil de GTA Cinematic."""
        visual_lib = VisualLibrary(
            color_palette=["#ff6b00", "#000000", "#1e90ff", "#ffd700"],
            visual_style="cinematic_gaming"
        )
        
        style_book = StyleBook()
        style_book.set_editing_style({
            "transitions": "smooth_fade",
            "color_grading": "vivid_saturated",
            "effects": ["motion_blur", "lens_flare"],
            "text_style": "gta_font",
            "overlay": "cinematic_bars"
        })
        
        style_book.hashtag_templates = [
            "#GTA5", "#GTAOnline", "#GTARP",
            "#GTACinematic", "#GTA", "#RockstarGames",
            "#GTAEdits", "#GamingEdits"
        ]
        
        return NicheProfile(
            niche=Niche.GTA_CINEMATIC,
            name="GTA Cinematic",
            description="Edits cinemáticos de GTA 5 / GTA RP",
            visual_library=visual_lib,
            style_book=style_book,
            platforms_priority=["tiktok", "youtube", "instagram"],
            content_sources=["gta_gameplay_db", "gta_rp_clips"],
            target_audience={
                "age_range": "16-35",
                "interests": ["gaming", "gta", "roleplay"]
            }
        )
    
    def _create_fifa_profile(self) -> NicheProfile:
        """Crea perfil de EA Sports / FIFA."""
        visual_lib = VisualLibrary(
            color_palette=["#00ff00", "#ffffff", "#000000", "#0066ff"],
            visual_style="sports_hype"
        )
        
        style_book = StyleBook()
        style_book.hashtag_templates = [
            "#FIFA", "#FIFA24", "#FIFAEdits",
            "#EASports", "#FUT", "#Football",
            "#Soccer", "#FIFAGoals"
        ]
        
        return NicheProfile(
            niche=Niche.EA_SPORTS_FIFA,
            name="EA Sports / FIFA Edits",
            description="Edits deportivos de FIFA",
            visual_library=visual_lib,
            style_book=style_book,
            platforms_priority=["tiktok", "instagram", "youtube"],
            content_sources=["fifa_gameplay_db"],
            target_audience={
                "age_range": "14-30",
                "interests": ["sports", "fifa", "football"]
            }
        )
    
    def _create_anime_profile(self) -> NicheProfile:
        """Crea perfil de Anime Edits."""
        visual_lib = VisualLibrary(
            color_palette=["#ff69b4", "#9370db", "#00ffff", "#ff1493"],
            visual_style="anime_aesthetic"
        )
        
        style_book = StyleBook()
        style_book.hashtag_templates = [
            "#Anime", "#AnimeEdits", "#AnimeEdit",
            "#Weeb", "#Otaku", "#AnimeAesthetic",
            "#AnimeTikTok", "#AnimeReels"
        ]
        
        return NicheProfile(
            niche=Niche.ANIME_EDITS,
            name="Anime Edits",
            description="Edits estéticos de anime",
            visual_library=visual_lib,
            style_book=style_book,
            platforms_priority=["tiktok", "instagram", "youtube"],
            content_sources=["anime_clips_db"],
            target_audience={
                "age_range": "14-26",
                "interests": ["anime", "manga", "japanese_culture"]
            }
        )
    
    def _create_corridos_profile(self) -> NicheProfile:
        """Crea perfil de Corridos Aesthetic."""
        visual_lib = VisualLibrary(
            color_palette=["#8b4513", "#ffd700", "#ff6347", "#2f4f4f"],
            visual_style="corridos_aesthetic"
        )
        
        style_book = StyleBook()
        style_book.hashtag_templates = [
            "#Corridos", "#CorridosTumbados", "#CorridosEdits",
            "#RegionalMexicano", "#Mexico", "#Aesthetic",
            "#CorridosAesthetic"
        ]
        
        return NicheProfile(
            niche=Niche.CORRIDOS_AESTHETIC,
            name="Corridos Aesthetic",
            description="Edits aesthetic de corridos",
            visual_library=visual_lib,
            style_book=style_book,
            platforms_priority=["tiktok", "instagram", "youtube"],
            content_sources=["corridos_clips_db"],
            target_audience={
                "age_range": "16-35",
                "interests": ["corridos", "regional_mexicano", "latin_culture"]
            }
        )
    
    def _create_lifestyle_neon_profile(self) -> NicheProfile:
        """Crea perfil de Lifestyle Neon Purple."""
        visual_lib = VisualLibrary(
            color_palette=["#9d00ff", "#ff00ff", "#00ffff", "#000000"],
            visual_style="neon_cyberpunk"
        )
        
        style_book = StyleBook()
        style_book.set_editing_style({
            "transitions": "neon_fade",
            "color_grading": "purple_neon",
            "effects": ["neon_glow", "chromatic_aberration"],
            "text_style": "neon_purple",
            "overlay": "purple_gradient"
        })
        
        style_book.hashtag_templates = [
            "#Aesthetic", "#NeonAesthetic", "#PurpleAesthetic",
            "#Lifestyle", "#Vibes", "#NeonVibes",
            "#CyberpunkAesthetic"
        ]
        
        return NicheProfile(
            niche=Niche.LIFESTYLE_NEON,
            name="Lifestyle Neon Purple",
            description="Lifestyle aesthetic con neon purple",
            visual_library=visual_lib,
            style_book=style_book,
            platforms_priority=["instagram", "tiktok", "youtube"],
            content_sources=["lifestyle_clips_db", "neon_city_clips"],
            target_audience={
                "age_range": "18-32",
                "interests": ["aesthetic", "lifestyle", "cyberpunk"]
            }
        )
    
    def assign_niche_to_account(
        self,
        account_id: str,
        niche: Niche
    ) -> bool:
        """
        Asigna nicho a cuenta satélite.
        
        Args:
            account_id: ID de cuenta
            niche: Nicho a asignar
            
        Returns:
            True si se asignó exitosamente
        """
        if niche not in self.niche_profiles:
            logger.error(f"Niche {niche} not found in profiles")
            return False
        
        self.account_niche_mapping[account_id] = niche
        
        logger.info(f"Niche assigned: {account_id} → {niche.value}")
        return True
    
    def get_account_niche(self, account_id: str) -> Optional[Niche]:
        """Obtiene nicho de cuenta."""
        return self.account_niche_mapping.get(account_id)
    
    def get_niche_profile(self, niche: Niche) -> Optional[NicheProfile]:
        """Obtiene perfil de nicho."""
        return self.niche_profiles.get(niche)
    
    def get_account_profile(self, account_id: str) -> Optional[NicheProfile]:
        """Obtiene perfil de cuenta (via su nicho)."""
        niche = self.get_account_niche(account_id)
        if niche:
            return self.get_niche_profile(niche)
        return None
    
    def get_stats(self) -> Dict[str, any]:
        """Obtiene estadísticas del niche engine."""
        return {
            "total_niches": len(self.niche_profiles),
            "assigned_accounts": len(self.account_niche_mapping),
            "niche_distribution": {
                niche.value: len([
                    acc for acc, n in self.account_niche_mapping.items()
                    if n == niche
                ])
                for niche in Niche
            }
        }
