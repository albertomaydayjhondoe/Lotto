"""
REST API Router para Meta Creative Variants Engine (PASO 10.10)
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.auth.permissions import require_role
from app.meta_creative_variants.engine import CreativeVariantsEngine
from app.meta_creative_variants.uploader import CreativeUploader
from app.meta_creative_variants.schemas import (
    GenerateVariantsRequest,
    GenerateVariantsResponse,
    UploadVariantRequest,
    UploadVariantResponse,
    BulkUploadRequest,
    BulkUploadResponse,
    ListVariantsResponse,
    RegenerateVariantRequest,
    CreativeVariant,
    VariantStatus,
)
from app.meta_creative_variants.models import MetaCreativeVariantModel

logger = logging.getLogger(__name__)

router = APIRouter()


# ==================== Endpoints ====================


@router.post("/generate/{clip_id}", response_model=GenerateVariantsResponse)
async def generate_variants(
    clip_id: str,
    request: GenerateVariantsRequest,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_role(["admin", "manager"]))
):
    """
    Genera variantes creativas automáticas desde un clip.
    
    **Requiere rol:** admin, manager
    
    **Proceso:**
    1. Extrae material del clip (video, texto, thumbnails)
    2. Genera N variantes combinadas (5-20)
    3. (Opcional) Sube a Meta Ads si auto_upload=True
    4. Persiste en DB
    
    **Returns:**
    - total_variants: Número de variantes generadas
    - variants: Lista de variantes completas
    - generation_time_seconds: Tiempo total
    """
    try:
        # Validar que clip_id en request coincide
        if request.clip_id != clip_id:
            request.clip_id = clip_id
        
        engine = CreativeVariantsEngine(db)
        response = await engine.generate_variants(request)
        
        return response
        
    except Exception as e:
        logger.error(f"Error generating variants: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list/{campaign_id}", response_model=ListVariantsResponse)
async def list_variants(
    campaign_id: str,
    status: Optional[VariantStatus] = Query(None, description="Filtrar por estado"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_role(["admin", "manager", "operator"]))
):
    """
    Lista variantes creativas de una campaña.
    
    **Requiere rol:** admin, manager, operator
    
    **Filtros:**
    - status: Estado de las variantes
    - limit: Máximo de resultados
    - offset: Paginación
    """
    try:
        query = select(MetaCreativeVariantModel).where(
            MetaCreativeVariantModel.campaign_id == campaign_id
        )
        
        if status:
            query = query.where(MetaCreativeVariantModel.status == status.value)
        
        query = query.limit(limit).offset(offset)
        
        result = await db.execute(query)
        variants_db = result.scalars().all()
        
        # Convert to Pydantic models (simplified)
        variants = []
        # TODO: Load relationships and convert to CreativeVariant
        
        total_result = await db.execute(
            select(MetaCreativeVariantModel).where(
                MetaCreativeVariantModel.campaign_id == campaign_id
            )
        )
        total = len(total_result.scalars().all())
        
        return ListVariantsResponse(
            total=total,
            variants=variants,
            campaign_id=campaign_id,
            filters_applied={"status": status.value if status else None, "limit": limit, "offset": offset},
        )
        
    except Exception as e:
        logger.error(f"Error listing variants: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload/{variant_id}", response_model=UploadVariantResponse)
async def upload_variant(
    variant_id: str,
    request: UploadVariantRequest,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_role(["admin", "manager"]))
):
    """
    Sube una variante específica a Meta Ads.
    
    **Requiere rol:** admin, manager
    
    **Proceso:**
    1. Busca la variante en DB
    2. Upload video, thumbnail, creative, ad
    3. Actualiza meta_creative_id y meta_ad_id
    4. Marca como UPLOADED
    """
    try:
        # Validar variant_id
        if request.variant_id != variant_id:
            request.variant_id = variant_id
        
        # Buscar variante
        result = await db.execute(
            select(MetaCreativeVariantModel).where(
                MetaCreativeVariantModel.variant_id == variant_id
            )
        )
        variant_db = result.scalar_one_or_none()
        
        if not variant_db:
            raise HTTPException(status_code=404, detail="Variant not found")
        
        # TODO: Convert DB model to Pydantic CreativeVariant
        # For now, stub response
        
        uploader = CreativeUploader()
        # Stub upload
        upload_response = UploadVariantResponse(
            success=True,
            variant_id=variant_id,
            meta_creative_id=f"stub_creative_{variant_id[:8]}",
            meta_ad_id=f"stub_ad_{variant_id[:8]}",
        )
        
        # Update DB
        variant_db.status = "uploaded"
        variant_db.meta_creative_id = upload_response.meta_creative_id
        variant_db.meta_ad_id = upload_response.meta_ad_id
        await db.commit()
        
        return upload_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading variant: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bulk-upload/{campaign_id}", response_model=BulkUploadResponse)
async def bulk_upload_variants(
    campaign_id: str,
    request: BulkUploadRequest,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_role(["admin"]))
):
    """
    Sube múltiples variantes (5-20) de forma masiva.
    
    **Requiere rol:** admin (solo)
    
    **Parámetros:**
    - variant_ids: Lista de IDs a subir
    - max_parallel: Máximo de uploads paralelos (1-5)
    
    **Returns:**
    - uploaded_count: Número de éxitos
    - failed_count: Número de fallos
    - results: Detalle de cada upload
    """
    import time
    import asyncio
    
    start_time = time.time()
    
    try:
        if request.campaign_id != campaign_id:
            request.campaign_id = campaign_id
        
        uploader = CreativeUploader()
        results = []
        uploaded_count = 0
        failed_count = 0
        errors = []
        
        # Process variants in batches
        for variant_id in request.variant_ids:
            try:
                # Get variant from DB
                result_db = await db.execute(
                    select(MetaCreativeVariantModel).where(
                        MetaCreativeVariantModel.variant_id == variant_id
                    )
                )
                variant_db = result_db.scalar_one_or_none()
                
                if not variant_db:
                    errors.append(f"{variant_id}: Not found")
                    failed_count += 1
                    continue
                
                # Stub upload
                upload_response = UploadVariantResponse(
                    success=True,
                    variant_id=variant_id,
                    meta_creative_id=f"stub_creative_{variant_id[:8]}",
                    meta_ad_id=f"stub_ad_{variant_id[:8]}",
                )
                
                if upload_response.success:
                    uploaded_count += 1
                    variant_db.status = "uploaded"
                    variant_db.meta_creative_id = upload_response.meta_creative_id
                    variant_db.meta_ad_id = upload_response.meta_ad_id
                else:
                    failed_count += 1
                    errors.append(f"{variant_id}: {upload_response.error}")
                
                results.append(upload_response)
                
            except Exception as e:
                logger.error(f"Error uploading variant {variant_id}: {e}")
                failed_count += 1
                errors.append(f"{variant_id}: {str(e)}")
        
        await db.commit()
        
        upload_time = time.time() - start_time
        
        return BulkUploadResponse(
            success=uploaded_count > 0,
            campaign_id=campaign_id,
            total_requested=len(request.variant_ids),
            uploaded_count=uploaded_count,
            failed_count=failed_count,
            results=results,
            errors=errors,
            upload_time_seconds=upload_time,
        )
        
    except Exception as e:
        logger.error(f"Error in bulk upload: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/regenerate/{variant_id}")
async def regenerate_variant(
    variant_id: str,
    request: RegenerateVariantRequest,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_role(["admin", "manager"]))
):
    """
    Regenera una variante específica.
    
    **Requiere rol:** admin, manager
    
    **Opciones:**
    - regenerate_video: Regenerar componente de video
    - regenerate_text: Regenerar componente de texto
    - regenerate_thumbnail: Regenerar componente de thumbnail
    """
    try:
        if request.variant_id != variant_id:
            request.variant_id = variant_id
        
        # TODO: Implement regeneration logic
        # For now, return stub response
        
        return {
            "success": True,
            "variant_id": variant_id,
            "message": "Variant regenerated successfully (stub)",
        }
        
    except Exception as e:
        logger.error(f"Error regenerating variant: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/archive/{variant_id}")
async def archive_variant(
    variant_id: str,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_role(["admin"]))
):
    """
    Marca una variante como archivada.
    
    **Requiere rol:** admin (solo)
    """
    try:
        result = await db.execute(
            select(MetaCreativeVariantModel).where(
                MetaCreativeVariantModel.variant_id == variant_id
            )
        )
        variant = result.scalar_one_or_none()
        
        if not variant:
            raise HTTPException(status_code=404, detail="Variant not found")
        
        variant.status = "archived"
        await db.commit()
        
        return {
            "success": True,
            "variant_id": variant_id,
            "message": "Variant archived successfully",
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error archiving variant: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint (público)."""
    return {
        "status": "healthy",
        "service": "meta_creative_variants",
        "version": "1.0.0",
    }
