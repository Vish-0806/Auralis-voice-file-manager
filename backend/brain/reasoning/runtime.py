"""Reasoning Runtime Coordinator for orchestrating the complete reasoning subsystem.

This module provides thread-safe runtime orchestration of IntentAnalyzer, ReasoningStrategySelector,
GoalExtractor, ConstraintAnalyzer, and ReasoningContextBuilder without executing commands,
creating execution plans, calling LLMs, accessing memory providers, or modifying conversations.
"""

from datetime import datetime, timezone
from enum import Enum
import logging
import threading
import time
from typing import Any, Dict, List, Optional

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict, Field

from brain.reasoning.constraint_analyzer import ConstraintAnalysisResult, ConstraintAnalyzer
from brain.reasoning.context_builder import ReasoningContext, ReasoningContextBuilder
from brain.reasoning.goal_extractor import GoalExtractionResult, GoalExtractor
from brain.reasoning.intent_analyzer import IntentAnalysisResult, IntentAnalyzer
from brain.reasoning.strategy_selector import ReasoningStrategySelector, StrategySelectionResult

logger = logging.getLogger(__name__)


class ReasoningRuntimeStatus(str, Enum):
    """Enumeration of reasoning runtime lifecycle status states."""

    INITIALIZING = "INITIALIZING"
    READY = "READY"
    DEGRADED = "DEGRADED"
    SHUTDOWN = "SHUTDOWN"
    ERROR = "ERROR"


class ReasoningRuntimeStats(BaseModel):
    """Immutable model representing reasoning runtime diagnostic statistics."""

    model_config = ConfigDict(frozen=True)

    requests_processed: int = 0
    contexts_built: int = 0
    average_runtime_ms: float = 0.0
    last_request_timestamp: Optional[datetime] = None
    startup_timestamp: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ReasoningRuntimeHealth(BaseModel):
    """Immutable model representing reasoning runtime health status."""

    model_config = ConfigDict(frozen=True)

    status: ReasoningRuntimeStatus = ReasoningRuntimeStatus.READY
    healthy: bool = True
    components: Dict[str, bool] = Field(default_factory=dict)
    statistics: Dict[str, Any] = Field(default_factory=dict)
    issues: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ReasoningRuntimeCoordinator:
    """Singleton runtime coordinator orchestrating the 5-stage reasoning pipeline."""

    def __init__(
        self,
        intent_analyzer: Optional[IntentAnalyzer] = None,
        strategy_selector: Optional[ReasoningStrategySelector] = None,
        goal_extractor: Optional[GoalExtractor] = None,
        constraint_analyzer: Optional[ConstraintAnalyzer] = None,
        context_builder: Optional[ReasoningContextBuilder] = None,
    ) -> None:
        """Initializes the coordinator with optional component instances."""
        self._lock = threading.RLock()
        self._status = ReasoningRuntimeStatus.INITIALIZING
        self._startup_timestamp: Optional[datetime] = None

        self._intent_analyzer = intent_analyzer or IntentAnalyzer()
        self._strategy_selector = strategy_selector or ReasoningStrategySelector()
        self._goal_extractor = goal_extractor or GoalExtractor()
        self._constraint_analyzer = constraint_analyzer or ConstraintAnalyzer()
        self._context_builder = context_builder or ReasoningContextBuilder()

        self._requests_processed = 0
        self._contexts_built = 0
        self._total_runtime_ms = 0.0
        self._last_request_timestamp: Optional[datetime] = None

    @property
    def intent_analyzer(self) -> IntentAnalyzer:
        return self._intent_analyzer

    @property
    def strategy_selector(self) -> ReasoningStrategySelector:
        return self._strategy_selector

    @property
    def goal_extractor(self) -> GoalExtractor:
        return self._goal_extractor

    @property
    def constraint_analyzer(self) -> ConstraintAnalyzer:
        return self._constraint_analyzer

    @property
    def context_builder(self) -> ReasoningContextBuilder:
        return self._context_builder

    @property
    def status(self) -> ReasoningRuntimeStatus:
        with self._lock:
            return self._status

    def initialize(self) -> bool:
        """Initializes all reasoning components and transitions status to READY."""
        with self._lock:
            if self._status == ReasoningRuntimeStatus.READY:
                return True

            self._startup_timestamp = datetime.now(timezone.utc)
            self._status = ReasoningRuntimeStatus.READY
            logger.info("Runtime Initialized")
            return True

    def shutdown(self) -> bool:
        """Shuts down the reasoning runtime safely."""
        with self._lock:
            if self._status == ReasoningRuntimeStatus.SHUTDOWN:
                return True

            self._status = ReasoningRuntimeStatus.SHUTDOWN
            logger.info("Runtime Shutdown")
            return True

    def clear(self) -> None:
        """Resets runtime statistics and clears component caches while preserving configuration."""
        with self._lock:
            self._requests_processed = 0
            self._contexts_built = 0
            self._total_runtime_ms = 0.0
            self._last_request_timestamp = None
            logger.info("Runtime Cleared")

    def process_request(self, request: str) -> ReasoningContext:
        """Executes the 5-stage deterministic reasoning pipeline for a user request."""
        start_time = time.perf_counter()
        with self._lock:
            if self._status == ReasoningRuntimeStatus.SHUTDOWN:
                self.initialize()

            req_str = request if isinstance(request, str) else ""

            # 1. Intent Analysis
            intent_res = self._intent_analyzer.analyze(req_str)

            # 2. Strategy Selection
            strat_res = self._strategy_selector.select_strategy(intent_res)

            # 3. Goal Extraction
            goal_res = self._goal_extractor.extract_goals(req_str, intent_res, strat_res)

            # 4. Constraint Analysis
            const_res = self._constraint_analyzer.analyze_constraints(req_str, intent_res, strat_res, goal_res)

            # 5. Reasoning Context Building
            context = self._context_builder.build_context(req_str, intent_res, strat_res, goal_res, const_res)

            # Update stats
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            self._requests_processed += 1
            self._contexts_built += 1
            self._total_runtime_ms += elapsed_ms
            self._last_request_timestamp = datetime.now(timezone.utc)

            logger.info("Request Processed")
            return context

    def health_check(self) -> ReasoningRuntimeHealth:
        """Generates real-time health diagnostic status report."""
        with self._lock:
            components_status = {
                "IntentAnalyzer": self._intent_analyzer is not None,
                "ReasoningStrategySelector": self._strategy_selector is not None,
                "GoalExtractor": self._goal_extractor is not None,
                "ConstraintAnalyzer": self._constraint_analyzer is not None,
                "ReasoningContextBuilder": self._context_builder is not None,
            }
            all_available = all(components_status.values())
            is_healthy = (self._status == ReasoningRuntimeStatus.READY) and all_available

            issues = []
            if not all_available:
                issues.append("One or more reasoning components are unavailable")
            if self._status != ReasoningRuntimeStatus.READY:
                issues.append(f"Runtime status is {self._status.value}")

            health = ReasoningRuntimeHealth(
                status=self._status,
                healthy=is_healthy,
                components=components_status,
                statistics=self.get_statistics().model_dump(),
                issues=issues,
                metadata={"thread_safety": "PROTECTED"},
            )
            logger.info("Health Check")
            return health

    def get_statistics(self) -> ReasoningRuntimeStats:
        """Retrieves runtime statistics snapshot."""
        with self._lock:
            avg_ms = (self._total_runtime_ms / self._requests_processed) if self._requests_processed > 0 else 0.0
            return ReasoningRuntimeStats(
                requests_processed=self._requests_processed,
                contexts_built=self._contexts_built,
                average_runtime_ms=avg_ms,
                last_request_timestamp=self._last_request_timestamp,
                startup_timestamp=self._startup_timestamp,
                metadata={},
            )

    def list_components(self) -> List[str]:
        """Lists registered reasoning components."""
        return [
            "IntentAnalyzer",
            "ReasoningStrategySelector",
            "GoalExtractor",
            "ConstraintAnalyzer",
            "ReasoningContextBuilder",
        ]


