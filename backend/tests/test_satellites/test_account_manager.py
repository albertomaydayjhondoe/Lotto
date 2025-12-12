"""
Tests for Account Manager
"""

import pytest
from datetime import datetime, timedelta

from app.satellites.config import SatelliteConfig
from app.satellites.models import SatelliteAccount
from app.satellites.account_management import AccountManager


@pytest.fixture
def config():
    """Fixture: Default config."""
    return SatelliteConfig()


@pytest.fixture
def manager(config):
    """Fixture: Account manager."""
    return AccountManager(config)


@pytest.fixture
def sample_account():
    """Fixture: Sample TikTok account."""
    return SatelliteAccount(
        account_id="acc_001",
        platform="tiktok",
        username="test_tiktok",
        daily_post_limit=5,
        posts_today=0,
        success_rate=1.0
    )


def test_add_account(manager, sample_account):
    """Test: Add account to manager."""
    manager.add_account(sample_account)
    
    assert len(manager.accounts) == 1
    assert manager.get_account("acc_001") == sample_account


def test_remove_account(manager, sample_account):
    """Test: Remove account from manager."""
    manager.add_account(sample_account)
    
    result = manager.remove_account("acc_001")
    
    assert result is True
    assert len(manager.accounts) == 0


def test_remove_nonexistent_account(manager):
    """Test: Remove non-existent account returns False."""
    result = manager.remove_account("nonexistent")
    
    assert result is False


def test_get_accounts_for_platform(manager):
    """Test: Get accounts filtered by platform."""
    # Add accounts for different platforms
    acc1 = SatelliteAccount(
        account_id="acc_001",
        platform="tiktok",
        username="user1"
    )
    acc2 = SatelliteAccount(
        account_id="acc_002",
        platform="tiktok",
        username="user2"
    )
    acc3 = SatelliteAccount(
        account_id="acc_003",
        platform="instagram",
        username="user3"
    )
    
    manager.add_account(acc1)
    manager.add_account(acc2)
    manager.add_account(acc3)
    
    tiktok_accounts = manager.get_accounts_for_platform("tiktok")
    instagram_accounts = manager.get_accounts_for_platform("instagram")
    
    assert len(tiktok_accounts) == 2
    assert len(instagram_accounts) == 1


def test_get_accounts_active_only(manager):
    """Test: Filter active accounts only."""
    acc1 = SatelliteAccount(
        account_id="acc_001",
        platform="tiktok",
        username="user1",
        is_active=True
    )
    acc2 = SatelliteAccount(
        account_id="acc_002",
        platform="tiktok",
        username="user2",
        is_active=False
    )
    
    manager.add_account(acc1)
    manager.add_account(acc2)
    
    active = manager.get_accounts_for_platform("tiktok", active_only=True)
    all_accounts = manager.get_accounts_for_platform("tiktok", active_only=False)
    
    assert len(active) == 1
    assert len(all_accounts) == 2


def test_get_best_account_by_success_rate(manager):
    """Test: Get best account prioritizes success rate."""
    acc1 = SatelliteAccount(
        account_id="acc_001",
        platform="tiktok",
        username="user1",
        success_rate=0.8,
        posts_today=0
    )
    acc2 = SatelliteAccount(
        account_id="acc_002",
        platform="tiktok",
        username="user2",
        success_rate=0.95,
        posts_today=0
    )
    
    manager.add_account(acc1)
    manager.add_account(acc2)
    
    best = manager.get_best_account("tiktok")
    
    assert best.account_id == "acc_002"  # Higher success rate


def test_get_best_account_respects_daily_limit(manager):
    """Test: Get best account skips accounts at daily limit."""
    acc1 = SatelliteAccount(
        account_id="acc_001",
        platform="tiktok",
        username="user1",
        daily_post_limit=5,
        posts_today=5  # At limit
    )
    acc2 = SatelliteAccount(
        account_id="acc_002",
        platform="tiktok",
        username="user2",
        daily_post_limit=5,
        posts_today=2  # Available
    )
    
    manager.add_account(acc1)
    manager.add_account(acc2)
    
    best = manager.get_best_account("tiktok")
    
    assert best.account_id == "acc_002"


