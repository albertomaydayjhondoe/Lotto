"""Legal module initialization"""

from .guardrails import (
    legal_guardrails,
    require_copyright_approval,
    CopyrightConfirmation,
    LegalApprovalLog,
    LegalGuardrails
)

__all__ = [
    "legal_guardrails",
    "require_copyright_approval",
    "CopyrightConfirmation",
    "LegalApprovalLog",
    "LegalGuardrails",
]
