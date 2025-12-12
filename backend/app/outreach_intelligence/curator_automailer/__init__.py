"""
Curator AutoMailer subsystem initialization

Exports components for automated curator outreach and email management.
"""

from .email_template_builder import EmailTemplateBuilder
from .auto_sender_stub import AutoSenderStub, SendStatus
from .followup_scheduler_stub import (
    FollowUpSchedulerStub,
    FollowUpReason
)
from .inbox_monitor_stub import (
    InboxMonitorStub,
    ResponseType
)

__all__ = [
    "EmailTemplateBuilder",
    "AutoSenderStub",
    "SendStatus",
    "FollowUpSchedulerStub",
    "FollowUpReason",
    "InboxMonitorStub",
    "ResponseType"
]
