"""
Memory Vault Pydantic Schemas

Request/Response schemas for Memory Vault API
"""
from datetime import datetime
from typing import Dict, Any, Optional, List
from uuid import UUID
from pydantic import BaseModel, Field


class MLFeatureCreate(BaseModel):
    """Schema for creating ML feature record"""
    feature_hash: Dict[str, Any] = Field(..., description="ML feature vectors and metadata")
    source: str = Field(..., description="Source of features (model name, extraction method)")
    version: int = Field(default=1, description="Feature schema version")
    run_id: Optional[UUID] = Field(None, description="Orchestrator run ID")
    entity_type: Optional[str] = Field(None, description="campaign, clip, creative, etc")
    entity_id: Optional[str] = Field(None, description="External entity ID")


class MLFeatureResponse(MLFeatureCreate):
    """Schema for ML feature response"""
    id: UUID
    timestamp: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True


class MemoryVaultStoreRequest(BaseModel):
    """Schema for storing data in Memory Vault"""
    subfolder: str = Field(..., description="ml_features, audits, campaign_history, clips_metadata, orchestrator_runs")
    entity_type: str = Field(..., description="Type of entity")
    data: Dict[str, Any] = Field(..., description="Data to store")
    entity_id: Optional[str] = Field(None, description="Entity ID")
    run_id: Optional[UUID] = Field(None, description="Orchestrator run ID")
    version: int = Field(default=1, description="Version number")
    is_summary: bool = Field(default=False, description="Summary data (longer retention)")


class MemoryVaultStoreResponse(BaseModel):
    """Schema for Memory Vault store response"""
    file_path: Optional[str] = Field(None, description="Local file path (STUB mode)")
    gdrive_path: Optional[str] = Field(None, description="Google Drive path (LIVE mode)")
    gdrive_file_id: Optional[str] = Field(None, description="Google Drive file ID (LIVE mode)")
    file_size_bytes: int
    entity_type: str
    entity_id: Optional[str]
    run_id: Optional[str]
    version: int
    is_summary: bool
    retention_until: str
    checksum: str
    created_at: str


class MemoryVaultRetrieveRequest(BaseModel):
    """Schema for retrieving data from Memory Vault"""
    subfolder: str = Field(..., description="Subfolder name")
    filename: str = Field(..., description="Filename to retrieve")


class MemoryVaultListRequest(BaseModel):
    """Schema for listing files in Memory Vault"""
    subfolder: str = Field(..., description="Subfolder name")
    entity_type: Optional[str] = Field(None, description="Filter by entity type")


class MemoryVaultListResponse(BaseModel):
    """Schema for Memory Vault list response"""
    subfolder: str
    files: List[str]
    count: int


class MemoryVaultCleanupRequest(BaseModel):
    """Schema for Memory Vault cleanup request"""
    dry_run: bool = Field(default=True, description="If True, only report what would be deleted")


class MemoryVaultCleanupResponse(BaseModel):
    """Schema for Memory Vault cleanup response"""
    dry_run: bool
    expired_files_count: int
    total_size_freed_bytes: int
    total_size_freed_mb: float
    expired_files: List[Dict[str, Any]]
    timestamp: str


class ACLCheckRequest(BaseModel):
    """Schema for ACL permission check"""
    role: str = Field(..., description="orchestrator, worker, auditor, dashboard, devops")
    resource: str = Field(..., description="Resource to check access for")
    action: str = Field(..., description="r (read), w (write)")


class ACLCheckResponse(BaseModel):
    """Schema for ACL check response"""
    role: str
    resource: str
    action: str
    allowed: bool
    permission: str
    reason: Optional[str] = None
