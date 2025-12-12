"""
Tests for Brand Rules Builder - Sprint 4

Tests the fusion engine that combines all data sources into BRAND_STATIC_RULES.json.
"""

import pytest
import json
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from brand_engine.brand_rules_builder import BrandRulesBuilder
from brand_engine.models import (
    BrandProfile,
    MetricInsights,
    AestheticDNA,
    BrandStaticRules,
    PerformancePattern
)


# ========================================
# Fixtures
# ========================================

@pytest.fixture
def builder():
    """Create a BrandRulesBuilder instance."""
    return BrandRulesBuilder()


@pytest.fixture
def sample_brand_profile():
    """Sample brand profile from interrogation."""
    return BrandProfile(
        user_id="test_user",
        aesthetic={
            "core_identity": "Trap oscuro con elementos futuristas",
            "visual_preferences": ["Neones morados", "Coches deportivos", "Noches urbanas"],
            "color_palette": ["#8B44FF", "#1A1A2E", "#16213E"]
        },
        narrative={
            "storytelling_style": "Narrativa de superación desde la calle",
            "key_themes": ["trap", "dinero", "coches", "éxito"],
            "target_emotion": "Motivación + Ambición"
        },
        cultural_references={
            "music_influences": ["Bad Bunny", "Anuel AA", "Mora"],
            "visual_influences": ["Blade Runner", "Drive", "Fast & Furious"],
            "regional_identity": "Galicia → Global"
        },
        prohibitions=[
            "Nada genérico sin identidad",
            "Contenido diurno sin atmósfera",
            "Escenas sin la estética morada característica"
        ],
        visual_rules={
            "mandatory": ["Paleta morada presente", "Lighting atmosférico"],
            "preferred": ["Coches deportivos", "Escenas nocturnas"],
            "avoid": ["Luz natural excesiva", "Colores pasteles"]
        },
        long_term_vision="Convertir el morado en icono visual del trap español",
        created_at=datetime.utcnow()
    )


@pytest.fixture
def sample_metric_insights():
    """Sample metric insights from performance analysis."""
    return MetricInsights(
        avg_retention=0.76,
        avg_ctr=0.08,
        avg_watch_time=165.0,
        total_views=750000,
        top_performing_aesthetics=[
            {"aesthetic": "purple_neon", "avg_retention": 0.85, "count": 12},
            {"aesthetic": "car_night", "avg_retention": 0.82, "count": 8}
        ],
        top_performing_scenes=[
            {"scene": "coche", "avg_retention": 0.83, "count": 10},
            {"scene": "calle", "avg_retention": 0.78, "count": 7}
        ],
        patterns=[
            PerformancePattern(
                pattern_type="aesthetic_correlation",
                description="Purple aesthetic correlates +25% retention",
                confidence=0.89,
                sample_size=12
            ),
            PerformancePattern(
                pattern_type="scene_correlation",
                description="Night scenes outperform day scenes by 40%",
                confidence=0.92,
                sample_size=15
            )
        ],
        recommendations=[
            "Increase purple aesthetic usage (top performer)",
            "Focus on night scenes (83% avg retention)",
            "Car scenes perform best for brand"
        ],
        analyzed_at=datetime.utcnow()
    )


@pytest.fixture
def sample_aesthetic_dna():
    """Sample aesthetic DNA from content analysis."""
    return AestheticDNA(
        dominant_colors=["#8B44FF", "#1A1A2E", "#16213E", "#0A0A0A"],
        recurring_scenes=[
            {"scene": "coche", "frequency": 0.45},
            {"scene": "calle", "frequency": 0.30},
            {"scene": "noche", "frequency": 0.25}
        ],
        signature_objects=["car", "person", "cell_phone", "bottle"],
        color_consistency_score=0.82,
        scene_distribution={
            "coche": 0.45,
            "calle": 0.30,
            "noche": 0.15,
            "club": 0.10
        },
        object_distribution={
            "car": 0.50,
            "person": 0.90,
            "cell_phone": 0.40,
            "bottle": 0.30
        },
        purple_prevalence=0.78,
        extracted_at=datetime.utcnow()
    )


# ========================================
# Test Initialization & Loading
# ========================================

