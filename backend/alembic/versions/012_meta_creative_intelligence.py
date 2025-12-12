"""Meta Creative Intelligence & Lifecycle System

Revision ID: 012_meta_creative_intelligence
Revises: 011_meta_ads_models
Create Date: 2025-11-27 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, TIMESTAMP

# revision identifiers, used by Alembic.
revision: str = '012_meta_creative_intelligence'
down_revision: Union[str, None] = '011_meta_ads_models'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Create 5 tables for Meta Creative Intelligence System:
    1. meta_creative_analysis - Visual analysis results (YOLO/CV)
    2. meta_creative_variant_generation - Generated variants metadata
    3. meta_publication_winner - Winner selections (performance-based)
    4. meta_thumbnail - Auto-generated thumbnails
    5. meta_creative_lifecycle - Fatigue detection + renewal actions
    """
    
    # 1. META CREATIVE ANALYSIS
    op.create_table(
        'meta_creative_analysis',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('video_asset_id', UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('mode', sa.String(20), nullable=False),  # "stub" or "live"
        
        # Detection results
        sa.Column('objects_detected', JSONB, nullable=True),  # List of ObjectDetection
        sa.Column('faces_detected', JSONB, nullable=True),    # List of FaceDetection
        sa.Column('texts_detected', JSONB, nullable=True),    # List of TextDetection
        
        # Scoring
        sa.Column('visual_scoring', JSONB, nullable=True),    # VisualScoring dict
        
        # Fragments
        sa.Column('fragments_extracted', JSONB, nullable=True),  # List of FragmentExtraction
        
        # Metrics
        sa.Column('total_objects', sa.Integer, nullable=False, default=0),
        sa.Column('total_faces', sa.Integer, nullable=False, default=0),
        sa.Column('total_texts', sa.Integer, nullable=False, default=0),
        sa.Column('total_fragments', sa.Integer, nullable=False, default=0),
        sa.Column('overall_score', sa.Float, nullable=True),
        
        # Processing
        sa.Column('processing_time_ms', sa.Integer, nullable=False),
        sa.Column('success', sa.Boolean, nullable=False, default=True),
        sa.Column('error_message', sa.Text, nullable=True),
        
        # Timestamps
        sa.Column('created_at', TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Indices for meta_creative_analysis
    op.create_index('idx_creative_analysis_video_created', 'meta_creative_analysis', ['video_asset_id', 'created_at'])
    op.create_index('idx_creative_analysis_overall_score', 'meta_creative_analysis', ['overall_score'])
    op.create_index('idx_creative_analysis_mode', 'meta_creative_analysis', ['mode'])
    
    # 2. META CREATIVE VARIANT GENERATION
    op.create_table(
        'meta_creative_variant_generation',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('video_asset_id', UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('analysis_id', UUID(as_uuid=True), nullable=True),  # FK to meta_creative_analysis
        sa.Column('mode', sa.String(20), nullable=False),
        
        # Configuration
        sa.Column('config', JSONB, nullable=False),  # VariantConfig dict
        
        # Results
        sa.Column('variants', JSONB, nullable=False),  # List of VariantMetadata
        
        # Metrics
        sa.Column('total_variants', sa.Integer, nullable=False, default=0),
        sa.Column('variants_with_reorder', sa.Integer, nullable=False, default=0),
        sa.Column('variants_with_subtitles', sa.Integer, nullable=False, default=0),
        sa.Column('variants_with_overlays', sa.Integer, nullable=False, default=0),
        sa.Column('variants_with_music', sa.Integer, nullable=False, default=0),
        sa.Column('variants_with_duration_change', sa.Integer, nullable=False, default=0),
        
        # Processing
        sa.Column('processing_time_ms', sa.Integer, nullable=False),
        sa.Column('success', sa.Boolean, nullable=False, default=True),
        sa.Column('error_message', sa.Text, nullable=True),
        
        # Timestamps
        sa.Column('created_at', TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # FK constraint
    op.create_foreign_key(
        'fk_variant_gen_analysis',
        'meta_creative_variant_generation', 'meta_creative_analysis',
        ['analysis_id'], ['id'],
        ondelete='SET NULL'
    )
    
    # Indices for meta_creative_variant_generation
    op.create_index('idx_variant_gen_video_created', 'meta_creative_variant_generation', ['video_asset_id', 'created_at'])
    op.create_index('idx_variant_gen_analysis', 'meta_creative_variant_generation', ['analysis_id'])
    
    # 3. META PUBLICATION WINNER
    op.create_table(
        'meta_publication_winner',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('campaign_id', UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('winner_asset_id', UUID(as_uuid=True), nullable=False),
        sa.Column('runner_up_asset_id', UUID(as_uuid=True), nullable=True),
        
        # Selection criteria
        sa.Column('criteria_weights', JSONB, nullable=False),  # {"roas": 0.40, "ctr": 0.25, ...}
        sa.Column('min_impressions', sa.Integer, nullable=False),
        
        # Scores
        sa.Column('winner_score', sa.Float, nullable=False),
        sa.Column('runner_up_score', sa.Float, nullable=True),
        sa.Column('all_scores', JSONB, nullable=False),  # {asset_id: score, ...}
        
        # Performance summary
        sa.Column('performance_summary', JSONB, nullable=True),  # Dict with metrics
        sa.Column('reasoning', sa.Text, nullable=True),
        
        # Publication status
        sa.Column('published', sa.Boolean, nullable=False, default=False),
        sa.Column('published_at', TIMESTAMP(timezone=True), nullable=True),
        
        # Timestamps
        sa.Column('created_at', TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Indices for meta_publication_winner
    op.create_index('idx_winner_campaign_created', 'meta_publication_winner', ['campaign_id', 'created_at'])
    op.create_index('idx_winner_asset', 'meta_publication_winner', ['winner_asset_id'])
    op.create_index('idx_winner_published', 'meta_publication_winner', ['published', 'published_at'])
    
    # 4. META THUMBNAIL
    op.create_table(
        'meta_thumbnail',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('video_asset_id', UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('analysis_id', UUID(as_uuid=True), nullable=True),  # FK to meta_creative_analysis
        sa.Column('mode', sa.String(20), nullable=False),
        
        # Selected thumbnail
        sa.Column('selected_frame', sa.Integer, nullable=False),
        sa.Column('selected_timestamp', sa.Float, nullable=False),
        sa.Column('thumbnail_url', sa.String(500), nullable=True),
        
        # Candidates
        sa.Column('candidates', JSONB, nullable=True),  # List of ThumbnailCandidate
        
        # Preferences
        sa.Column('prefer_faces', sa.Boolean, nullable=False, default=True),
        sa.Column('prefer_action', sa.Boolean, nullable=False, default=True),
        sa.Column('avoid_text', sa.Boolean, nullable=False, default=False),
        
        # Reasoning
        sa.Column('reasoning', sa.Text, nullable=True),
        
        # Timestamps
        sa.Column('created_at', TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # FK constraint
    op.create_foreign_key(
        'fk_thumbnail_analysis',
        'meta_thumbnail', 'meta_creative_analysis',
        ['analysis_id'], ['id'],
        ondelete='SET NULL'
    )
    
    # Indices for meta_thumbnail
    op.create_index('idx_thumbnail_video_created', 'meta_thumbnail', ['video_asset_id', 'created_at'])
    op.create_index('idx_thumbnail_analysis', 'meta_thumbnail', ['analysis_id'])
    
    # 5. META CREATIVE LIFECYCLE
    op.create_table(
        'meta_creative_lifecycle',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('creative_id', UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('action', sa.String(50), nullable=False),  # "fatigue_check" or "renewal"
        sa.Column('strategy', sa.String(50), nullable=True),  # "generate_variant", "replace_entirely", "refresh_targeting"
        
        # Fatigue detection
        sa.Column('is_fatigued', sa.Boolean, nullable=False, default=False),
        sa.Column('fatigue_score', sa.Float, nullable=True),  # 0-100
        sa.Column('metrics_trend', JSONB, nullable=True),  # Dict with baseline vs recent metrics
        
        # Renewal
        sa.Column('new_creative_id', UUID(as_uuid=True), nullable=True),
        sa.Column('actions_taken', JSONB, nullable=True),  # List of actions
        
        # Lifecycle metrics
        sa.Column('days_active', sa.Integer, nullable=True),
        sa.Column('impressions_total', sa.Integer, nullable=True),
        
        # Result
        sa.Column('success', sa.Boolean, nullable=False, default=True),
        sa.Column('recommendation', sa.Text, nullable=True),
        sa.Column('message', sa.Text, nullable=True),
        sa.Column('details', JSONB, nullable=True),
        
        # Timestamps
        sa.Column('created_at', TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Indices for meta_creative_lifecycle
    op.create_index('idx_lifecycle_creative_action', 'meta_creative_lifecycle', ['creative_id', 'action'])
    op.create_index('idx_lifecycle_fatigued', 'meta_creative_lifecycle', ['is_fatigued', 'fatigue_score'])
    op.create_index('idx_lifecycle_created', 'meta_creative_lifecycle', ['created_at'])


def downgrade() -> None:
    """Drop all Meta Creative Intelligence tables"""
    
    # Drop tables in reverse order (respecting FK constraints)
    op.drop_table('meta_creative_lifecycle')
    op.drop_table('meta_thumbnail')
    op.drop_table('meta_publication_winner')
    op.drop_table('meta_creative_variant_generation')
    op.drop_table('meta_creative_analysis')
