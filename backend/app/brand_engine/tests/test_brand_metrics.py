"""
Tests for Brand Metrics Analyzer - Sprint 4

Tests real performance data analysis and pattern detection.
"""

import pytest
from datetime import datetime, timedelta
import numpy as np

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from brand_engine.brand_metrics import BrandMetricsAnalyzer
from brand_engine.models import (
    ContentMetric,
    MetricInsights,
    PerformancePattern
)


# ========================================
# Fixtures
# ========================================

@pytest.fixture
def analyzer():
    """Create a BrandMetricsAnalyzer instance."""
    return BrandMetricsAnalyzer()


@pytest.fixture
def sample_metrics():
    """Sample content metrics for testing."""
    metrics = []
    
    # High performance content
    for i in range(10):
        metrics.append(ContentMetric(
            content_id=f"high_perf_{i}",
            views=50000 + i * 1000,
            retention_rate=0.75 + i * 0.01,
            ctr=0.08 + i * 0.005,
            watch_time_avg=180 + i * 5,
            skip_rate=0.15 - i * 0.01,
            aesthetic_tags=["purple", "neon", "urban", "night"],
            scene_types=["coche", "calle", "noche"],
            timestamp=datetime.utcnow() - timedelta(days=i)
        ))
    
    # Low performance content
    for i in range(5):
        metrics.append(ContentMetric(
            content_id=f"low_perf_{i}",
            views=5000 + i * 100,
            retention_rate=0.35 + i * 0.02,
            ctr=0.02 + i * 0.001,
            watch_time_avg=60 + i * 2,
            skip_rate=0.65 - i * 0.02,
            aesthetic_tags=["generic", "daytime"],
            scene_types=["interior"],
            timestamp=datetime.utcnow() - timedelta(days=i + 10)
        ))
    
    return metrics


# ========================================
# Test Metrics Analysis
# ========================================

def test_analyzer_initialization(analyzer):
    """Test analyzer initializes correctly."""
    assert analyzer is not None
    assert len(analyzer.metrics) == 0


def test_add_metrics(analyzer, sample_metrics):
    """Test adding metrics."""
    analyzer.add_metrics(sample_metrics)
    
    assert len(analyzer.metrics) == len(sample_metrics)


def test_calculate_average_retention(analyzer, sample_metrics):
    """Test average retention calculation."""
    analyzer.add_metrics(sample_metrics)
    
    avg_retention = analyzer.calculate_average_retention()
    
    assert 0.0 <= avg_retention <= 1.0
    assert avg_retention > 0.5  # High perf metrics should dominate


def test_calculate_average_ctr(analyzer, sample_metrics):
    """Test average CTR calculation."""
    analyzer.add_metrics(sample_metrics)
    
    avg_ctr = analyzer.calculate_average_ctr()
    
    assert 0.0 <= avg_ctr <= 1.0


def test_calculate_average_watch_time(analyzer, sample_metrics):
    """Test average watch time calculation."""
    analyzer.add_metrics(sample_metrics)
    
    avg_watch_time = analyzer.calculate_average_watch_time()
    
    assert avg_watch_time > 0
    assert avg_watch_time > 100  # Should be influenced by high perf


# ========================================
# Test Pattern Detection
# ========================================

def test_identify_top_performing_content(analyzer, sample_metrics):
    """Test identifying top performers."""
    analyzer.add_metrics(sample_metrics)
    
    top = analyzer.identify_top_performing(top_k=5, metric="retention_rate")
    
    assert len(top) == 5
    assert all("high_perf" in m.content_id for m in top)
    # Should be sorted descending
    assert top[0].retention_rate >= top[-1].retention_rate


def test_identify_worst_performing_content(analyzer, sample_metrics):
    """Test identifying worst performers."""
    analyzer.add_metrics(sample_metrics)
    
    worst = analyzer.identify_worst_performing(bottom_k=3, metric="retention_rate")
    
    assert len(worst) <= 3
    assert any("low_perf" in m.content_id for m in worst)


def test_analyze_aesthetic_performance(analyzer, sample_metrics):
    """Test aesthetic-performance correlation."""
    analyzer.add_metrics(sample_metrics)
    
    aesthetic_perf = analyzer.analyze_aesthetic_performance()
    
    assert "purple" in aesthetic_perf
    assert aesthetic_perf["purple"]["count"] > 0
    assert aesthetic_perf["purple"]["avg_retention"] > 0.5


def test_analyze_scene_performance(analyzer, sample_metrics):
    """Test scene-performance correlation."""
    analyzer.add_metrics(sample_metrics)
    
    scene_perf = analyzer.analyze_scene_performance()
    
    assert "coche" in scene_perf
    assert scene_perf["coche"]["count"] > 0
    assert scene_perf["coche"]["avg_views"] > 10000


def test_detect_patterns(analyzer, sample_metrics):
    """Test pattern detection."""
    analyzer.add_metrics(sample_metrics)
    
    patterns = analyzer.detect_patterns()
    
    assert len(patterns) > 0
    assert any(p.pattern_type == "aesthetic_correlation" for p in patterns)


def test_pattern_confidence_scores(analyzer, sample_metrics):
    """Test pattern confidence is calculated."""
    analyzer.add_metrics(sample_metrics)
    
    patterns = analyzer.detect_patterns()
    
    for pattern in patterns:
        assert 0.0 <= pattern.confidence <= 1.0


# ========================================
# Test Format Analysis
# ========================================

