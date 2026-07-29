"""Reasoning Strategy Selector for selecting reasoning strategies based on IntentAnalysisResult.

This module provides thread-safe strategy selection without executing commands, calling LLMs,
creating execution plans, modifying conversations, or accessing memory providers.
"""

from enum import Enum
import logging
import threading
from typing import Any, Dict, List, Optional

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict, Field

from brain.reasoning.intent_analyzer import IntentAnalysisResult, IntentCategory, IntentConfidence

logger = logging.getLogger(__name__)


class ReasoningStrategy(str, Enum):
    """Enumeration of available reasoning strategies."""

    DIRECT_RESPONSE = "DIRECT_RESPONSE"
    FILE_REASONING = "FILE_REASONING"
    SEARCH_REASONING = "SEARCH_REASONING"
    CONVERSATIONAL_REASONING = "CONVERSATIONAL_REASONING"
    PLANNING_REASONING = "PLANNING_REASONING"
    SCHEDULING_REASONING = "SCHEDULING_REASONING"
    SYSTEM_REASONING = "SYSTEM_REASONING"
    HELP_REASONING = "HELP_REASONING"
    CLARIFICATION_REQUIRED = "CLARIFICATION_REQUIRED"
    UNKNOWN = "UNKNOWN"


class StrategyPriority(str, Enum):
    """Enumeration representing priority levels for reasoning strategies."""

    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class StrategySelectionResult(BaseModel):
    """Immutable model representing the outcome of reasoning strategy selection."""

    model_config = ConfigDict(frozen=True)

    strategy: ReasoningStrategy = ReasoningStrategy.UNKNOWN
    priority: StrategyPriority = StrategyPriority.NORMAL
    reason: str = ""
    source_intent: Optional[IntentCategory] = None
    requires_clarification: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class StrategySelectorConfig(BaseModel):
    """Configuration options for ReasoningStrategySelector behavior."""

    default_priority: StrategyPriority = StrategyPriority.NORMAL
    enable_fallback: bool = True
    strict_matching: bool = True


DEFAULT_MAPPINGS: Dict[IntentCategory, Dict[str, Any]] = {
    IntentCategory.FILE_MANAGEMENT: {
        "strategy": ReasoningStrategy.FILE_REASONING,
        "priority": StrategyPriority.HIGH,
        "requires_clarification": False,
        "reason": "File management intent mapped to file reasoning strategy",
    },
    IntentCategory.FILE_SEARCH: {
        "strategy": ReasoningStrategy.SEARCH_REASONING,
        "priority": StrategyPriority.NORMAL,
        "requires_clarification": False,
        "reason": "File search intent mapped to search reasoning strategy",
    },
    IntentCategory.QUESTION_ANSWERING: {
        "strategy": ReasoningStrategy.DIRECT_RESPONSE,
        "priority": StrategyPriority.NORMAL,
        "requires_clarification": False,
        "reason": "Question answering intent mapped to direct response strategy",
    },
    IntentCategory.CONVERSATION: {
        "strategy": ReasoningStrategy.CONVERSATIONAL_REASONING,
        "priority": StrategyPriority.NORMAL,
        "requires_clarification": False,
        "reason": "Conversation intent mapped to conversational reasoning strategy",
    },
    IntentCategory.PLANNING: {
        "strategy": ReasoningStrategy.PLANNING_REASONING,
        "priority": StrategyPriority.HIGH,
        "requires_clarification": False,
        "reason": "Planning intent mapped to planning reasoning strategy",
    },
    IntentCategory.SCHEDULING: {
        "strategy": ReasoningStrategy.SCHEDULING_REASONING,
        "priority": StrategyPriority.NORMAL,
        "requires_clarification": False,
        "reason": "Scheduling intent mapped to scheduling reasoning strategy",
    },
    IntentCategory.SYSTEM_CONTROL: {
        "strategy": ReasoningStrategy.SYSTEM_REASONING,
        "priority": StrategyPriority.CRITICAL,
        "requires_clarification": False,
        "reason": "System control intent mapped to system reasoning strategy",
    },
    IntentCategory.HELP: {
        "strategy": ReasoningStrategy.HELP_REASONING,
        "priority": StrategyPriority.LOW,
        "requires_clarification": False,
        "reason": "Help intent mapped to help reasoning strategy",
    },
    IntentCategory.UNKNOWN: {
        "strategy": ReasoningStrategy.CLARIFICATION_REQUIRED,
        "priority": StrategyPriority.LOW,
        "requires_clarification": True,
        "reason": "Unknown intent requires clarification",
    },
}


