"""
Industry Crawler subsystem initialization

Exports components for industry-wide contact discovery.
"""

from .crawler_stub import CrawlerStub, PlatformType
from .parser_stub import ParserStub
from .discovery_rules import DiscoveryRules, DiscoveryPriority
from .scoring_model_stub import ScoringModelStub
from .legal_compliance import LegalCompliance, ComplianceStatus

__all__ = [
    "CrawlerStub",
    "PlatformType",
    "ParserStub",
    "DiscoveryRules",
    "DiscoveryPriority",
    "ScoringModelStub",
    "LegalCompliance",
    "ComplianceStatus"
]
