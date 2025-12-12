# 🟣 Vision Engine - STAKAZO Sprint 3

**Status:** ✅ COMPLETE  
**Version:** 1.0.0  
**Date:** December 7, 2025

---

## 📋 Overview

The **Vision Engine** is the complete visual intelligence subsystem for STAKAZO. It analyzes video content using state-of-the-art computer vision and deep learning to generate rich visual metadata that powers content selection, virality prediction, and brand alignment.

### Key Components

1. **YOLO Runner** - Ultralytics YOLOv8/v11 object detection
2. **COCO Mapper** - Semantic enrichment (80 COCO classes → Stakazo tags)
3. **Visual Embeddings** - CLIP embeddings + FAISS similarity search
4. **Scene Classifier** - Context detection (calle, club, coche, noche, etc.)
5. **Color Extractor** - Dominant palette + purple aesthetic scoring
6. **Clip Tagger** - Complete pipeline orchestrator

---

## 🎯 Objectives

### Primary Goals

✅ **Visual Object Detection:** Identify objects in video frames using YOLO  
✅ **Semantic Understanding:** Map detected objects to brand-relevant semantics  
✅ **Visual Similarity:** Generate embeddings for content matching and discovery  
✅ **Scene Context:** Classify scenes into brand-relevant categories  
✅ **Aesthetic Scoring:** Quantify brand alignment (purple aesthetic, urban vibe)  
✅ **Virality Prediction:** Score visual content for viral potential

### Integration Points

- **Content Engine:** Visual metadata enhances clip selection
- **Satellite Engine:** Visual scores guide publication decisions
- **Orchestrator:** Feeds visual signals to ML pipeline
- **Rules Engine:** Visual features in virality rules

---

## 🏗️ Architecture

```
Vision Engine Pipeline
├─ Input: Video file or frame batch
│
├─ 1. YOLO Detection (yolo_runner.py)
│   └─ Detect objects in sampled frames (1 FPS)
│
├─ 2. COCO Mapping (coco_mapper.py)
│   └─ Enrich detections with semantic tags
│
├─ 3. Visual Embeddings (visual_embeddings.py)
│   └─ Generate CLIP embeddings for similarity
│
├─ 4. Scene Classification (scene_classifier.py)
│   └─ Classify scenes (calle, club, coche, etc.)
│
├─ 5. Color Extraction (color_extractor.py)
│   └─ Extract palette + purple aesthetic score
│
└─ Output: ClipMetadata (complete visual intelligence)
```

---

## 📦 Module Specifications

### 1. YOLO Runner (`yolo_runner.py`)

**Purpose:** Real-time object detection using Ultralytics YOLO.

**Features:**
- YOLOv8/v11 model loading (nano, small, medium)
- Frame-by-frame and batch inference
- CPU/GPU auto-detection
- FPS throttling (1 FPS default for cost optimization)
- 80 COCO class detection

**Key Methods:**
```python
runner = YOLORunner(config)
runner.load_model("yolov8n.pt")

# Single frame
detections = runner.detect_frame(frame, frame_id, timestamp_ms)

# Video file
all_detections = runner.detect_video(video_path, max_frames=30, target_fps=1.0)

# Batch processing
detections = runner.detect_batch(frames, frame_ids, timestamps_ms)
```

**Output:** `FrameDetections` with list of `YOLODetection` objects.

---

### 2. COCO Mapper (`coco_mapper.py`)

**Purpose:** Translate COCO labels into Stakazo's semantic space.

**Semantic Mappings (Examples):**
- `"car"` → `["coche", "asfalto", "velocidad", "trap-street"]`
- `"person"` → `["callejero", "urbano", "flow", "presencia"]`
- `"bottle"` → `["club", "fiesta", "noche", "celebracion"]`
- `"cell phone"` → `["moderno", "selfie", "viral", "social-media"]`

**Scoring:**
- **Brand Affinity:** How well the object aligns with Stakazo brand (0-1)
- **Virality Potential:** How likely the object drives viral content (0-1)

