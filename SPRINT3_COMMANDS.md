# 🟣 Sprint 3 - Vision Engine - Comandos Útiles

## 🚀 Setup Inicial

```bash
# 1. Instalar dependencias + descargar modelos
./setup-vision-engine.sh

# 2. Verificar instalación
cd backend
python -c "from ml.clip_tagger import ClipTagger; print('✅ ML module ready')"
```

---

## 🧪 Testing

```bash
# Tests ML completos
cd backend
pytest app/ml/tests/test_vision_engine.py -v

# Tests Content Engine (ClipSelector)
pytest app/content_engine/tests/test_clip_selector.py -v

# Todos los tests Vision Engine
pytest app/ml/tests app/content_engine/tests -v

# Con coverage
pytest app/ml/tests --cov=ml --cov-report=html
pytest app/content_engine/tests --cov=content_engine --cov-report=html

# Tests específicos
pytest app/ml/tests/test_vision_engine.py::test_coco_mapper_initialization -v
```

---

## 💻 Uso en Código

### Example 1: Procesar un clip

```python
from ml.clip_tagger import ClipTagger

tagger = ClipTagger()
tagger.initialize()

metadata = tagger.process_video_clip(
    video_path="path/to/video.mp4",
    clip_id="clip_001",
    video_id="video_001",
    max_frames=30
)

print(f"Objects: {metadata.objects_detected}")
print(f"Scene: {metadata.dominant_scene}")
print(f"Virality: {metadata.virality_score_visual:.2f}")
print(f"Purple: {metadata.color_palette.purple_score:.2f}")
```

### Example 2: Seleccionar mejores clips

```python
from content_engine.clip_selector import ClipSelector

selector = ClipSelector()

best = selector.select_best_clips(
    clips_metadata,
    top_k=5,
    min_score=0.6,
    filters={"dominant_scene": "coche", "min_purple_score": 0.5}
)

for clip in best:
    print(f"{clip.clip_id}: {selector.score_clip(clip):.2f}")
```

### Example 3: Recomendación de publicación

```python
rec = selector.get_publication_recommendation(metadata, platform="instagram")

if rec["recommendation"] == "publish_immediately":
    # Publicar ahora
    publish_to_instagram(clip.clip_id)
```

### Example 4: Búsqueda por similitud

```python
from ml.visual_embeddings import VisualEmbeddingsEngine

engine = VisualEmbeddingsEngine()
engine.load_model()
engine.initialize_faiss_index()

# Indexar clips
for clip in clips:
    embedding = engine.generate_embedding(clip.frame, clip.id)
    engine.add_to_index(embedding, metadata={"clip_id": clip.id})

# Buscar similares
query_embedding = engine.generate_embedding(query_frame, "query")
results = engine.search_similar(query_embedding, top_k=5)

print(f"Similar clips: {[r['metadata']['clip_id'] for r in results.similar_embeddings]}")
```

---

## 🔧 Debugging

### Ver detecciones YOLO

```python
from ml.yolo_runner import YOLORunner
import cv2

runner = YOLORunner()
runner.load_model()

# Procesar un frame
cap = cv2.VideoCapture("video.mp4")
ret, frame = cap.read()
frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

detections = runner.detect_frame(frame_rgb, frame_id=0, timestamp_ms=0.0)

for det in detections.detections:
    print(f"{det.label}: {det.confidence:.2f} at ({det.bbox.x}, {det.bbox.y})")
```

### Ver mappings COCO

```python
from ml.coco_mapper import COCOMapper

mapper = COCOMapper()

# Ver mapeo de "car"
print(mapper.SEMANTIC_MAPPINGS["car"])
# Output: {"tags": ["coche", "asfalto", ...], "affinity": 0.85, "virality": 0.72}
```

### Ver estadísticas del pipeline

```python
stats = tagger.get_pipeline_stats()

print(f"YOLO: {stats['yolo_model']}")
print(f"FAISS: {stats['embeddings_index']['total_embeddings']} embeddings")
print(f"Cost: €{stats['total_cost_eur']:.4f}")
```

---

## 📊 Performance Testing

### Benchmark de procesamiento