def test_get_best_account_respects_cooldown(manager, config):
    """Test: Get best account respects time between posts."""
    recent_post = datetime.utcnow() - timedelta(seconds=300)  # 5 minutes ago
    
    acc1 = SatelliteAccount(
        account_id="acc_001",
        platform="instagram",
        username="user1",
        posts_today=0,
        last_post_at=recent_post  # Too recent
    )
    acc2 = SatelliteAccount(
        account_id="acc_002",
        platform="instagram",
        username="user2",
        posts_today=0,
        last_post_at=None  # No recent post
    )
    
    manager.add_account(acc1)
    manager.add_account(acc2)
    
    best = manager.get_best_account("instagram")
    
    # Should pick acc2 since acc1 needs cooldown
    assert best.account_id == "acc_002"


def test_get_best_account_no_available(manager):
    """Test: Get best account returns None if none available."""
    acc = SatelliteAccount(
        account_id="acc_001",
        platform="youtube",
        username="user1",
        daily_post_limit=3,
        posts_today=3  # At limit
    )
    
    manager.add_account(acc)
    
    best = manager.get_best_account("youtube")
    
    assert best is None


def test_update_post_stats_success(manager, sample_account):
    """Test: Update post stats after successful upload."""
    manager.add_account(sample_account)
    
    manager.update_post_stats("acc_001", success=True)
    
    account = manager.get_account("acc_001")
    assert account.total_uploads == 1
    assert account.failed_uploads == 0
    assert account.success_rate == 1.0
    assert account.posts_today == 1


def test_update_post_stats_failure(manager, sample_account):
    """Test: Update post stats after failed upload."""
    manager.add_account(sample_account)
    
    manager.update_post_stats("acc_001", success=False)
    
    account = manager.get_account("acc_001")
    assert account.total_uploads == 1
    assert account.failed_uploads == 1
    assert account.success_rate == 0.0


def test_update_post_stats_recalculates_success_rate(manager, sample_account):
    """Test: Success rate recalculation."""
    manager.add_account(sample_account)
    
    # 3 successful, 1 failed = 75% success rate
    manager.update_post_stats("acc_001", success=True)
    manager.update_post_stats("acc_001", success=True)
    manager.update_post_stats("acc_001", success=True)
    manager.update_post_stats("acc_001", success=False)
    
    account = manager.get_account("acc_001")
    assert account.success_rate == 0.75


def test_reset_daily_counters(manager):
    """Test: Reset daily counters for all accounts."""
    acc1 = SatelliteAccount(
        account_id="acc_001",
        platform="tiktok",
        username="user1",
        posts_today=3
    )
    acc2 = SatelliteAccount(
        account_id="acc_002",
        platform="instagram",
        username="user2",
        posts_today=5
    )
    
    manager.add_account(acc1)
    manager.add_account(acc2)
    
    manager.reset_daily_counters()
    
    assert manager.get_account("acc_001").posts_today == 0
    assert manager.get_account("acc_002").posts_today == 0


def test_setup_gologin_profile(manager, sample_account):
    """Test: Setup GoLogin profile (STUB)."""
    manager.add_account(sample_account)
    
    result = manager.setup_gologin_profile("acc_001", "gologin_profile_123")
    
    assert result is True
    account = manager.get_account("acc_001")
    assert account.gologin_profile_id == "gologin_profile_123"


def test_setup_proxy(manager, sample_account):
    """Test: Setup proxy config (STUB)."""
    manager.add_account(sample_account)
    
    proxy_config = {
        "host": "proxy.example.com",
        "port": 8080,
        "username": "user",
        "password": "pass"
    }
    
    result = manager.setup_proxy("acc_001", proxy_config)
    
    assert result is True
    account = manager.get_account("acc_001")
    assert account.proxy_config == proxy_config


def test_get_summary(manager):
    """Test: Get account manager summary."""
    acc1 = SatelliteAccount(
        account_id="acc_001",
        platform="tiktok",
        username="user1",
        is_active=True,
        total_uploads=10,
        failed_uploads=2
    )
    acc2 = SatelliteAccount(
        account_id="acc_002",
        platform="instagram",
        username="user2",
        is_active=False,
        total_uploads=5,
        failed_uploads=0
    )
    
    manager.add_account(acc1)
    manager.add_account(acc2)
    
    summary = manager.get_summary()
    
    assert summary["total_accounts"] == 2
    assert summary["active_accounts"] == 1
    assert summary["total_uploads"] == 15
    assert summary["total_failures"] == 2
