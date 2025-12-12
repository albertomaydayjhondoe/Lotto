"""
Curator AutoMailer Module

STUB MODE - No real email sending or API calls.
"""

from .curator_database_stub import CuratorDatabaseStub, CuratorData
from .email_builder_stub import EmailBuilderStub
from .email_sender_stub import EmailSenderStub
from .engagement_tracker_stub import EngagementTrackerStub
from .response_handler_stub import ResponseHandlerStub, ResponseType
from .blacklist_manager_stub import BlacklistManagerStub, BlacklistType
from .routing_logic import RoutingLogic, CampaignPhase

__all__ = [
    "CuratorDatabaseStub",
    "CuratorData",
    "EmailBuilderStub",
    "EmailSenderStub",
    "EngagementTrackerStub",
    "ResponseHandlerStub",
    "ResponseType",
    "BlacklistManagerStub",
    "BlacklistType",
    "RoutingLogic",
    "CampaignPhase",
]
