"""
Satellite Generator: Transforms onboarding answers into satellite_rules.json

This module automates the generation of satellite channel rules for experimental
content that operates with more freedom than official brand content.
"""

import json
from typing import Dict, List, Any
from pathlib import Path


class SatelliteGenerator:
    """
    Generates satellite_rules.json from onboarding questionnaire answers.
    
    Satellite rules govern experimental channels that test trends, formats,
    and viral content without brand compliance constraints.
    """
    
    def __init__(self, answers_path: str):
        """
        Initialize generator with onboarding answers.
        
        Args:
            answers_path: Path to onboarding_answers.json file
        """
        self.answers_path = Path(answers_path)
        with open(self.answers_path, 'r', encoding='utf-8') as f:
            self.answers = json.load(f)
    
    def generate(self) -> Dict[str, Any]:
        """
        Generate complete satellite_rules.json from answers.
        
        Returns:
            Dict containing satellite channel rules
        """
        satellite_rules = {
            "version": "1.0.0",
            "artist_id": self.answers.get("artist_id"),
            "artist_name": self.answers.get("artist_name"),
            "generated_at": self.answers.get("completed_at"),
            "channel_type": "satellite",
            
            "philosophy": self._generate_philosophy(),
            "content_rules": self._generate_content_rules(),
            "prohibitions": self._generate_prohibitions(),
            "freedoms": self._generate_freedoms(),
            "quality_standards": self._generate_quality_standards(),
            "posting_strategy": self._generate_posting_strategy(),
            "experimentation_rules": self._generate_experimentation_rules(),
            "ml_learning_rules": self._generate_ml_learning_rules()
        }
        
        return satellite_rules
    
    def _generate_philosophy(self) -> Dict[str, Any]:
        """Generate satellite channel philosophy."""
        return {
            "purpose": "Experimental testing ground for trends, formats, and viral content",
            "objective": "Collect ML training data and identify winning patterns without brand risk",
            "relationship_to_official": "Completely separate - NO brand validation required",
            "key_principles": [
                "Experimentation over perfection",
                "Rapid iteration and learning",
                "Trend testing without brand constraints",
                "ML data collection focus",
                "Never show real artist identity"
            ]
        }
    
    def _generate_content_rules(self) -> Dict[str, Any]:
        """Generate satellite content rules."""
        official_vs_sat = self.answers.get("official_vs_satellite", {})
        
        return {
            "allowed_content_types": official_vs_sat.get("q31_satellite_content_types", []),
            "content_categories": {
                "viral_edits": {
                    "enabled": True,
                    "description": "Fast-paced edits with trending music",
                    "examples": ["lyric_edits", "beat_sync_edits", "transition_edits"]
                },
                "ai_videos": {
                    "enabled": True,
                    "description": "AI-generated videos and experimental AI content",
                    "examples": ["AI_music_videos", "style_transfer", "deepfake_experiments"]
                },
                "game_clips": {
                    "enabled": True,
                    "description": "GTA, anime, movie/series clips with music overlay",
                    "examples": ["GTA_edits", "anime_AMV", "movie_scene_edits"]
                },
                "trend_testing": {
                    "enabled": True,
                    "description": "Testing popular TikTok/Instagram trends",
                    "examples": ["dance_trends", "audio_trends", "format_trends"]
                },
                "format_experiments": {
                    "enabled": True,
                    "description": "New video formats and editing styles",
                    "examples": ["vertical_video", "split_screen", "text_heavy"]
                }
            },
            "content_sources": [
                "AI_generated",
                "stock_footage",
                "game_clips",
                "anime_clips",
                "movie_clips",
                "public_domain",
                "creative_commons"
            ]
        }
    
    def _generate_prohibitions(self) -> Dict[str, Any]:
        """Generate strict prohibitions for satellite content."""
        official_vs_sat = self.answers.get("official_vs_satellite", {})
        satellite_rules = official_vs_sat.get("q32_satellite_rules", [])
        
        # Extract NO_ rules
        no_rules = [rule for rule in satellite_rules if rule.startswith("NO_")]
        
        return {
            "absolute_prohibitions": no_rules,
            "detailed_rules": {
                "NO_mostrar_artista_real": {
                    "rule": "Never show real artist face, body, or recognizable features",
                    "reason": "Satellite is separate from artist's real identity",
                    "enforcement": "automatic_rejection",
                    "exceptions": []
                },
                "NO_mezclar_estetica_oficial": {
                    "rule": "Never use official brand aesthetic, colors, or visual style",
                    "reason": "Maintain clear separation between official and satellite",
                    "enforcement": "automatic_rejection",
                    "exceptions": []
                },
                "NO_usar_vestuario_oficial": {
                    "rule": "Never use artist's official wardrobe, accessories, or fashion",
                    "reason": "Prevent brand identity confusion",
                    "enforcement": "automatic_rejection",
                    "exceptions": []
                }
            },
            "content_restrictions": {
                "no_brand_validation": "Satellite content does NOT require brand compliance",
                "no_color_palette_enforcement": "Official color palette does NOT apply",
                "no_aesthetic_coherence": "Aesthetic coherence with official NOT required",
                "no_narrative_alignment": "Narrative alignment with brand NOT required"
            }
        }
    
    def _generate_freedoms(self) -> Dict[str, Any]:
        """Generate freedoms and permissions for satellite content."""
        official_vs_sat = self.answers.get("official_vs_satellite", {})
        satellite_rules = official_vs_sat.get("q32_satellite_rules", [])
        
        # Extract SI_ rules
        si_rules = [rule for rule in satellite_rules if rule.startswith("SI_")]
        
        return {
            "creative_freedoms": si_rules,
            "detailed_permissions": {
                "SI_experimentar_libremente": {
                    "freedom": "Complete creative freedom to experiment",
                    "scope": "Unlimited experimentation with formats, styles, trends",
                    "only_limit": "Must not violate prohibitions (NO_ rules)"
                },
                "SI_usar_IA": {
                    "freedom": "Full permission to use AI-generated content",
                    "scope": "AI videos, AI images, AI music, deepfakes, style transfer",
                    "quality": "No minimum quality requirements"
                },
                "SI_contenido_edgy": {
                    "freedom": "Permission for edgy, controversial, experimental content",
                    "scope": "Content that wouldn't fit official brand can be tested",
                    "guardrails": "Legal compliance only (no illegal content)"
                }
            },
            "no_validation_required": [
                "brand_compliance_check",
                "color_palette_validation",
                "aesthetic_coherence_check",
                "narrative_alignment_check",
                "quality_gate_official"
            ]
        }
    
    def _generate_quality_standards(self) -> Dict[str, Any]:
        """Generate quality standards for satellite content."""
        official_vs_sat = self.answers.get("official_vs_satellite", {})
        
        return {
            "minimum_quality_score": official_vs_sat.get("q34_quality_threshold_satellite", 5),
            "quality_philosophy": "Good enough to test, not necessarily polished",
            "acceptance_criteria": {
                "technical_quality": 5.0,
                "watchability": 5.0,
                "no_brand_validation": True,
                "no_aesthetic_validation": True
            },
            "rejection_criteria": [
                "extremely_low_resolution",
                "unwatchable_quality",
                "copyright_violation",
                "illegal_content"
            ],
            "iteration_approach": "Post, measure, learn, iterate rapidly"
        }
    
    def _generate_posting_strategy(self) -> Dict[str, Any]:
        """Generate posting strategy for satellite channels."""
        strategy = self.answers.get("content_strategy", {})
        audience = self.answers.get("audience_targeting", {})
        
        return {
            "frequency": {
                "posts_per_week": strategy.get("q40_posting_frequency_satellite", 15),
                "posts_per_day": 3,
                "posting_rhythm": "rapid_iteration"
            },
            "timing": {
                "optimal_times": strategy.get("q41_optimal_posting_times", []),
                "flexible_scheduling": True,
                "test_different_times": True
            },
            "volume_philosophy": "High volume for rapid learning and pattern discovery",
            "platforms": {
                "primary": audience.get("q38_content_consumption", []),
                "format_per_platform": {
                    "tiktok": ["short_form", "trends", "edits"],
                    "instagram_reels": ["viral_edits", "music_edits"],
                    "youtube_shorts": ["experimental", "ai_content"]
                }
            }
        }
    
    def _generate_experimentation_rules(self) -> Dict[str, Any]:
        """Generate experimentation guidelines."""
        strategy = self.answers.get("content_strategy", {})
        
        return {
            "experimentation_tolerance": strategy.get("q43_experimentation_tolerance", 7),
            "trend_adoption_speed": strategy.get("q44_trend_adoption_speed", 6),
            "testing_framework": {
                "approach": "Rapid prototyping and iteration",
                "cycle": "Post → Measure → Learn → Iterate (24-48h cycles)",
                "success_metrics": ["engagement_rate", "retention_rate", "virality_score"]
            },
            "trend_testing": {
                "methodology": "Test trends immediately when detected",
                "adaptation_required": False,
                "brand_filter": False,
                "speed_priority": "Fast execution over perfect alignment"
            },
            "format_experiments": [
                "new_editing_styles",
                "new_video_formats",
                "new_music_combinations",
                "ai_techniques",
                "viral_formulas"
            ],
            "learning_objectives": [
                "Identify winning patterns",
                "Discover viral formulas",
                "Test audience preferences",
                "Collect ML training data",
                "Find inspiration for official content"
            ]
        }
    
    def _generate_ml_learning_rules(self) -> Dict[str, Any]:
        """Generate ML learning and data collection rules."""
        metrics = self.answers.get("metrics_priorities", {})
        
        return {
            "data_collection": {
                "enabled": True,
                "purpose": "Train ML models to predict content performance",
                "metrics_tracked": metrics.get("q48_primary_kpis", []),
                "storage": "All satellite content metrics stored for ML training"
            },
            "learning_pipeline": {
                "step_1": "Post satellite content with experiments",
                "step_2": "Measure engagement, retention, virality",
                "step_3": "Identify patterns in successful content",
                "step_4": "Validate patterns across multiple posts",
                "step_5": "Apply learnings to official content strategy"
            },
            "pattern_discovery": {
                "track": [
                    "editing_styles_performance",
                    "music_choice_impact",
                    "thumbnail_effectiveness",
                    "caption_engagement",
                    "posting_time_correlation"
                ],
                "threshold_for_pattern": "3+ successful posts with same attribute",
                "confidence_level": 0.7
            },
            "success_transfer": {
                "from_satellite_to_official": "Proven patterns can inform official strategy",
                "validation_required": True,
                "adaptation_needed": "Translate satellite patterns to brand-aligned format"
            }
        }
    
    def save(self, output_path: str) -> None:
        """
        Generate and save satellite_rules.json.
        
        Args:
            output_path: Path where satellite_rules.json will be saved
        """
        satellite_rules = self.generate()
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(satellite_rules, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Satellite rules generated: {output_file}")
        print(f"   - Artist: {satellite_rules['artist_name']}")
        print(f"   - Channel type: {satellite_rules['channel_type']}")
        print(f"   - Quality threshold: {satellite_rules['quality_standards']['minimum_quality_score']}/10")
        print(f"   - Posts per week: {satellite_rules['posting_strategy']['frequency']['posts_per_week']}")
        print(f"   - Prohibitions: {len(satellite_rules['prohibitions']['absolute_prohibitions'])}")


def generate_satellite_rules(answers_path: str, output_path: str) -> Dict[str, Any]:
    """
    Convenience function to generate satellite rules.
    
    Args:
        answers_path: Path to onboarding_answers.json
        output_path: Path to save satellite_rules.json
        
    Returns:
        Generated satellite rules dictionary
    """
    generator = SatelliteGenerator(answers_path)
    generator.save(output_path)
    return generator.generate()


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python satellite_generator.py <answers_path> <output_path>")
        print("Example: python satellite_generator.py onboarding_answers.json ../brand/satellite_rules.json")
        sys.exit(1)
    
    answers_path = sys.argv[1]
    output_path = sys.argv[2]
    
    generate_satellite_rules(answers_path, output_path)