**Key Methods:**
```python
mapper = COCOMapper()

# Map single detection
mapping = mapper.map_detection(yolo_detection)

# Enrich detection
enriched = mapper.enrich_detection(yolo_detection)

# Get unique semantic tags
tags = mapper.get_unique_tags(detections)

# Aggregate scores
scores = mapper.calculate_aggregate_scores(detections)
```

---

### 3. Visual Embeddings Engine (`visual_embeddings.py`)

**Purpose:** Generate visual embeddings for similarity search and content matching.

**Technology:**
- **CLIP** (Contrastive Language-Image Pre-training) from OpenAI
- **FAISS** (Facebook AI Similarity Search) for fast vector search
- Supports 512-dim and 768-dim embeddings

**Features:**
- Batch embedding generation
- FAISS index for similarity search
- Cosine similarity computation
- Clip-level average embeddings

**Key Methods:**
```python
engine = VisualEmbeddingsEngine(config)
engine.load_model("clip-vit-base-patch32")
engine.initialize_faiss_index(dimension=512)

# Generate embedding
embedding = engine.generate_embedding(frame, embedding_id="emb_001")

# Batch generation
embeddings = engine.generate_batch_embeddings(frames, embedding_ids)

# Add to FAISS index
engine.add_to_index(embedding, metadata={"clip_id": "clip_123"})

# Search similar
results = engine.search_similar(query_embedding, top_k=5)

# Average embeddings (clip-level)
avg_emb = engine.average_embeddings(embeddings)
```

---

### 4. Scene Classifier (`scene_classifier.py`)

**Purpose:** Classify video frames into contextual scene categories.

**Scene Categories:**
- `calle` - Street scenes
- `coche` - Car/driving scenes
- `noche` - Nighttime
- `club` - Nightclub/party
- `trap_house` - Interior trap aesthetic
- `costa` - Coastal/beach (Galicia)
- `rural_galicia` - Countryside
- `urbano` - Urban environment

**Classification Logic:**
- Rule-based heuristics
- Object co-occurrence patterns
- Color palette analysis
- Brightness checks (for nighttime)

**Key Methods:**
```python
classifier = SceneClassifier()

# Classify frame
scenes = classifier.classify_frame(
    detections=yolo_detections,
    color_palette=palette,
    frame_id=0,
    timestamp_ms=0.0
)

# Classify entire clip
dominant_scene = classifier.classify_clip(frame_scenes)

# Get scene distribution
distribution = classifier.get_scene_distribution(frame_scenes)
```

---

### 5. Color Extractor (`color_extractor.py`)

**Purpose:** Extract dominant color palettes and compute aesthetic scores.

