"""
Tests for Memory Vault Storage

Phase 1: STUB mode tests
"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4
import json
import os

from app.memory_vault.storage import (
    MemoryVaultStorage,
    MemoryVaultConfig
)


@pytest.fixture
def vault_storage():
    """Create a test Memory Vault storage instance"""
    storage = MemoryVaultStorage(mode="STUB")
    yield storage
    # Cleanup test files
    import shutil
    if os.path.exists(MemoryVaultConfig.ROOT_PATH):
        shutil.rmtree(MemoryVaultConfig.ROOT_PATH)


def test_memory_vault_initialization(vault_storage):
    """Test Memory Vault initializes correctly"""
    assert vault_storage.mode == "STUB"
    assert vault_storage.config is not None
    
    # Check that stub directories are created
    for subfolder in vault_storage.config.SUBFOLDERS.values():
        path = vault_storage.config.get_local_path(subfolder)
        assert path.exists()


def test_generate_filename(vault_storage):
    """Test filename generation follows naming convention"""
    filename = vault_storage.generate_filename("campaign", version=1)
    
    assert "campaign" in filename
    assert filename.endswith(".json")
    assert "__" in filename
    assert "_v1" in filename


def test_store_and_retrieve(vault_storage):
    """Test storing and retrieving data"""
    test_data = {
        "test_field": "test_value",
        "number": 42,
        "nested": {"key": "value"}
    }
    
    # Store data
    result = vault_storage.store(
        subfolder="ml_features",
        entity_type="test_entity",
        data=test_data,
        entity_id="test_123",
        version=1
    )
    
    assert result["entity_type"] == "test_entity"
    assert result["entity_id"] == "test_123"
    assert result["file_size_bytes"] > 0
    assert result["checksum"] is not None
    
    # Retrieve data
    filename = os.path.basename(result["file_path"])
    retrieved = vault_storage.retrieve(
        subfolder="ml_features",
        filename=filename
    )
    
    assert retrieved is not None
    assert retrieved["data"] == test_data
    assert retrieved["metadata"]["entity_type"] == "test_entity"


def test_retention_policy(vault_storage):
    """Test retention policy calculation"""
    # Raw data retention
    result = vault_storage.store(
        subfolder="audits",
        entity_type="audit_log",
        data={"log": "test"},
        is_summary=False
    )
    
    retention_until = datetime.fromisoformat(result["retention_until"])
    expected_retention = datetime.utcnow() + timedelta(days=365)
    
    # Allow 1 minute difference
    assert abs((retention_until - expected_retention).total_seconds()) < 60
    
    # Summary retention
    result = vault_storage.store(
        subfolder="audits",
        entity_type="audit_summary",
        data={"summary": "test"},
        is_summary=True
    )
    
    retention_until = datetime.fromisoformat(result["retention_until"])
    expected_retention = datetime.utcnow() + timedelta(days=365 * 5)
    
    # Allow 1 minute difference
    assert abs((retention_until - expected_retention).total_seconds()) < 60


def test_list_files(vault_storage):
    """Test listing files in subfolder"""
    # Store multiple files with different entity types
    vault_storage.store(
        subfolder="clips_metadata",
        entity_type="clip",
        data={"id": 1}
    )
    
    vault_storage.store(
        subfolder="clips_metadata",
        entity_type="campaign",
        data={"id": 2}
    )
    
    vault_storage.store(
        subfolder="clips_metadata",
        entity_type="analysis",
        data={"id": 3}
    )
    
    # List all files
    files = vault_storage.list_files(subfolder="clips_metadata")
    assert len(files) == 3, f"Expected 3 files, got {len(files)}: {files}"
    
    # List filtered by entity type
    files = vault_storage.list_files(
        subfolder="clips_metadata",
        entity_type="clip"
    )
    assert len(files) == 1, f"Expected 1 clip file, got {len(files)}"
    assert all("clip" in f for f in files)


def test_cleanup_expired(vault_storage):
    """Test cleanup of expired files"""
    # Store file with past retention date
    result = vault_storage.store(
        subfolder="orchestrator_runs",
        entity_type="test_run",
        data={"test": "data"}
    )
    
    # Manually modify retention date to past
    filename = os.path.basename(result["file_path"])
    file_path = vault_storage.config.get_local_path("orchestrator_runs/") / filename
    
    with open(file_path, 'r') as f:
        file_data = json.load(f)
    
    # Set retention to 1 day ago
    file_data["metadata"]["retention_until"] = (
        datetime.utcnow() - timedelta(days=1)
    ).isoformat()
    
    with open(file_path, 'w') as f:
        json.dump(file_data, f)
    
    # Run cleanup (dry run)
    report = vault_storage.cleanup_expired(dry_run=True)
    assert report["expired_files_count"] >= 1
    assert report["dry_run"] is True
    
    # File should still exist
    assert file_path.exists()
    
    # Run cleanup (actual)
    report = vault_storage.cleanup_expired(dry_run=False)
    assert report["expired_files_count"] >= 1
    assert report["dry_run"] is False
    
    # File should be deleted
    assert not file_path.exists()


def test_checksum_calculation(vault_storage):
    """Test checksum calculation is consistent"""
    data1 = {"a": 1, "b": 2}
    data2 = {"b": 2, "a": 1}  # Same data, different order
    
    checksum1 = vault_storage.calculate_checksum(data1)
    checksum2 = vault_storage.calculate_checksum(data2)
    
    # Should be identical (order-independent due to sort_keys)
    assert checksum1 == checksum2
    assert len(checksum1) == 64  # SHA-256 hex length


def test_invalid_subfolder(vault_storage):
    """Test error handling for invalid subfolder"""
    with pytest.raises(ValueError, match="Invalid subfolder"):
        vault_storage.store(
            subfolder="invalid_folder",
            entity_type="test",
            data={}
        )


def test_retrieve_nonexistent_file(vault_storage):
    """Test retrieving non-existent file returns None"""
    result = vault_storage.retrieve(
        subfolder="ml_features",
        filename="nonexistent_file.json"
    )
    assert result is None
