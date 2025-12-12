"""
Vision Engine - Complete Usage Example

Sprint 3: Demonstrates full pipeline from video to publication recommendation.
"""

import asyncio
from pathlib import Path

# ML modules
from ml.clip_tagger import ClipTagger
from ml.models import VisionConfig

# Content Engine integration
from content_engine.clip_selector import ClipSelector


async def main():
    """Complete Vision Engine pipeline example."""
    
    print("🟣 STAKAZO Vision Engine - Complete Example")
    print("=" * 60)
    print()
    
    # ========================================
    # 1. Initialize Vision Engine
    # ========================================
    
    print("1️⃣  Initializing Vision Engine...")
    
    config = VisionConfig(
        yolo_model="yolov8n.pt",
        yolo_confidence_threshold=0.3,
        target_fps=1.0,
        max_frames_per_clip=30,
        embedding_model="clip-vit-base-patch32",
        use_faiss=True,
        max_cost_per_clip_eur=0.01,
        enable_telemetry=True
    )
    
    tagger = ClipTagger(config)
    
    try:
        tagger.initialize()
        print("   ✅ Vision Engine initialized")
        print()
    except Exception as e:
        print(f"   ❌ Initialization failed: {e}")
        print("   💡 Run ./setup-vision-engine.sh first")
        return
    
    # ========================================
    # 2. Process Video Clips
    # ========================================
    
    print("2️⃣  Processing video clips...")
    print()
    
    # Sample video paths (replace with actual videos)
    video_paths = [
        ("sample_video_1.mp4", "clip_001", "video_001"),
        ("sample_video_2.mp4", "clip_002", "video_001"),
        ("sample_video_3.mp4", "clip_003", "video_002"),
    ]
    
    clips_metadata = []
    
    for video_path, clip_id, video_id in video_paths:
        if not Path(video_path).exists():
            print(f"   ⚠️  Video not found: {video_path} (skipping)")
            continue
        
        try:
            print(f"   📹 Processing {clip_id}...")
            
            metadata = tagger.process_video_clip(
                video_path=video_path,
                clip_id=clip_id,
                video_id=video_id,
                max_frames=30
            )
            
            clips_metadata.append(metadata)
            
            # Print results
            print(f"      Objects: {', '.join(metadata.objects_detected[:5])}")
            print(f"      Scene: {metadata.dominant_scene}")
            print(f"      Virality: {metadata.virality_score_visual:.2f}")
            print(f"      Brand Affinity: {metadata.brand_affinity_score:.2f}")
            print(f"      Aesthetic: {metadata.aesthetic_score:.2f}")
            if metadata.color_palette:
                print(f"      Purple Score: {metadata.color_palette.purple_score:.2f}")
            print(f"      Cost: €{metadata.processing_cost_eur:.4f}")
            print()
        
        except Exception as e:
            print(f"   ❌ Failed to process {clip_id}: {e}")
            print()
    
    if not clips_metadata:
        print("   ⚠️  No clips processed. Add sample videos or use:")
        print("      metadata = tagger.process_frame_batch(frames, clip_id, video_id)")
        print()
        return
    
    # ========================================
    # 3. Clip Selection
    # ========================================
    
    print("3️⃣  Selecting best clips...")
    print()
    
    selector = ClipSelector(vision_tagger=tagger)
    
    # Select top 3 clips
    best_clips = selector.select_best_clips(
        clips_metadata=clips_metadata,
        top_k=3,
        min_score=0.0  # No minimum for demo
    )
    
    print(f"   🏆 Top {len(best_clips)} clips:")
    for i, clip in enumerate(best_clips, 1):
        score = selector.score_clip(clip)
        print(f"      {i}. {clip.clip_id} - Score: {score:.2f}")
    print()
    
    # ========================================
    # 4. Filter by Aesthetic
    # ========================================
    
    print("4️⃣  Filtering by aesthetic...")
    print()
    
    purple_clips = selector.filter_by_aesthetic(
        clips_metadata=clips_metadata,
        aesthetic_type="morado_dominante",
        min_threshold=0.5
    )
    
    print(f"   🟣 Purple aesthetic clips: {len(purple_clips)}")
    for clip in purple_clips:
        print(f"      - {clip.clip_id} (purple: {clip.color_palette.purple_score:.2f})")
    print()
    
    # ========================================
    # 5. Publication Recommendations
    # ========================================
    
    print("5️⃣  Publication recommendations...")
    print()
    
    platforms = ["instagram", "tiktok", "youtube"]
    
    for clip in best_clips[:2]:  # Top 2 clips
        print(f"   📱 {clip.clip_id}:")
        
        for platform in platforms:
            rec = selector.get_publication_recommendation(clip, platform=platform)
            
            emoji = "🟢" if rec["priority"] == "high" else "🟡" if rec["priority"] == "medium" else "🔴"
            print(f"      {emoji} {platform.upper()}: {rec['recommendation']} (score: {rec['score']:.2f})")
        
        print()
    
    # ========================================
    # 6. Clip Comparison
    # ========================================
    
    if len(clips_metadata) >= 2:
        print("6️⃣  Comparing clips...")
        print()
        
        comparison = selector.compare_clips(clips_metadata[0], clips_metadata[1])
        
        print(f"   🥊 Winner: {comparison['winner_clip_id']}")
        print(f"   📊 Scores:")
        for clip_id, score in comparison['scores'].items():
            print(f"      - {clip_id}: {score:.2f}")
        print()
    
    # ========================================
    # 7. Pipeline Statistics
    # ========================================
    
    print("7️⃣  Pipeline statistics...")
    print()
    
    stats = tagger.get_pipeline_stats()
    
    print(f"   📊 Total clips processed: {len(clips_metadata)}")
    print(f"   💰 Total cost: €{stats['total_cost_eur']:.4f}")
    print(f"   🎯 YOLO model: {stats['yolo_model']['model_path']}")
    print(f"   🖼️  FAISS index: {stats['embeddings_index']['total_embeddings']} embeddings")
    print()
    
    # ========================================
    # Summary
    # ========================================
    
    print("=" * 60)
    print("✅ Vision Engine pipeline complete!")
    print()
    print("Next steps:")
    print("  • Integrate with Satellite Engine for publishing")
    print("  • Add visual features to Rules Engine")
    print("  • Visualize results in Dashboard")
    print("  • Optimize with GPU inference")
    print()


if __name__ == "__main__":
    asyncio.run(main())
