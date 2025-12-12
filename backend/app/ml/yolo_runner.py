"""
YOLO Runner - Ultralytics YOLOv8/v11 Integration

Sprint 3: Vision Engine

Features:
- Load YOLOv8/v11 models from Ultralytics
- Frame-by-frame or batch inference
- CPU/GPU auto-detection
- FPS throttling for cost optimization
- Fallback to E2B for heavy inference
- Telemetry + cost guards
"""

import logging
import time
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from pathlib import Path

if TYPE_CHECKING:
    from ultralytics import YOLO

try:
    from ultralytics import YOLO  # type: ignore
    ULTRALYTICS_AVAILABLE = True
except ImportError:
    ULTRALYTICS_AVAILABLE = False
    YOLO = None  # type: ignore
    logging.warning("Ultralytics not installed. YOLO inference will fail.")

import torch
import numpy as np
from PIL import Image

from .models import (
    YOLODetection,
    FrameDetections,
    BoundingBox,
    VisionConfig
)

logger = logging.getLogger(__name__)


class YOLORunner:
    """
    Ultralytics YOLO integration for object detection.
    
    Supports:
    - YOLOv8n, YOLOv8s, YOLOv8m (nano, small, medium)
    - YOLOv11 (latest)
    - Auto GPU/CPU detection
    - Batch processing
    - Cost throttling via FPS sampling
    """
    
    # COCO class names (80 classes)
    COCO_CLASSES = [
        'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat',
        'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat',
        'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe', 'backpack',
        'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball',
        'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 'tennis racket',
        'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple',
        'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair',
        'couch', 'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse',
        'remote', 'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink', 'refrigerator',
        'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier', 'toothbrush'
    ]
    
    def __init__(self, config: Optional[VisionConfig] = None):
        """
        Initialize YOLO runner.
        
        Args:
            config: Vision configuration. Defaults to VisionConfig().
        """
        self.config = config or VisionConfig()
        self.model: Optional[Any] = None
        self.device = self._detect_device()
        
        logger.info(
            f"YOLORunner initialized with model={self.config.yolo_model}, "
            f"device={self.device}, confidence_threshold={self.config.yolo_confidence_threshold}"
        )
    
    def _detect_device(self) -> str:
        """Auto-detect best available device (CUDA > CPU)."""
        if self.config.yolo_device != "cpu":
            if torch.cuda.is_available():
                logger.info("CUDA available. Using GPU.")
                return "cuda"
        logger.info("Using CPU for inference.")
        return "cpu"
    
    def load_model(self, model_path: Optional[str] = None) -> None:
        """
        Load YOLO model from Ultralytics.
        
        Args:
            model_path: Path to model weights. If None, uses config.yolo_model.
        
        Raises:
            RuntimeError: If Ultralytics is not installed or model fails to load.
        """
        if not ULTRALYTICS_AVAILABLE:
            raise RuntimeError(
                "Ultralytics not installed. Install with: pip install ultralytics"
            )
        
        model_path = model_path or self.config.yolo_model
        
        try:
            logger.info(f"Loading YOLO model from {model_path}...")
            self.model = YOLO(model_path)
            logger.info(f"✅ YOLO model loaded successfully: {model_path}")
        except Exception as e:
            logger.error(f"Failed to load YOLO model: {e}")
            raise RuntimeError(f"YOLO model load failed: {e}")
    
    def detect_frame(
        self,
        frame: np.ndarray,
        frame_id: int,
        timestamp_ms: float
    ) -> FrameDetections:
        """
        Run YOLO inference on a single frame.
        
        Args:
            frame: Frame as numpy array (H, W, 3) in RGB
            frame_id: Frame index
            timestamp_ms: Timestamp in video (ms)
        
        Returns:
            FrameDetections with all detected objects
        """
        if self.model is None:
            raise RuntimeError("YOLO model not loaded. Call load_model() first.")
        
        start_time = time.time()
        
        try:
            # Run inference
            results = self.model(
                frame,
                conf=self.config.yolo_confidence_threshold,
                device=self.device,
                verbose=False
            )
            
            # Parse detections
            detections = []
            if len(results) > 0:
                result = results[0]  # Single frame result
                
                if result.boxes is not None:
                    boxes = result.boxes.xyxy.cpu().numpy()  # [x1, y1, x2, y2]
                    confidences = result.boxes.conf.cpu().numpy()
                    class_ids = result.boxes.cls.cpu().numpy().astype(int)
                    
                    for i in range(len(boxes)):
                        x1, y1, x2, y2 = boxes[i]
                        confidence = float(confidences[i])
                        class_id = int(class_ids[i])
                        
                        # Convert to XYWH
                        bbox = BoundingBox(
                            x=float(x1),
                            y=float(y1),
                            w=float(x2 - x1),
                            h=float(y2 - y1)
                        )
                        
                        label = self.COCO_CLASSES[class_id] if class_id < len(self.COCO_CLASSES) else f"class_{class_id}"
                        
                        detection = YOLODetection(
                            label=label,
                            confidence=confidence,
                            bbox=bbox,
                            class_id=class_id
                        )
                        detections.append(detection)
            
            processing_time_ms = (time.time() - start_time) * 1000
            
            return FrameDetections(
                frame_id=frame_id,
                timestamp_ms=timestamp_ms,
                detections=detections,
                processing_time_ms=processing_time_ms
            )
        
        except Exception as e:
            logger.error(f"YOLO inference failed on frame {frame_id}: {e}")
            # Return empty detections on error
            return FrameDetections(
                frame_id=frame_id,
                timestamp_ms=timestamp_ms,
                detections=[],
                processing_time_ms=(time.time() - start_time) * 1000
            )
    
    def detect_video(
        self,
        video_path: str,
        max_frames: Optional[int] = None,
        target_fps: Optional[float] = None
    ) -> List[FrameDetections]:
        """
        Run YOLO inference on a video file with FPS throttling.
        
        Args:
            video_path: Path to video file
            max_frames: Maximum number of frames to process
            target_fps: Target FPS for sampling. If None, uses config.target_fps.
        
        Returns:
            List of FrameDetections for sampled frames
        """
        import cv2
        
        if self.model is None:
            raise RuntimeError("YOLO model not loaded. Call load_model() first.")
        
        target_fps = target_fps or self.config.target_fps
        max_frames = max_frames or self.config.max_frames_per_clip
        
        logger.info(
            f"Processing video: {video_path} (target_fps={target_fps}, max_frames={max_frames})"
        )
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Failed to open video: {video_path}")
        
        video_fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Calculate frame sampling interval
        frame_interval = max(1, int(video_fps / target_fps))
        
        logger.info(
            f"Video: fps={video_fps}, total_frames={total_frames}, "
            f"frame_interval={frame_interval}"
        )
        
        all_detections = []
        frame_count = 0
        processed_count = 0
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Sample frames based on interval
                if frame_count % frame_interval == 0:
                    # Convert BGR to RGB
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    
                    timestamp_ms = (frame_count / video_fps) * 1000
                    
                    detections = self.detect_frame(
                        frame=frame_rgb,
                        frame_id=frame_count,
                        timestamp_ms=timestamp_ms
                    )
                    all_detections.append(detections)
                    
                    processed_count += 1
                    
                    if processed_count >= max_frames:
                        logger.info(f"Reached max_frames limit: {max_frames}")
                        break
                
                frame_count += 1
        
        finally:
            cap.release()
        
        logger.info(
            f"✅ Processed {processed_count} frames from {video_path} "
            f"({len(all_detections)} with detections)"
        )
        
        return all_detections
    
    def detect_batch(
        self,
        frames: List[np.ndarray],
        frame_ids: Optional[List[int]] = None,
        timestamps_ms: Optional[List[float]] = None
    ) -> List[FrameDetections]:
        """
        Run YOLO inference on a batch of frames.
        
        More efficient than single-frame processing for multiple frames.
        
        Args:
            frames: List of frames as numpy arrays
            frame_ids: Optional list of frame IDs
            timestamps_ms: Optional list of timestamps
        
        Returns:
            List of FrameDetections
        """
        if self.model is None:
            raise RuntimeError("YOLO model not loaded. Call load_model() first.")
        
        if frame_ids is None:
            frame_ids = list(range(len(frames)))
        if timestamps_ms is None:
            timestamps_ms = [i * 1000.0 for i in range(len(frames))]
        
        logger.info(f"Processing batch of {len(frames)} frames...")
        
        all_detections = []
        
        try:
            # Batch inference
            results = self.model(
                frames,
                conf=self.config.yolo_confidence_threshold,
                device=self.device,
                verbose=False
            )
            
            for i, result in enumerate(results):
                detections = []
                
                if result.boxes is not None:
                    boxes = result.boxes.xyxy.cpu().numpy()
                    confidences = result.boxes.conf.cpu().numpy()
                    class_ids = result.boxes.cls.cpu().numpy().astype(int)
                    
                    for j in range(len(boxes)):
                        x1, y1, x2, y2 = boxes[j]
                        confidence = float(confidences[j])
                        class_id = int(class_ids[j])
                        
                        bbox = BoundingBox(
                            x=float(x1),
                            y=float(y1),
                            w=float(x2 - x1),
                            h=float(y2 - y1)
                        )
                        
                        label = self.COCO_CLASSES[class_id] if class_id < len(self.COCO_CLASSES) else f"class_{class_id}"
                        
                        detection = YOLODetection(
                            label=label,
                            confidence=confidence,
                            bbox=bbox,
                            class_id=class_id
                        )
                        detections.append(detection)
                
                frame_detections = FrameDetections(
                    frame_id=frame_ids[i],
                    timestamp_ms=timestamps_ms[i],
                    detections=detections,
                    processing_time_ms=0.0  # Batch timing is shared
                )
                all_detections.append(frame_detections)
        
        except Exception as e:
            logger.error(f"Batch inference failed: {e}")
            raise
        
        return all_detections
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded YOLO model."""
        if self.model is None:
            return {"loaded": False}
        
        return {
            "loaded": True,
            "model_path": self.config.yolo_model,
            "device": self.device,
            "confidence_threshold": self.config.yolo_confidence_threshold,
            "num_classes": len(self.COCO_CLASSES)
        }
