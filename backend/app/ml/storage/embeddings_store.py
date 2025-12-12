"""
Embeddings Store - CRUD for embeddings with dual backend support

Supports:
- FAISS (local, fast, for development/small scale)
- pgvector (cloud, scalable, for production)

Features:
- store_embedding()
- search_similar()
- delete_embedding()
- update_embedding()
- batch operations
"""

from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from pathlib import Path
import logging
import json
import time
import uuid

import numpy as np

from .schemas import (
    StoredEmbedding,
    EmbeddingType,
    EmbeddingMetadata,
    SimilaritySearchRequest,
    SimilaritySearchResponse,
    SimilaritySearchResult,
    BatchEmbeddingRequest,
    BatchEmbeddingResponse,
    EmbeddingDeletionRequest,
    EmbeddingDeletionResponse
)

logger = logging.getLogger(__name__)


class EmbeddingsStore:
    """
    Main embeddings store with dual backend support.
    
    Backends:
    - FAISS: Local, fast, good for dev/testing
    - pgvector: Cloud, scalable, good for production
    """
    
    def __init__(
        self,
        backend: str = "faiss",  # "faiss" or "pgvector"
        storage_path: Optional[str] = None,
        db_connection: Optional[Any] = None,
        dimension: int = 512  # Default CLIP dimension
    ):
        """
        Initialize embeddings store.
        
        Args:
            backend: "faiss" or "pgvector"
            storage_path: Path for FAISS indices
            db_connection: PostgreSQL connection for pgvector
            dimension: Embedding dimension
        """
        self.backend = backend
        self.dimension = dimension
        
        # Storage paths
        if storage_path:
            self.storage_path = Path(storage_path)
        else:
            self.storage_path = Path("/workspaces/stakazo/backend/storage/embeddings")
        
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Backend-specific setup
        if backend == "faiss":
            self._init_faiss()
        elif backend == "pgvector":
            self.db_connection = db_connection
            self._init_pgvector()
        else:
            raise ValueError(f"Unknown backend: {backend}")
        
        # In-memory metadata store (for FAISS)
        # TODO: Replace with proper database for production
        self.metadata_store: Dict[str, StoredEmbedding] = {}
        self._load_metadata()
        
        logger.info(f"EmbeddingsStore initialized with backend: {backend}")
    
    def _init_faiss(self):
        """Initialize FAISS backend."""
        try:
            import faiss
            self.faiss = faiss
            
            # Create indices for each embedding type
            self.indices: Dict[EmbeddingType, Any] = {}
            self.id_maps: Dict[EmbeddingType, Dict[str, int]] = {}
            
            for emb_type in EmbeddingType:
                self.indices[emb_type] = None
                self.id_maps[emb_type] = {}
                
                # Try to load existing index
                index_path = self.storage_path / f"{emb_type.value}.index"
                if index_path.exists():
                    self._load_faiss_index(emb_type)
            
            logger.info("FAISS backend initialized")
            
        except ImportError:
            logger.error("FAISS not installed. Install with: pip install faiss-cpu")
            raise
    
    def _init_pgvector(self):
        """Initialize pgvector backend."""
        if not self.db_connection:
            logger.warning("pgvector backend selected but no DB connection provided")
            return
        
        # TODO: Create pgvector tables and indices
        # CREATE EXTENSION vector;
        # CREATE TABLE embeddings (
        #     id TEXT PRIMARY KEY,
        #     type TEXT,
        #     vector vector(512),
        #     metadata JSONB
        # );
        # CREATE INDEX ON embeddings USING ivfflat (vector vector_cosine_ops);
        
        logger.info("pgvector backend initialized")
    
    def _load_metadata(self):
        """Load metadata from disk."""
        metadata_path = self.storage_path / "metadata.json"
        
        if metadata_path.exists():
            try:
                with open(metadata_path, 'r') as f:
                    data = json.load(f)
                
                for emb_id, emb_data in data.items():
                    self.metadata_store[emb_id] = StoredEmbedding(**emb_data)
                
                logger.info(f"Loaded {len(self.metadata_store)} embeddings metadata")
            except Exception as e:
                logger.error(f"Failed to load metadata: {e}")
    
    def _save_metadata(self):
        """Save metadata to disk."""
        metadata_path = self.storage_path / "metadata.json"
        
        try:
            data = {
                emb_id: emb.dict()
                for emb_id, emb in self.metadata_store.items()
            }
            
            with open(metadata_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            logger.debug(f"Saved {len(self.metadata_store)} embeddings metadata")
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")
    
    def _load_faiss_index(self, emb_type: EmbeddingType):
        """Load FAISS index from disk."""
        index_path = self.storage_path / f"{emb_type.value}.index"
        id_map_path = self.storage_path / f"{emb_type.value}_ids.json"
        
        try:
            self.indices[emb_type] = self.faiss.read_index(str(index_path))
            
            if id_map_path.exists():
                with open(id_map_path, 'r') as f:
                    # Convert string keys to int for reverse lookup
                    id_map = json.load(f)
                    self.id_maps[emb_type] = {v: int(k) for k, v in id_map.items()}
            
            logger.info(f"Loaded FAISS index for {emb_type.value}: {self.indices[emb_type].ntotal} vectors")
        except Exception as e:
            logger.error(f"Failed to load FAISS index for {emb_type.value}: {e}")
            self.indices[emb_type] = None
    
    def _save_faiss_index(self, emb_type: EmbeddingType):
        """Save FAISS index to disk."""
        if self.indices[emb_type] is None:
            return
        
        index_path = self.storage_path / f"{emb_type.value}.index"
        id_map_path = self.storage_path / f"{emb_type.value}_ids.json"
        
        try:
            self.faiss.write_index(self.indices[emb_type], str(index_path))
            
            # Save ID map (int -> embedding_id)
            id_map = {idx: emb_id for emb_id, idx in self.id_maps[emb_type].items()}
            with open(id_map_path, 'w') as f:
                json.dump(id_map, f, indent=2)
            
            logger.debug(f"Saved FAISS index for {emb_type.value}")
        except Exception as e:
            logger.error(f"Failed to save FAISS index for {emb_type.value}: {e}")
    
    async def store_embedding(
        self,
        embedding: StoredEmbedding,
        skip_if_exists: bool = True
    ) -> Dict[str, Any]:
        """
        Store a single embedding.
        
        Args:
            embedding: StoredEmbedding to store
            skip_if_exists: Skip if embedding_id already exists
            
        Returns:
            Result dict with status
        """
        # Check if exists
        if skip_if_exists and embedding.embedding_id in self.metadata_store:
            return {
                "success": False,
                "error": "ALREADY_EXISTS",
                "embedding_id": embedding.embedding_id
            }
        
        # Validate dimension
        if len(embedding.vector) != self.dimension:
            return {
                "success": False,
                "error": "DIMENSION_MISMATCH",
                "expected": self.dimension,
                "got": len(embedding.vector)
            }
        
        try:
            if self.backend == "faiss":
                result = await self._store_embedding_faiss(embedding)
            elif self.backend == "pgvector":
                result = await self._store_embedding_pgvector(embedding)
            else:
                raise ValueError(f"Unknown backend: {self.backend}")
            
            if result["success"]:
                # Update metadata store
                embedding.indexed = True
                embedding.stored_at = datetime.utcnow()
                self.metadata_store[embedding.embedding_id] = embedding
                self._save_metadata()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to store embedding {embedding.embedding_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "embedding_id": embedding.embedding_id
            }
    
    async def _store_embedding_faiss(self, embedding: StoredEmbedding) -> Dict[str, Any]:
        """Store embedding in FAISS."""
        emb_type = embedding.embedding_type
        
        # Initialize index if needed
        if self.indices[emb_type] is None:
            self.indices[emb_type] = self.faiss.IndexFlatL2(self.dimension)
            logger.info(f"Created new FAISS index for {emb_type.value}")
        
        # Convert to numpy array
        vector = np.array([embedding.vector], dtype=np.float32)
        
        # Add to index
        idx = self.indices[emb_type].ntotal
        self.indices[emb_type].add(vector)
        
        # Update ID map
        self.id_maps[emb_type][embedding.embedding_id] = idx
        
        # Save index periodically (every 10 embeddings)
        if idx % 10 == 0:
            self._save_faiss_index(emb_type)
        
        return {
            "success": True,
            "embedding_id": embedding.embedding_id,
            "index": idx,
            "backend": "faiss"
        }
    
    async def _store_embedding_pgvector(self, embedding: StoredEmbedding) -> Dict[str, Any]:
        """Store embedding in pgvector."""
        # TODO: Implement pgvector storage
        # INSERT INTO embeddings (id, type, vector, metadata) VALUES (%s, %s, %s, %s)
        
        return {
            "success": True,
            "embedding_id": embedding.embedding_id,
            "backend": "pgvector"
        }
    
    async def search_similar(
        self,
        request: SimilaritySearchRequest
    ) -> SimilaritySearchResponse:
        """
        Search for similar embeddings.
        
        Args:
            request: Search request with query vector and filters
            
        Returns:
            Search response with results
        """
        start_time = time.time()
        
        try:
            if self.backend == "faiss":
                results = await self._search_similar_faiss(request)
            elif self.backend == "pgvector":
                results = await self._search_similar_pgvector(request)
            else:
                raise ValueError(f"Unknown backend: {self.backend}")
            
            search_time_ms = (time.time() - start_time) * 1000
            
            return SimilaritySearchResponse(
                query_type=request.embedding_type,
                results=results,
                total_found=len(results),
                search_time_ms=search_time_ms,
                filters_applied=request.filters,
                index_used=self.backend
            )
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise
    
    async def _search_similar_faiss(
        self,
        request: SimilaritySearchRequest
    ) -> List[SimilaritySearchResult]:
        """Search using FAISS."""
        emb_type = request.embedding_type
        
        if self.indices[emb_type] is None or self.indices[emb_type].ntotal == 0:
            return []
        
        # Convert query to numpy
        query = np.array([request.query_vector], dtype=np.float32)
        
        # Search
        k = min(request.top_k, self.indices[emb_type].ntotal)
        distances, indices = self.indices[emb_type].search(query, k)
        
        # Convert results
        results = []
        reverse_id_map = {idx: emb_id for emb_id, idx in self.id_maps[emb_type].items()}
        
        for rank, (distance, idx) in enumerate(zip(distances[0], indices[0])):
            if idx == -1:  # No result
                continue
            
            embedding_id = reverse_id_map.get(idx)
            if not embedding_id:
                continue
            
            # Convert L2 distance to similarity score (0-1)
            similarity_score = 1.0 / (1.0 + float(distance))
            
            # Apply min_score filter
            if request.min_score and similarity_score < request.min_score:
                continue
            
            # Get metadata if requested
            embedding = None
            metadata = None
            if request.include_metadata and embedding_id in self.metadata_store:
                stored_emb = self.metadata_store[embedding_id]
                metadata = stored_emb.metadata
                if request.include_metadata:
                    embedding = stored_emb
            
            # Apply filters
            if request.filters and metadata:
                skip = False
                for key, value in request.filters.items():
                    if hasattr(metadata, key) and getattr(metadata, key) != value:
                        skip = True
                        break
                if skip:
                    continue
            
            results.append(SimilaritySearchResult(
                embedding_id=embedding_id,
                similarity_score=similarity_score,
                distance=float(distance),
                embedding=embedding,
                metadata=metadata,
                rank=rank + 1
            ))
        
        return results[:request.top_k]
    
    async def _search_similar_pgvector(
        self,
        request: SimilaritySearchRequest
    ) -> List[SimilaritySearchResult]:
        """Search using pgvector."""
        # TODO: Implement pgvector search
        # SELECT id, vector <=> %s as distance FROM embeddings ORDER BY distance LIMIT %s
        
        return []
    
    async def delete_embedding(
        self,
        request: EmbeddingDeletionRequest
    ) -> EmbeddingDeletionResponse:
        """
        Delete embeddings.
        
        Args:
            request: Deletion request with IDs or filters
            
        Returns:
            Deletion response
        """
        if not request.confirm_deletion:
            return EmbeddingDeletionResponse(
                deleted_count=0,
                deleted_ids=[],
                dry_run=True
            )
        
        deleted_ids = []
        errors = {}
        
        # Delete by IDs
        if request.embedding_ids:
            for emb_id in request.embedding_ids:
                try:
                    if emb_id in self.metadata_store:
                        del self.metadata_store[emb_id]
                        deleted_ids.append(emb_id)
                    else:
                        errors[emb_id] = "NOT_FOUND"
                except Exception as e:
                    errors[emb_id] = str(e)
        
        # TODO: Delete by filters
        
        # Save metadata
        if deleted_ids:
            self._save_metadata()
            # TODO: Rebuild indices
        
        return EmbeddingDeletionResponse(
            deleted_count=len(deleted_ids),
            deleted_ids=deleted_ids,
            errors=errors
        )
    
    async def update_embedding(
        self,
        embedding_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update embedding metadata.
        
        Args:
            embedding_id: ID of embedding to update
            updates: Fields to update
            
        Returns:
            Result dict
        """
        if embedding_id not in self.metadata_store:
            return {
                "success": False,
                "error": "NOT_FOUND",
                "embedding_id": embedding_id
            }
        
        try:
            embedding = self.metadata_store[embedding_id]
            
            # Update metadata fields
            for key, value in updates.items():
                if hasattr(embedding.metadata, key):
                    setattr(embedding.metadata, key, value)
            
            embedding.updated_at = datetime.utcnow()
            self.metadata_store[embedding_id] = embedding
            self._save_metadata()
            
            return {
                "success": True,
                "embedding_id": embedding_id,
                "updated_fields": list(updates.keys())
            }
            
        except Exception as e:
            logger.error(f"Failed to update embedding {embedding_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "embedding_id": embedding_id
            }
    
    async def batch_store(
        self,
        request: BatchEmbeddingRequest
    ) -> BatchEmbeddingResponse:
        """
        Store multiple embeddings in batch.
        
        Args:
            request: Batch request with embeddings
            
        Returns:
            Batch response with results
        """
        start_time = time.time()
        batch_id = request.batch_id or f"batch_{uuid.uuid4().hex[:8]}"
        
        stored = 0
        skipped = 0
        failed = 0
        failed_ids = []
        errors = {}
        
        for embedding in request.embeddings:
            result = await self.store_embedding(
                embedding,
                skip_if_exists=request.skip_if_exists
            )
            
            if result["success"]:
                stored += 1
            elif result.get("error") == "ALREADY_EXISTS":
                skipped += 1
            else:
                failed += 1
                failed_ids.append(embedding.embedding_id)
                errors[embedding.embedding_id] = result.get("error", "UNKNOWN")
        
        # Rebuild indices if requested
        if request.rebuild_index:
            for emb_type in EmbeddingType:
                if self.indices.get(emb_type):
                    self._save_faiss_index(emb_type)
        
        processing_time_ms = (time.time() - start_time) * 1000
        
        return BatchEmbeddingResponse(
            batch_id=batch_id,
            total_requested=len(request.embeddings),
            stored=stored,
            skipped=skipped,
            failed=failed,
            processing_time_ms=processing_time_ms,
            failed_ids=failed_ids,
            errors=errors
        )
    
    def get_stats(self, emb_type: Optional[EmbeddingType] = None) -> Dict[str, Any]:
        """Get statistics for embeddings store."""
        if self.backend == "faiss":
            if emb_type:
                total = self.indices[emb_type].ntotal if self.indices[emb_type] else 0
                return {
                    "embedding_type": emb_type.value,
                    "total_embeddings": total,
                    "backend": "faiss"
                }
            else:
                return {
                    "backend": "faiss",
                    "total_embeddings": sum(
                        idx.ntotal for idx in self.indices.values() if idx
                    ),
                    "by_type": {
                        emb_type.value: idx.ntotal
                        for emb_type, idx in self.indices.items() if idx
                    }
                }
        else:
            return {
                "backend": "pgvector",
                "total_embeddings": len(self.metadata_store)
            }
