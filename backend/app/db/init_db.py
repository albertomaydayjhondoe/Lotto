"""
Database initialization and seeding script.
Run this to create initial database schema and seed data.
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from uuid import uuid4
from datetime import datetime

from app.core.config import settings
from app.core.database import Base
from app.models.database import (
    VideoAsset, Clip, Job, Campaign, PlatformRule,
    JobStatus, ClipStatus, CampaignStatus, RuleStatus
)


async def init_database():
    """Initialize database and create tables."""
    print("🔧 Initializing database...")
    
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    
    async with engine.begin() as conn:
        # Drop all tables (for development)
        await conn.run_sync(Base.metadata.drop_all)
        print("✅ Dropped existing tables")
        
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
        print("✅ Created all tables")
    
    await engine.dispose()


async def seed_database():
    """Seed database with initial data."""
    print("\n🌱 Seeding database...")
    
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Create sample video asset
        video = VideoAsset(
            id=uuid4(),
            title="Sample Music Video",
            description="A sample music video for testing",
            release_date=datetime.utcnow(),
            file_path="/uploads/sample.mp4",
            file_size=50000000,
            duration_ms=240000
        )
        session.add(video)
        
        # Create sample clip
        clip = Clip(
            id=uuid4(),
            video_asset_id=video.id,
            start_ms=10000,
            end_ms=40000,
            duration_ms=30000,
            visual_score=0.85,
            status=ClipStatus.READY
        )
        session.add(clip)
        
        # Create sample job
        job = Job(
            id=uuid4(),
            job_type="analyze_video",
            status=JobStatus.COMPLETED,
            video_asset_id=video.id,
            params={"auto_generated": True}
        )
        session.add(job)
        
        # Create sample campaign
        campaign = Campaign(
            id=uuid4(),
            name="Sample Campaign",
            clip_id=clip.id,
            budget_cents=100000,
            targeting={"countries": ["ES"], "age_range": [18, 35]},
            status=CampaignStatus.DRAFT
        )
        session.add(campaign)
        
        # Create default platform rules
        instagram_rules = PlatformRule(
            id=uuid4(),
            name="Instagram Default Rules",
            rules={
                "max_duration_seconds": 60,
                "aspect_ratio": "9:16",
                "min_visual_score": 0.7,
                "min_retention": 0.5
            },
            status=RuleStatus.ACTIVE
        )
        session.add(instagram_rules)
        
        tiktok_rules = PlatformRule(
            id=uuid4(),
            name="TikTok Default Rules",
            rules={
                "max_duration_seconds": 60,
                "aspect_ratio": "9:16",
                "min_visual_score": 0.75,
                "min_retention": 0.6
            },
            status=RuleStatus.ACTIVE
        )
        session.add(tiktok_rules)
        
        await session.commit()
        print("✅ Seeded sample data")
        print(f"   - Video: {video.id}")
        print(f"   - Clip: {clip.id}")
        print(f"   - Job: {job.id}")
        print(f"   - Campaign: {campaign.id}")
        print(f"   - Rules: 2 platform rules")
    
    await engine.dispose()


async def main():
    """Main function."""
    print("=" * 60)
    print("  Stakazo Database Initialization")
    print("=" * 60)
    
    await init_database()
    await seed_database()
    
    print("\n" + "=" * 60)
    print("  ✅ Database ready!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
