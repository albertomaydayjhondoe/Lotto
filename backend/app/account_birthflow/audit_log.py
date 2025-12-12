"""
SPRINT 12 - Account BirthFlow & Lifecycle Management
Module: Audit Log

Sistema de audit log inmutable para trazabilidad completa.
"""

import logging
import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .account_models import AccountState, ActionType

logger = logging.getLogger(__name__)


# ============================================================================
# CONFIG
# ============================================================================

@dataclass
class AuditLogConfig:
    """Configuración del audit log"""
    
    # Storage
    log_file_path: str = "/tmp/account_birthflow_audit.jsonl"
    enable_file_logging: bool = True
    enable_console_logging: bool = False
    
    # Retention
    max_log_entries: int = 100000
    rotation_enabled: bool = True


# ============================================================================
# AUDIT LOG ENTRY
# ============================================================================

@dataclass
class AuditLogEntry:
    """Entry individual del audit log"""
    
    timestamp: datetime
    account_id: str
    event_type: str
    action: Optional[str] = None
    from_state: Optional[AccountState] = None
    to_state: Optional[AccountState] = None
    reason: str = ""
    risk_score: float = 0.0
    triggered_by: str = "system"
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict:
        """Convert to dict for serialization"""
        data = asdict(self)
        
        # Convert datetime to ISO format
        data['timestamp'] = self.timestamp.isoformat()
        
        # Convert enums to strings
        if self.from_state:
            data['from_state'] = self.from_state.value
        if self.to_state:
            data['to_state'] = self.to_state.value
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'AuditLogEntry':
        """Create from dict"""
        
        # Parse timestamp
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        
        # Parse states
        if data.get('from_state'):
            data['from_state'] = AccountState(data['from_state'])
        if data.get('to_state'):
            data['to_state'] = AccountState(data['to_state'])
        
        return cls(**data)


# ============================================================================
# AUDIT LOGGER
# ============================================================================

