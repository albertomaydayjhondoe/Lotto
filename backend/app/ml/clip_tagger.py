"""
Clip Tagger - Vision Engine Orchestrator

Sprint 3: Vision Engine

Complete visual metadata generation pipeline.

Fusion of:
- YOLO detections
- COCO semantic mappings
- Visual embeddings (CLIP)
- Scene classifications
- Color palette extraction

Outputs: ClipMetadata with all visual intelligence.
"""

import logging
import time
from typing import List, Optional, Dict, Any
from datetime import datetime
import numpy as np

from .models import (
    ClipMetadata,
    EnrichedDetection,
    VisualEmbedding,
    SceneClassification,
    ColorPalette,
    VisionConfig,
    FrameDetections
)
from .yolo_runner import YOLORunner
from .coco_mapper import COCOMapper
from .visual_embeddings import VisualEmbeddingsEngine
from .scene_classifier import SceneClassifier
from .color_extractor import ColorExtractor

logger = logging.getLogger(__name__)


class ClipTagger:
    """
    Complete vision pipeline orchestrator.
    
    Pipeline:
    1. YOLO detection on sampled frames
    2. COCO semantic enrichment
    3. Visual embedding generation (CLIP)
    4. Scene classification
    5. Color palette extraction
    6. Aggregate scoring (virality, brand affinity, aesthetic)
    7. Output ClipMetadata
    """
    
    def __init__(self, config: Optional[VisionConfig] = None):
        """
        Initialize clip tagger with all subsystems.
        
        Args:
            config: Vision configuration
        """
        self.config = config or VisionConfig()
        
        # Initialize subsystems
        self.yolo_runner = YOLORunner(self.config)
        self.coco_mapper = COCOMapper()
        self.embeddings_engine = VisualEmbeddingsEngine(self.config)
        self.scene_classifier = SceneClassifier()
        self.color_extractor = ColorExtractor(num_colors=5)
        
        # Cost tracking
        self.total_cost_eur = 0.0
        
        logger.info("ClipTagger initialized with all subsystems")
    
    def initialize(self) -> None:
        """
        Load all ML models.
        
        Call this once at startup to load YOLO, CLIP, etc.
        """
        logger.info("Initializing ClipTagger models...")
        
        try:
            # Load YOLO
            self.yolo_runner.load_model()
            
            # Load CLIP
            self.embeddings_engine.load_model()
            
            # Initialize FAISS index
            if self.config.use_faiss:
                self.embeddings_engine.initialize_faiss_index(dimension=512)
            
            logger.info("✅ ClipTagger models loaded successfully")
        
        except Exception as e:
            logger.error(f"Failed to initialize ClipTagger models: {e}")
            raise
    
    def process_video_clip(
        self,
        video_path: str,
        clip_id: str,
        video_id: str,
        max_frames: Optional[int] = None
    ) -> ClipMetadata:
        """
        Process a video clip through the complete vision pipeline.
        
        Args:
            video_path: Path to video file
            clip_id: Clip UUID
            video_id: Source video UUID
            max_frames: Max frames to process (overrides config)
        
        Returns:
            ClipMetadata with all visual intelligence
        """
        start_time = time.time()
        
        logger.info(
            f"Processing clip {clip_id} from video {video_id}: {video_path}"
        )
        
        max_frames = max_frames or self.config.max_frames_per_clip
        
        try:
            # Step 1: YOLO detection on video frames
            logger.debug("Step 1: YOLO detection...")
            frame_detections_list = self.yolo_runner.detect_video(
                video_path=video_path,
                max_frames=max_frames,
                target_fps=self.config.target_fps
            )
            
            # Extract frames for further processing
            import cv2
            cap = cv2.VideoCapture(video_path)
            
            frames = []
            frame_ids_to_process = [fd.frame_id for fd in frame_detections_list]
            
            for frame_id in frame_ids_to_process:
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_id)
                ret, frame = cap.read()
                if ret:
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    frames.append(frame_rgb)
            
            cap.release()
            
            # Step 2: COCO semantic enrichment
            logger.debug("Step 2: COCO semantic enrichment...")
            all_enriched_detections = []
            all_detections = []
            
            for frame_det in frame_detections_list:
                enriched = self.coco_mapper.enrich_all(frame_det.detections)
                all_enriched_detections.extend(enriched)
                all_detections.extend(frame_det.detections)
            
            # Get unique objects
            objects_detected = list(set(d.label for d in all_detections))
            
            # Step 3: Visual embeddings (CLIP)
            logger.debug("Step 3: Generating visual embeddings...")
            embeddings = []
            
            if frames:
                embedding_ids = [f"{clip_id}_frame_{fd.frame_id}" for fd in frame_detections_list]
                frame_ids = [fd.frame_id for fd in frame_detections_list]
                timestamps_ms = [fd.timestamp_ms for fd in frame_detections_list]
                
                embeddings = self.embeddings_engine.generate_batch_embeddings(
                    images=frames,
                    embedding_ids=embedding_ids,
                    frame_ids=frame_ids,
                    timestamps_ms=timestamps_ms
                )
                
                # Add to FAISS index
                if self.config.use_faiss:
                    for emb in embeddings:
                        self.embeddings_engine.add_to_index(
                            emb,
                            metadata={"clip_id": clip_id, "video_id": video_id}
                        )
            
            # Calculate average embedding for clip
            avg_embedding = None
            if embeddings:
                avg_embedding = self.embeddings_engine.average_embeddings(embeddings)
            
            # Step 4: Scene classification
            logger.debug("Step 4: Scene classification...")
            all_scenes = []
            semantic_tags = self.coco_mapper.get_unique_tags(all_detections)
            
            for i, frame_det in enumerate(frame_detections_list):
                # Extract color palette for this frame
                frame_palette = None
                if i < len(frames):
                    frame_palette = self.color_extractor.extract_palette(frames[i])
                
                scenes = self.scene_classifier.classify_frame(
                    detections=frame_det.detections,
                    color_palette=frame_palette,
                    frame_id=frame_det.frame_id,
                    timestamp_ms=frame_det.timestamp_ms,
                    semantic_tags=semantic_tags
                )
                
                if scenes:
                    all_scenes.append(scenes)
            
            # Determine dominant scene
            dominant_scene = self.scene_classifier.classify_clip(all_scenes)
            
            # Step 5: Color palette extraction (clip-level)
            logger.debug("Step 5: Color palette extraction...")
            color_palette = None
            if frames:
                color_palette = self.color_extractor.extract_average_palette(frames)
            
            # Step 6: Aggregate scoring
            logger.debug("Step 6: Calculating aggregate scores...")
            aggregate_scores = self.coco_mapper.calculate_aggregate_scores(all_detections)
            
            virality_score_visual = aggregate_scores.get("avg_virality", 0.0)
            brand_affinity_score = aggregate_scores.get("avg_affinity", 0.0)
            
            # Aesthetic score (based on color palette)
            aesthetic_score = 0.5
            if color_palette:
                aesthetic_score = color_palette.purple_score * 0.6 + 0.4
            
            # Step 7: Cost calculation
            processing_time_s = time.time() - start_time
            processing_cost_eur = self._estimate_cost(
                num_frames=len(frames),
                num_embeddings=len(embeddings)
            )
            
            self.total_cost_eur += processing_cost_eur
            
            # Build ClipMetadata
            metadata = ClipMetadata(
                clip_id=clip_id,
                video_id=video_id,
                detections=all_enriched_detections,
                objects_detected=objects_detected,
                embeddings=embeddings,
                avg_embedding=avg_embedding,
                scenes=[scene for scenes in all_scenes for scene in scenes],  # Flatten
                dominant_scene=dominant_scene,
                color_palette=color_palette,
                virality_score_visual=virality_score_visual,
                brand_affinity_score=brand_affinity_score,
                aesthetic_score=aesthetic_score,
                processed_at=datetime.utcnow(),
                processing_cost_eur=processing_cost_eur
            )
            
            logger.info(
                f"✅ Clip {clip_id} processed successfully. "
                f"Time={processing_time_s:.2f}s, Cost={processing_cost_eur:.4f}€, "
                f"Objects={len(objects_detected)}, Embeddings={len(embeddings)}, "
                f"Scene={dominant_scene}"
            )
            
            return metadata
        
        except Exception as e:
            logger.error(f"Failed to process clip {clip_id}: {e}", exc_info=True)
            raise
    
    def process_frame_batch(
        self,
        frames: List[np.ndarray],
        clip_id: str,
        video_id: str,
        frame_ids: Optional[List[int]] = None,
        timestamps_ms: Optional[List[float]] = None
    ) -> ClipMetadata:
        """
        Process a batch of frames (in-memory processing).
        
        Useful when frames are already loaded (e.g., from stream).
        
        Args:
            frames: List of frames as numpy arrays
            clip_id: Clip UUID
            video_id: Video UUID
            frame_ids: Optional frame IDs
            timestamps_ms: Optional timestamps
        
        Returns:
            ClipMetadata
        """
        start_time = time.time()
        
        if frame_ids is None:
            frame_ids = list(range(len(frames)))
        if timestamps_ms is None:
            timestamps_ms = [i * 1000.0 for i in range(len(frames))]
        
        try:
            # YOLO detection
            frame_detections_list = self.yolo_runner.detect_batch(
                frames=frames,
                frame_ids=frame_ids,
                timestamps_ms=timestamps_ms
            )
            
            # COCO enrichment
            all_enriched_detections = []
            all_detections = []
            
            for frame_det in frame_detections_list:
                enriched = self.coco_mapper.enrich_all(frame_det.detections)
                all_enriched_detections.extend(enriched)
                all_detections.extend(frame_det.detections)
            
            objects_detected = list(set(d.label for d in all_detections))
            
            # Embeddings
            embeddings = []
            if frames:
                embedding_ids = [f"{clip_id}_frame_{fid}" for fid in frame_ids]
                
                embeddings = self.embeddings_engine.generate_batch_embeddings(
                    images=frames,
                    embedding_ids=embedding_ids,
                    frame_ids=frame_ids,
                    timestamps_ms=timestamps_ms
                )
            
            avg_embedding = None
            if embeddings:
                avg_embedding = self.embeddings_engine.average_embeddings(embeddings)
            
            # Scene classification
            all_scenes = []
            semantic_tags = self.coco_mapper.get_unique_tags(all_detections)
            
            for i, frame_det in enumerate(frame_detections_list):
                frame_palette = self.color_extractor.extract_palette(frames[i])
                
                scenes = self.scene_classifier.classify_frame(
                    detections=frame_det.detections,
                    color_palette=frame_palette,
                    frame_id=frame_det.frame_id,
                    timestamp_ms=frame_det.timestamp_ms,
                    semantic_tags=semantic_tags
                )
                
                if scenes:
                    all_scenes.append(scenes)
            
            dominant_scene = self.scene_classifier.classify_clip(all_scenes)
            
            # Color palette
            color_palette = self.color_extractor.extract_average_palette(frames)
            
            # Scoring
            aggregate_scores = self.coco_mapper.calculate_aggregate_scores(all_detections)
            
            virality_score_visual = aggregate_scores.get("avg_virality", 0.0)
            brand_affinity_score = aggregate_scores.get("avg_affinity", 0.0)
            aesthetic_score = color_palette.purple_score * 0.6 + 0.4 if color_palette else 0.5
            
            # Cost
            processing_cost_eur = self._estimate_cost(
                num_frames=len(frames),
                num_embeddings=len(embeddings)
            )
            
            metadata = ClipMetadata(
                clip_id=clip_id,
                video_id=video_id,
                detections=all_enriched_detections,
                objects_detected=objects_detected,
                embeddings=embeddings,
                avg_embedding=avg_embedding,
                scenes=[scene for scenes in all_scenes for scene in scenes],
                dominant_scene=dominant_scene,
                color_palette=color_palette,
                virality_score_visual=virality_score_visual,
                brand_affinity_score=brand_affinity_score,
                aesthetic_score=aesthetic_score,
                processed_at=datetime.utcnow(),
                processing_cost_eur=processing_cost_eur
            )
            
            logger.info(f"✅ Processed {len(frames)} frames for clip {clip_id}")
            
            return metadata
        
        except Exception as e:
            logger.error(f"Frame batch processing failed: {e}", exc_info=True)
            raise
    
    def _estimate_cost(self, num_frames: int, num_embeddings: int) -> float:
        """
        Estimate processing cost.
        
        Args:
            num_frames: Number of frames processed
            num_embeddings: Number of embeddings generated
        
        Returns:
            Estimated cost in EUR
        """
        # Cost model (rough estimates):
        # - YOLO inference: ~0.0001€ per frame (CPU)
        # - CLIP embeddings: ~0.0002€ per embedding
        
        yolo_cost = num_frames * 0.0001
        clip_cost = num_embeddings * 0.0002
        
        total_cost = yolo_cost + clip_cost
        
        return round(total_cost, 6)
    
    def get_pipeline_stats(self) -> Dict[str, Any]:
        """Get statistics about the vision pipeline."""
        return {
            "yolo_model": self.yolo_runner.get_model_info(),
            "embeddings_index": self.embeddings_engine.get_index_stats(),
            "total_cost_eur": self.total_cost_eur,
            "config": {
                "target_fps": self.config.target_fps,
                "max_frames_per_clip": self.config.max_frames_per_clip,
                "yolo_confidence": self.config.yolo_confidence_threshold,
                "use_faiss": self.config.use_faiss
            }
        }
