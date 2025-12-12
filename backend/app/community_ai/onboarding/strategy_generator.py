"""
Strategy Generator: Transforms onboarding answers into content_strategy.json

This module automates the generation of content strategy including posting
schedules, content mix, timing optimization, and KPI priorities.
"""

import json
from typing import Dict, List, Any
from pathlib import Path


class StrategyGenerator:
    """
    Generates content_strategy.json from onboarding questionnaire answers.
    
    Transforms artist preferences into actionable content strategy with
    posting schedules, content mix, and optimization guidelines.
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
        Generate complete content_strategy.json from answers.
        
        Returns:
            Dict containing complete content strategy
        """
        content_strategy = {
            "version": "1.0.0",
            "artist_id": self.answers.get("artist_id"),
            "artist_name": self.answers.get("artist_name"),
            "generated_at": self.answers.get("completed_at"),
            
            "official_channel": self._generate_official_strategy(),
            "satellite_channels": self._generate_satellite_strategy(),
            "content_mix": self._generate_content_mix(),
            "timing_optimization": self._generate_timing_optimization(),
            "platform_strategies": self._generate_platform_strategies(),
            "kpi_framework": self._generate_kpi_framework(),
            "experimentation_guidelines": self._generate_experimentation_guidelines(),
            "adaptation_rules": self._generate_adaptation_rules()
        }
        
        return content_strategy
    
    def _generate_official_strategy(self) -> Dict[str, Any]:
        """Generate official channel strategy."""
        strategy = self.answers.get("content_strategy", {})
        official_vs_sat = self.answers.get("official_vs_satellite", {})
        
        posts_per_week = strategy.get("q39_posting_frequency_official", 5)
        
        return {
            "philosophy": "Quality over quantity - every post must meet brand standards",
            "posting_schedule": {
                "posts_per_week": posts_per_week,
                "posts_per_day": round(posts_per_week / 7, 1),
                "rhythm": "consistent_quality",
                "recommended_days": ["monday", "wednesday", "friday", "saturday", "sunday"]
            },
            "content_types": official_vs_sat.get("q29_official_content_types", []),
            "quality_requirements": {
                "minimum_quality": official_vs_sat.get("q33_quality_threshold_official", 8),
                "brand_compliance": 0.8,
                "aesthetic_coherence": 0.7,
                "narrative_depth": True
            },
            "content_calendar": {
                "weekly_structure": {
                    "monday": "teaser_or_preview",
                    "wednesday": "behind_scenes_or_narrative",
                    "friday": "high_production_reel",
                    "saturday": "videoclip_or_major_release",
                    "sunday": "aesthetic_post_or_story"
                },
                "monthly_structure": {
                    "week_1": "buildup_content",
                    "week_2": "major_release",
                    "week_3": "engagement_content",
                    "week_4": "narrative_continuation"
                }
            }
        }
    
    def _generate_satellite_strategy(self) -> Dict[str, Any]:
        """Generate satellite channels strategy."""
        strategy = self.answers.get("content_strategy", {})
        official_vs_sat = self.answers.get("official_vs_satellite", {})
        
        posts_per_week = strategy.get("q40_posting_frequency_satellite", 15)
        
        return {
            "philosophy": "Rapid iteration and learning - volume enables discovery",
            "posting_schedule": {
                "posts_per_week": posts_per_week,
                "posts_per_day": round(posts_per_week / 7),
                "rhythm": "rapid_iteration",
                "distribution": "3-5 posts daily across satellite channels"
            },
            "content_types": official_vs_sat.get("q31_satellite_content_types", []),
            "quality_requirements": {
                "minimum_quality": official_vs_sat.get("q34_quality_threshold_satellite", 5),
                "brand_compliance": None,
                "aesthetic_coherence": None,
                "watchability": "baseline_only"
            },
            "iteration_cycles": {
                "test_cycle": "24-48 hours",
                "measurement_window": "48-72 hours",
                "decision_threshold": "3 posts to identify pattern"
            },
            "channel_allocation": {
                "channel_1": {
                    "focus": "viral_edits",
                    "posts_per_week": 6
                },
                "channel_2": {
                    "focus": "ai_experiments",
                    "posts_per_week": 5
                },
                "channel_3": {
                    "focus": "trend_testing",
                    "posts_per_week": 4
                }
            }
        }
    
    def _generate_content_mix(self) -> Dict[str, Any]:
        """Generate content mix guidelines."""
        strategy = self.answers.get("content_strategy", {})
        
        content_mix = strategy.get("q42_content_mix", {})
        
        return {
            "official_mix": content_mix,
            "official_breakdown": {
                "high_production": {
                    "percentage": content_mix.get("videoclips_oficiales", 30) + content_mix.get("teasers_previews", 25),
                    "types": ["videoclips", "teasers"],
                    "frequency": "2-3 per week"
                },
                "mid_production": {
                    "percentage": content_mix.get("reels_narrativos", 20) + content_mix.get("behind_scenes", 15),
                    "types": ["narrative_reels", "behind_scenes"],
                    "frequency": "2 per week"
                },
                "low_production": {
                    "percentage": content_mix.get("stories_aesthetic", 10),
                    "types": ["aesthetic_posts", "stories"],
                    "frequency": "daily"
                }
            },
            "satellite_mix": {
                "viral_edits": 40,
                "ai_content": 25,
                "trend_tests": 20,
                "experimental": 15
            },
            "balance_rules": {
                "high_low_ratio": "60% high production, 40% supporting content",
                "narrative_promotional_ratio": "70% narrative/artistic, 30% promotional",
                "evergreen_trending_ratio": "80% evergreen brand content, 20% trend adaptation"
            }
        }
    
    def _generate_timing_optimization(self) -> Dict[str, Any]:
        """Generate timing optimization strategy."""
        strategy = self.answers.get("content_strategy", {})
        audience = self.answers.get("audience_targeting", {})
        
        optimal_times = strategy.get("q41_optimal_posting_times", ["20:00", "21:30", "23:00"])
        
        return {
            "optimal_posting_times": optimal_times,
            "timezone": "artist_local_time",
            "audience_activity_windows": {
                "primary_window": {
                    "start": "20:00",
                    "end": "23:59",
                    "description": "Night owls - main target audience active"
                },
                "secondary_window": {
                    "start": "17:00",
                    "end": "20:00",
                    "description": "After school/work - secondary audience window"
                }
            },
            "platform_specific_timing": {
                "instagram": {
                    "best_times": optimal_times,
                    "best_days": ["friday", "saturday", "sunday"],
                    "reasoning": "Weekend engagement peaks for lifestyle content"
                },
                "tiktok": {
                    "best_times": ["14:00", "18:00", "21:00"],
                    "best_days": ["all"],
                    "reasoning": "Multiple daily windows due to algorithm behavior"
                },
                "youtube": {
                    "best_times": ["20:00"],
                    "best_days": ["friday", "saturday"],
                    "reasoning": "Weekend viewing for longer content"
                }
            },
            "seasonal_adjustments": {
                "summer": "Post slightly later (21:00-00:00)",
                "winter": "Standard times work best",
                "holidays": "Increase frequency by 20%"
            }
        }
    
    def _generate_platform_strategies(self) -> Dict[str, Any]:
        """Generate platform-specific strategies."""
        platform = self.answers.get("platform_guidelines", {})
        audience = self.answers.get("audience_targeting", {})
        
        return {
            "instagram": {
                "strategy": platform.get("q45_instagram_strategy", []),
                "content_priority": ["reels", "posts", "stories"],
                "posting_frequency": {
                    "reels": "2-3 per week",
                    "posts": "1-2 per week",
                    "stories": "daily"
                },
                "format_guidelines": {
                    "reels": "15-30s, cinematic, brand-aligned",
                    "posts": "Aesthetic photos, carousels with narrative",
                    "stories": "Behind scenes, teasers, engagement"
                },
                "hashtag_strategy": "5-10 targeted hashtags, avoid generic ones"
            },
            "tiktok": {
                "strategy": platform.get("q46_tiktok_strategy", []),
                "content_priority": ["videos", "series"],
                "posting_frequency": {
                    "official": "1-2 per day",
                    "satellite": "3-5 per day"
                },
                "format_guidelines": {
                    "videos": "15-60s, hook in first 3s, trend-aware",
                    "series": "Multi-part narratives, serialized content"
                },
                "algorithm_optimization": "Post consistently, engage with comments, use trending sounds"
            },
            "youtube": {
                "strategy": platform.get("q47_youtube_strategy", []),
                "content_priority": ["videos", "shorts"],
                "posting_frequency": {
                    "videos": "1-2 per month (high production)",
                    "shorts": "2-3 per week"
                },
                "format_guidelines": {
                    "videos": "Official videoclips, making-of documentaries",
                    "shorts": "Teasers, viral edits, behind scenes"
                },
                "seo_strategy": "Descriptive titles, full descriptions, targeted keywords"
            },
            "cross_platform": {
                "repurposing": "Adapt content to platform specs, don't just repost",
                "timing": "Stagger posts across platforms (30min-2h gaps)",
                "unique_value": "Each platform gets unique angle or exclusive content"
            }
        }
    
    def _generate_kpi_framework(self) -> Dict[str, Any]:
        """Generate KPI framework and success metrics."""
        metrics = self.answers.get("metrics_priorities", {})
        
        primary_kpis = metrics.get("q48_primary_kpis", [])
        
        return {
            "primary_kpis": primary_kpis,
            "kpi_definitions": {
                "retention_rate": {
                    "description": "Percentage of video watched",
                    "target": "> 70%",
                    "priority": 1,
                    "calculation": "average_watch_time / video_duration"
                },
                "engagement_rate": {
                    "description": "Likes, comments, shares per view",
                    "target": "> 5%",
                    "priority": 2,
                    "calculation": "(likes + comments + shares) / views * 100"
                },
                "views": {
                    "description": "Total video views",
                    "target": "Growth trajectory more important than absolute number",
                    "priority": 3,
                    "calculation": "sum(views)"
                },
                "shares": {
                    "description": "Content virality indicator",
                    "target": "> 2% of views",
                    "priority": 4,
                    "calculation": "shares / views * 100"
                }
            },
            "success_definition": metrics.get("q49_success_definition", ""),
            "success_criteria": {
                "excellent": "Retention > 80%, Engagement > 8%, Organic shares",
                "good": "Retention > 70%, Engagement > 5%, Growth trajectory",
                "acceptable": "Retention > 60%, Engagement > 3%, Learning opportunity",
                "failure": "Retention < 50%, Engagement < 2%, No learnings"
            },
            "failure_tolerance": metrics.get("q50_failure_tolerance", 3),
            "optimization_focus": [
                "retention_rate",
                "engagement_quality",
                "brand_coherence"
            ]
        }
    
    def _generate_experimentation_guidelines(self) -> Dict[str, Any]:
        """Generate experimentation guidelines."""
        strategy = self.answers.get("content_strategy", {})
        
        return {
            "experimentation_tolerance": strategy.get("q43_experimentation_tolerance", 7),
            "trend_adoption_speed": strategy.get("q44_trend_adoption_speed", 6),
            "official_channel_experiments": {
                "allowed": [
                    "new_editing_techniques",
                    "new_music_combinations",
                    "narrative_innovations",
                    "format_variations_within_brand"
                ],
                "restrictions": [
                    "Must maintain brand compliance",
                    "Must meet quality threshold",
                    "Must align with aesthetic"
                ],
                "approval_required": True
            },
            "satellite_channel_experiments": {
                "allowed": [
                    "everything_not_prohibited",
                    "unlimited_format_testing",
                    "ai_experiments",
                    "trend_testing",
                    "viral_formulas"
                ],
                "restrictions": [
                    "NO show real artist",
                    "NO use official aesthetic",
                    "Legal compliance only"
                ],
                "approval_required": False
            },
            "testing_framework": {
                "hypothesis": "Define what you're testing",
                "control": "Compare against baseline",
                "measurement": "Track specific metrics",
                "duration": "Minimum 3 posts to identify pattern",
                "decision": "Keep, iterate, or discard"
            }
        }
    
    def _generate_adaptation_rules(self) -> Dict[str, Any]:
        """Generate strategy adaptation rules."""
        return {
            "performance_triggers": {
                "underperformance": {
                    "threshold": "3 consecutive posts below expectations",
                    "action": "Review and adjust strategy",
                    "adjustments": [
                        "Change posting times",
                        "Adjust content mix",
                        "Review quality thresholds",
                        "Test different formats"
                    ]
                },
                "overperformance": {
                    "threshold": "3 consecutive posts exceed expectations",
                    "action": "Identify winning pattern and replicate",
                    "adjustments": [
                        "Increase similar content percentage",
                        "Document successful formula",
                        "Test pattern variations"
                    ]
                }
            },
            "trend_adaptation": {
                "official_channel": {
                    "approach": "Filter trends through brand lens",
                    "speed": "Measured adoption (2-3 days evaluation)",
                    "modification": "Adapt trend to brand aesthetic"
                },
                "satellite_channels": {
                    "approach": "Immediate trend testing",
                    "speed": "Rapid adoption (same day)",
                    "modification": "Minimal - test raw trend"
                }
            },
            "seasonal_adjustments": {
                "review_frequency": "Monthly",
                "adjustment_areas": [
                    "posting_times",
                    "content_mix",
                    "platform_priorities",
                    "audience_targeting"
                ],
                "data_driven": "Base decisions on performance data, not assumptions"
            },
            "learning_integration": {
                "satellite_to_official": "Successful satellite patterns inform official strategy",
                "validation_required": "Test pattern compatibility with brand",
                "adaptation_process": "Transform satellite learnings to brand-aligned format"
            }
        }
    
    def save(self, output_path: str) -> None:
        """
        Generate and save content_strategy.json.
        
        Args:
            output_path: Path where content_strategy.json will be saved
        """
        content_strategy = self.generate()
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(content_strategy, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Content strategy generated: {output_file}")
        print(f"   - Artist: {content_strategy['artist_name']}")
        print(f"   - Official posts/week: {content_strategy['official_channel']['posting_schedule']['posts_per_week']}")
        print(f"   - Satellite posts/week: {content_strategy['satellite_channels']['posting_schedule']['posts_per_week']}")
        print(f"   - Primary KPIs: {len(content_strategy['kpi_framework']['primary_kpis'])}")


def generate_content_strategy(answers_path: str, output_path: str) -> Dict[str, Any]:
    """
    Convenience function to generate content strategy.
    
    Args:
        answers_path: Path to onboarding_answers.json
        output_path: Path to save content_strategy.json
        
    Returns:
        Generated content strategy dictionary
    """
    generator = StrategyGenerator(answers_path)
    generator.save(output_path)
    return generator.generate()


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python strategy_generator.py <answers_path> <output_path>")
        print("Example: python strategy_generator.py onboarding_answers.json ../brand/content_strategy.json")
        sys.exit(1)
    
    answers_path = sys.argv[1]
    output_path = sys.argv[2]
    
    generate_content_strategy(answers_path, output_path)