class ReasoningStrategySelector:
    """Thread-safe engine for selecting reasoning strategies based on IntentAnalysisResult."""

    def __init__(self, config: Optional[StrategySelectorConfig] = None) -> None:
        """Initializes the ReasoningStrategySelector with optional configuration and thread lock."""
        self.config = config or StrategySelectorConfig()
        self._strategy_registry: Dict[IntentCategory, Dict[str, Any]] = {}
        self._lock = threading.RLock()

        # Pre-populate default strategy mappings
        for intent, rule in DEFAULT_MAPPINGS.items():
            self._strategy_registry[intent] = dict(rule)

    def register_strategy(
        self,
        intent: IntentCategory,
        strategy: ReasoningStrategy,
        priority: StrategyPriority = StrategyPriority.NORMAL,
        requires_clarification: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Registers a strategy mapping rule for a specific IntentCategory."""
        with self._lock:
            rule = {
                "strategy": strategy,
                "priority": priority,
                "requires_clarification": requires_clarification,
                "reason": f"Custom strategy rule for intent {intent}",
                "metadata": metadata or {},
            }
            self._strategy_registry[intent] = rule
            logger.info("Strategy Registered: intent=%s, strategy=%s", intent, strategy)
            return True

    def remove_strategy(self, intent: IntentCategory) -> bool:
        """Removes a registered strategy rule for an IntentCategory."""
        with self._lock:
            if intent in self._strategy_registry:
                del self._strategy_registry[intent]
                logger.info("Strategy Removed: intent=%s", intent)
                return True
            return False

    def clear_strategies(self) -> None:
        """Clears all strategy rules from the registry."""
        with self._lock:
            self._strategy_registry.clear()
            logger.info("Strategy Registry Cleared")

    def select_strategy(
        self,
        intent_result: Optional[IntentAnalysisResult] = None,
    ) -> StrategySelectionResult:
        """Deterministically selects a reasoning strategy based on an IntentAnalysisResult."""
        with self._lock:
            if (
                intent_result is None
                or intent_result.intent == IntentCategory.UNKNOWN
                or intent_result.confidence == IntentConfidence.VERY_LOW
            ):
                source = intent_result.intent if intent_result else None
                result = StrategySelectionResult(
                    strategy=ReasoningStrategy.CLARIFICATION_REQUIRED,
                    priority=StrategyPriority.LOW,
                    reason="Intent unknown or confidence below threshold",
                    source_intent=source,
                    requires_clarification=True,
                )
                logger.info("Strategy Selected: intent=%s, strategy=%s", source, result.strategy)
                return result

            rule = self._strategy_registry.get(intent_result.intent)
            if rule is not None:
                result = StrategySelectionResult(
                    strategy=rule["strategy"],
                    priority=rule.get("priority", self.config.default_priority),
                    reason=rule.get("reason", f"Mapped from {intent_result.intent}"),
                    source_intent=intent_result.intent,
                    requires_clarification=rule.get("requires_clarification", False),
                    metadata=rule.get("metadata", {}),
                )
                logger.info("Strategy Selected: intent=%s, strategy=%s", intent_result.intent, result.strategy)
                return result

            if self.config.enable_fallback:
                result = StrategySelectionResult(
                    strategy=ReasoningStrategy.CLARIFICATION_REQUIRED,
                    priority=StrategyPriority.LOW,
                    reason=f"Unmapped intent {intent_result.intent} fallback to clarification",
                    source_intent=intent_result.intent,
                    requires_clarification=True,
                )
                logger.info("Strategy Selected: intent=%s, strategy=%s", intent_result.intent, result.strategy)
                return result

            result = StrategySelectionResult(
                strategy=ReasoningStrategy.UNKNOWN,
                priority=StrategyPriority.LOW,
                reason=f"Unmapped intent {intent_result.intent} without fallback",
                source_intent=intent_result.intent,
                requires_clarification=True,
            )
            logger.info("Strategy Selected: intent=%s, strategy=%s", intent_result.intent, result.strategy)
            return result

    def list_strategies(self) -> Dict[str, Dict[str, Any]]:
        """Lists all registered strategy rules."""
        with self._lock:
            return {k.value: dict(v) for k, v in self._strategy_registry.items()}
