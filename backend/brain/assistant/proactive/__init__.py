"""Proactive Assistant & Notification Subsystem for Auralis (Phase 13.8).

Provides proactive evaluation, deterministic recommendations, priority scoring, duplicate suppression,
rule evaluation, and assistant-level notification management without AI inference or OS automation commands.
"""

from brain.assistant.proactive.exceptions import (
    NotificationException,
    ProactiveEvaluationException,
    ProactiveException,
    RecommendationException,
    RuleValidationException,
)
from brain.assistant.proactive.interfaces import (
    INotificationManager,
    IProactiveCoordinator,
    IProactiveProvider,
    IProactiveRuntime,
    IRecommendationEngine,
    IRuleEvaluator,
)
from brain.assistant.proactive.models import (
    EvaluationResult,
    NotificationType,
    ProactiveCapabilities,
    ProactiveContext,
    ProactiveEvaluation,
    ProactiveEvent,
    ProactiveHealth,
    ProactiveNotification,
    ProactiveRecommendation,
    ProactiveRule,
    ProactiveState,
    ProactiveStatistics,
    ProactiveSuggestion,
    SuggestionPriority,
    SuggestionType,
)
from brain.assistant.proactive.notification_manager import NotificationManager
from brain.assistant.proactive.proactive_coordinator import ProactiveCoordinator
from brain.assistant.proactive.proactive_provider import ProactiveProvider
from brain.assistant.proactive.proactive_runtime import ProactiveRuntime
from brain.assistant.proactive.recommendation_engine import RecommendationEngine
from brain.assistant.proactive.rule_evaluator import RuleEvaluator
from brain.assistant.proactive.runtime import (
    get_proactive_runtime,
    reset_proactive_runtime,
)

__all__ = [
    # Enums & Models
    "SuggestionPriority",
    "SuggestionType",
    "NotificationType",
    "ProactiveState",
    "EvaluationResult",
    "ProactiveEvent",
    "ProactiveSuggestion",
    "ProactiveRecommendation",
    "ProactiveNotification",
    "ProactiveContext",
    "ProactiveRule",
    "ProactiveStatistics",
    "ProactiveHealth",
    "ProactiveCapabilities",
    "ProactiveEvaluation",
    # Exceptions
    "ProactiveException",
    "ProactiveEvaluationException",
    "RecommendationException",
    "NotificationException",
    "RuleValidationException",
    # Interfaces
    "IRuleEvaluator",
    "IRecommendationEngine",
    "INotificationManager",
    "IProactiveCoordinator",
    "IProactiveProvider",
    "IProactiveRuntime",
    # Managers & Components
    "RuleEvaluator",
    "RecommendationEngine",
    "NotificationManager",
    "ProactiveCoordinator",
    "ProactiveProvider",
    "ProactiveRuntime",
    # Singleton accessors
    "get_proactive_runtime",
    "reset_proactive_runtime",
]
