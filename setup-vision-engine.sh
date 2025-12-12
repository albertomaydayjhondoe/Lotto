#!/bin/bash

# Sprint 3 - Vision Engine Setup Script
# Instala dependencias ML y descarga modelos

set -e

echo "🟣 SPRINT 3 - VISION ENGINE SETUP"
echo "=================================="
echo ""

# 1. Instalar dependencias Python
echo "📦 Instalando dependencias Python..."
cd /workspaces/stakazo/backend
pip install -r requirements.txt --quiet

echo "✅ Dependencias instaladas"
echo ""

# 2. Descargar modelos YOLO (opcional, se descarga en primer uso)
echo "🎯 Preparando modelos YOLO..."
python -c "
try:
    from ultralytics import YOLO
    print('   → Descargando YOLOv8n...')
    model = YOLO('yolov8n.pt')
    print('   ✅ YOLOv8n listo')
except Exception as e:
    print(f'   ⚠️  YOLO download skipped: {e}')
" || echo "   ⚠️  YOLO se descargará en primer uso"

echo ""

# 3. Descargar modelos CLIP (opcional)
echo "🖼️  Preparando modelos CLIP..."
python -c "
try:
    from transformers import CLIPModel, CLIPProcessor
    print('   → Descargando CLIP ViT-Base...')
    model = CLIPModel.from_pretrained('openai/clip-vit-base-patch32')
    processor = CLIPProcessor.from_pretrained('openai/clip-vit-base-patch32')
    print('   ✅ CLIP ViT-Base listo')
except Exception as e:
    print(f'   ⚠️  CLIP download skipped: {e}')
" || echo "   ⚠️  CLIP se descargará en primer uso"

echo ""

# 4. Verificar instalación
echo "🔍 Verificando instalación..."
python -c "
import sys
modules = [
    'ultralytics',
    'cv2',
    'PIL',
    'torch',
    'transformers',
    'faiss',
    'sklearn',
    'numpy'
]

missing = []
for module in modules:
    try:
        __import__(module)
        print(f'   ✅ {module}')
    except ImportError:
        print(f'   ❌ {module} - NOT FOUND')
        missing.append(module)

if missing:
    print(f'\n⚠️  Missing modules: {missing}')
    sys.exit(1)
else:
    print('\n✅ All modules installed successfully')
"

echo ""
echo "🎉 Vision Engine setup complete!"
echo ""
echo "Next steps:"
echo "  1. Initialize Vision Engine in your code:"
echo "     from ml.clip_tagger import ClipTagger"
echo "     tagger = ClipTagger()"
echo "     tagger.initialize()"
echo ""
echo "  2. Run tests:"
echo "     pytest app/ml/tests/test_vision_engine.py -v"
echo ""
echo "  3. Process a video:"
echo "     metadata = tagger.process_video_clip('video.mp4', 'clip_001', 'video_001')"
echo ""
