# 🟣 Vision Engine - ML Module

**Sprint 3: Complete Visual Intelligence for STAKAZO**

---

## Quick Start

### 1. Install Dependencies

```bash
./setup-vision-engine.sh
```

### 2. Initialize Vision Engine

```python
from ml.clip_tagger import ClipTagger

tagger = ClipTagger()
tagger.initialize()  # Loads YOLO + CLIP models (~30s first time)
```

### 3. Process a Video Clip

```python
metadata = tagger.process_video_clip(
    video_path="path/to/video.mp4",
    clip_id="clip_001",
    video_id="video_001",
    max_frames=30
)

print(f"Objects: {metadata.objects_detected}")
print(f"Scene: {metadata.dominant_scene}")
print(f"Virality Score: {metadata.virality_score_visual}")
print(f"Purple Score: {metadata.color_palette.purple_score}")
```

---

## Module Structure

```
ml/
├── __init__.py               # Module exports
├── models.py                 # Pydantic models (400+ lines)
├── yolo_runner.py            # YOLO object detection (350+ lines)
├── coco_mapper.py            # Semantic mapping (400+ lines)
├── visual_embeddings.py      # CLIP + FAISS (450+ lines)
├── scene_classifier.py       # Scene classification (400+ lines)
├── color_extractor.py        # Color extraction (350+ lines)
├── clip_tagger.py            # Pipeline orchestrator (500+ lines)
└── tests/
    ├── __init__.py
    └── test_vision_engine.py # 30+ tests (600+ lines)
```

**Total:** ~3,800 lines of code

---

## Core Components

### 1. YOLO Runner

**Object detection using Ultralytics YOLOv8/v11**

```python
from ml.yolo_runner import YOLORunner

runner = YOLORunner()
runner.load_model("yolov8n.pt")

# Process video
detections = runner.detect_video(
    "video.mp4",
    max_frames=30,
    target_fps=1.0
)
```

**Output:** List of `FrameDetections` with 80 COCO classes

---

### 2. COCO Mapper

**Semantic enrichment (COCO → Stakazo tags)**

```python
from ml.coco_mapper import COCOMapper

mapper = COCOMapper()
enriched = mapper.enrich_detection(yolo_detection)

# "car" → ["coche", "asfalto", "velocidad", "trap-street"]
# affinity_score: 0.85, virality_score: 0.72
```

**Output:** `EnrichedDetection` with semantic tags + scores

---

### 3. Visual Embeddings

**CLIP embeddings + FAISS similarity**

```python
from ml.visual_embeddings import VisualEmbeddingsEngine

engine = VisualEmbeddingsEngine()
engine.load_model("clip-vit-base-patch32")
engine.initialize_faiss_index(dimension=512)

# Generate embedding
embedding = engine.generate_embedding(frame, "emb_001")

# Search similar
results = engine.search_similar(embedding, top_k=5)
```

**Output:** 512-dim embeddings + similarity search

---

### 4. Scene Classifier

**Contextual scene detection**

```python
from ml.scene_classifier import SceneClassifier

classifier = SceneClassifier()
scenes = classifier.classify_frame(detections, color_palette)

# Detects: calle, coche, noche, club, trap_house, costa, etc.
```

**Output:** List of `SceneClassification` with confidence scores

---

### 5. Color Extractor

**Dominant palette + purple aesthetic**

```python
from ml.color_extractor import ColorExtractor

extractor = ColorExtractor(num_colors=5)
palette = extractor.extract_palette(frame)

# colors_hex: ["#8B44FF", "#1A1A2E", ...]
# purple_score: 0.75
```

**Output:** `ColorPalette` with hex colors + aesthetic scores

---

### 6. Clip Tagger

**Complete pipeline orchestrator**

```python
from ml.clip_tagger import ClipTagger

tagger = ClipTagger()
tagger.initialize()

metadata = tagger.process_video_clip(
    video_path="video.mp4",
    clip_id="clip_001",
    video_id="video_001"
)
```

**Output:** `ClipMetadata` with:
- YOLO detections + COCO mappings
- Visual embeddings
- Scene classifications
- Color palette
- Virality/brand affinity/aesthetic scores
- Processing cost (€)

---

## Configuration

```python
from ml.models import VisionConfig

config = VisionConfig(
    yolo_model="yolov8n.pt",
    yolo_confidence_threshold=0.25,
    target_fps=1.0,
    max_frames_per_clip=30,
    embedding_model="clip-vit-base-patch32",
    use_faiss=True,
    max_cost_per_clip_eur=0.01
)

tagger = ClipTagger(config)
```

---

## Testing

```bash
# Run all ML tests
pytest app/ml/tests/test_vision_engine.py -v

# Run with coverage
pytest app/ml/tests --cov=ml --cov-report=html
```

**Expected:** 30+ tests passing, >80% coverage

---

## Cost Optimization

- **FPS Throttling:** 1 FPS default (30x reduction)
- **Frame Sampling:** Max 30 frames per clip
- **Batch Processing:** Multiple frames at once
- **Model Selection:** YOLOv8n (nano) for speed

**Target:** < €0.01 per clip (< €10/month for 1,000 clips)

---

## Integration Examples

### With Content Engine

```python
from ml.clip_tagger import ClipTagger
from content_engine.clip_selector import ClipSelector

# Process clips
tagger = ClipTagger()
tagger.initialize()

clips_metadata = [
    tagger.process_video_clip(path, clip_id, video_id)
    for path, clip_id, video_id in video_paths
]

# Select best
selector = ClipSelector()
best = selector.select_best_clips(
    clips_metadata,
    top_k=5,
    min_score=0.6,
    filters={"dominant_scene": "coche"}
)
```

### With Satellite Engine

```python
from ml.clip_tagger import ClipTagger
from satellites.scheduler import SatelliteScheduler

tagger = ClipTagger()
tagger.initialize()

metadata = tagger.process_video_clip("clip.mp4", "clip_001", "video_001")

# Publish if high quality
if metadata.virality_score_visual > 0.7 and metadata.aesthetic_score > 0.6:
    scheduler.publish_clip(metadata.clip_id, platform="instagram")
```

---

## Performance

### Benchmarks (CPU)

- **YOLO inference:** ~50ms per frame
- **CLIP embedding:** ~100ms per frame
- **Total pipeline:** ~5s for 30 frames @ 1 FPS

### With GPU (CUDA)

- **10x faster:** ~500ms for 30 frames

---

## Dependencies

```
ultralytics==8.1.0
opencv-python==4.8.1.78
pillow==10.1.0
torch==2.1.1
torchvision==0.16.1
transformers==4.36.0
faiss-cpu==1.7.4
scikit-learn==1.3.2
numpy==1.24.3
```

---

## Documentation

- **Full docs:** `/workspaces/stakazo/docs/vision_engine.md`
- **Sprint summary:** `/workspaces/stakazo/SPRINT3_SUMMARY.md`
- **Tests:** `/workspaces/stakazo/backend/app/ml/tests/`

---

## Next Steps

1. **Satellite Engine Integration:** Use visual metadata for publication decisions
2. **Rules Engine:** Add visual-based rules for virality prediction
3. **Dashboard:** Visualize color palettes, scenes, objects
4. **Optimization:** Export to ONNX/TensorRT, GPU inference

---

**🟣 STAKAZO Vision Engine - Sprint 3 COMPLETE ✅**