def test_best_formats_by_retention(analyzer, sample_metrics):
    """Test finding best formats."""
    analyzer.add_metrics(sample_metrics)
    
    best_formats = analyzer.get_best_formats(metric="retention_rate", top_k=3)
    
    assert len(best_formats) > 0
    assert "scene_type" in best_formats[0] or "aesthetic" in best_formats[0]


def test_worst_formats(analyzer, sample_metrics):
    """Test finding worst formats."""
    analyzer.add_metrics(sample_metrics)
    
    worst_formats = analyzer.get_worst_formats(metric="skip_rate", bottom_k=2)
    
    assert len(worst_formats) > 0


# ========================================
# Test Time-based Analysis
# ========================================

def test_performance_over_time(analyzer, sample_metrics):
    """Test analyzing performance trends over time."""
    analyzer.add_metrics(sample_metrics)
    
    trend = analyzer.analyze_time_trend(days=14)
    
    assert "retention_trend" in trend
    assert "ctr_trend" in trend


def test_recent_performance(analyzer, sample_metrics):
    """Test filtering to recent content."""
    analyzer.add_metrics(sample_metrics)
    
    recent = analyzer.get_recent_metrics(days=7)
    
    assert len(recent) > 0
    assert len(recent) < len(sample_metrics)


# ========================================
# Test Insights Building
# ========================================

def test_build_insights_no_metrics(analyzer):
    """Test building insights with no metrics raises error."""
    with pytest.raises(ValueError, match="No metrics"):
        analyzer.build_insights()


def test_build_insights_complete(analyzer, sample_metrics):
    """Test building complete insights."""
    analyzer.add_metrics(sample_metrics)
    
    insights = analyzer.build_insights()
    
    assert isinstance(insights, MetricInsights)
    assert insights.avg_retention > 0
    assert insights.avg_ctr > 0
    assert len(insights.top_performing_aesthetics) > 0
    assert len(insights.patterns) > 0


def test_insights_include_recommendations(analyzer, sample_metrics):
    """Test insights include actionable recommendations."""
    analyzer.add_metrics(sample_metrics)
    
    insights = analyzer.build_insights()
    
    assert len(insights.recommendations) > 0
    assert any("aesthetic" in r.lower() for r in insights.recommendations)


# ========================================
# Test Statistical Analysis
# ========================================

def test_calculate_correlation(analyzer, sample_metrics):
    """Test correlation calculation."""
    analyzer.add_metrics(sample_metrics)
    
    # Correlation between retention and watch time
    correlation = analyzer.calculate_correlation("retention_rate", "watch_time_avg")
    
    assert -1.0 <= correlation <= 1.0
    assert correlation > 0  # These should be positively correlated


def test_identify_outliers(analyzer, sample_metrics):
    """Test outlier detection."""
    analyzer.add_metrics(sample_metrics)
    
    outliers = analyzer.identify_outliers(metric="retention_rate", threshold=2.0)
    
    assert isinstance(outliers, list)


# ========================================
# Test Export
# ========================================

def test_export_insights(analyzer, sample_metrics, tmp_path):
    """Test exporting insights to JSON."""
    analyzer.add_metrics(sample_metrics)
    insights = analyzer.build_insights()
    
    export_path = tmp_path / "insights.json"
    analyzer.export_insights(insights, str(export_path))
    
    assert export_path.exists()


def test_export_metrics_csv(analyzer, sample_metrics, tmp_path):
    """Test exporting raw metrics to CSV."""
    analyzer.add_metrics(sample_metrics)
    
    export_path = tmp_path / "metrics.csv"
    analyzer.export_metrics_csv(str(export_path))
    
    assert export_path.exists()


# ========================================
# Test Filtering
# ========================================

def test_filter_by_aesthetic(analyzer, sample_metrics):
    """Test filtering metrics by aesthetic."""
    analyzer.add_metrics(sample_metrics)
    
    purple_metrics = analyzer.filter_by_aesthetic("purple")
    
    assert len(purple_metrics) > 0
    assert all("purple" in m.aesthetic_tags for m in purple_metrics)


def test_filter_by_scene(analyzer, sample_metrics):
    """Test filtering metrics by scene type."""
    analyzer.add_metrics(sample_metrics)
    
    coche_metrics = analyzer.filter_by_scene("coche")
    
    assert len(coche_metrics) > 0
    assert all("coche" in m.scene_types for m in coche_metrics)


def test_filter_by_performance_threshold(analyzer, sample_metrics):
    """Test filtering by performance threshold."""
    analyzer.add_metrics(sample_metrics)
    
    high_retention = analyzer.filter_by_threshold("retention_rate", min_value=0.7)
    
    assert len(high_retention) > 0
    assert all(m.retention_rate >= 0.7 for m in high_retention)


# ========================================
# Test Summary Statistics
# ========================================

def test_get_summary_stats(analyzer, sample_metrics):
    """Test getting summary statistics."""
    analyzer.add_metrics(sample_metrics)
    
    stats = analyzer.get_summary_stats()
    
    assert "total_content" in stats
    assert "avg_retention" in stats
    assert "avg_ctr" in stats
    assert "total_views" in stats


def test_summary_includes_percentiles(analyzer, sample_metrics):
    """Test summary includes percentile information."""
    analyzer.add_metrics(sample_metrics)
    
    stats = analyzer.get_summary_stats()
    
    assert "retention_p50" in stats
    assert "retention_p90" in stats


# ========================================
# Run tests
# ========================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
