"""
Memory Vault Storage Layer (STUB Mode)

Phase 1: Local file system stub
Phase 2: Google Drive API integration
"""
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List
from uuid import UUID, uuid4
import hashlib
import logging

logger = logging.getLogger(__name__)


class MemoryVaultConfig:
    """Configuration for Memory Vault storage"""
    
    # STUB: Local paths (will be GDrive paths in Phase 2)
    ROOT_PATH = "/tmp/stakazo_memory_vault"  # STUB: Local temp directory
    GDRIVE_ROOT = "gdrive:/stakazo/memory_vault/"  # Future: Real GDrive path
    
    SUBFOLDERS = {
        "ml_features": "ml_features/",
        "audits": "audits/",
        "campaign_history": "campaign_history/",
        "clips_metadata": "clips_metadata/",
        "orchestrator_runs": "orchestrator_runs/",
    }
    
    # Retention policies
    RAW_DATA_RETENTION_DAYS = 365
    SUMMARY_RETENTION_YEARS = 5
    
    # Naming convention
    NAMING_PATTERN = "{entity}__{date}_v{version}.json"
    
    @classmethod
    def get_local_path(cls, subfolder: str) -> Path:
        """Get local stub path for a subfolder"""
        path = Path(cls.ROOT_PATH) / subfolder
        path.mkdir(parents=True, exist_ok=True)
        return path


