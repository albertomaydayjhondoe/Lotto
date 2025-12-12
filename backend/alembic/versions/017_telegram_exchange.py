"""Create telegram_exchange_bot tables

Revision ID: 017_telegram_exchange
Revises: 016_meta_creative_optimizer
Create Date: 2025-12-08 (Sprint 7B)

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '017_telegram_exchange'
down_revision = '016_meta_creative_optimizer'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create tables for Telegram Exchange Bot Sprint 7B."""
    
    # 1. Exchange Accounts (Non-official accounts pool)
    op.create_table(
        'exchange_accounts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('account_id', sa.String(100), nullable=False, unique=True),
        sa.Column('platform', sa.String(20), nullable=False),  # youtube, instagram, tiktok
        sa.Column('username', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=True),
        
        # Role
        sa.Column('role', sa.String(20), nullable=False, default='exchange'),  # support, exchange, fanpage
        
        # Status
        sa.Column('status', sa.String(20), nullable=False, default='active'),  # active, warming_up, cooldown, blocked, suspended
        sa.Column('health', sa.String(20), nullable=False, default='healthy'),  # healthy, degraded, unhealthy
        
        # Metrics
        sa.Column('total_interactions', sa.Integer(), default=0),
        sa.Column('successful_interactions', sa.Integer(), default=0),
        sa.Column('failed_interactions', sa.Integer(), default=0),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        
        # Rate limits
        sa.Column('interactions_today', sa.Integer(), default=0),
        sa.Column('interactions_this_hour', sa.Integer(), default=0),
        
        # Security
        sa.Column('last_proxy_used', sa.String(500), nullable=True),
        sa.Column('last_fingerprint_id', sa.String(100), nullable=True),
        
        # Metadata
        sa.Column('metadata', postgresql.JSONB(), default={}),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_exchange_accounts_platform', 'platform'),
        sa.Index('idx_exchange_accounts_status', 'status'),
        sa.Index('idx_exchange_accounts_health', 'health'),
    )
    
    # 2. Exchange Interactions Executed (Log completo)
    op.create_table(
        'exchange_interactions_executed',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('interaction_id', sa.String(100), nullable=False, unique=True),
        sa.Column('executed_at', sa.DateTime(timezone=True), nullable=False),
        
        # Contexto
        sa.Column('interaction_type', sa.String(50), nullable=False),  # youtube_like, instagram_comment, etc.
        sa.Column('platform', sa.String(20), nullable=False),
        sa.Column('target_url', sa.String(1000), nullable=False),
        
        # Cuenta usada
        sa.Column('account_id', sa.String(100), nullable=False),
        sa.Column('account_username', sa.String(255), nullable=False),
        
        # Usuario objetivo
        sa.Column('target_user_id', sa.String(100), nullable=True),
        sa.Column('target_username', sa.String(255), nullable=True),
        
        # Origen (Telegram)
        sa.Column('telegram_group_id', sa.String(100), nullable=True),
        sa.Column('telegram_group_name', sa.String(255), nullable=True),
        
        # Resultado
        sa.Column('status', sa.String(20), nullable=False),  # success, failed, retrying, aborted
        sa.Column('execution_time_seconds', sa.Float(), default=0.0),
        sa.Column('error', sa.Text(), nullable=True),
        
        # Seguridad
        sa.Column('vpn_active', sa.Boolean(), default=False),
        sa.Column('proxy_used', sa.String(500), nullable=True),
        sa.Column('fingerprint_id', sa.String(100), nullable=True),
        
        # Metadata
        sa.Column('metadata', postgresql.JSONB(), default={}),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['account_id'], ['exchange_accounts.account_id'], ondelete='CASCADE'),
        sa.Index('idx_interactions_executed_at', 'executed_at'),
        sa.Index('idx_interactions_platform', 'platform'),
        sa.Index('idx_interactions_status', 'status'),
        sa.Index('idx_interactions_group', 'telegram_group_id'),
        sa.Index('idx_interactions_target_user', 'target_user_id'),
    )
    
    # 3. Exchange Metrics (Agregados ROI)
    op.create_table(
        'exchange_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('metric_id', sa.String(100), nullable=False, unique=True),
        
        # Entidad
        sa.Column('entity_id', sa.String(100), nullable=False),  # group_id, user_id, or platform
        sa.Column('entity_type', sa.String(20), nullable=False),  # group, user, platform
        sa.Column('entity_name', sa.String(255), nullable=True),
        
        # Período
        sa.Column('period', sa.String(20), nullable=False),  # daily, weekly, monthly, all_time
        sa.Column('period_start', sa.Date(), nullable=False),
        sa.Column('period_end', sa.Date(), nullable=False),
        
        # Interacciones
        sa.Column('total_interactions', sa.Integer(), default=0),
        sa.Column('successful_interactions', sa.Integer(), default=0),
        sa.Column('failed_interactions', sa.Integer(), default=0),
        
        # Breakdown
        sa.Column('likes_given', sa.Integer(), default=0),
        sa.Column('comments_given', sa.Integer(), default=0),
        sa.Column('subscribes_given', sa.Integer(), default=0),
        
        # Reciprocidad
        sa.Column('support_given', sa.Integer(), default=0),
        sa.Column('support_received', sa.Integer(), default=0),
        
        # ROI
        sa.Column('roi_ratio', sa.Float(), default=0.0),  # support_received / support_given
        sa.Column('success_rate', sa.Float(), default=0.0),  # successful / total
        
        # Costos
        sa.Column('estimated_cost_eur', sa.Float(), default=0.0),
        
        # Metadata
        sa.Column('metadata', postgresql.JSONB(), default={}),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_metrics_entity', 'entity_id', 'entity_type'),
        sa.Index('idx_metrics_period', 'period', 'period_start'),
        sa.Index('idx_metrics_roi', 'roi_ratio'),
    )
    
    # 4. Telegram Groups (Tracking de grupos)
    op.create_table(
        'telegram_groups',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.String(100), nullable=False, unique=True),
        sa.Column('group_name', sa.String(255), nullable=False),
        sa.Column('group_username', sa.String(255), nullable=True),
        
        # Estado
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_monitored', sa.Boolean(), default=True),
        
        # Métricas
        sa.Column('members_count', sa.Integer(), nullable=True),
        sa.Column('message_count', sa.Integer(), default=0),
        sa.Column('exchange_count', sa.Integer(), default=0),
        
        # Eficiencia
        sa.Column('support_given', sa.Integer(), default=0),
        sa.Column('support_received', sa.Integer(), default=0),
        sa.Column('efficiency_ratio', sa.Float(), default=0.0),  # support_received / support_given
        
        # Metadata
        sa.Column('metadata', postgresql.JSONB(), default={}),
        
        # Timestamps
        sa.Column('joined_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('last_message_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_groups_active', 'is_active'),
        sa.Index('idx_groups_monitored', 'is_monitored'),
        sa.Index('idx_groups_efficiency', 'efficiency_ratio'),
    )
    
    # 5. Our Content (Contenido propio a promocionar)
    op.create_table(
        'our_content',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('content_id', sa.String(100), nullable=False, unique=True),
        sa.Column('platform', sa.String(20), nullable=False),
        sa.Column('content_url', sa.String(1000), nullable=False),
        
        # Metadata
        sa.Column('title', sa.String(500), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        
        # Estado
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_priority', sa.Boolean(), default=False),
        sa.Column('priority_level', sa.Integer(), default=3),  # 1=CRITICAL, 2=HIGH, 3=MEDIUM, 4=LOW
        
        # Métricas objetivo
        sa.Column('target_likes', sa.Integer(), nullable=True),
        sa.Column('target_comments', sa.Integer(), nullable=True),
        sa.Column('target_subscribes', sa.Integer(), nullable=True),
        
        # Métricas actuales
        sa.Column('current_likes', sa.Integer(), default=0),
        sa.Column('current_comments', sa.Integer(), default=0),
        sa.Column('current_subscribes', sa.Integer(), default=0),
        
        # Metadata
        sa.Column('metadata', postgresql.JSONB(), default={}),
        
        # Timestamps
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_content_platform', 'platform'),
        sa.Index('idx_content_active', 'is_active'),
        sa.Index('idx_content_priority', 'priority_level'),
        sa.Index('idx_content_published', 'published_at'),
    )


def downgrade() -> None:
    """Drop Telegram Exchange Bot tables."""
    op.drop_table('our_content')
    op.drop_table('telegram_groups')
    op.drop_table('exchange_metrics')
    op.drop_table('exchange_interactions_executed')
    op.drop_table('exchange_accounts')
