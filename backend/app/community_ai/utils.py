"""
Utility functions for Community Manager AI.
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime, time
import hashlib


def load_brand_rules(filepath: str) -> Dict[str, Any]:
    """
    Load BRAND_STATIC_RULES.json.
    
    Args:
        filepath: Path to rules JSON
    
    Returns:
        Brand rules dict
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_brand_rules(rules: Dict[str, Any], filepath: str) -> None:
    """
    Save brand rules to JSON.
    
    Args:
        rules: Rules dict
        filepath: Output path
    """
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(rules, f, indent=2, ensure_ascii=False)


def calculate_confidence_score(
    data_points: int,
    pattern_strength: float,
    time_stability: float
) -> float:
    """
    Calculate confidence score for recommendations.
    
    Args:
        data_points: Number of data points (more = higher confidence)
        pattern_strength: Strength of pattern (0.0 - 1.0)
        time_stability: Temporal stability (0.0 - 1.0)
    
    Returns:
        Confidence score (0.0 - 1.0)
    """
    # Normalize data points (cap at 100)
    data_normalized = min(data_points / 100, 1.0)
    
    # Weighted average
    confidence = (
        data_normalized * 0.4 +
        pattern_strength * 0.4 +
        time_stability * 0.2
    )
    
    return max(0.0, min(1.0, confidence))