**Features:**
- K-means clustering for dominant colors (5 colors default)
- Purple aesthetic scoring (Stakazo brand color: #8B44FF)
- HSV color space analysis
- Aesthetic categorization

**Key Methods:**
```python
extractor = ColorExtractor(num_colors=5)

# Extract palette from frame
palette = extractor.extract_palette(frame)

# Average palette from multiple frames
avg_palette = extractor.extract_average_palette(frames)

# Check purple aesthetic
is_purple = extractor.is_purple_aesthetic(palette, threshold=0.5)

# Get aesthetic category
category = extractor.get_aesthetic_category(palette)
# Returns: "morado_dominante", "morado_presente", "oscuro", "luminoso", "equilibrado"
```

**ColorPalette Output:**
- `colors_hex`: List of hex colors (e.g., `["#8B44FF", "#1A1A2E"]`)
- `percentages`: Percentage of each color
- `purple_score`: Purple aesthetic score (0-1)
- `morado_ratio`: Ratio of purple tones (0-1)
- `dominant_color`: Most prominent color

---

### 6. Clip Tagger (`clip_tagger.py`)

**Purpose:** Orchestrate the complete vision pipeline and generate unified `ClipMetadata`.

**Full Pipeline:**
1. YOLO detection on sampled frames
2. COCO semantic enrichment
3. CLIP embedding generation
4. Scene classification
5. Color palette extraction
6. Aggregate scoring (virality, brand affinity, aesthetic)
7. Cost estimation

**Key Methods:**
```python
tagger = ClipTagger(config)
tagger.initialize()  # Load all models

# Process video clip
metadata = tagger.process_video_clip(
    video_path="path/to/video.mp4",
    clip_id="clip_abc123",
    video_id="video_xyz789",
    max_frames=30
)

# Process frame batch (in-memory)
metadata = tagger.process_frame_batch(
    frames=frames,
    clip_id="clip_abc123",
    video_id="video_xyz789"
)

# Get pipeline stats
stats = tagger.get_pipeline_stats()
```

**ClipMetadata Output:**
```python
{
    "clip_id": "clip_abc123",
    "video_id": "video_xyz789",
    "detections": [...],  # List of EnrichedDetection
    "objects_detected": ["car", "person", "cell_phone"],
    "embeddings": [...],  # List of VisualEmbedding
    "avg_embedding": [0.1, 0.2, ...],  # Clip-level embedding
    "scenes": [...],  # List of SceneClassification
    "dominant_scene": "coche",
    "color_palette": {...},  # ColorPalette
    "virality_score_visual": 0.82,
    "brand_affinity_score": 0.76,
    "aesthetic_score": 0.88,
    "processed_at": "2025-12-07T10:30:00Z",
    "processing_cost_eur": 0.0023
}
```

---

## ⚙️ Configuration

### VisionConfig

```python
from ml.models import VisionConfig

config = VisionConfig(
    # YOLO
    yolo_model="yolov8n.pt",  # or "yolov8s.pt", "yolov8m.pt", "yolov11n.pt"
    yolo_confidence_threshold=0.25,
    yolo_device="cpu",  # or "cuda"
    
    # Frame sampling
    target_fps=1.0,  # Process 1 frame per second
    max_frames_per_clip=30,  # Max 30 frames per clip
    
    # Embeddings
    embedding_model="clip-vit-base-patch32",  # or "clip-vit-large-patch14"
    use_faiss=True,  # Enable FAISS similarity search
    
    # Cost guards
    max_cost_per_clip_eur=0.01,  # Max €0.01 per clip
    enable_e2b_fallback=True,  # Use E2B for heavy inference
    
    # Telemetry
    enable_telemetry=True
)
```

---

## 💰 Cost Optimization

### Strategies

1. **FPS Throttling:** Process 1 FPS instead of full framerate (30x cost reduction)
2. **Frame Sampling:** Max 30 frames per clip
3. **Model Selection:** Use YOLOv8n (nano) for fast inference
4. **Batch Processing:** Process multiple frames in batches
5. **E2B Fallback:** Offload heavy inference to E2B runners

### Cost Model

- **YOLO inference:** ~€0.0001 per frame (CPU)
- **CLIP embeddings:** ~€0.0002 per embedding
- **Target:** < €0.01 per clip (≤10 frames processed)

**Monthly Budget:** < €10 for 1,000 clips

---

## 🧪 Testing

### Test Suite (`tests/test_vision_engine.py`)

**Coverage:**
- Model validation (Pydantic)
- COCO Mapper (mappings, scoring, enrichment)
- Scene Classifier (classification, aggregation)
- Color Extractor (palette extraction, purple scoring)
- Integration tests (mocked pipeline)

**Run Tests:**
```bash
cd backend/app/ml
pytest tests/test_vision_engine.py -v
```

**Expected:** 30+ tests passing with >80% coverage

---

## 🔗 Integration Examples

### Example 1: Content Engine Integration

```python
from ml.clip_tagger import ClipTagger
from content_engine.orchestrator import ContentEngineOrchestrator

# Initialize
tagger = ClipTagger()
tagger.initialize()

# Process clip
metadata = tagger.process_video_clip(
    video_path="/path/to/clip.mp4",
    clip_id="clip_001",
    video_id="video_001"
)

# Use metadata in Content Engine
if metadata.virality_score_visual > 0.7 and metadata.aesthetic_score > 0.6:
    # High-quality clip → prioritize for publication
    content_engine.prioritize_clip(metadata.clip_id)
```

### Example 2: Satellite Engine Integration

```python
from ml.clip_tagger import ClipTagger
from satellites.scheduler import SatelliteScheduler

tagger = ClipTagger()
tagger.initialize()

# Process multiple clips
clips_metadata = [
    tagger.process_video_clip(path, clip_id, video_id)
    for path, clip_id, video_id in clip_paths
]

# Select best clip based on visual scores
best_clip = max(
    clips_metadata,
    key=lambda m: m.virality_score_visual * 0.5 + m.aesthetic_score * 0.5
)

# Publish to satellite account
scheduler.publish_clip(best_clip.clip_id, platform="instagram")
```

### Example 3: Similarity Search

```python
from ml.visual_embeddings import VisualEmbeddingsEngine

engine = VisualEmbeddingsEngine()
engine.load_model()
engine.initialize_faiss_index()

# Index all clips
for clip in clips:
    embedding = engine.generate_embedding(clip.frame, clip.id)
    engine.add_to_index(embedding, metadata={"clip_id": clip.id})

# Find similar clips
query_embedding = engine.generate_embedding(query_frame, "query")
results = engine.search_similar(query_embedding, top_k=5)

# Results contain similar clip IDs
similar_clips = [r["metadata"]["clip_id"] for r in results.similar_embeddings]
```

---

## 📊 Metrics & Telemetry

### Tracked Metrics

- **Processing Time:** Time per clip (seconds)
- **Cost:** EUR per clip
- **Objects Detected:** Number of unique objects
- **Embeddings Generated:** Count
- **Scene Classifications:** Distribution
- **Aesthetic Scores:** Purple score, brand affinity, virality

### Monitoring

```python
stats = tagger.get_pipeline_stats()

print(f"YOLO Model: {stats['yolo_model']}")
print(f"FAISS Index: {stats['embeddings_index']['total_embeddings']} embeddings")
print(f"Total Cost: €{stats['total_cost_eur']:.4f}")
```

---

## 🚀 Deployment

### Prerequisites

```bash
pip install ultralytics opencv-python pillow torch transformers faiss-cpu scikit-learn
```

### Initialization

```python
from ml.clip_tagger import ClipTagger

tagger = ClipTagger()
tagger.initialize()  # Loads YOLO + CLIP models
```

### Production Recommendations

1. **GPU:** Use CUDA for faster inference (10x speedup)
2. **Model Caching:** Download models once, cache locally
3. **Batch Processing:** Process multiple clips in batches
4. **Async Processing:** Use background workers for heavy processing
5. **FAISS Persistence:** Save FAISS index to disk periodically

---

## 🔮 Future Enhancements

### Phase 2 (Post-Sprint 3)

- [ ] **Temporal Analysis:** Track objects across frames (tracking)
- [ ] **Action Recognition:** Detect actions (dancing, driving, etc.)
- [ ] **Face Detection:** Detect and anonymize faces (privacy)
- [ ] **Audio-Visual Fusion:** Combine audio embeddings with visual
- [ ] **Optimized Models:** Export to ONNX/TensorRT for faster inference
- [ ] **Real-time Processing:** Stream processing for live content

---

## 📝 Summary

**Sprint 3: Vision Engine** is COMPLETE ✅

**Deliverables:**
- ✅ 6 core modules implemented
- ✅ 30+ tests passing
- ✅ Full integration with Content Engine
- ✅ Cost guards active (< €10/month target)
- ✅ Documentation complete

**Next Steps:**
- Integrate with Satellite Engine
- Train Rules Engine with visual features
- Optimize inference performance
- Collect production metrics

---

**🟣 STAKAZO Vision Engine - Powered by Ultralytics, CLIP, and FAISS** 🎥✨