class AuditLogger:
    """
    Sistema de audit log inmutable.
    
    Responsabilidades:
    - Registrar todos los eventos de lifecycle
    - Persistir a disco (JSONL)
    - Permitir queries por account_id, event_type, etc.
    - Garantizar inmutabilidad (append-only)
    """
    
    def __init__(self, config: Optional[AuditLogConfig] = None):
        self.config = config or AuditLogConfig()
        
        # In-memory buffer
        self._entries: List[AuditLogEntry] = []
        
        # Ensure log directory exists
        if self.config.enable_file_logging:
            log_path = Path(self.config.log_file_path)
            log_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"AuditLogger initialized (file: {self.config.log_file_path})")
    
    # ========================================================================
    # PUBLIC API - LOGGING
    # ========================================================================
    
    def log_event(
        self,
        account_id: str,
        event_type: str,
        reason: str = "",
        **kwargs
    ):
        """
        Registra un evento en el audit log.
        
        Args:
            account_id: ID de la cuenta
            event_type: Tipo de evento
            reason: Razón del evento
            **kwargs: Campos adicionales
        """
        entry = AuditLogEntry(
            timestamp=datetime.now(),
            account_id=account_id,
            event_type=event_type,
            reason=reason,
            action=kwargs.get('action'),
            from_state=kwargs.get('from_state'),
            to_state=kwargs.get('to_state'),
            risk_score=kwargs.get('risk_score', 0.0),
            triggered_by=kwargs.get('triggered_by', 'system'),
            metadata=kwargs.get('metadata', {})
        )
        
        self._entries.append(entry)
        
        # Persist to file
        if self.config.enable_file_logging:
            self._write_to_file(entry)
        
        # Console log
        if self.config.enable_console_logging:
            logger.info(f"AUDIT: {entry.event_type} | {account_id} | {reason}")
    
    def log_state_transition(
        self,
        account_id: str,
        from_state: AccountState,
        to_state: AccountState,
        reason: str,
        triggered_by: str = "system"
    ):
        """Log state transition"""
        self.log_event(
            account_id=account_id,
            event_type="state_transition",
            reason=reason,
            from_state=from_state,
            to_state=to_state,
            triggered_by=triggered_by
        )
    
    def log_action_performed(
        self,
        account_id: str,
        action_type: ActionType,
        success: bool,
        metadata: Optional[Dict] = None
    ):
        """Log action performed"""
        self.log_event(
            account_id=account_id,
            event_type="action_performed",
            action=action_type.value,
            reason="success" if success else "failed",
            metadata=metadata or {}
        )
    
    def log_risk_event(
        self,
        account_id: str,
        risk_score: float,
        reason: str,
        triggered_by: str = "system"
    ):
        """Log risk event"""
        self.log_event(
            account_id=account_id,
            event_type="risk_detected",
            reason=reason,
            risk_score=risk_score,
            triggered_by=triggered_by
        )
    
    def log_security_violation(
        self,
        account_id: str,
        violation_type: str,
        reason: str
    ):
        """Log security violation"""
        self.log_event(
            account_id=account_id,
            event_type="security_violation",
            reason=reason,
            metadata={"violation_type": violation_type}
        )
    
    def log_lock(
        self,
        account_id: str,
        reason: str,
        triggered_by: str = "system"
    ):
        """Log account lock"""
        self.log_event(
            account_id=account_id,
            event_type="account_locked",
            reason=reason,
            triggered_by=triggered_by
        )
    
    # ========================================================================
    # PUBLIC API - QUERIES
    # ========================================================================
    
    def get_logs_for_account(
        self,
        account_id: str,
        limit: int = 100
    ) -> List[AuditLogEntry]:
        """Get all logs for specific account"""
        logs = [e for e in self._entries if e.account_id == account_id]
        return sorted(logs, key=lambda x: x.timestamp, reverse=True)[:limit]
    
    def get_logs_by_event_type(
        self,
        event_type: str,
        limit: int = 100
    ) -> List[AuditLogEntry]:
        """Get logs by event type"""
        logs = [e for e in self._entries if e.event_type == event_type]
        return sorted(logs, key=lambda x: x.timestamp, reverse=True)[:limit]
    
    def get_recent_logs(
        self,
        limit: int = 100
    ) -> List[AuditLogEntry]:
        """Get most recent logs"""
        return sorted(self._entries, key=lambda x: x.timestamp, reverse=True)[:limit]
    
    def get_logs_by_timerange(
        self,
        start: datetime,
        end: datetime
    ) -> List[AuditLogEntry]:
        """Get logs within timerange"""
        return [
            e for e in self._entries
            if start <= e.timestamp <= end
        ]
    
    def count_events_for_account(
        self,
        account_id: str,
        event_type: Optional[str] = None
    ) -> int:
        """Count events for account"""
        logs = [e for e in self._entries if e.account_id == account_id]
        
        if event_type:
            logs = [e for e in logs if e.event_type == event_type]
        
        return len(logs)
    
    # ========================================================================
    # INTERNAL - FILE OPERATIONS
    # ========================================================================
    
    def _write_to_file(self, entry: AuditLogEntry):
        """Write entry to file (append-only)"""
        try:
            with open(self.config.log_file_path, 'a') as f:
                json_line = json.dumps(entry.to_dict())
                f.write(json_line + '\n')
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")
    
    def load_from_file(self):
        """Load existing logs from file"""
        if not Path(self.config.log_file_path).exists():
            logger.warning(f"Audit log file not found: {self.config.log_file_path}")
            return
        
        try:
            with open(self.config.log_file_path, 'r') as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        entry = AuditLogEntry.from_dict(data)
                        self._entries.append(entry)
            
            logger.info(f"Loaded {len(self._entries)} audit log entries")
        
        except Exception as e:
            logger.error(f"Failed to load audit log: {e}")
    
    def rotate_log_file(self):
        """Rotate log file (if too large)"""
        if not self.config.rotation_enabled:
            return
        
        if len(self._entries) > self.config.max_log_entries:
            # Keep only recent entries
            self._entries = self._entries[-self.config.max_log_entries:]
            
            # Rewrite file
            try:
                with open(self.config.log_file_path, 'w') as f:
                    for entry in self._entries:
                        json_line = json.dumps(entry.to_dict())
                        f.write(json_line + '\n')
                
                logger.info("Audit log rotated")
            
            except Exception as e:
                logger.error(f"Failed to rotate audit log: {e}")


# ============================================================================
# GLOBAL AUDIT LOGGER INSTANCE
# ============================================================================

_global_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get global audit logger instance"""
    global _global_audit_logger
    
    if _global_audit_logger is None:
        _global_audit_logger = AuditLogger()
    
    return _global_audit_logger


def set_audit_logger(logger_instance: AuditLogger):
    """Set global audit logger instance"""
    global _global_audit_logger
    _global_audit_logger = logger_instance


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def create_audit_logger(config: Optional[AuditLogConfig] = None) -> AuditLogger:
    """Helper para crear audit logger"""
    return AuditLogger(config)


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "AuditLogConfig",
    "AuditLogEntry",
    "AuditLogger",
    "get_audit_logger",
    "set_audit_logger",
    "create_audit_logger",
]