def test_builder_initialization(builder):
    """Test builder initializes correctly."""
    assert builder is not None
    assert builder.profile is None
    assert builder.metrics is None
    assert builder.aesthetic_dna is None


def test_load_profile(builder, sample_brand_profile):
    """Test loading brand profile."""
    builder.load_profile(sample_brand_profile)
    
    assert builder.profile is not None
    assert builder.profile.user_id == "test_user"


def test_load_metrics(builder, sample_metric_insights):
    """Test loading metric insights."""
    builder.load_metrics(sample_metric_insights)
    
    assert builder.metrics is not None
    assert builder.metrics.avg_retention > 0


def test_load_aesthetic_dna(builder, sample_aesthetic_dna):
    """Test loading aesthetic DNA."""
    builder.load_aesthetic_dna(sample_aesthetic_dna)
    
    assert builder.aesthetic_dna is not None
    assert len(builder.aesthetic_dna.dominant_colors) > 0


# ========================================
# Test Fusion Logic
# ========================================

def test_fuse_all_missing_components(builder):
    """Test fusion fails with missing components."""
    with pytest.raises(ValueError, match="All components required"):
        builder.fuse_all()


def test_fuse_profile_only(builder, sample_brand_profile):
    """Test fusion fails with only profile."""
    builder.load_profile(sample_brand_profile)
    
    with pytest.raises(ValueError, match="All components required"):
        builder.fuse_all()


def test_fuse_all_complete(builder, sample_brand_profile, sample_metric_insights, sample_aesthetic_dna):
    """Test complete fusion."""
    builder.load_profile(sample_brand_profile)
    builder.load_metrics(sample_metric_insights)
    builder.load_aesthetic_dna(sample_aesthetic_dna)
    
    rules = builder.fuse_all()
    
    assert isinstance(rules, BrandStaticRules)


def test_fused_rules_structure(builder, sample_brand_profile, sample_metric_insights, sample_aesthetic_dna):
    """Test fused rules have correct structure."""
    builder.load_profile(sample_brand_profile)
    builder.load_metrics(sample_metric_insights)
    builder.load_aesthetic_dna(sample_aesthetic_dna)
    
    rules = builder.fuse_all()
    
    assert hasattr(rules, "aesthetic")
    assert hasattr(rules, "content")
    assert hasattr(rules, "prohibitions")
    assert hasattr(rules, "performance")


# ========================================
# Test Rule Generation
# ========================================

def test_generate_aesthetic_rules(builder, sample_brand_profile, sample_metric_insights, sample_aesthetic_dna):
    """Test aesthetic rules generation."""
    builder.load_profile(sample_brand_profile)
    builder.load_metrics(sample_metric_insights)
    builder.load_aesthetic_dna(sample_aesthetic_dna)
    
    rules = builder.fuse_all()
    
    assert "colors" in rules.aesthetic
    assert "#8B44FF" in rules.aesthetic["colors"]


def test_generate_content_rules(builder, sample_brand_profile, sample_metric_insights, sample_aesthetic_dna):
    """Test content rules generation."""
    builder.load_profile(sample_brand_profile)
    builder.load_metrics(sample_metric_insights)
    builder.load_aesthetic_dna(sample_aesthetic_dna)
    
    rules = builder.fuse_all()
    
    assert "themes" in rules.content
    assert len(rules.content["themes"]) > 0


def test_generate_prohibition_rules(builder, sample_brand_profile, sample_metric_insights, sample_aesthetic_dna):
    """Test prohibition rules generation."""
    builder.load_profile(sample_brand_profile)
    builder.load_metrics(sample_metric_insights)
    builder.load_aesthetic_dna(sample_aesthetic_dna)
    
    rules = builder.fuse_all()
    
    assert len(rules.prohibitions) > 0
    assert any("genérico" in p.lower() for p in rules.prohibitions)


def test_generate_performance_rules(builder, sample_brand_profile, sample_metric_insights, sample_aesthetic_dna):
    """Test performance-based rules generation."""
    builder.load_profile(sample_brand_profile)
    builder.load_metrics(sample_metric_insights)
    builder.load_aesthetic_dna(sample_aesthetic_dna)
    
    rules = builder.fuse_all()
    
    assert "top_aesthetics" in rules.performance
    assert len(rules.performance["top_aesthetics"]) > 0


