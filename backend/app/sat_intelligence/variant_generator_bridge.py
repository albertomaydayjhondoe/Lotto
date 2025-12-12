"""
SPRINT 11 - Satellite Intelligence Optimization
Module: Variant Generator Bridge

Bridge al sistema de generación de variantes de contenido:
- Captions
- Hashtags
- Thumbnail selection
- Audio start offsets

Usa templates de nicho y randomization para evitar duplicación.
"""

import logging
import random
import hashlib
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

from .sat_intel_contracts import ContentVariant, AccountProfile

logger = logging.getLogger(__name__)


# ============================================================================
# CONFIG
# ============================================================================

@dataclass
class VariantConfig:
    """Configuración del variant generator"""
    
    # Caption settings
    max_caption_length: int = 150
    min_caption_length: int = 20
    
    # Hashtag settings
    min_hashtags: int = 3
    max_hashtags: int = 8
    
    # Thumbnail settings
    thumbnail_count: int = 3  # Number of frame options
    
    # Audio settings
    max_audio_offset_seconds: float = 5.0


# ============================================================================
# TEMPLATES
# ============================================================================

# Caption templates por nicho
CAPTION_TEMPLATES = {
    "music": [
        "🎵 {hook} {emoji}",
        "{hook} 🔥",
        "POV: {scenario} {emoji}",
        "{question} 🎶",
        "When {situation} hits different {emoji}",
    ],
    "dance": [
        "💃 {hook} {emoji}",
        "{hook} ✨",
        "POV: {scenario} {emoji}",
        "This choreo though {emoji}",
        "{situation} vibes {emoji}",
    ],
    "comedy": [
        "😂 {hook}",
        "POV: {scenario}",
        "When {situation} 💀",
        "{question} 🤔",
        "Not me {situation} {emoji}",
    ],
    "food": [
        "🍴 {hook} {emoji}",
        "POV: {scenario}",
        "Made this {situation} {emoji}",
        "{question} 👀",
        "Recipe in comments {emoji}",
    ],
}

# Hashtag pools por nicho
HASHTAG_POOLS = {
    "music": [
        "#music", "#song", "#newmusic", "#indie", "#pop",
        "#viral", "#fyp", "#foryou", "#trending", "#vibes",
        "#artist", "#musician", "#producer", "#beats",
    ],
    "dance": [
        "#dance", "#dancer", "#choreography", "#dancing", "#moves",
        "#viral", "#fyp", "#foryou", "#trending", "#dancechallenge",
        "#hiphop", "#contemporary", "#freestyle",
    ],
    "comedy": [
        "#funny", "#comedy", "#memes", "#lol", "#humor",
        "#viral", "#fyp", "#foryou", "#trending", "#relatable",
        "#comedy", "#sketch", "#pov",
    ],
    "food": [
        "#food", "#cooking", "#recipe", "#foodie", "#yummy",
        "#viral", "#fyp", "#foryou", "#trending", "#easyrecipe",
        "#homemade", "#delicious", "#foodtok",
    ],
}

# Emoji pools por nicho
EMOJI_POOLS = {
    "music": ["🎵", "🎶", "🎤", "🎧", "🔥", "✨", "💫", "⭐"],
    "dance": ["💃", "🕺", "✨", "🔥", "💫", "⚡", "💯"],
    "comedy": ["😂", "🤣", "💀", "😭", "🤡", "👀", "🙃"],
    "food": ["🍴", "👨‍🍳", "🔥", "😋", "🤤", "✨", "💯"],
}


# ============================================================================
# VARIANT GENERATOR BRIDGE
# ============================================================================

