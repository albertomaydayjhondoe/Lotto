"""
Integration Test: Artist Onboarding System

This test validates the complete onboarding flow:
1. Load questionnaire and answers
2. Run all generators
3. Validate generated configurations
4. Test integration with CM modules (mock)
"""

import json
import pytest
from pathlib import Path

# Adjust path for imports
import sys
sys.path.append(str(Path(__file__).parent.parent))

from onboarding.brand_generator import BrandGenerator
from onboarding.satellite_generator import SatelliteGenerator
from onboarding.strategy_generator import StrategyGenerator


class TestOnboardingIntegration:
    """Integration tests for complete onboarding system."""
    
    @pytest.fixture
    def onboarding_dir(self):
        """Get onboarding directory path."""
        return Path(__file__).parent.parent / "onboarding"
    
    @pytest.fixture
    def answers_path(self, onboarding_dir):
        """Get answers file path."""
        return onboarding_dir / "onboarding_answers.json"
    
    @pytest.fixture
    def answers_data(self, answers_path):
        """Load answers data."""
        with open(answers_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def test_answers_file_exists(self, answers_path):
        """Test that onboarding_answers.json exists."""
        assert answers_path.exists(), "onboarding_answers.json not found"
    
    def test_answers_complete(self, answers_data):
        """Test that all required sections are present in answers."""
        required_sections = [
            "visual_identity",
            "brand_tone",
            "music_context",
            "fashion_identity",
            "narrative_storytelling",
            "official_vs_satellite",
            "audience_targeting",
            "content_strategy",
            "platform_guidelines",
            "metrics_priorities"
        ]
        
        for section in required_sections:
            assert section in answers_data, f"Missing section: {section}"
            assert len(answers_data[section]) > 0, f"Empty section: {section}"
    
    def test_critical_questions_answered(self, answers_data):
        """Test that critical questions have answers."""
        # Section 6: Official vs Satellite (CRITICAL)
        official_vs_sat = answers_data["official_vs_satellite"]
        
        assert "q29_official_content_types" in official_vs_sat
        assert len(official_vs_sat["q29_official_content_types"]) > 0
        
        assert "q31_satellite_content_types" in official_vs_sat
        assert len(official_vs_sat["q31_satellite_content_types"]) > 0
        
        assert "q32_satellite_rules" in official_vs_sat
        assert len(official_vs_sat["q32_satellite_rules"]) > 0
        
        assert "q33_quality_threshold_official" in official_vs_sat
        assert official_vs_sat["q33_quality_threshold_official"] >= 8
        
        assert "q34_quality_threshold_satellite" in official_vs_sat
        assert official_vs_sat["q34_quality_threshold_satellite"] >= 5
    
    def test_brand_generator_execution(self, answers_path):
        """Test brand generator execution."""
        generator = BrandGenerator(str(answers_path))
        brand_rules = generator.generate()
        
        # Validate structure
        assert "version" in brand_rules
        assert "artist_id" in brand_rules
        assert "artist_name" in brand_rules
        
        # Validate sections
        required_sections = [
            "artist_identity",
            "visual_rules",
            "content_boundaries",
            "platform_guidelines",
            "music_context",
            "brand_signature",
            "quality_standards",
            "metrics_priorities"
        ]
        
        for section in required_sections:
            assert section in brand_rules, f"Missing section: {section}"
    
    def test_brand_rules_visual_section(self, answers_path):
        """Test brand rules visual section generation."""
        generator = BrandGenerator(str(answers_path))
        brand_rules = generator.generate()
        
        visual_rules = brand_rules["visual_rules"]
        
        # Color palette
        assert "color_palette" in visual_rules
        assert "allowed" in visual_rules["color_palette"]
        assert len(visual_rules["color_palette"]["allowed"]) > 0
        assert "signature_color" in visual_rules["color_palette"]
        
        # Scenes
        assert "scenes" in visual_rules
        assert "allowed" in visual_rules["scenes"]
        assert "forbidden" in visual_rules["scenes"]
        
        # Editing
        assert "editing" in visual_rules
        assert "preferred_styles" in visual_rules["editing"]
        assert "forbidden_styles" in visual_rules["editing"]
    
    def test_brand_rules_quality_standards(self, answers_path):
        """Test brand rules quality standards."""
        generator = BrandGenerator(str(answers_path))
        brand_rules = generator.generate()
        
        quality_standards = brand_rules["quality_standards"]
        
        # Official channel standards
        assert "official_channel" in quality_standards
        assert "minimum_quality_score" in quality_standards["official_channel"]
        assert quality_standards["official_channel"]["minimum_quality_score"] >= 8
        
        # Validation gates
        assert "validation_gates" in quality_standards
        gates = quality_standards["validation_gates"]
        assert "brand_compliance" in gates
        assert gates["brand_compliance"] == 0.8
        assert "aesthetic_coherence" in gates
        assert gates["aesthetic_coherence"] == 0.7
    
    def test_satellite_generator_execution(self, answers_path):
        """Test satellite generator execution."""
        generator = SatelliteGenerator(str(answers_path))
        satellite_rules = generator.generate()
        
        # Validate structure
        assert "version" in satellite_rules
        assert "channel_type" in satellite_rules
        assert satellite_rules["channel_type"] == "satellite"
        
        # Validate sections
        required_sections = [
            "philosophy",
            "content_rules",
            "prohibitions",
            "freedoms",
            "quality_standards",
            "posting_strategy",
            "experimentation_rules",
            "ml_learning_rules"
        ]
        
        for section in required_sections:
            assert section in satellite_rules, f"Missing section: {section}"
    
    def test_satellite_prohibitions(self, answers_path):
        """Test satellite prohibitions are enforced."""
        generator = SatelliteGenerator(str(answers_path))
        satellite_rules = generator.generate()
        
        prohibitions = satellite_rules["prohibitions"]
        
        # Check absolute prohibitions
        assert "absolute_prohibitions" in prohibitions
        absolute = prohibitions["absolute_prohibitions"]
        
        # Must include NO_ rules
        no_rules = [p for p in absolute if p.startswith("NO_")]
        assert len(no_rules) >= 3, "Must have at least 3 NO_ prohibitions"
        
        # Check detailed rules
        assert "detailed_rules" in prohibitions
        detailed = prohibitions["detailed_rules"]
        
        # Critical prohibitions
        if "NO_mostrar_artista_real" in detailed:
            assert detailed["NO_mostrar_artista_real"]["enforcement"] == "automatic_rejection"
    
    def test_satellite_freedoms(self, answers_path):
        """Test satellite freedoms are enabled."""
        generator = SatelliteGenerator(str(answers_path))
        satellite_rules = generator.generate()
        
        freedoms = satellite_rules["freedoms"]
        
        # Check creative freedoms
        assert "creative_freedoms" in freedoms
        creative = freedoms["creative_freedoms"]
        
        # Must include SI_ rules
        si_rules = [f for f in creative if f.startswith("SI_")]
        assert len(si_rules) >= 3, "Must have at least 3 SI_ freedoms"
        
        # Check no validation required
        assert "no_validation_required" in freedoms
        no_validation = freedoms["no_validation_required"]
        assert "brand_compliance_check" in no_validation
        assert "color_palette_validation" in no_validation
    
    def test_satellite_quality_standards(self, answers_path):
        """Test satellite quality standards."""
        generator = SatelliteGenerator(str(answers_path))
        satellite_rules = generator.generate()
        
        quality_standards = satellite_rules["quality_standards"]
        
        # Lower quality threshold
        assert "minimum_quality_score" in quality_standards
        assert quality_standards["minimum_quality_score"] <= 6
        
        # Philosophy
        assert "quality_philosophy" in quality_standards
        assert "good enough to test" in quality_standards["quality_philosophy"].lower()
    
    def test_strategy_generator_execution(self, answers_path):
        """Test strategy generator execution."""
        generator = StrategyGenerator(str(answers_path))
        content_strategy = generator.generate()
        
        # Validate structure
        assert "version" in content_strategy
        assert "artist_id" in content_strategy
        
        # Validate sections
        required_sections = [
            "official_channel",
            "satellite_channels",
            "content_mix",
            "timing_optimization",
            "platform_strategies",
            "kpi_framework",
            "experimentation_guidelines",
            "adaptation_rules"
        ]
        
        for section in required_sections:
            assert section in content_strategy, f"Missing section: {section}"
    
    def test_strategy_posting_schedules(self, answers_path):
        """Test strategy posting schedules."""
        generator = StrategyGenerator(str(answers_path))
        content_strategy = generator.generate()
        
        # Official channel
        official = content_strategy["official_channel"]
        assert "posting_schedule" in official
        official_schedule = official["posting_schedule"]
        assert "posts_per_week" in official_schedule
        assert official_schedule["posts_per_week"] <= 7  # Max 1 per day
        
        # Satellite channels
        satellite = content_strategy["satellite_channels"]
        assert "posting_schedule" in satellite
        satellite_schedule = satellite["posting_schedule"]
        assert "posts_per_week" in satellite_schedule
        assert satellite_schedule["posts_per_week"] >= official_schedule["posts_per_week"]
    
    def test_strategy_kpi_framework(self, answers_path):
        """Test strategy KPI framework."""
        generator = StrategyGenerator(str(answers_path))
        content_strategy = generator.generate()
        
        kpi_framework = content_strategy["kpi_framework"]
        
        # Primary KPIs
        assert "primary_kpis" in kpi_framework
        assert len(kpi_framework["primary_kpis"]) > 0
        
        # KPI definitions
        assert "kpi_definitions" in kpi_framework
        definitions = kpi_framework["kpi_definitions"]
        
        # Check retention_rate definition
        if "retention_rate" in definitions:
            assert "target" in definitions["retention_rate"]
            assert "calculation" in definitions["retention_rate"]
    
    def test_official_vs_satellite_distinction(self, answers_path):
        """Test Official vs Satellite distinction is clear."""
        brand_gen = BrandGenerator(str(answers_path))
        satellite_gen = SatelliteGenerator(str(answers_path))
        
        brand_rules = brand_gen.generate()
        satellite_rules = satellite_gen.generate()
        
        # Official quality > Satellite quality
        official_quality = brand_rules["quality_standards"]["official_channel"]["minimum_quality_score"]
        satellite_quality = satellite_rules["quality_standards"]["minimum_quality_score"]
        assert official_quality > satellite_quality
        
        # Official has validation gates
        assert "validation_gates" in brand_rules["quality_standards"]
        
        # Satellite has NO validation gates (only prohibitions)
        assert "prohibitions" in satellite_rules
        assert "freedoms" in satellite_rules
    
    def test_integration_with_cm_mock(self, answers_path):
        """Test integration with CM modules (mock)."""
        brand_gen = BrandGenerator(str(answers_path))
        brand_rules = brand_gen.generate()
        
        # Mock CM Planner usage
        signature_color = brand_rules["brand_signature"]["visual_dna"]["signature_color"]
        assert signature_color.startswith("#")
        
        # Mock Vision Engine usage
        allowed_colors = brand_rules["visual_rules"]["color_palette"]["allowed"]
        assert len(allowed_colors) > 0
        
        # Mock Validator usage
        brand_compliance_threshold = brand_rules["content_boundaries"]["brand_compliance_threshold"]
        assert 0 <= brand_compliance_threshold <= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
