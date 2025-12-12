"""Memory Vault Foundations Migration (Phase 1)

Revision ID: 019
Revises: 018
Create Date: 2025-11-28

Creates:
- ml_features: Machine learning features storage with JSONB
- memory_vault_index: Index for Google Drive storage tracking
- acl_permissions: Access control matrix
- backup_metadata: Backup tracking
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers
revision = '019'
down_revision = '018'
branch_labels = None
depends_on = None

def upgrade():
    """Create Memory Vault and ACL infrastructure tables"""
    
    # 1. Create ml_features table (TAREA A)
    op.create_table(
        'ml_features',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('feature_hash', JSONB, nullable=False, comment='ML feature vectors and metadata'),
        sa.Column('source', sa.Text, nullable=False, comment='Source of the features (model name, extraction method)'),
        sa.Column('version', sa.Integer, nullable=False, server_default='1', comment='Feature schema version'),
        sa.Column('timestamp', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('run_id', UUID(as_uuid=True), nullable=True, comment='Orchestrator run ID'),
        sa.Column('entity_type', sa.String(50), nullable=True, comment='campaign, clip, creative, etc'),
        sa.Column('entity_id', sa.String(100), nullable=True, comment='External entity ID'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    
    # Indices for ml_features
    op.create_index('idx_ml_feature_hash', 'ml_features', ['feature_hash'], postgresql_using='gin')
    op.create_index('idx_run_id_timestamp', 'ml_features', ['run_id', 'timestamp'])
    op.create_index('idx_ml_entity', 'ml_features', ['entity_type', 'entity_id'])
    
    # 2. Create memory_vault_index table
    op.create_table(
        'memory_vault_index',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('entity_type', sa.String(50), nullable=False, comment='ml_features, audits, campaign_history, etc'),
        sa.Column('entity_id', sa.String(100), nullable=False),
        sa.Column('gdrive_path', sa.Text, nullable=False, comment='Full path in Google Drive'),
        sa.Column('gdrive_file_id', sa.String(100), nullable=True, comment='Google Drive file ID'),
        sa.Column('local_path', sa.Text, nullable=True, comment='Local stub path for development'),
        sa.Column('feature_hash', JSONB, nullable=True, comment='Quick access to feature metadata'),
        sa.Column('source', sa.String(50), nullable=True),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.Column('timestamp', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('run_id', UUID(as_uuid=True), nullable=True),
        sa.Column('metadata', JSONB, nullable=True, comment='Additional metadata'),
        sa.Column('retention_until', sa.TIMESTAMP(timezone=True), nullable=True, comment='Retention expiry date'),
        sa.Column('is_summary', sa.Boolean, nullable=False, server_default='false', comment='Summary vs raw data'),
        sa.Column('encrypted', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('file_size_bytes', sa.BigInteger, nullable=True),
        sa.Column('checksum_sha256', sa.String(64), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    
    # Indices for memory_vault_index
    op.create_index('idx_mv_feature_hash', 'memory_vault_index', ['feature_hash'], postgresql_using='gin')
    op.create_index('idx_mv_run_id_timestamp', 'memory_vault_index', ['run_id', 'timestamp'])
    op.create_index('idx_mv_entity_type', 'memory_vault_index', ['entity_type', 'entity_id'])
    op.create_index('idx_mv_gdrive_path', 'memory_vault_index', ['gdrive_path'], postgresql_using='hash')
    op.create_index('idx_mv_retention', 'memory_vault_index', ['retention_until'])
    
    # 3. Create acl_permissions table (TAREA B)
    op.create_table(
        'acl_permissions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('role', sa.String(50), nullable=False, comment='orchestrator, worker, auditor, dashboard, devops'),
        sa.Column('resource', sa.String(50), nullable=False, comment='campaign_history, ml_features, audits, etc'),
        sa.Column('permission', sa.String(10), nullable=False, comment='r, w, r/w, -'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.UniqueConstraint('role', 'resource', name='uq_role_resource'),
    )
    
    # Seed ACL matrix data
    op.execute("""
        INSERT INTO acl_permissions (role, resource, permission) VALUES
        -- Orchestrator permissions
        ('orchestrator', 'campaign_history', 'r/w'),
        ('orchestrator', 'ml_features', 'r/w'),
        ('orchestrator', 'audits', 'r'),
        ('orchestrator', 'orchestrator_runs', 'r/w'),
        ('orchestrator', 'clips_metadata', 'r/w'),
        ('orchestrator', 'memory_vault', 'r/w'),
        ('orchestrator', 'backups', '-'),
        ('orchestrator', 'config', 'r'),
        
        -- Worker permissions
        ('worker', 'campaign_history', 'r'),
        ('worker', 'ml_features', 'r/w'),
        ('worker', 'audits', '-'),
        ('worker', 'orchestrator_runs', '-'),
        ('worker', 'clips_metadata', 'r/w'),
        ('worker', 'memory_vault', 'r'),
        ('worker', 'backups', '-'),
        ('worker', 'config', 'r'),
        
        -- Auditor permissions
        ('auditor', 'campaign_history', 'r'),
        ('auditor', 'ml_features', 'r'),
        ('auditor', 'audits', 'r/w'),
        ('auditor', 'orchestrator_runs', 'r'),
        ('auditor', 'clips_metadata', 'r'),
        ('auditor', 'memory_vault', 'r'),
        ('auditor', 'backups', '-'),
        ('auditor', 'config', '-'),
        
        -- Dashboard permissions
        ('dashboard', 'campaign_history', 'r'),
        ('dashboard', 'ml_features', 'r'),
        ('dashboard', 'audits', '-'),
        ('dashboard', 'orchestrator_runs', '-'),
        ('dashboard', 'clips_metadata', 'r'),
        ('dashboard', 'memory_vault', 'r'),
        ('dashboard', 'backups', '-'),
        ('dashboard', 'config', 'r'),
        
        -- DevOps permissions (full access)
        ('devops', 'campaign_history', 'r'),
        ('devops', 'ml_features', 'r'),
        ('devops', 'audits', 'r/w'),
        ('devops', 'orchestrator_runs', 'r'),
        ('devops', 'clips_metadata', 'r'),
        ('devops', 'memory_vault', 'r'),
        ('devops', 'backups', 'r/w'),
        ('devops', 'config', 'r/w')
    """)
    
    # 4. Create backup_metadata table (TAREA D)
    op.create_table(
        'backup_metadata',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('backup_type', sa.String(50), nullable=False, comment='postgres_daily, vault_monthly, manual'),
        sa.Column('backup_path', sa.Text, nullable=False),
        sa.Column('file_size_bytes', sa.BigInteger, nullable=True),
        sa.Column('checksum_sha256', sa.String(64), nullable=True),
        sa.Column('encrypted', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('retention_until', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, comment='pending, completed, failed, expired'),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('restore_tested_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('restore_test_status', sa.String(20), nullable=True, comment='passed, failed, not_tested'),
        sa.Column('metadata', JSONB, nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('completed_at', sa.TIMESTAMP(timezone=True), nullable=True),
    )
    
    # Indices for backup_metadata
    op.create_index('idx_backup_type_created', 'backup_metadata', ['backup_type', 'created_at'])
    op.create_index('idx_backup_retention', 'backup_metadata', ['retention_until'])
    op.create_index('idx_backup_status', 'backup_metadata', ['status'])


def downgrade():
    """Drop Memory Vault and ACL infrastructure tables"""
    
    # Drop in reverse order
    op.drop_index('idx_backup_status', table_name='backup_metadata')
    op.drop_index('idx_backup_retention', table_name='backup_metadata')
    op.drop_index('idx_backup_type_created', table_name='backup_metadata')
    op.drop_table('backup_metadata')
    
    op.drop_table('acl_permissions')
    
    op.drop_index('idx_mv_retention', table_name='memory_vault_index')
    op.drop_index('idx_mv_gdrive_path', table_name='memory_vault_index')
    op.drop_index('idx_mv_entity_type', table_name='memory_vault_index')
    op.drop_index('idx_mv_run_id_timestamp', table_name='memory_vault_index')
    op.drop_index('idx_mv_feature_hash', table_name='memory_vault_index')
    op.drop_table('memory_vault_index')
    
    op.drop_index('idx_ml_entity', table_name='ml_features')
    op.drop_index('idx_run_id_timestamp', table_name='ml_features')
    op.drop_index('idx_ml_feature_hash', table_name='ml_features')
    op.drop_table('ml_features')
