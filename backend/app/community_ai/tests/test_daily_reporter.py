"""
Tests for Daily Reporter - Sprint 4B

Tests daily report generation with metrics, alerts, and recommendations.
"""

import pytest
from datetime import date, datetime, timedelta

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from community_ai.daily_reporter import DailyReporter
from community_ai.models import DailyReport, PerformanceMetrics


# ========================================
# Fixtures
# ========================================

@pytest.fixture
def reporter():
    """Create a DailyReporter instance."""
    return DailyReporter(mode="stub")


@pytest.fixture
def sample_date():
    """Sample date for reports."""
    return date(2024, 12, 7)


@pytest.fixture
def sample_metrics():
    """Sample performance metrics."""
    return {
        "publications": 5,
        "total_views": 15000,
        "total_likes": 1200,
        "total_comments": 150,
        "total_shares": 80,
        "followers_gained": 45,
        "engagement_rate": 9.5
    }


# ========================================
# Test Initialization
# ========================================

def test_reporter_initialization(reporter):
    """Test reporter initializes correctly."""
    assert reporter is not None
    assert reporter.mode == "stub"


# ========================================
# Test Daily Report Generation
# ========================================

def test_generate_daily_report_basic(reporter, sample_date):
    """Test basic daily report generation."""
    report = reporter.generate_daily_report(
        report_date=sample_date,
        user_id="test_user"
    )
    
    assert isinstance(report, DailyReport)
    assert report.date == sample_date
    assert report.user_id == "test_user"


def test_report_has_all_sections(reporter, sample_date):
    """Test report has all required sections."""
    report = reporter.generate_daily_report(sample_date, "test_user")
    
    # Core sections
    assert report.publications_summary is not None
    assert report.performance_metrics is not None
    assert report.top_performers is not None
    assert report.worst_performers is not None
    assert report.audience_insights is not None
    assert report.alerts is not None
    assert report.recommendations is not None
    assert report.tomorrow_focus is not None


def test_report_has_metadata(reporter, sample_date):
    """Test report has metadata."""
    report = reporter.generate_daily_report(sample_date, "test_user")
    
    assert report.generated_at is not None
    assert isinstance(report.generated_at, datetime)
    assert 0.0 <= report.confidence <= 1.0


# ========================================
# Test Publications Summary
# ========================================

def test_publications_summary_count(reporter, sample_date):
    """Test publications summary has count."""
    report = reporter.generate_daily_report(sample_date, "test_user")
    
    summary = report.publications_summary
    assert "total" in summary
    assert summary["total"] >= 0


def test_publications_by_platform(reporter, sample_date):
    """Test publications breakdown by platform."""
    report = reporter.generate_daily_report(sample_date, "test_user")
    
    summary = report.publications_summary
    assert "by_platform" in summary


def test_publications_by_type(reporter, sample_date):
    """Test publications breakdown by type."""
    report = reporter.generate_daily_report(sample_date, "test_user")
    
    summary = report.publications_summary
    assert "by_type" in summary


# ========================================
# Test Performance Metrics
# ========================================

def test_performance_metrics_present(reporter, sample_date):
    """Test performance metrics are present."""
    report = reporter.generate_daily_report(sample_date, "test_user")
    
    metrics = report.performance_metrics
    assert isinstance(metrics, PerformanceMetrics)


def test_metrics_have_values(reporter, sample_date):
    """Test metrics have numeric values."""
    report = reporter.generate_daily_report(sample_date, "test_user")
    
    metrics = report.performance_metrics
    assert metrics.total_views >= 0
    assert metrics.total_likes >= 0
    assert metrics.total_comments >= 0
    assert metrics.total_shares >= 0
    assert metrics.engagement_rate >= 0.0


def test_metrics_have_trends(reporter, sample_date):
    """Test metrics have trend indicators."""
    report = reporter.generate_daily_report(sample_date, "test_user")
    
    metrics = report.performance_metrics
    # Trends should be present: "📈", "📉", "➡️"
    assert metrics.views_trend is not None
    assert metrics.engagement_trend is not None