_global_lock = threading.RLock()
_global_reasoning_runtime: Optional[ReasoningRuntimeCoordinator] = None


def get_reasoning_runtime(
    intent_analyzer: Optional[IntentAnalyzer] = None,
    strategy_selector: Optional[ReasoningStrategySelector] = None,
    goal_extractor: Optional[GoalExtractor] = None,
    constraint_analyzer: Optional[ConstraintAnalyzer] = None,
    context_builder: Optional[ReasoningContextBuilder] = None,
    reset: bool = False,
) -> ReasoningRuntimeCoordinator:
    """Singleton accessor for the global ReasoningRuntimeCoordinator instance."""
    global _global_reasoning_runtime
    with _global_lock:
        if reset or _global_reasoning_runtime is None:
            _global_reasoning_runtime = ReasoningRuntimeCoordinator(
                intent_analyzer=intent_analyzer,
                strategy_selector=strategy_selector,
                goal_extractor=goal_extractor,
                constraint_analyzer=constraint_analyzer,
                context_builder=context_builder,
            )
            _global_reasoning_runtime.initialize()
        return _global_reasoning_runtime


def reset_reasoning_runtime() -> None:
    """Resets the global ReasoningRuntimeCoordinator instance."""
    global _global_reasoning_runtime
    with _global_lock:
        if _global_reasoning_runtime is not None:
            _global_reasoning_runtime.shutdown()
            _global_reasoning_runtime.clear()
            _global_reasoning_runtime = None