# ========================================
# Test Priority & Weighting
# ========================================

def test_metrics_override_profile_when_conflicting(builder, sample_brand_profile, sample_metric_insights, sample_aesthetic_dna):
    """Test metrics data takes priority over profile when conflicting."""
    builder.load_profile(sample_brand_profile)
    builder.load_metrics(sample_metric_insights)
    builder.load_aesthetic_dna(sample_aesthetic_dna)
    
    rules = builder.fuse_all()
    
    # Should prioritize actual performance data
    assert rules.performance["top_aesthetics"][0]["aesthetic"] == "purple_neon"


def test_aesthetic_dna_consistency_check(builder, sample_brand_profile, sample_metric_insights, sample_aesthetic_dna):
    """Test aesthetic DNA is validated against profile."""
    builder.load_profile(sample_brand_profile)
    builder.load_metrics(sample_metric_insights)
    builder.load_aesthetic_dna(sample_aesthetic_dna)
    
    rules = builder.fuse_all()
    
    # Should detect consistency between profile and DNA
    assert rules.aesthetic["colors"][0] in sample_aesthetic_dna.dominant_colors


# ========================================
# Test Validation
# ========================================

def test_validate_rules_complete(builder, sample_brand_profile, sample_metric_insights, sample_aesthetic_dna):
    """Test rules validation passes for complete rules."""
    builder.load_profile(sample_brand_profile)
    builder.load_metrics(sample_metric_insights)
    builder.load_aesthetic_dna(sample_aesthetic_dna)
    
    rules = builder.fuse_all()
    is_valid, errors = builder.validate_rules(rules)
    
    assert is_valid
    assert len(errors) == 0


def test_validate_rules_missing_aesthetic(builder):
    """Test validation fails with missing aesthetic section."""
    incomplete_rules = BrandStaticRules(
        aesthetic={},  # Empty
        content={"themes": ["trap"]},
        prohibitions=["generic"],
        performance={"top_aesthetics": []},
        version="1.0",
        generated_at=datetime.utcnow()
    )
    
    is_valid, errors = builder.validate_rules(incomplete_rules)
    
    assert not is_valid
    assert any("aesthetic" in e.lower() for e in errors)


def test_validate_rules_empty_prohibitions(builder):
    """Test validation warns about empty prohibitions."""
    rules_no_prohibitions = BrandStaticRules(
        aesthetic={"colors": ["#8B44FF"]},
        content={"themes": ["trap"]},
        prohibitions=[],  # Empty
        performance={"top_aesthetics": []},
        version="1.0",
        generated_at=datetime.utcnow()
    )
    
    is_valid, errors = builder.validate_rules(rules_no_prohibitions)
    
    # Should still be valid but generate warning
    assert any("prohibition" in e.lower() for e in errors) or is_valid


# ========================================
# Test JSON Generation
# ========================================

def test_generate_json_structure(builder, sample_brand_profile, sample_metric_insights, sample_aesthetic_dna):
    """Test JSON generation produces valid structure."""
    builder.load_profile(sample_brand_profile)
    builder.load_metrics(sample_metric_insights)
    builder.load_aesthetic_dna(sample_aesthetic_dna)
    
    rules = builder.fuse_all()
    rules_json = builder.to_json(rules)
    
    # Should be valid JSON
    parsed = json.loads(rules_json)
    assert "aesthetic" in parsed
    assert "content" in parsed
    assert "version" in parsed


def test_json_includes_metadata(builder, sample_brand_profile, sample_metric_insights, sample_aesthetic_dna):
    """Test JSON includes metadata."""
    builder.load_profile(sample_brand_profile)
    builder.load_metrics(sample_metric_insights)
    builder.load_aesthetic_dna(sample_aesthetic_dna)
    
    rules = builder.fuse_all()
    rules_json = builder.to_json(rules)
    parsed = json.loads(rules_json)
    
    assert "version" in parsed
    assert "generated_at" in parsed


# ========================================
# Test File Operations
# ========================================

def test_save_rules(builder, sample_brand_profile, sample_metric_insights, sample_aesthetic_dna, tmp_path):
    """Test saving rules to file."""
    builder.load_profile(sample_brand_profile)
    builder.load_metrics(sample_metric_insights)
    builder.load_aesthetic_dna(sample_aesthetic_dna)
    
    rules = builder.fuse_all()
    
    output_path = tmp_path / "BRAND_STATIC_RULES.json"
    builder.save_rules(rules, str(output_path))
    
    assert output_path.exists()


