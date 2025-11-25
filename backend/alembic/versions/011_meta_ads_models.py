"""meta_ads_models

Revision ID: 011_meta_ads_models
Revises: 010_iam_layer
Create Date: 2024-11-24

PASO 10.1: Meta Ads Model Layer

Creates complete database schema for Meta (Facebook) Ads integration:
- meta_accounts: Links Meta Business accounts to social_accounts
- meta_pixels: Tracks Meta Pixel IDs for conversion tracking
- meta_creatives: Stores creative assets (videos/images) uploaded to Meta
- meta_campaigns: Top-level campaign structure
- meta_adsets: Mid-level adset structure with targeting
- meta_ads: Individual ads linking creatives to campaigns
- meta_ad_insights: Time-series performance metrics

Features:
- Full hierarchy: Campaign → Adset → Ad → Insights
- Human control flags (approval, review)
- Content restrictions (genre, subgenre, age)
- UTM tracking parameters
- Video performance metrics
- ROAS and conversion tracking
- Optimized indexes for queries
- SQLite + PostgreSQL compatible
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from uuid import uuid4

# revision identifiers, used by Alembic
revision = '011_meta_ads_models'
down_revision = '010_iam_layer'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create Meta Ads tables."""
    
    # ========================================================================
    # 1. META ACCOUNTS
    # ========================================================================
    op.create_table(
        'meta_accounts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid4),
        sa.Column('social_account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('ad_account_id', sa.String(255), nullable=False),
        sa.Column('business_id', sa.String(255), nullable=True),
        sa.Column('account_name', sa.String(255), nullable=True),
        sa.Column('currency', sa.String(10), nullable=True),
        sa.Column('timezone', sa.String(50), nullable=True),
        sa.Column('is_active', sa.Integer, nullable=False, default=1),
        sa.Column('account_status', sa.String(50), nullable=True),
        sa.Column('spend_cap', sa.Float, nullable=True),
        sa.Column('amount_spent', sa.Float, nullable=True),
        sa.Column('extra_metadata', sa.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        
        sa.ForeignKeyConstraint(['social_account_id'], ['social_accounts.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('social_account_id', name='uq_meta_accounts_social_account'),
        sa.UniqueConstraint('ad_account_id', name='uq_meta_accounts_ad_account_id'),
    )
    
    # Indexes for meta_accounts
    op.create_index('ix_meta_accounts_ad_account_id', 'meta_accounts', ['ad_account_id'])
    op.create_index('ix_meta_accounts_business_id', 'meta_accounts', ['business_id'])
    
    # ========================================================================
    # 2. META PIXELS
    # ========================================================================
    op.create_table(
        'meta_pixels',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid4),
        sa.Column('meta_account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('pixel_id', sa.String(255), nullable=False),
        sa.Column('pixel_name', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Integer, nullable=False, default=1),
        sa.Column('extra_metadata', sa.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        
        sa.ForeignKeyConstraint(['meta_account_id'], ['meta_accounts.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('pixel_id', name='uq_meta_pixels_pixel_id'),
    )
    
    # Indexes for meta_pixels
    op.create_index('ix_meta_pixels_meta_account_id', 'meta_pixels', ['meta_account_id'])
    op.create_index('ix_meta_pixels_pixel_id', 'meta_pixels', ['pixel_id'])
    
    # ========================================================================
    # 3. META CREATIVES
    # ========================================================================
    op.create_table(
        'meta_creatives',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid4),
        sa.Column('video_asset_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('creative_id', sa.String(255), nullable=False),
        sa.Column('creative_name', sa.String(255), nullable=True),
        sa.Column('creative_type', sa.String(50), nullable=False),
        sa.Column('video_url', sa.Text, nullable=True),
        sa.Column('thumbnail_url', sa.Text, nullable=True),
        sa.Column('duration_ms', sa.Integer, nullable=True),
        sa.Column('status', sa.String(50), nullable=False, default='active'),
        
        # Human control
        sa.Column('is_approved', sa.Integer, nullable=False, default=0),
        sa.Column('is_reviewed', sa.Integer, nullable=False, default=0),
        sa.Column('reviewed_by', sa.String(255), nullable=True),
        sa.Column('reviewed_at', sa.DateTime, nullable=True),
        
        # Content restrictions
        sa.Column('genre', sa.String(100), nullable=True),
        sa.Column('subgenre', sa.String(100), nullable=True),
        sa.Column('age_restriction', sa.String(20), nullable=True),
        
        sa.Column('extra_metadata', sa.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        
        sa.ForeignKeyConstraint(['video_asset_id'], ['video_assets.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('creative_id', name='uq_meta_creatives_creative_id'),
    )
    
    # Indexes for meta_creatives
    op.create_index('ix_meta_creatives_video_asset_id', 'meta_creatives', ['video_asset_id'])
    op.create_index('ix_meta_creatives_creative_id', 'meta_creatives', ['creative_id'])
    op.create_index('ix_meta_creatives_created_at', 'meta_creatives', ['created_at'])
    op.create_index('ix_meta_creatives_status', 'meta_creatives', ['status'])
    
    # ========================================================================
    # 4. META CAMPAIGNS
    # ========================================================================
    op.create_table(
        'meta_campaigns',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid4),
        sa.Column('meta_account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('campaign_id', sa.String(255), nullable=False),
        sa.Column('campaign_name', sa.String(255), nullable=False),
        sa.Column('objective', sa.String(100), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, default='PAUSED'),
        
        # Budget
        sa.Column('daily_budget', sa.Float, nullable=True),
        sa.Column('lifetime_budget', sa.Float, nullable=True),
        sa.Column('budget_remaining', sa.Float, nullable=True),
        
        # Schedule
        sa.Column('start_time', sa.DateTime, nullable=True),
        sa.Column('stop_time', sa.DateTime, nullable=True),
        
        # Human control
        sa.Column('requires_approval', sa.Integer, nullable=False, default=1),
        sa.Column('is_approved', sa.Integer, nullable=False, default=0),
        sa.Column('approved_by', sa.String(255), nullable=True),
        sa.Column('approved_at', sa.DateTime, nullable=True),
        
        # UTM tracking
        sa.Column('utm_source', sa.String(100), nullable=True),
        sa.Column('utm_medium', sa.String(100), nullable=True),
        sa.Column('utm_campaign', sa.String(255), nullable=True),
        sa.Column('utm_content', sa.String(255), nullable=True),
        
        sa.Column('extra_metadata', sa.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        
        sa.ForeignKeyConstraint(['meta_account_id'], ['meta_accounts.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('campaign_id', name='uq_meta_campaigns_campaign_id'),
    )
    
    # Indexes for meta_campaigns
    op.create_index('ix_meta_campaigns_meta_account_id', 'meta_campaigns', ['meta_account_id'])
    op.create_index('ix_meta_campaigns_campaign_id', 'meta_campaigns', ['campaign_id'])
    op.create_index('ix_meta_campaigns_status', 'meta_campaigns', ['status'])
    op.create_index('ix_meta_campaigns_created_at', 'meta_campaigns', ['created_at'])
    
    # ========================================================================
    # 5. META ADSETS
    # ========================================================================
    op.create_table(
        'meta_adsets',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid4),
        sa.Column('campaign_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('adset_id', sa.String(255), nullable=False),
        sa.Column('adset_name', sa.String(255), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, default='PAUSED'),
        
        # Budget
        sa.Column('daily_budget', sa.Float, nullable=True),
        sa.Column('lifetime_budget', sa.Float, nullable=True),
        sa.Column('bid_amount', sa.Float, nullable=True),
        sa.Column('bid_strategy', sa.String(50), nullable=True),
        
        # Targeting
        sa.Column('targeting', sa.JSON, nullable=True),
        sa.Column('age_min', sa.Integer, nullable=True),
        sa.Column('age_max', sa.Integer, nullable=True),
        sa.Column('gender', sa.String(20), nullable=True),
        sa.Column('locations', sa.JSON, nullable=True),
        sa.Column('interests', sa.JSON, nullable=True),
        
        # Placement
        sa.Column('placements', sa.JSON, nullable=True),
        
        # Schedule
        sa.Column('start_time', sa.DateTime, nullable=True),
        sa.Column('end_time', sa.DateTime, nullable=True),
        
        # Optimization
        sa.Column('optimization_goal', sa.String(100), nullable=True),
        sa.Column('billing_event', sa.String(50), nullable=True),
        
        sa.Column('extra_metadata', sa.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        
        sa.ForeignKeyConstraint(['campaign_id'], ['meta_campaigns.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('adset_id', name='uq_meta_adsets_adset_id'),
    )
    
    # Indexes for meta_adsets
    op.create_index('ix_meta_adsets_campaign_id', 'meta_adsets', ['campaign_id'])
    op.create_index('ix_meta_adsets_adset_id', 'meta_adsets', ['adset_id'])
    op.create_index('ix_meta_adsets_status', 'meta_adsets', ['status'])
    op.create_index('ix_meta_adsets_created_at', 'meta_adsets', ['created_at'])
    
    # ========================================================================
    # 6. META ADS
    # ========================================================================
    op.create_table(
        'meta_ads',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid4),
        sa.Column('adset_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('creative_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('ad_id', sa.String(255), nullable=False),
        sa.Column('ad_name', sa.String(255), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, default='PAUSED'),
        
        # Ad copy
        sa.Column('headline', sa.String(500), nullable=True),
        sa.Column('primary_text', sa.Text, nullable=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('call_to_action', sa.String(50), nullable=True),
        
        # Landing page
        sa.Column('link_url', sa.Text, nullable=True),
        sa.Column('display_link', sa.String(255), nullable=True),
        
        # Pixel tracking
        sa.Column('pixel_id', sa.String(255), nullable=True),
        
        # Human review
        sa.Column('is_reviewed', sa.Integer, nullable=False, default=0),
        sa.Column('reviewed_by', sa.String(255), nullable=True),
        sa.Column('reviewed_at', sa.DateTime, nullable=True),
        sa.Column('review_notes', sa.Text, nullable=True),
        
        sa.Column('extra_metadata', sa.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        
        sa.ForeignKeyConstraint(['adset_id'], ['meta_adsets.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['creative_id'], ['meta_creatives.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('ad_id', name='uq_meta_ads_ad_id'),
    )
    
    # Indexes for meta_ads
    op.create_index('ix_meta_ads_adset_id', 'meta_ads', ['adset_id'])
    op.create_index('ix_meta_ads_creative_id', 'meta_ads', ['creative_id'])
    op.create_index('ix_meta_ads_ad_id', 'meta_ads', ['ad_id'])
    op.create_index('ix_meta_ads_status', 'meta_ads', ['status'])
    op.create_index('ix_meta_ads_pixel_id', 'meta_ads', ['pixel_id'])
    op.create_index('ix_meta_ads_created_at', 'meta_ads', ['created_at'])
    
    # ========================================================================
    # 7. META AD INSIGHTS
    # ========================================================================
    op.create_table(
        'meta_ad_insights',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid4),
        sa.Column('ad_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('date', sa.DateTime, nullable=False),
        sa.Column('date_start', sa.DateTime, nullable=True),
        sa.Column('date_stop', sa.DateTime, nullable=True),
        
        # Delivery metrics
        sa.Column('impressions', sa.Integer, nullable=True, default=0),
        sa.Column('reach', sa.Integer, nullable=True, default=0),
        sa.Column('frequency', sa.Float, nullable=True, default=0.0),
        
        # Engagement metrics
        sa.Column('clicks', sa.Integer, nullable=True, default=0),
        sa.Column('inline_link_clicks', sa.Integer, nullable=True, default=0),
        sa.Column('unique_clicks', sa.Integer, nullable=True, default=0),
        sa.Column('ctr', sa.Float, nullable=True, default=0.0),
        
        # Video metrics
        sa.Column('video_views', sa.Integer, nullable=True, default=0),
        sa.Column('video_views_3s', sa.Integer, nullable=True, default=0),
        sa.Column('video_views_10s', sa.Integer, nullable=True, default=0),
        sa.Column('video_views_25_percent', sa.Integer, nullable=True, default=0),
        sa.Column('video_views_50_percent', sa.Integer, nullable=True, default=0),
        sa.Column('video_views_75_percent', sa.Integer, nullable=True, default=0),
        sa.Column('video_views_100_percent', sa.Integer, nullable=True, default=0),
        sa.Column('video_avg_watch_time', sa.Float, nullable=True, default=0.0),
        
        # Cost metrics
        sa.Column('spend', sa.Float, nullable=True, default=0.0),
        sa.Column('cpc', sa.Float, nullable=True, default=0.0),
        sa.Column('cpm', sa.Float, nullable=True, default=0.0),
        sa.Column('cpp', sa.Float, nullable=True, default=0.0),
        
        # Conversion metrics
        sa.Column('actions', sa.JSON, nullable=True),
        sa.Column('conversions', sa.Integer, nullable=True, default=0),
        sa.Column('conversion_rate', sa.Float, nullable=True, default=0.0),
        sa.Column('cost_per_conversion', sa.Float, nullable=True, default=0.0),
        
        # ROAS
        sa.Column('purchase_value', sa.Float, nullable=True, default=0.0),
        sa.Column('roas', sa.Float, nullable=True, default=0.0),
        
        # Attribution
        sa.Column('attribution_setting', sa.String(50), nullable=True),
        
        sa.Column('extra_metadata', sa.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        
        sa.ForeignKeyConstraint(['ad_id'], ['meta_ads.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('ad_id', 'date', name='uq_meta_insights_ad_date'),
    )
    
    # Indexes for meta_ad_insights
    op.create_index('ix_meta_ad_insights_ad_id', 'meta_ad_insights', ['ad_id'])
    op.create_index('ix_meta_ad_insights_date', 'meta_ad_insights', ['date'])
    op.create_index('ix_meta_ad_insights_ad_id_date', 'meta_ad_insights', ['ad_id', 'date'])


def downgrade() -> None:
    """Drop Meta Ads tables."""
    op.drop_table('meta_ad_insights')
    op.drop_table('meta_ads')
    op.drop_table('meta_adsets')
    op.drop_table('meta_campaigns')
    op.drop_table('meta_creatives')
    op.drop_table('meta_pixels')
    op.drop_table('meta_accounts')