```python
import time

start = time.time()

metadata = tagger.process_video_clip("video.mp4", "clip_001", "video_001")

elapsed = time.time() - start

print(f"Processing time: {elapsed:.2f}s")
print(f"Frames processed: {len(metadata.embeddings)}")
print(f"Time per frame: {elapsed / len(metadata.embeddings):.2f}s")
print(f"Cost: €{metadata.processing_cost_eur:.4f}")
```

---

## 🐛 Troubleshooting

### Error: "Ultralytics not installed"

```bash
pip install ultralytics
```

### Error: "CLIP model not found"

```bash
# Descargar manualmente
python -c "from transformers import CLIPModel; CLIPModel.from_pretrained('openai/clip-vit-base-patch32')"
```

### Error: "FAISS not available"

```bash
pip install faiss-cpu
# O para GPU:
pip install faiss-gpu
```

### Error: "scikit-learn not installed"

```bash
pip install scikit-learn
```

### Performance lento (CPU)

```python
# Opción 1: Usar GPU
config = VisionConfig(yolo_device="cuda")

# Opción 2: Reducir frames
config = VisionConfig(target_fps=0.5, max_frames_per_clip=10)

# Opción 3: Desactivar FAISS
config = VisionConfig(use_faiss=False)
```

---

## 📈 Monitoreo en Producción

```python
# Telemetría
from ml.clip_tagger import ClipTagger

tagger = ClipTagger()
tagger.initialize()

# Procesar múltiples clips
for video_path, clip_id, video_id in clips:
    metadata = tagger.process_video_clip(video_path, clip_id, video_id)
    
    # Log metrics
    print(f"Clip: {clip_id}")
    print(f"  Cost: €{metadata.processing_cost_eur:.4f}")
    print(f"  Time: {metadata.processing_time_ms:.0f}ms")
    print(f"  Virality: {metadata.virality_score_visual:.2f}")

# Stats finales
stats = tagger.get_pipeline_stats()
print(f"\nTotal cost: €{stats['total_cost_eur']:.4f}")
```

---

## 🔄 Integración con Satellite Engine (Próximo)

```python
# TODO: Sprint 4
from ml.clip_tagger import ClipTagger
from satellites.scheduler import SatelliteScheduler

tagger = ClipTagger()
tagger.initialize()

metadata = tagger.process_video_clip("video.mp4", "clip_001", "video_001")

# Si score es alto, publicar
if metadata.virality_score_visual > 0.7 and metadata.aesthetic_score > 0.6:
    scheduler = SatelliteScheduler()
    scheduler.publish_clip(
        clip_id=metadata.clip_id,
        platform="instagram",
        priority="high",
        visual_metadata=metadata
    )
```

---

## 🔮 Próximas Mejoras (Post-Sprint 3)

1. **GPU Optimization**
   ```bash
   # Install CUDA + cuDNN
   pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
   ```

2. **ONNX Export** (10x faster)
   ```python
   # Export YOLO to ONNX
   from ultralytics import YOLO
   model = YOLO("yolov8n.pt")
   model.export(format="onnx")
   ```

3. **Real-time Processing**
   ```python
   # Stream processing
   import asyncio
   
   async def process_stream(video_stream):
       async for frame in video_stream:
           metadata = await tagger.process_frame_async(frame)
           yield metadata
   ```

4. **Temporal Tracking**
   ```python
   # Track objects across frames
   from ml.temporal_tracker import TemporalTracker
   
   tracker = TemporalTracker()
   tracked_objects = tracker.track(detections_sequence)
   ```

---

## 📚 Referencias

- **Documentación completa:** `/workspaces/stakazo/docs/vision_engine.md`
- **Sprint summary:** `/workspaces/stakazo/SPRINT3_SUMMARY.md`
- **ML README:** `/workspaces/stakazo/backend/app/ml/README.md`
- **Example usage:** `/workspaces/stakazo/backend/app/ml/example_usage.py`
- **Tests:** `/workspaces/stakazo/backend/app/ml/tests/`

---

**🟣 STAKAZO Vision Engine - Sprint 3 COMPLETE ✅**