class MemoryVaultStorage:
    """
    Memory Vault Storage Manager (STUB Mode)
    
    Phase 1: Local file system operations
    Phase 2: Google Drive API with KMS encryption
    """
    
    def __init__(self, mode: str = "STUB"):
        self.mode = mode
        self.config = MemoryVaultConfig()
        logger.info(f"MemoryVaultStorage initialized in {mode} mode")
        
        # Initialize local stub directories
        if mode == "STUB":
            self._init_stub_directories()
    
    def _init_stub_directories(self):
        """Initialize local stub directory structure"""
        for subfolder in self.config.SUBFOLDERS.values():
            path = self.config.get_local_path(subfolder)
            logger.debug(f"Initialized stub directory: {path}")
    
    def generate_filename(
        self,
        entity_type: str,
        version: int = 1,
        date: Optional[datetime] = None
    ) -> str:
        """Generate filename following naming convention"""
        if date is None:
            date = datetime.utcnow()
        
        date_str = date.strftime("%Y%m%d")
        return self.config.NAMING_PATTERN.format(
            entity=entity_type,
            date=date_str,
            version=version
        )
    
    def calculate_checksum(self, data: Dict[str, Any]) -> str:
        """Calculate SHA-256 checksum of data"""
        json_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()
    
    def store(
        self,
        subfolder: str,
        entity_type: str,
        data: Dict[str, Any],
        entity_id: Optional[str] = None,
        run_id: Optional[UUID] = None,
        version: int = 1,
        is_summary: bool = False
    ) -> Dict[str, Any]:
        """
        Store data in Memory Vault
        
        Args:
            subfolder: One of the configured subfolders
            entity_type: Type of entity (campaign, clip, etc)
            data: Data to store
            entity_id: Optional entity ID
            run_id: Optional orchestrator run ID
            version: Version number
            is_summary: Whether this is summary data (longer retention)
        
        Returns:
            Metadata about stored file
        """
        if subfolder not in self.config.SUBFOLDERS:
            raise ValueError(f"Invalid subfolder: {subfolder}")
        
        # Generate filename
        filename = self.generate_filename(entity_type, version)
        
        # Calculate retention
        retention_days = (
            self.config.SUMMARY_RETENTION_YEARS * 365
            if is_summary
            else self.config.RAW_DATA_RETENTION_DAYS
        )
        retention_until = datetime.utcnow() + timedelta(days=retention_days)
        
        # Prepare metadata
        metadata = {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "run_id": str(run_id) if run_id else None,
            "version": version,
            "is_summary": is_summary,
            "retention_until": retention_until.isoformat(),
            "checksum": self.calculate_checksum(data),
            "created_at": datetime.utcnow().isoformat(),
        }
        
        # Add metadata to data
        full_data = {
            "metadata": metadata,
            "data": data
        }
        
        if self.mode == "STUB":
            # STUB: Write to local filesystem
            local_path = self.config.get_local_path(self.config.SUBFOLDERS[subfolder])
            file_path = local_path / filename
            
            with open(file_path, 'w') as f:
                json.dump(full_data, f, indent=2)
            
            file_size = os.path.getsize(file_path)
            
            result = {
                "file_path": str(file_path),
                "gdrive_path": None,  # STUB: No GDrive yet
                "gdrive_file_id": None,  # STUB: No GDrive yet
                "file_size_bytes": file_size,
                **metadata
            }
            
            logger.info(f"[STUB] Stored {entity_type} to {file_path}")
            return result
        
        else:
            # LIVE: Would integrate with Google Drive API here
            raise NotImplementedError("LIVE mode not implemented yet (Phase 2)")
    
    def retrieve(
        self,
        subfolder: str,
        filename: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve data from Memory Vault
        
        Args:
            subfolder: Subfolder name
            filename: Filename to retrieve
        
        Returns:
            Retrieved data or None if not found
        """
        if subfolder not in self.config.SUBFOLDERS:
            raise ValueError(f"Invalid subfolder: {subfolder}")
        
        if self.mode == "STUB":
            # STUB: Read from local filesystem
            local_path = self.config.get_local_path(self.config.SUBFOLDERS[subfolder])
            file_path = local_path / filename
            
            if not file_path.exists():
                logger.warning(f"[STUB] File not found: {file_path}")
                return None
            
            with open(file_path, 'r') as f:
                full_data = json.load(f)
            
            logger.info(f"[STUB] Retrieved {filename} from {file_path}")
            return full_data
        
        else:
            # LIVE: Would integrate with Google Drive API here
            raise NotImplementedError("LIVE mode not implemented yet (Phase 2)")
    
    def list_files(
        self,
        subfolder: str,
        entity_type: Optional[str] = None
    ) -> List[str]:
        """
        List files in a subfolder
        
        Args:
            subfolder: Subfolder name
            entity_type: Optional filter by entity type
        
        Returns:
            List of filenames
        """
        if subfolder not in self.config.SUBFOLDERS:
            raise ValueError(f"Invalid subfolder: {subfolder}")
        
        if self.mode == "STUB":
            # STUB: List local filesystem
            local_path = self.config.get_local_path(self.config.SUBFOLDERS[subfolder])
            
            files = [f.name for f in local_path.iterdir() if f.is_file()]
            
            if entity_type:
                files = [f for f in files if f.startswith(f"{entity_type}__")]
            
            logger.info(f"[STUB] Listed {len(files)} files in {subfolder}")
            return sorted(files)
        
        else:
            # LIVE: Would integrate with Google Drive API here
            raise NotImplementedError("LIVE mode not implemented yet (Phase 2)")
    
    def cleanup_expired(self, dry_run: bool = True) -> Dict[str, Any]:
        """
        Clean up expired files based on retention policy
        
        Args:
            dry_run: If True, only report what would be deleted
        
        Returns:
            Cleanup report
        """
        now = datetime.utcnow()
        expired_files = []
        total_size_freed = 0
        
        for subfolder_key, subfolder_path in self.config.SUBFOLDERS.items():
            if self.mode == "STUB":
                local_path = self.config.get_local_path(subfolder_path)
                
                for file_path in local_path.iterdir():
                    if not file_path.is_file():
                        continue
                    
                    try:
                        with open(file_path, 'r') as f:
                            full_data = json.load(f)
                        
                        retention_str = full_data.get("metadata", {}).get("retention_until")
                        if not retention_str:
                            continue
                        
                        retention_until = datetime.fromisoformat(retention_str)
                        
                        if now > retention_until:
                            file_size = os.path.getsize(file_path)
                            expired_files.append({
                                "subfolder": subfolder_key,
                                "filename": file_path.name,
                                "size_bytes": file_size,
                                "retention_until": retention_str
                            })
                            total_size_freed += file_size
                            
                            if not dry_run:
                                file_path.unlink()
                                logger.info(f"[STUB] Deleted expired file: {file_path}")
                    
                    except Exception as e:
                        logger.error(f"Error processing {file_path}: {e}")
        
        report = {
            "dry_run": dry_run,
            "expired_files_count": len(expired_files),
            "total_size_freed_bytes": total_size_freed,
            "total_size_freed_mb": round(total_size_freed / 1024 / 1024, 2),
            "expired_files": expired_files,
            "timestamp": now.isoformat()
        }
        
        logger.info(
            f"[STUB] Cleanup report: {len(expired_files)} files, "
            f"{report['total_size_freed_mb']} MB (dry_run={dry_run})"
        )
        
        return report


# Global instance (STUB mode by default)
storage = MemoryVaultStorage(mode="STUB")
