"""
Brand Generator: Transforms onboarding answers into brand_static_rules.json

This module automates the generation of comprehensive brand rules from artist
questionnaire responses, ensuring consistent brand identity across all content.
"""

import json
from typing import Dict, List, Any
from pathlib import Path


class BrandGenerator:
    """
    Generates brand_static_rules.json from onboarding questionnaire answers.
    
    Transforms structured artist responses into comprehensive brand guidelines
    that govern Official channel content creation and validation.
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
        Generate complete brand_static_rules.json from answers.
        
        Returns:
            Dict containing complete brand rules structure
        """
        brand_rules = {
            "version": "1.0.0",
            "artist_id": self.answers.get("artist_id"),
            "artist_name": self.answers.get("artist_name"),
            "generated_at": self.answers.get("completed_at"),
            
            "artist_identity": self._generate_artist_identity(),
            "visual_rules": self._generate_visual_rules(),
            "content_boundaries": self._generate_content_boundaries(),
            "platform_guidelines": self._generate_platform_guidelines(),
            "music_context": self._generate_music_context(),
            "brand_signature": self._generate_brand_signature(),
            "quality_standards": self._generate_quality_standards(),
            "metrics_priorities": self._generate_metrics_priorities()
        }
        
        return brand_rules
    
    def _generate_artist_identity(self) -> Dict[str, Any]:
        """Generate artist identity section."""
        brand_tone = self.answers.get("brand_tone", {})
        
        return {
            "core_personality": brand_tone.get("q13_brand_personality", []),
            "emotional_palette": {
                "transmit": brand_tone.get("q11_emotional_tone", []),
                "avoid": brand_tone.get("q12_forbidden_emotions", [])
            },
            "uniqueness_statement": brand_tone.get("q14_artist_uniqueness", ""),
            "inspirations": brand_tone.get("q15_artist_inspirations", []),
            "philosophy": self.answers.get("additional_notes", {}).get("brand_philosophy", "")
        }
    
    def _generate_visual_rules(self) -> Dict[str, Any]:
        """Generate comprehensive visual rules section."""
        visual = self.answers.get("visual_identity", {})
        fashion = self.answers.get("fashion_identity", {})
        
        return {
            "color_palette": {
                "allowed": visual.get("q1_color_palette", []),
                "forbidden": visual.get("q2_forbidden_colors", []),
                "signature_color": visual.get("q1_color_palette", [""])[0],  # First color as signature
                "color_match_threshold": 0.6
            },
            "visual_style": {
                "keywords": visual.get("q3_visual_style", []),
                "references": visual.get("q10_visual_references", [])
            },
            "camera_work": {
                "preferred_styles": visual.get("q4_camera_style", []),
                "forbidden_styles": []
            },
            "lighting": {
                "preferred": visual.get("q5_lighting_preference", []),
                "signature": "high_contrast_neon"
            },
            "scenes": {
                "allowed": visual.get("q6_scene_preference", []),
                "forbidden": visual.get("q7_forbidden_scenes", [])
            },
            "editing": {
                "preferred_styles": visual.get("q8_editing_style", []),
                "forbidden_styles": visual.get("q9_forbidden_edits", [])
            },
            "wardrobe": {
                "allowed": fashion.get("q21_wardrobe_style", []),
                "forbidden": fashion.get("q22_forbidden_fashion", []),
                "key_accessories": fashion.get("q23_accessories", []),
                "aesthetic_keywords": fashion.get("q24_fashion_aesthetic", [])
            }
        }
    
    def _generate_content_boundaries(self) -> Dict[str, Any]:
        """Generate content boundaries and restrictions."""
        official_vs_sat = self.answers.get("official_vs_satellite", {})
        narrative = self.answers.get("narrative_storytelling", {})
        music = self.answers.get("music_context", {})
        
        return {
            "official_content": {
                "allowed_types": official_vs_sat.get("q29_official_content_types", []),
                "forbidden_types": official_vs_sat.get("q30_official_forbidden", []),
                "quality_threshold": official_vs_sat.get("q33_quality_threshold_official", 8)
            },
            "narrative_rules": {
                "allowed_stories": narrative.get("q25_story_types", []),
                "repeatable_themes": narrative.get("q26_repeatable_themes", []),
                "forbidden_narratives": narrative.get("q27_avoided_narratives", []),
                "storytelling_style": narrative.get("q28_storytelling_style", [])
            },
            "lyrical_themes": {
                "allowed": music.get("q19_lyrical_themes", []),
                "forbidden": music.get("q20_forbidden_themes", [])
            },
            "brand_compliance_threshold": 0.8,
            "aesthetic_coherence_threshold": 0.7
        }
    
    def _generate_platform_guidelines(self) -> Dict[str, Any]:
        """Generate platform-specific guidelines."""
        platform = self.answers.get("platform_guidelines", {})
        strategy = self.answers.get("content_strategy", {})
        audience = self.answers.get("audience_targeting", {})
        
        return {
            "posting_schedule": {
                "frequency_per_week": strategy.get("q39_posting_frequency_official", 5),
                "optimal_times": strategy.get("q41_optimal_posting_times", []),
                "content_mix": strategy.get("q42_content_mix", {})
            },
            "instagram": {
                "strategy": platform.get("q45_instagram_strategy", []),
                "format_priority": ["reels", "posts", "stories"]
            },
            "tiktok": {
                "strategy": platform.get("q46_tiktok_strategy", []),
                "format_priority": ["videos", "series"]
            },
            "youtube": {
                "strategy": platform.get("q47_youtube_strategy", []),
                "format_priority": ["videos", "shorts"]
            },
            "target_audience": {
                "age_range": audience.get("q35_target_audience_age", [16, 28]),
                "characteristics": audience.get("q36_audience_characteristics", []),
                "engagement_drivers": audience.get("q37_engagement_drivers", []),
                "platforms": audience.get("q38_content_consumption", [])
            }
        }
    
    def _generate_music_context(self) -> Dict[str, Any]:
        """Generate music context section."""
        music = self.answers.get("music_context", {})
        
        return {
            "genres": music.get("q16_genres", []),
            "moods": music.get("q17_moods", []),
            "vocal_style": music.get("q18_vocal_style", []),
            "primary_genre": music.get("q16_genres", [""])[0] if music.get("q16_genres") else "",
            "signature_mood": "dark_atmospheric"
        }
    
    def _generate_brand_signature(self) -> Dict[str, Any]:
        """Generate brand signature elements."""
        visual = self.answers.get("visual_identity", {})
        narrative = self.answers.get("narrative_storytelling", {})
        
        signature_color = visual.get("q1_color_palette", [""])[0]
        
        return {
            "visual_dna": {
                "signature_color": signature_color,
                "signature_aesthetic": "purple_neon_cyberpunk",
                "visual_keywords": visual.get("q3_visual_style", [])[:3]
            },
            "narrative_dna": {
                "core_themes": narrative.get("q26_repeatable_themes", [])[:5],
                "storytelling_style": narrative.get("q28_storytelling_style", [])
            },
            "recognizability_elements": [
                f"Purple neon glow ({signature_color})",
                "High contrast lighting",
                "Urban night scenes",
                "Cinematic camera work",
                "Dark atmospheric mood"
            ]
        }
    
    def _generate_quality_standards(self) -> Dict[str, Any]:
        """Generate quality standards and thresholds."""
        official_vs_sat = self.answers.get("official_vs_satellite", {})
        strategy = self.answers.get("content_strategy", {})
        
        return {
            "official_channel": {
                "minimum_quality_score": official_vs_sat.get("q33_quality_threshold_official", 8),
                "brand_compliance_required": True,
                "aesthetic_coherence_required": True,
                "narrative_depth_required": True
            },
            "experimentation": {
                "tolerance_level": strategy.get("q43_experimentation_tolerance", 7),
                "trend_adoption_speed": strategy.get("q44_trend_adoption_speed", 6),
                "allowed_deviations": [
                    "new_editing_techniques",
                    "trend_adaptation_with_brand_filter",
                    "format_experimentation"
                ]
            },
            "validation_gates": {
                "color_palette_match": 0.6,
                "brand_compliance": 0.8,
                "aesthetic_coherence": 0.7,
                "narrative_alignment": 0.7
            }
        }
    
    def _generate_metrics_priorities(self) -> Dict[str, Any]:
        """Generate metrics and success criteria."""
        metrics = self.answers.get("metrics_priorities", {})
        
        return {
            "primary_kpis": metrics.get("q48_primary_kpis", []),
            "success_definition": metrics.get("q49_success_definition", ""),
            "failure_tolerance": metrics.get("q50_failure_tolerance", 3),
            "optimization_focus": [
                "retention_rate",
                "engagement_quality",
                "brand_coherence"
            ],
            "secondary_metrics": [
                "follower_growth",
                "share_rate",
                "comment_sentiment"
            ]
        }
    
    def save(self, output_path: str) -> None:
        """
        Generate and save brand_static_rules.json.
        
        Args:
            output_path: Path where brand_static_rules.json will be saved
        """
        brand_rules = self.generate()
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(brand_rules, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Brand rules generated: {output_file}")
        print(f"   - Artist: {brand_rules['artist_name']}")
        print(f"   - Sections: {len(brand_rules) - 3}")  # Exclude version, artist_id, generated_at
        print(f"   - Signature color: {brand_rules['brand_signature']['visual_dna']['signature_color']}")
        print(f"   - Quality threshold: {brand_rules['quality_standards']['official_channel']['minimum_quality_score']}/10")


def generate_brand_rules(answers_path: str, output_path: str) -> Dict[str, Any]:
    """
    Convenience function to generate brand rules.
    
    Args:
        answers_path: Path to onboarding_answers.json
        output_path: Path to save brand_static_rules.json
        
    Returns:
        Generated brand rules dictionary
    """
    generator = BrandGenerator(answers_path)
    generator.save(output_path)
    return generator.generate()


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python brand_generator.py <answers_path> <output_path>")
        print("Example: python brand_generator.py onboarding_answers.json ../brand/brand_static_rules.json")
        sys.exit(1)
    
    answers_path = sys.argv[1]
    output_path = sys.argv[2]
    
    generate_brand_rules(answers_path, output_path)
