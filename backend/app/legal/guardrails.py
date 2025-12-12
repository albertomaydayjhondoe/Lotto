"""
Legal Guardrails and Copyright Compliance

Ensures copyright compliance and legal approval before paid campaigns.
Phase 1: STUB mode with basic validation
Phase 2: Integration with external copyright databases
"""
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID, uuid4
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)


class CopyrightConfirmation(BaseModel):
    """Copyright confirmation schema"""
    clip_id: Optional[UUID] = Field(None, description="Clip ID (if applicable)")
    campaign_id: Optional[UUID] = Field(None, description="Campaign ID")
    user_id: UUID = Field(..., description="User confirming rights")
    copyright_confirmed: bool = Field(..., description="User confirms having copyright/usage rights")
    legal_disclaimer_accepted: bool = Field(..., description="User accepts legal terms")
    content_description: Optional[str] = Field(None, description="Brief description of content")
    rights_type: Optional[str] = Field(None, description="owned, licensed, fair_use, public_domain")
    confirmed_at: datetime = Field(default_factory=datetime.utcnow)


class LegalApprovalLog(BaseModel):
    """Legal approval audit log"""
    id: UUID = Field(default_factory=uuid4)
    entity_type: str = Field(..., description="clip, campaign, creative")
    entity_id: UUID = Field(..., description="Entity ID")
    user_id: UUID
    copyright_confirmed: bool
    legal_disclaimer_accepted: bool
    content_description: Optional[str]
    rights_type: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    approved_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None


class LegalGuardrails:
    """
    Legal guardrails system for copyright compliance
    
    Phase 1: STUB mode with basic validation
    Phase 2: External API integration for copyright checks
    """
    
    DISCLAIMER_TEXT = """
    ⚠️ AVISO LEGAL
    
    Todos los clips y contenidos subidos deben contar con derechos de uso apropiados.
    El usuario es responsable de verificar y garantizar que tiene permisos de copyright
    antes de publicar contenido en plataformas pagadas.
    
    Al confirmar, usted declara que:
    1. Es el propietario del contenido O tiene una licencia válida para su uso
    2. El contenido no infringe derechos de autor de terceros
    3. Acepta toda la responsabilidad legal por el uso del contenido
    4. Ha leído y acepta los términos y condiciones de servicio
    
    El incumplimiento de estas declaraciones puede resultar en:
    - Suspensión de cuenta
    - Responsabilidad legal y daños
    - Eliminación de contenido
    """
    
    def __init__(self, mode: str = "STUB"):
        self.mode = mode
        # STUB: In-memory approval logs
        self.approval_logs: Dict[UUID, LegalApprovalLog] = {}
        logger.info(f"LegalGuardrails initialized in {mode} mode")
    
    def get_disclaimer(self) -> str:
        """Get legal disclaimer text"""
        return self.DISCLAIMER_TEXT
    
    def validate_confirmation(self, confirmation: CopyrightConfirmation) -> tuple[bool, Optional[str]]:
        """
        Validate copyright confirmation
        
        Args:
            confirmation: Copyright confirmation data
        
        Returns:
            Tuple of (valid: bool, error_message: Optional[str])
        """
        # Both checkboxes must be true
        if not confirmation.copyright_confirmed:
            return False, "Copyright confirmation is required"
        
        if not confirmation.legal_disclaimer_accepted:
            return False, "Legal disclaimer acceptance is required"
        
        # In LIVE mode, would perform additional checks:
        # - Cross-reference with copyright databases
        # - Check against known infringement lists
        # - Verify user's history/reputation
        
        return True, None
    
    def log_approval(
        self,
        entity_type: str,
        entity_id: UUID,
        user_id: UUID,
        confirmation: CopyrightConfirmation,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> LegalApprovalLog:
        """
        Log legal approval for audit trail
        
        Args:
            entity_type: Type of entity (clip, campaign, creative)
            entity_id: Entity ID
            user_id: User who approved
            confirmation: Copyright confirmation details
            ip_address: User's IP address
            user_agent: User's browser/client
            metadata: Additional metadata
        
        Returns:
            LegalApprovalLog instance
        """
        log = LegalApprovalLog(
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            copyright_confirmed=confirmation.copyright_confirmed,
            legal_disclaimer_accepted=confirmation.legal_disclaimer_accepted,
            content_description=confirmation.content_description,
            rights_type=confirmation.rights_type,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata,
        )
        
        # STUB: Store in memory
        self.approval_logs[log.id] = log
        
        logger.info(
            f"[LEGAL] Logged approval for {entity_type}:{entity_id} "
            f"by user {user_id}"
        )
        
        # In production, would also:
        # - Store in database with retention policy
        # - Trigger compliance webhook
        # - Send confirmation email to user
        
        return log
    
    def check_approval_exists(self, entity_type: str, entity_id: UUID) -> bool:
        """Check if entity has valid approval"""
        # STUB: Check in-memory logs
        for log in self.approval_logs.values():
            if log.entity_type == entity_type and log.entity_id == entity_id:
                return log.copyright_confirmed and log.legal_disclaimer_accepted
        
        return False
    
    def require_approval(self, entity_type: str, entity_id: UUID) -> bool:
        """
        Require approval before proceeding (used as gate check)
        
        Raises:
            PermissionError: If approval not found or invalid
        
        Returns:
            True if approved
        """
        if not self.check_approval_exists(entity_type, entity_id):
            raise PermissionError(
                f"Legal approval required for {entity_type}:{entity_id}. "
                "User must confirm copyright ownership and accept terms."
            )
        
        return True
    
    def get_approval_log(self, entity_type: str, entity_id: UUID) -> Optional[LegalApprovalLog]:
        """Get approval log for entity"""
        for log in self.approval_logs.values():
            if log.entity_type == entity_type and log.entity_id == entity_id:
                return log
        
        return None
    
    def revoke_approval(self, log_id: UUID, reason: str) -> bool:
        """Revoke a previous approval (admin function)"""
        if log_id not in self.approval_logs:
            return False
        
        log = self.approval_logs[log_id]
        
        # In production, would update database record
        logger.warning(
            f"[LEGAL] Approval {log_id} revoked for {log.entity_type}:{log.entity_id}. "
            f"Reason: {reason}"
        )
        
        # Remove from active approvals
        del self.approval_logs[log_id]
        
        return True


# Global instance
legal_guardrails = LegalGuardrails(mode="STUB")


def require_copyright_approval(entity_type: str, entity_id: UUID) -> bool:
    """
    Decorator helper for requiring copyright approval
    
    Usage:
        require_copyright_approval("campaign", campaign_id)
    """
    return legal_guardrails.require_approval(entity_type, entity_id)