class VariantGeneratorBridge:
    """
    Bridge al sistema de generación de variantes.
    
    Genera variaciones únicas de contenido usando:
    - Templates de caption
    - Pools de hashtags
    - Thumbnail selection
    - Audio offsets
    - Randomization con seeds
    """
    
    def __init__(self, config: Optional[VariantConfig] = None):
        self.config = config or VariantConfig()
        self._rng = random.Random()
        logger.info("VariantGeneratorBridge initialized")
    
    # ========================================================================
    # PUBLIC API
    # ========================================================================
    
    def generate_variant(
        self,
        content_id: str,
        account: AccountProfile,
        audio_track_id: Optional[str] = None,
        seed: Optional[int] = None
    ) -> ContentVariant:
        """
        Genera una variante única de contenido para una cuenta.
        
        Args:
            content_id: ID del contenido
            account: Perfil de la cuenta
            audio_track_id: ID del audio track (opcional)
            seed: Seed para reproducibilidad (opcional)
        
        Returns:
            ContentVariant con caption, hashtags, thumbnail, etc.
        """
        # Use seed if provided, else generate from content_id + account_id
        if seed is None:
            seed = self._generate_seed(content_id, account.account_id)
        
        self._rng.seed(seed)
        
        logger.debug(f"Generating variant for {content_id} / {account.account_id} (seed={seed})")
        
        # 1. Generate caption
        caption = self._generate_caption(account.niche_id)
        
        # 2. Generate hashtags
        hashtags = self._generate_hashtags(account.niche_id)
        
        # 3. Select thumbnail
        thumbnail_index = self._select_thumbnail()
        
        # 4. Audio offset
        audio_start_offset = self._generate_audio_offset() if audio_track_id else 0.0
        
        variant_id = f"var_{content_id}_{account.account_id}_{seed}"
        
        variant = ContentVariant(
            variant_id=variant_id,
            caption=caption,
            hashtags=hashtags,
            thumbnail_index=thumbnail_index,
            audio_track_id=audio_track_id,
            audio_start_offset=audio_start_offset,
            template_used=None,  # Could track template
            randomization_seed=seed,
        )
        
        logger.debug(f"Generated variant {variant_id}: caption_len={len(caption)}, "
                    f"hashtags={len(hashtags)}, thumbnail={thumbnail_index}")
        
        return variant
    
    def batch_generate_variants(
        self,
        content_ids: List[str],
        accounts: List[AccountProfile],
        audio_track_ids: Optional[Dict[str, str]] = None
    ) -> Dict[str, Dict[str, ContentVariant]]:
        """
        Genera variantes para múltiples contenidos y cuentas.
        
        Returns:
            Dict[content_id][account_id] = ContentVariant
        """
        audio_track_ids = audio_track_ids or {}
        variants = {}
        
        for content_id in content_ids:
            variants[content_id] = {}
            for account in accounts:
                audio_id = audio_track_ids.get(content_id)
                variant = self.generate_variant(content_id, account, audio_id)
                variants[content_id][account.account_id] = variant
        
        logger.info(f"Generated {len(content_ids)} × {len(accounts)} = "
                   f"{len(content_ids) * len(accounts)} variants")
        
        return variants
    
    def regenerate_variant(
        self,
        content_id: str,
        account: AccountProfile,
        avoid_seeds: List[int],
        audio_track_id: Optional[str] = None
    ) -> ContentVariant:
        """
        Re-genera una variante con un seed diferente.
        
        Útil cuando una variante falla validation.
        """
        # Generate new seed not in avoid_seeds
        max_attempts = 100
        for _ in range(max_attempts):
            seed = self._rng.randint(1, 1_000_000)
            if seed not in avoid_seeds:
                return self.generate_variant(content_id, account, audio_track_id, seed)
        
        logger.warning(f"Could not find unique seed after {max_attempts} attempts")
        return self.generate_variant(content_id, account, audio_track_id, seed)
    
    # ========================================================================
    # CAPTION GENERATION
    # ========================================================================
    
    def _generate_caption(self, niche_id: str) -> str:
        """Genera caption usando templates del nicho"""
        
        templates = CAPTION_TEMPLATES.get(niche_id, CAPTION_TEMPLATES["music"])
        template = self._rng.choice(templates)
        
        # Fill template variables
        variables = {
            "hook": self._generate_hook(niche_id),
            "scenario": self._generate_scenario(niche_id),
            "situation": self._generate_situation(niche_id),
            "question": self._generate_question(niche_id),
            "emoji": self._pick_emoji(niche_id),
        }
        
        try:
            caption = template.format(**variables)
        except KeyError:
            # Template doesn't use all variables, that's OK
            caption = template
        
        # Trim to max length
        if len(caption) > self.config.max_caption_length:
            caption = caption[:self.config.max_caption_length - 3] + "..."
        
        return caption
    
    def _generate_hook(self, niche_id: str) -> str:
        """Genera hook para caption"""
        hooks = {
            "music": ["This hits different", "Can't stop listening", "On repeat", "Pure vibes"],
            "dance": ["This choreo", "Watch this", "Learning this", "Nailed it"],
            "comedy": ["Wait for it", "Not me", "Tell me why", "This energy"],
            "food": ["Made this", "Cooking up", "Easy recipe", "Quick meal"],
        }
        return self._rng.choice(hooks.get(niche_id, ["Check this out"]))
    
    def _generate_scenario(self, niche_id: str) -> str:
        """Genera scenario para POV captions"""
        scenarios = {
            "music": ["you discover the perfect song", "this comes on shuffle", "the beat drops"],
            "dance": ["you learn the choreo", "the music hits", "you freestyle"],
            "comedy": ["that moment when", "you realize", "nobody is watching"],
            "food": ["you make this recipe", "it's dinner time", "you're hungry"],
        }
        return self._rng.choice(scenarios.get(niche_id, ["something amazing happens"]))
    
    def _generate_situation(self, niche_id: str) -> str:
        """Genera situation para captions"""
        situations = {
            "music": ["at 3am", "on the way home", "in the car", "alone"],
            "dance": ["for the first time", "in public", "with friends", "at home"],
            "comedy": ["when nobody asked", "at the worst time", "in front of everyone"],
            "food": ["in 10 minutes", "with leftovers", "for dinner", "first try"],
        }
        return self._rng.choice(situations.get(niche_id, ["right now"]))
    
    def _generate_question(self, niche_id: str) -> str:
        """Genera question para captions"""
        questions = {
            "music": ["What's your favorite part?", "Who else loves this?", "Rate this 1-10?"],
            "dance": ["Can you do this?", "Should I post more?", "Which move is harder?"],
            "comedy": ["Why is this so accurate?", "Am I the only one?", "Who relates?"],
            "food": ["Would you try this?", "What should I make next?", "Too much cheese?"],
        }
        return self._rng.choice(questions.get(niche_id, ["What do you think?"]))
    
    def _pick_emoji(self, niche_id: str) -> str:
        """Elige emoji aleatorio del pool del nicho"""
        emojis = EMOJI_POOLS.get(niche_id, ["✨", "🔥", "💫"])
        return self._rng.choice(emojis)
    
    # ========================================================================
    # HASHTAG GENERATION
    # ========================================================================
    
    def _generate_hashtags(self, niche_id: str) -> List[str]:
        """Genera lista de hashtags del pool del nicho"""
        
        pool = HASHTAG_POOLS.get(niche_id, HASHTAG_POOLS["music"])
        
        # Count de hashtags
        count = self._rng.randint(self.config.min_hashtags, self.config.max_hashtags)
        
        # Sample sin replacement
        hashtags = self._rng.sample(pool, min(count, len(pool)))
        
        return hashtags
    
    # ========================================================================
    # THUMBNAIL & AUDIO
    # ========================================================================
    
    def _select_thumbnail(self) -> int:
        """Selecciona índice de thumbnail"""
        return self._rng.randint(0, self.config.thumbnail_count - 1)
    
    def _generate_audio_offset(self) -> float:
        """Genera audio start offset aleatorio"""
        return self._rng.uniform(0.0, self.config.max_audio_offset_seconds)
    
    # ========================================================================
    # HELPERS
    # ========================================================================
    
    def _generate_seed(self, content_id: str, account_id: str) -> int:
        """Genera seed determinístico desde content_id + account_id"""
        combined = f"{content_id}_{account_id}"
        hash_bytes = hashlib.sha256(combined.encode()).digest()
        seed = int.from_bytes(hash_bytes[:4], byteorder="big")
        return seed


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def generate_simple_variant(
    content_id: str,
    account_id: str,
    niche_id: str = "music"
) -> ContentVariant:
    """Helper para generar variante simple"""
    
    bridge = VariantGeneratorBridge()
    
    # Mock account
    account = AccountProfile(
        account_id=account_id,
        niche_id=niche_id,
        niche_name=niche_id.title(),
        is_active=True,
    )
    
    return bridge.generate_variant(content_id, account)


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "VariantConfig",
    "VariantGeneratorBridge",
    "generate_simple_variant",
]