def is_optimal_posting_time(
    hour: int,
    platform: str,
    historical_data: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Check if given hour is optimal for posting.
    
    Args:
        hour: Hour (0-23)
        platform: Platform name
        historical_data: Optional historical performance by hour
    
    Returns:
        True if optimal time
    """
    # Default optimal hours by platform
    default_optimal = {
        "instagram": [12, 19, 20, 21],
        "tiktok": [18, 19, 20, 21, 22],
        "youtube": [17, 18, 19, 20]
    }
    
    if historical_data and platform in historical_data:
        optimal_hours = historical_data[platform].get("best_hours", [])
        if optimal_hours:
            return hour in optimal_hours
    
    return hour in default_optimal.get(platform, [20])


def format_caption_with_hashtags(
    caption: str,
    hashtags: List[str],
    max_length: int = 2200
) -> str:
    """
    Format caption with hashtags.
    
    Args:
        caption: Main caption text
        hashtags: List of hashtags
        max_length: Max caption length
    
    Returns:
        Formatted caption
    """
    # Add line break before hashtags
    full_caption = f"{caption}\n\n{' '.join(hashtags)}"
    
    # Truncate if needed
    if len(full_caption) > max_length:
        available_space = max_length - len(caption) - 4  # Account for "\n\n"
        hashtags_str = ' '.join(hashtags)
        if len(hashtags_str) > available_space:
            # Trim hashtags
            hashtags_str = hashtags_str[:available_space-3] + "..."
        full_caption = f"{caption}\n\n{hashtags_str}"
    
    return full_caption


def generate_post_id(
    user_id: str,
    platform: str,
    timestamp: datetime
) -> str:
    """
    Generate unique post ID.
    
    Args:
        user_id: User ID
        platform: Platform name
        timestamp: Post timestamp
    
    Returns:
        Unique post ID
    """
    base = f"{user_id}_{platform}_{timestamp.strftime('%Y%m%d_%H%M%S')}"
    hash_suffix = hashlib.md5(base.encode()).hexdigest()[:8]
    return f"{platform}_{timestamp.strftime('%Y%m%d')}_{hash_suffix}"


def calculate_virality_score(
    engagement_rate: float,
    growth_velocity: float,
    share_rate: float
) -> float:
    """
    Calculate virality score.
    
    Args:
        engagement_rate: Engagement rate (0.0 - 1.0)
        growth_velocity: Growth velocity (relative)
        share_rate: Share/save rate (0.0 - 1.0)
    
    Returns:
        Virality score (0.0 - 1.0)
    """
    # Normalize growth velocity (cap at 5x)
    growth_normalized = min(growth_velocity / 5.0, 1.0)
    
    # Weighted combination
    virality = (
        engagement_rate * 0.3 +
        growth_normalized * 0.4 +
        share_rate * 0.3
    )
    
    return max(0.0, min(1.0, virality))


def estimate_llm_cost(
    input_tokens: int,
    output_tokens: int,
    model: str = "gemini-1.5-flash"
) -> float:
    """
    Estimate LLM API cost.
    
    Args:
        input_tokens: Input tokens
        output_tokens: Output tokens
        model: Model name
    
    Returns:
        Estimated cost in EUR
    """
    # Cost per 1M tokens (approximate)
    costs = {
        "gemini-1.5-flash": {"input": 0.075, "output": 0.30},  # USD per 1M tokens
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "gpt-4o": {"input": 5.00, "output": 15.00}
    }
    
    if model not in costs:
        model = "gemini-1.5-flash"
    
    input_cost = (input_tokens / 1_000_000) * costs[model]["input"]
    output_cost = (output_tokens / 1_000_000) * costs[model]["output"]
    
    total_usd = input_cost + output_cost
    total_eur = total_usd * 0.95  # Approximate EUR conversion
    
    return total_eur


def validate_brand_compliance(
    content: Dict[str, Any],
    brand_rules: Dict[str, Any]
) -> tuple[bool, float, List[str]]:
    """
    Validate content against brand rules.
    
    Args:
        content: Content to validate
        brand_rules: Brand rules
    
    Returns:
        (is_compliant, score, violations)
    """
    violations = []
    score = 1.0
    
    # Check prohibitions
    if "prohibitions" in brand_rules:
        caption = content.get("caption", "").lower()
        for prohibition in brand_rules["prohibitions"]:
            if prohibition.lower() in caption:
                violations.append(f"Prohibition violated: {prohibition}")
                score -= 0.3
    
    # Check aesthetic requirements
    if "aesthetic" in brand_rules:
        required = brand_rules["aesthetic"].get("mandatory", [])
        content_aesthetics = content.get("aesthetic_tags", [])
        
        missing_required = [r for r in required if not any(r.lower() in a.lower() for a in content_aesthetics)]
        if missing_required:
            violations.append(f"Missing required aesthetics: {', '.join(missing_required)}")
            score -= 0.2 * len(missing_required)
    
    # Check content themes
    if "content" in brand_rules:
        allowed_themes = brand_rules["content"].get("themes", [])
        if allowed_themes:
            content_themes = content.get("themes", [])
            if not any(theme in content_themes for theme in allowed_themes):
                violations.append("Content theme not aligned with brand")
                score -= 0.15
    
    score = max(0.0, score)
    is_compliant = score >= 0.7 and len(violations) == 0
    
    return is_compliant, score, violations


def extract_hook_from_caption(caption: str) -> str:
    """
    Extract first sentence as hook.
    
    Args:
        caption: Full caption
    
    Returns:
        Hook (first sentence)
    """
    # Find first sentence
    sentences = caption.split('.')
    if sentences:
        hook = sentences[0].strip()
        if len(hook) > 80:
            # Truncate long hooks
            hook = hook[:77] + "..."
        return hook
    return caption[:80]


def merge_hashtags(
    base_tags: List[str],
    trending_tags: List[str],
    max_tags: int = 30
) -> List[str]:
    """
    Merge base and trending hashtags.
    
    Args:
        base_tags: Base brand hashtags
        trending_tags: Trending hashtags
        max_tags: Maximum number of tags
    
    Returns:
        Merged hashtag list
    """
    # Remove duplicates, preserve order
    seen = set()
    merged = []
    
    # Add base tags first
    for tag in base_tags:
        tag_clean = tag.strip().lower()
        if tag_clean not in seen:
            seen.add(tag_clean)
            merged.append(tag)
    
    # Add trending tags
    for tag in trending_tags:
        tag_clean = tag.strip().lower()
        if tag_clean not in seen and len(merged) < max_tags:
            seen.add(tag_clean)
            merged.append(tag)
    
    return merged[:max_tags]