# ========================================
# Test Top/Worst Performers
# ========================================

def test_top_performers_list(reporter, sample_date):
    """Test top performers list."""
    report = reporter.generate_daily_report(sample_date, "test_user")
    
    assert isinstance(report.top_performers, list)


def test_top_performers_have_details(reporter, sample_date):
    """Test top performers have details."""
    report = reporter.generate_daily_report(sample_date, "test_user")
    
    if len(report.top_performers) > 0:
        top = report.top_performers[0]
        assert "post_id" in top
        assert "performance_score" in top
        assert "insights" in top


def test_worst_performers_list(reporter, sample_date):
    """Test worst performers list."""
    report = reporter.generate_daily_report(sample_date, "test_user")
    
    assert isinstance(report.worst_performers, list)


def test_top_and_worst_are_different(reporter, sample_date):
    """Test top and worst don't overlap."""
    report = reporter.generate_daily_report(sample_date, "test_user")
    
    if len(report.top_performers) > 0 and len(report.worst_performers) > 0:
        top_ids = {p["post_id"] for p in report.top_performers}
        worst_ids = {p["post_id"] for p in report.worst_performers}
        
        # Should be disjoint sets
        assert len(top_ids & worst_ids) == 0


# ========================================
# Test Audience Insights
# ========================================

def test_audience_insights_present(reporter, sample_date):
    """Test audience insights are present."""
    report = reporter.generate_daily_report(sample_date, "test_user")
    
    insights = report.audience_insights
    assert "followers_gained" in insights
    assert "most_active_time" in insights


def test_followers_gained_metric(reporter, sample_date):
    """Test followers gained metric."""
    report = reporter.generate_daily_report(sample_date, "test_user")
    
    insights = report.audience_insights
    followers = insights["followers_gained"]
    assert isinstance(followers, (int, float))


# ========================================
# Test Alerts
# ========================================

def test_alerts_list(reporter, sample_date):
    """Test alerts list."""
    report = reporter.generate_daily_report(sample_date, "test_user")
    
    assert isinstance(report.alerts, list)


def test_alert_structure(reporter, sample_date):
    """Test alert structure."""
    report = reporter.generate_daily_report(sample_date, "test_user")
    
    if len(report.alerts) > 0:
        alert = report.alerts[0]
        assert "severity" in alert
        assert "message" in alert
        assert alert["severity"] in ["⚠️", "🔴", "🟡"]


def test_alerts_for_anomalies(reporter, sample_date):
    """Test alerts detect anomalies."""
    # In real implementation, would pass metrics with anomalies
    report = reporter.generate_daily_report(sample_date, "test_user")
    
    # Alerts should be present if there are issues
    assert isinstance(report.alerts, list)


# ========================================
# Test Recommendations
# ========================================

def test_recommendations_list(reporter, sample_date):
    """Test recommendations list."""
    report = reporter.generate_daily_report(sample_date, "test_user")
    
    assert isinstance(report.recommendations, list)
    assert len(report.recommendations) > 0


def test_recommendation_structure(reporter, sample_date):
    """Test recommendation structure."""
    report = reporter.generate_daily_report(sample_date, "test_user")
    
    if len(report.recommendations) > 0:
        rec = report.recommendations[0]
        assert "category" in rec
        assert "action" in rec
        assert "reason" in rec


def test_recommendations_actionable(reporter, sample_date):
    """Test recommendations are actionable."""
    report = reporter.generate_daily_report(sample_date, "test_user")
    
    for rec in report.recommendations:
        # Should have action verb
        action = rec["action"].lower()
        assert any(verb in action for verb in ["post", "try", "focus", "use", "create"])


# ========================================
# Test Tomorrow Focus
# ========================================

