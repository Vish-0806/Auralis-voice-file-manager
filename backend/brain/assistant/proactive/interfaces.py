"""Abstract Interfaces for Proactive Assistant & Notification Runtime (Phase 13.8).

Defines Python ABC abstract interfaces for rule evaluation, recommendation generation,
notification management, proactive coordination, provider aggregation, and top-level runtime orchestration.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from brain.assistant.proactive.models import (
    EvaluationResult,
    ProactiveCapabilities,
    ProactiveContext,
    ProactiveEvaluation,
    ProactiveEvent,
    ProactiveHealth,
    ProactiveNotification,
    ProactiveRecommendation,
    ProactiveRule,
    ProactiveStatistics,
    ProactiveSuggestion,
)


class IRuleEvaluator(ABC):
    """Abstract interface for evaluating proactive rules against context snapshots and events."""

    @abstractmethod
    def evaluate_rule(
        self,
        rule: ProactiveRule,
        context: ProactiveContext,
        event: Optional[ProactiveEvent] = None,
    ) -> EvaluationResult:
        """Evaluate whether a proactive rule should trigger."""
        pass

    @abstractmethod
    def register_rule(self, rule: ProactiveRule) -> None:
        """Register a proactive rule."""
        pass


class IRecommendationEngine(ABC):
    """Abstract interface for generating deterministic proactive recommendations and suggestions."""

    @abstractmethod
    def generate_recommendations(
        self,
        context: ProactiveContext,
        event: Optional[ProactiveEvent] = None,
    ) -> List[ProactiveRecommendation]:
        """Generate ranked, deduplicated proactive recommendations."""
        pass


class INotificationManager(ABC):
    """Abstract interface for assistant-level notification lifecycle management."""

    @abstractmethod
    def create_notification(
        self,
        title: str,
        message: str,
        notification_type: str = "INFO",
        priority: str = "MEDIUM",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ProactiveNotification:
        """Create and register a new assistant-level ProactiveNotification."""
        pass

    @abstractmethod
    def dismiss_notification(self, notification_id: str) -> bool:
        """Dismiss an active notification."""
        pass

    @abstractmethod
    def archive_notification(self, notification_id: str) -> bool:
        """Archive a notification."""
        pass

    @abstractmethod
    def list_active_notifications(self) -> List[ProactiveNotification]:
        """List active non-dismissed and non-expired notifications."""
        pass


class IProactiveCoordinator(ABC):
    """Abstract interface for coordinating proactive evaluation across assistant and system runtimes."""

    @abstractmethod
    def evaluate_proactive_behavior(
        self,
        event: Optional[ProactiveEvent] = None,
        context: Optional[ProactiveContext] = None,
        runtimes: Optional[Dict[str, Any]] = None,
    ) -> ProactiveEvaluation:
        """Evaluate whether the assistant should proactively notify or suggest an action."""
        pass


class IProactiveProvider(ABC):
    """Abstract interface aggregating coordinator, recommendation engine, notification manager, and rule evaluator."""

    @property
    @abstractmethod
    def coordinator(self) -> IProactiveCoordinator:
        """Get the proactive coordinator."""
        pass

    @property
    @abstractmethod
    def recommendation_engine(self) -> IRecommendationEngine:
        """Get the recommendation engine."""
        pass

    @property
    @abstractmethod
    def notification_manager(self) -> INotificationManager:
        """Get the notification manager."""
        pass

    @property
    @abstractmethod
    def rule_evaluator(self) -> IRuleEvaluator:
        """Get the rule evaluator."""
        pass

    @abstractmethod
    def get_capabilities(self) -> ProactiveCapabilities:
        """Get proactive capabilities."""
        pass

    @abstractmethod
    def get_health(self) -> ProactiveHealth:
        """Get diagnostic health report."""
        pass

    @abstractmethod
    def get_statistics(self) -> ProactiveStatistics:
        """Get aggregated performance metrics."""
        pass

    @abstractmethod
    def initialize(self) -> None:
        """Initialize provider resources."""
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown provider resources."""
        pass

    @property
    @abstractmethod
    def is_initialized(self) -> bool:
        """Check if provider is initialized."""
        pass


class IProactiveRuntime(ABC):
    """Abstract interface for top-level Proactive Assistant & Notification Runtime orchestration."""

    @abstractmethod
    def initialize(self) -> None:
        """Initialize proactive runtime."""
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown proactive runtime."""
        pass

    @abstractmethod
    def restart(self) -> None:
        """Restart proactive runtime."""
        pass

    @abstractmethod
    def get_health(self) -> ProactiveHealth:
        """Get overall health status."""
        pass

    @abstractmethod
    def get_statistics(self) -> ProactiveStatistics:
        """Get runtime performance statistics."""
        pass

    @abstractmethod
    def get_capabilities(self) -> ProactiveCapabilities:
        """Get proactive capabilities."""
        pass

    @property
    @abstractmethod
    def is_initialized(self) -> bool:
        """Check if runtime is initialized."""
        pass
