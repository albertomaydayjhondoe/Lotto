"""
Platform-specific heuristics - hard rules for each platform.
"""
from typing import Dict
from app.rules_engine.models import AdaptiveRuleSet


def apply_platform_heuristics(
    rules: AdaptiveRuleSet,
    platform: str
) -> AdaptiveRuleSet:
    """
    Apply platform-specific heuristics to rule weights.
    
    Args:
        rules: Base adaptive rule set
        platform: Target platform
        
    Returns:
        Modified rule set with platform heuristics applied
    """
    weights = rules.weights.copy()
    
    if platform == "tiktok":
        weights = _apply_tiktok_heuristics(weights)
    elif platform == "instagram":
        weights = _apply_instagram_heuristics(weights)
    elif platform == "youtube":
        weights = _apply_youtube_heuristics(weights)
    
    # Normalize weights
    weights = _normalize_weights(weights)
    
    return AdaptiveRuleSet(
        platform=rules.platform,
        weights=weights,
        updated_at=rules.updated_at
    )


def _apply_tiktok_heuristics(weights: Dict[str, float]) -> Dict[str, float]:
    """
    TikTok prioritizes:
    - Short duration (≤15s)
    - High motion intensity
    - Fast-paced content
    """
    weights = weights.copy()
    
    # Increase motion_intensity weight
    weights["motion_intensity"] = weights.get("motion_intensity", 0.1) * 1.5
    
    # Slightly decrease duration weight (shorter is better)
    weights["duration_ms"] = weights.get("duration_ms", 0.2) * 0.8
    
    return weights


def _apply_instagram_heuristics(weights: Dict[str, float]) -> Dict[str, float]:
    """
    Instagram prioritizes:
    - Visual quality (aesthetic)
    - Medium duration (15-30s)
    - Polished content
    """
    weights = weights.copy()
    
    # Increase visual_score weight
    weights["visual_score"] = weights.get("visual_score", 0.5) * 1.3
    
    # Balanced duration
    weights["duration_ms"] = weights.get("duration_ms", 0.2) * 1.0
    
    return weights


def _apply_youtube_heuristics(weights: Dict[str, float]) -> Dict[str, float]:
    """
    YouTube prioritizes:
    - Longer duration (45-60s+)
    - Narrative/storytelling
    - Content depth
    """
    weights = weights.copy()
    
    # Increase duration weight (longer is better)
    weights["duration_ms"] = weights.get("duration_ms", 0.2) * 1.4
    
    # Increase cut_position weight (narrative flow)
    weights["cut_position"] = weights.get("cut_position", 0.2) * 1.2
    
    return weights


def _normalize_weights(weights: Dict[str, float]) -> Dict[str, float]:
    """
    Normalize weights to sum to 1.0.
    """
    total = sum(weights.values())
    
    if total == 0:
        return weights
    
    return {name: w / total for name, w in weights.items()}


def get_optimal_duration_range(platform: str) -> tuple[float, float]:
    """
    Get optimal duration range for a platform (in milliseconds).
    
    Returns:
        (min_ms, max_ms) tuple
    """
    if platform == "tiktok":
        return (5000, 15000)  # 5-15 seconds
    elif platform == "instagram":
        return (15000, 30000)  # 15-30 seconds
    elif platform == "youtube":
        return (45000, 90000)  # 45-90 seconds
    else:
        return (10000, 60000)  # default