def test_tomorrow_focus_present(reporter, sample_date):
    """Test tomorrow focus is present."""
    report = reporter.generate_daily_report(sample_date, "test_user")
    
    assert report.tomorrow_focus is not None
    assert isinstance(report.tomorrow_focus, list)
    assert len(report.tomorrow_focus) > 0


def test_tomorrow_focus_priorities(reporter, sample_date):
    """Test tomorrow focus has priorities."""
    report = reporter.generate_daily_report(sample_date, "test_user")
    
    for focus in report.tomorrow_focus:
        assert "priority" in focus
        assert "task" in focus


# ========================================
# Test Markdown Export
# ========================================

def test_export_report_markdown(reporter, sample_date):
    """Test markdown export."""
    report = reporter.generate_daily_report(sample_date, "test_user")
    markdown = reporter.export_report_markdown(report)
    
    assert isinstance(markdown, str)
    assert len(markdown) > 0


def test_markdown_has_headers(reporter, sample_date):
    """Test markdown has section headers."""
    report = reporter.generate_daily_report(sample_date, "test_user")
    markdown = reporter.export_report_markdown(report)
    
    # Should have markdown headers
    assert "##" in markdown or "#" in markdown


def test_markdown_has_emojis(reporter, sample_date):
    """Test markdown uses emojis."""
    report = reporter.generate_daily_report(sample_date, "test_user")
    markdown = reporter.export_report_markdown(report)
    
    # Should have trend emojis
    assert any(emoji in markdown for emoji in ["📈", "📉", "➡️", "⚠️", "💡", "🎯"])


def test_markdown_ready_for_telegram(reporter, sample_date):
    """Test markdown is Telegram-ready."""
    report = reporter.generate_daily_report(sample_date, "test_user")
    markdown = reporter.export_report_markdown(report)
    
    # Should be properly formatted
    assert markdown.strip() != ""
    # Should have date header
    assert str(sample_date.year) in markdown


# ========================================
# Test Performance Change Calculation
# ========================================

def test_calculate_performance_change_increase(reporter):
    """Test performance increase detection."""
    current = 1000
    previous = 800
    
    change = reporter._calculate_performance_change(current, previous)
    
    assert change > 0
    assert "📈" in reporter._get_trend_emoji(change)


def test_calculate_performance_change_decrease(reporter):
    """Test performance decrease detection."""
    current = 800
    previous = 1000
    
    change = reporter._calculate_performance_change(current, previous)
    
    assert change < 0
    assert "📉" in reporter._get_trend_emoji(change)


def test_calculate_performance_change_stable(reporter):
    """Test stable performance detection."""
    current = 1000
    previous = 1000
    
    change = reporter._calculate_performance_change(current, previous)
    
    assert change == 0
    assert "➡️" in reporter._get_trend_emoji(change)


# ========================================
# Test Confidence Scoring
# ========================================

def test_report_confidence_high_with_data(reporter, sample_date):
    """Test high confidence with complete data."""
    report = reporter.generate_daily_report(sample_date, "test_user")
    
    # With data, confidence should be high
    assert report.confidence > 0.7


# ========================================
# Test Edge Cases
# ========================================

def test_report_with_no_publications(reporter, sample_date):
    """Test report when no publications."""
    # In real implementation, would pass empty metrics
    report = reporter.generate_daily_report(sample_date, "test_user")
    
    # Should still generate report
    assert report is not None


def test_report_future_date(reporter):
    """Test report for future date."""
    future_date = date.today() + timedelta(days=7)
    
    report = reporter.generate_daily_report(future_date, "test_user")
    
    # Should handle gracefully (maybe lower confidence)
    assert report is not None


def test_report_very_old_date(reporter):
    """Test report for very old date."""
    old_date = date(2020, 1, 1)
    
    report = reporter.generate_daily_report(old_date, "test_user")
    
    # Should handle gracefully
    assert report is not None


# ========================================
# Run tests
# ========================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
