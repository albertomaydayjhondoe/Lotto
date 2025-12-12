"""
Telegram Exchange Bot - Sprint 7C
Sistema automatizado de intercambio multiplataforma vía Telegram.
Includes: Live API Integration, Dashboard, Auto-Scaler, ML ROI Predictor, Production Hardening
"""

# Sprint 7A - Core Models & Components
from app.telegram_exchange_bot.models import (
    # Modelos principales
    TelegramGroup,
    TelegramUser,
    ExchangeMessage,
    ExchangeInteraction,
    OurContent,
    BotConfig,
    # Enums
    Platform,
    InteractionType,
    MessageStatus,
    AccountRole,
    PriorityLevel,
    # Response models
    ExchangeStats,
    BotStatus
)

from app.telegram_exchange_bot.emotional import (
    EmotionalMessageGenerator,
    MessageType
)

from app.telegram_exchange_bot.listener import (
    MessageListener,
    URLDetector,
    KeywordMatcher,
    MessageClassifier,
    OpportunityQueue
)

from app.telegram_exchange_bot.announcer import (
    GroupAnnouncer,
    RateLimitManager
)

from app.telegram_exchange_bot.dm_flow import (
    DMNegotiationFlow,
    ConversationState,
    AcceptanceSignal,
    RejectionSignal,
    ConversationContext,
    ResponseAnalyzer,
    InteractionRequestBuilder
)

from app.telegram_exchange_bot.auto_joiner import (
    AutoGroupJoiner,
    GroupSearcher,
    GroupValidator,
    GroupCandidate
)

from app.telegram_exchange_bot.captcha_resolver import (
    CaptchaResolver,
    CaptchaDetector,
    SimpleCaptchaSolver
)

# Sprint 7B - Execution & Security
from app.telegram_exchange_bot.accounts_pool import (
    NonOfficialAccountsPool,
    NonOfficialAccount,
    AccountStatus,
    AccountHealth,
    AccountHealthMonitor,
    AccountRotationStrategy
)

from app.telegram_exchange_bot.security import (
    TelegramBotSecurityLayer,
    SecurityContext,
    SecurityValidator,
    SecurityException,
    AntiShadowbanProtection
)

from app.telegram_exchange_bot.executor import (
    InteractionExecutor,
    ExecutionResult,
    ExecutionStatus,
    PlatformExecutor,
    YouTubeExecutor,
    InstagramExecutor
)

from app.telegram_exchange_bot.prioritization import (
    PriorityManager,
    ContentPriorityScore,
    UserExchangeScore,
    ContentStrategy
)

from app.telegram_exchange_bot.metrics import (
    MetricsCollector,
    InteractionMetric,
    ROIMetrics,
    PerformanceDashboard,
    MetricPeriod
)

# Sprint 7C - Live APIs
from app.telegram_exchange_bot.platforms import (
    YouTubeLiveAPI,
    InstagramLiveAPI,
    TikTokLiveAPI
)

# Sprint 7C - Dashboard
from app.telegram_exchange_bot.dashboard import dashboard_router

# Sprint 7C - Auto-Scaler
from app.telegram_exchange_bot.autoscaler import (
    AccountAutoScaler,
    ScalingTrigger,
    ScalingEvent
)

# Sprint 7C - ML ROI Predictor
from app.telegram_exchange_bot.ml_roi_predictor import (
    MLROIPredictor,
    ROIPredictionInput,
    ROIPredictionOutput
)

# Sprint 7C - Production Hardening
from app.telegram_exchange_bot.production_hardening import (
    KillSwitch,
    Watchdog,
    IsolatedExecutionQueue,
    ProductionHardening,
    SystemState,
    AnomalyType,
    Anomaly
)

__all__ = [
    # Models
    "TelegramGroup",
    "TelegramUser",
    "ExchangeMessage",
    "ExchangeInteraction",
    "OurContent",
    "BotConfig",
    "Platform",
    "InteractionType",
    "MessageStatus",
    "AccountRole",
    "PriorityLevel",
    "ExchangeStats",
    "BotStatus",
    # Emotional
    "EmotionalMessageGenerator",
    "MessageType",
    # Listener
    "MessageListener",
    "URLDetector",
    "KeywordMatcher",
    "MessageClassifier",
    "OpportunityQueue",
    # Announcer
    "GroupAnnouncer",
    "RateLimitManager",
    # DM Flow
    "DMNegotiationFlow",
    "ConversationState",
    "AcceptanceSignal",
    "RejectionSignal",
    "ConversationContext",
    "ResponseAnalyzer",
    "InteractionRequestBuilder",
    # Auto Joiner
    "AutoGroupJoiner",
    "GroupSearcher",
    "GroupValidator",
    "GroupCandidate",
    # CAPTCHA
    "CaptchaResolver",
    "CaptchaDetector",
    "SimpleCaptchaSolver",
    # Sprint 7B - Accounts Pool
    "NonOfficialAccountsPool",
    "NonOfficialAccount",
    "AccountStatus",
    "AccountHealth",
    "AccountHealthMonitor",
    "AccountRotationStrategy",
    # Sprint 7B - Security
    "TelegramBotSecurityLayer",
    "SecurityContext",
    "SecurityValidator",
    "SecurityException",
    "AntiShadowbanProtection",
    # Sprint 7B - Executor
    "InteractionExecutor",
    "ExecutionResult",
    "ExecutionStatus",
    "PlatformExecutor",
    "YouTubeExecutor",
    "InstagramExecutor",
    # Sprint 7B - Prioritization
    "PriorityManager",
    "ContentPriorityScore",
    "UserExchangeScore",
    "ContentStrategy",
    # Sprint 7B - Metrics
    "MetricsCollector",
    "InteractionMetric",
    "ROIMetrics",
    "PerformanceDashboard",
    "MetricPeriod",
    # Sprint 7C - Live APIs
    "YouTubeLiveAPI",
    "InstagramLiveAPI",
    "TikTokLiveAPI",
    # Sprint 7C - Dashboard
    "dashboard_router",
    # Sprint 7C - Auto-Scaler
    "AccountAutoScaler",
    "ScalingTrigger",
    "ScalingEvent",
    # Sprint 7C - ML ROI Predictor
    "MLROIPredictor",
    "ROIPredictionInput",
    "ROIPredictionOutput",
    # Sprint 7C - Production Hardening
    "KillSwitch",
    "Watchdog",
    "IsolatedExecutionQueue",
    "ProductionHardening",
    "SystemState",
    "AnomalyType",
    "Anomaly",
]

__version__ = "0.3.0"
__sprint__ = "7C"
