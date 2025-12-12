"""
Visual Embeddings Engine - CLIP + FAISS Integration

Sprint 3: Vision Engine

Features:
- CLIP (Contrastive Language-Image Pre-training) embeddings
- Vision Transformer embeddings
- FAISS vector similarity search
- Embedding persistence and retrieval
- Clip-level similarity for content discovery
"""

import logging
import time
from typing import List, Optional, Dict, Any, Tuple
import numpy as np
from pathlib import Path

try:
    from transformers import CLIPProcessor, CLIPModel
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logging.warning("Transformers not installed. CLIP embeddings will fail.")

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    logging.warning("FAISS not installed. Similarity search will be limited.")

from PIL import Image

from .models import VisualEmbedding, SimilarityResult, VisionConfig

logger = logging.getLogger(__name__)


class VisualEmbeddingsEngine:
    """
    Visual embeddings generation and similarity search.
    
    Uses:
    - CLIP for robust visual embeddings
    - FAISS for fast similarity search
    - Supports both frame-level and clip-level embeddings
    """
    
    def __init__(self, config: Optional[VisionConfig] = None):
        """
        Initialize visual embeddings engine.
        
        Args:
            config: Vision configuration
        """
        self.config = config or VisionConfig()
        self.model: Optional[Any] = None
        self.processor: Optional[Any] = None
        self.device = self._detect_device()
        
        # FAISS index
        self.faiss_index: Optional[Any] = None
        self.embedding_metadata: Dict[str, Dict] = {}  # embedding_id -> metadata
        
        logger.info(
            f"VisualEmbeddingsEngine initialized with model={self.config.embedding_model}, "
            f"device={self.device}, faiss_enabled={self.config.use_faiss}"
        )
    
    def _detect_device(self) -> str:
        """Detect best available device."""
        try:
            import torch
            if torch.cuda.is_available():
                return "cuda"
        except:
            pass
        return "cpu"
    
    def load_model(self, model_name: Optional[str] = None) -> None:
        """
        Load CLIP model from HuggingFace.
        
        Args:
            model_name: Model name. If None, uses config.embedding_model.
        
        Raises:
            RuntimeError: If transformers is not installed
        """
        if not TRANSFORMERS_AVAILABLE:
            raise RuntimeError(
                "Transformers not installed. Install with: pip install transformers"
            )
        
        model_name = model_name or self.config.embedding_model
        
        # Map friendly names to HuggingFace model IDs
        model_mapping = {
            "clip-vit-base-patch32": "openai/clip-vit-base-patch32",
            "clip-vit-large-patch14": "openai/clip-vit-large-patch14",
        }
        
        hf_model_name = model_mapping.get(model_name, model_name)
        
        try:
            logger.info(f"Loading CLIP model: {hf_model_name}...")
            self.processor = CLIPProcessor.from_pretrained(hf_model_name)
            self.model = CLIPModel.from_pretrained(hf_model_name).to(self.device)
            self.model.eval()
            logger.info(f"✅ CLIP model loaded successfully: {hf_model_name}")
        except Exception as e:
            logger.error(f"Failed to load CLIP model: {e}")
            raise RuntimeError(f"CLIP model load failed: {e}")
    
    def generate_embedding(
        self,
        image: np.ndarray,
        embedding_id: str,
        frame_id: Optional[int] = None,
        timestamp_ms: Optional[float] = None
    ) -> VisualEmbedding:
        """
        Generate CLIP embedding for a single image.
        
        Args:
            image: Image as numpy array (H, W, 3) RGB
            embedding_id: Unique ID for this embedding
            frame_id: Optional frame index
            timestamp_ms: Optional timestamp
        
        Returns:
            VisualEmbedding with vector
        """
        if self.model is None or self.processor is None:
            raise RuntimeError("CLIP model not loaded. Call load_model() first.")
        
        try:
            # Convert numpy to PIL
            if isinstance(image, np.ndarray):
                pil_image = Image.fromarray(image.astype('uint8'), 'RGB')
            else:
                pil_image = image
            
            # Process image
            inputs = self.processor(images=pil_image, return_tensors="pt")
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Generate embedding
            with torch.no_grad():
                image_features = self.model.get_image_features(**inputs)
                # Normalize embedding
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)
                embedding_vector = image_features.cpu().numpy()[0].tolist()
            
            return VisualEmbedding(
                embedding_id=embedding_id,
                vector=embedding_vector,
                model_name=self.config.embedding_model,
                frame_id=frame_id,
                timestamp_ms=timestamp_ms
            )
        
        except Exception as e:
            logger.error(f"Failed to generate embedding for {embedding_id}: {e}")
            raise
    
    def generate_batch_embeddings(
        self,
        images: List[np.ndarray],
        embedding_ids: List[str],
        frame_ids: Optional[List[int]] = None,
        timestamps_ms: Optional[List[float]] = None
    ) -> List[VisualEmbedding]:
        """
        Generate embeddings for a batch of images (more efficient).
        
        Args:
            images: List of images as numpy arrays
            embedding_ids: List of unique IDs
            frame_ids: Optional list of frame indices
            timestamps_ms: Optional list of timestamps
        
        Returns:
            List of VisualEmbeddings
        """
        if self.model is None or self.processor is None:
            raise RuntimeError("CLIP model not loaded. Call load_model() first.")
        
        if frame_ids is None:
            frame_ids = [None] * len(images)
        if timestamps_ms is None:
            timestamps_ms = [None] * len(images)
        
        try:
            # Convert to PIL images
            pil_images = []
            for img in images:
                if isinstance(img, np.ndarray):
                    pil_images.append(Image.fromarray(img.astype('uint8'), 'RGB'))
                else:
                    pil_images.append(img)
            
            # Process batch
            inputs = self.processor(images=pil_images, return_tensors="pt", padding=True)
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Generate embeddings
            with torch.no_grad():
                image_features = self.model.get_image_features(**inputs)
                # Normalize
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)
                embedding_vectors = image_features.cpu().numpy()
            
            # Create VisualEmbedding objects
            embeddings = []
            for i in range(len(images)):
                embedding = VisualEmbedding(
                    embedding_id=embedding_ids[i],
                    vector=embedding_vectors[i].tolist(),
                    model_name=self.config.embedding_model,
                    frame_id=frame_ids[i],
                    timestamp_ms=timestamps_ms[i]
                )
                embeddings.append(embedding)
            
            logger.info(f"✅ Generated {len(embeddings)} embeddings in batch")
            return embeddings
        
        except Exception as e:
            logger.error(f"Batch embedding generation failed: {e}")
            raise
    
    def average_embeddings(self, embeddings: List[VisualEmbedding]) -> List[float]:
        """
        Average multiple embeddings into a single clip-level embedding.
        
        Args:
            embeddings: List of VisualEmbeddings
        
        Returns:
            Averaged embedding vector
        """
        if not embeddings:
            raise ValueError("Cannot average empty embeddings list")
        
        vectors = np.array([e.vector for e in embeddings])
        avg_vector = np.mean(vectors, axis=0)
        
        # Normalize
        norm = np.linalg.norm(avg_vector)
        if norm > 0:
            avg_vector = avg_vector / norm
        
        return avg_vector.tolist()
    
    def initialize_faiss_index(self, dimension: int = 512) -> None:
        """
        Initialize FAISS index for similarity search.
        
        Args:
            dimension: Embedding dimension (512 for CLIP base, 768 for large)
        """
        if not FAISS_AVAILABLE:
            logger.warning("FAISS not available. Similarity search will be disabled.")
            return
        
        if not self.config.use_faiss:
            logger.info("FAISS disabled in config.")
            return
        
        try:
            # Use L2 distance (cosine similarity after normalization)
            self.faiss_index = faiss.IndexFlatL2(dimension)
            logger.info(f"✅ FAISS index initialized with dimension={dimension}")
        except Exception as e:
            logger.error(f"Failed to initialize FAISS: {e}")
            self.faiss_index = None
    
    def add_to_index(self, embedding: VisualEmbedding, metadata: Optional[Dict] = None) -> None:
        """
        Add an embedding to FAISS index.
        
        Args:
            embedding: VisualEmbedding to add
            metadata: Optional metadata to store with embedding
        """
        if self.faiss_index is None:
            if self.config.use_faiss and FAISS_AVAILABLE:
                self.initialize_faiss_index(dimension=len(embedding.vector))
            else:
                logger.warning("FAISS index not available. Skipping add.")
                return
        
        # Add vector to FAISS
        vector = np.array([embedding.vector], dtype=np.float32)
        self.faiss_index.add(vector)
        
        # Store metadata
        idx = self.faiss_index.ntotal - 1
        self.embedding_metadata[str(idx)] = {
            "embedding_id": embedding.embedding_id,
            "frame_id": embedding.frame_id,
            "timestamp_ms": embedding.timestamp_ms,
            **(metadata or {})
        }
        
        logger.debug(f"Added embedding {embedding.embedding_id} to FAISS (idx={idx})")
    
    def search_similar(
        self,
        query_embedding: VisualEmbedding,
        top_k: int = 5
    ) -> SimilarityResult:
        """
        Search for similar embeddings using FAISS.
        
        Args:
            query_embedding: Query embedding
            top_k: Number of results to return
        
        Returns:
            SimilarityResult with similar embeddings
        """
        if self.faiss_index is None or self.faiss_index.ntotal == 0:
            logger.warning("FAISS index is empty or not initialized.")
            return SimilarityResult(
                query_embedding_id=query_embedding.embedding_id,
                similar_embeddings=[],
                search_time_ms=0.0
            )
        
        start_time = time.time()
        
        try:
            # Query vector
            query_vector = np.array([query_embedding.vector], dtype=np.float32)
            
            # Search
            distances, indices = self.faiss_index.search(query_vector, min(top_k, self.faiss_index.ntotal))
            
            # Build results
            similar_embeddings = []
            for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
                if idx == -1:  # FAISS returns -1 for invalid indices
                    continue
                
                metadata = self.embedding_metadata.get(str(idx), {})
                similar_embeddings.append({
                    "rank": i + 1,
                    "embedding_id": metadata.get("embedding_id", f"idx_{idx}"),
                    "distance": float(dist),
                    "similarity": float(1.0 / (1.0 + dist)),  # Convert distance to similarity
                    "metadata": metadata
                })
            
            search_time_ms = (time.time() - start_time) * 1000
            
            return SimilarityResult(
                query_embedding_id=query_embedding.embedding_id,
                similar_embeddings=similar_embeddings,
                search_time_ms=search_time_ms
            )
        
        except Exception as e:
            logger.error(f"FAISS search failed: {e}")
            return SimilarityResult(
                query_embedding_id=query_embedding.embedding_id,
                similar_embeddings=[],
                search_time_ms=(time.time() - start_time) * 1000
            )
    
    def cosine_similarity(self, emb1: VisualEmbedding, emb2: VisualEmbedding) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            emb1: First embedding
            emb2: Second embedding
        
        Returns:
            Cosine similarity (0-1)
        """
        vec1 = np.array(emb1.vector)
        vec2 = np.array(emb2.vector)
        
        # Cosine similarity
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        similarity = dot_product / (norm1 * norm2)
        
        # Clamp to [0, 1]
        return float(max(0.0, min(1.0, (similarity + 1) / 2)))
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics about the FAISS index."""
        if self.faiss_index is None:
            return {
                "initialized": False,
                "total_embeddings": 0
            }
        
        return {
            "initialized": True,
            "total_embeddings": self.faiss_index.ntotal,
            "dimension": self.faiss_index.d if hasattr(self.faiss_index, 'd') else None,
            "model_name": self.config.embedding_model
        }
