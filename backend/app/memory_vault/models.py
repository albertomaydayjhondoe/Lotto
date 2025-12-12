"""
Memory Vault Database Models

SQLAlchemy models for Memory Vault tracking
"""
from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy import Column, String, Integer, BigInteger, Boolean, Text, TIMESTAMP, Index
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class MLFeature(Base):
    """Machine Learning Features Storage"""
    __tablename__ = "ml_features"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    feature_hash = Column(JSONB, nullable=False, comment="ML feature vectors and metadata")
    source = Column(Text, nullable=False, comment="Source of features (model name, extraction method)")
    version = Column(Integer, nullable=False, default=1, comment="Feature schema version")
    timestamp = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow)
    run_id = Column(PGUUID(as_uuid=True), nullable=True, comment="Orchestrator run ID")
    entity_type = Column(String(50), nullable=True, comment="campaign, clip, creative, etc")
    entity_id = Column(String(100), nullable=True, comment="External entity ID")
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_ml_feature_hash', 'feature_hash', postgresql_using='gin'),
        Index('idx_run_id_timestamp', 'run_id', 'timestamp'),
        Index('idx_ml_entity', 'entity_type', 'entity_id'),
    )


class MemoryVaultIndex(Base):
    """Index for Google Drive Memory Vault storage"""
    __tablename__ = "memory_vault_index"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    entity_type = Column(String(50), nullable=False, comment="ml_features, audits, campaign_history, etc")
    entity_id = Column(String(100), nullable=False)
    gdrive_path = Column(Text, nullable=False, comment="Full path in Google Drive")
    gdrive_file_id = Column(String(100), nullable=True, comment="Google Drive file ID")
    local_path = Column(Text, nullable=True, comment="Local stub path for development")
    feature_hash = Column(JSONB, nullable=True, comment="Quick access to feature metadata")
    source = Column(String(50), nullable=True)
    version = Column(Integer, nullable=False, default=1)
    timestamp = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow)
    run_id = Column(PGUUID(as_uuid=True), nullable=True)
    metadata = Column(JSONB, nullable=True, comment="Additional metadata")
    retention_until = Column(TIMESTAMP(timezone=True), nullable=True, comment="Retention expiry date")
    is_summary = Column(Boolean, nullable=False, default=False, comment="Summary vs raw data")
    encrypted = Column(Boolean, nullable=False, default=True)
    file_size_bytes = Column(BigInteger, nullable=True)
    checksum_sha256 = Column(String(64), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_mv_feature_hash', 'feature_hash', postgresql_using='gin'),
        Index('idx_mv_run_id_timestamp', 'run_id', 'timestamp'),
        Index('idx_mv_entity_type', 'entity_type', 'entity_id'),
        Index('idx_mv_gdrive_path', 'gdrive_path', postgresql_using='hash'),
        Index('idx_mv_retention', 'retention_until'),
    )


class ACLPermission(Base):
    """Access Control List Permissions"""
    __tablename__ = "acl_permissions"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    role = Column(String(50), nullable=False, comment="orchestrator, worker, auditor, dashboard, devops")
    resource = Column(String(50), nullable=False, comment="campaign_history, ml_features, audits, etc")
    permission = Column(String(10), nullable=False, comment="r, w, r/w, -")
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow)
    
    __table_args__ = (
        Index('uq_role_resource', 'role', 'resource', unique=True),
    )


class BackupMetadata(Base):
    """Backup tracking metadata"""
    __tablename__ = "backup_metadata"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    backup_type = Column(String(50), nullable=False, comment="postgres_daily, vault_monthly, manual")
    backup_path = Column(Text, nullable=False)
    file_size_bytes = Column(BigInteger, nullable=True)
    checksum_sha256 = Column(String(64), nullable=True)
    encrypted = Column(Boolean, nullable=False, default=True)
    retention_until = Column(TIMESTAMP(timezone=True), nullable=True)
    status = Column(String(20), nullable=False, comment="pending, completed, failed, expired")
    error_message = Column(Text, nullable=True)
    restore_tested_at = Column(TIMESTAMP(timezone=True), nullable=True)
    restore_test_status = Column(String(20), nullable=True, comment="passed, failed, not_tested")
    metadata = Column(JSONB, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow)
    completed_at = Column(TIMESTAMP(timezone=True), nullable=True)
    
    __table_args__ = (
        Index('idx_backup_type_created', 'backup_type', 'created_at'),
        Index('idx_backup_retention', 'retention_until'),
        Index('idx_backup_status', 'status'),
    )