def test_load_rules(builder, sample_brand_profile, sample_metric_insights, sample_aesthetic_dna, tmp_path):
    """Test loading rules from file."""
    builder.load_profile(sample_brand_profile)
    builder.load_metrics(sample_metric_insights)
    builder.load_aesthetic_dna(sample_aesthetic_dna)
    
    rules = builder.fuse_all()
    
    output_path = tmp_path / "BRAND_STATIC_RULES.json"
    builder.save_rules(rules, str(output_path))
    
    # Load back
    loaded_rules = builder.load_rules_from_file(str(output_path))
    
    assert loaded_rules.aesthetic == rules.aesthetic


def test_versioning(builder, sample_brand_profile, sample_metric_insights, sample_aesthetic_dna, tmp_path):
    """Test rules versioning."""
    builder.load_profile(sample_brand_profile)
    builder.load_metrics(sample_metric_insights)
    builder.load_aesthetic_dna(sample_aesthetic_dna)
    
    rules_v1 = builder.fuse_all()
    
    output_path = tmp_path / "BRAND_STATIC_RULES_v1.json"
    builder.save_rules(rules_v1, str(output_path), version="1.0")
    
    # Modify and save v2
    rules_v2 = builder.fuse_all()
    output_path_v2 = tmp_path / "BRAND_STATIC_RULES_v2.json"
    builder.save_rules(rules_v2, str(output_path_v2), version="2.0")
    
    assert output_path.exists()
    assert output_path_v2.exists()


# ========================================
# Test Diff & Comparison
# ========================================

def test_compare_versions(builder, sample_brand_profile, sample_metric_insights, sample_aesthetic_dna):
    """Test comparing two rule versions."""
    builder.load_profile(sample_brand_profile)
    builder.load_metrics(sample_metric_insights)
    builder.load_aesthetic_dna(sample_aesthetic_dna)
    
    rules_v1 = builder.fuse_all()
    
    # Modify metrics
    sample_metric_insights.avg_retention = 0.90
    builder.load_metrics(sample_metric_insights)
    rules_v2 = builder.fuse_all()
    
    diff = builder.compare_rules(rules_v1, rules_v2)
    
    assert len(diff) > 0


# ========================================
# Test Edge Cases
# ========================================

def test_fusion_with_low_confidence_patterns(builder, sample_brand_profile, sample_metric_insights, sample_aesthetic_dna):
    """Test fusion handles low confidence patterns."""
    # Lower confidence
    sample_metric_insights.patterns[0].confidence = 0.3
    
    builder.load_profile(sample_brand_profile)
    builder.load_metrics(sample_metric_insights)
    builder.load_aesthetic_dna(sample_aesthetic_dna)
    
    rules = builder.fuse_all()
    
    # Should still generate rules but with caveats
    assert isinstance(rules, BrandStaticRules)


def test_fusion_with_conflicting_data(builder, sample_brand_profile, sample_metric_insights, sample_aesthetic_dna):
    """Test fusion handles conflicting data sources."""
    # Profile says purple, but DNA shows low purple
    sample_aesthetic_dna.purple_prevalence = 0.1
    
    builder.load_profile(sample_brand_profile)
    builder.load_metrics(sample_metric_insights)
    builder.load_aesthetic_dna(sample_aesthetic_dna)
    
    rules = builder.fuse_all()
    
    # Should prioritize actual data (low purple) with warning
    assert isinstance(rules, BrandStaticRules)


# ========================================
# Test Summary
# ========================================

def test_get_summary(builder, sample_brand_profile, sample_metric_insights, sample_aesthetic_dna):
    """Test getting summary of fusion process."""
    builder.load_profile(sample_brand_profile)
    builder.load_metrics(sample_metric_insights)
    builder.load_aesthetic_dna(sample_aesthetic_dna)
    
    rules = builder.fuse_all()
    summary = builder.get_summary(rules)
    
    assert "total_rules" in summary
    assert "aesthetic_rules_count" in summary
    assert "prohibition_count" in summary


# ========================================
# Run tests
# ========================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
