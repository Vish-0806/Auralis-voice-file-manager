"""Reasoning Context Builder for combining all reasoning outputs into a single immutable ReasoningContext.

This module provides thread-safe context building without executing commands, generating execution plans,
calling LLMs, accessing memory providers, modifying conversations, or modifying upstream reasoning results.
"""

from datetime import datetime, timezone
import logging
import threading
from typing import Any, Callable, Dict, List, Optional

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict, Field

from brain.reasoning.constraint_analyzer import ConstraintAnalysisResult
from brain.reasoning.goal_extractor import GoalExtractionResult
from brain.reasoning.intent_analyzer import IntentAnalysisResult
from brain.reasoning.strategy_selector import StrategySelectionResult

logger = logging.getLogger(__name__)


class ReasoningContext(BaseModel):
    """Immutable model representing the combined outcome of multi-stage reasoning analysis."""

    model_config = ConfigDict(frozen=True)

    request: str = ""
    intent: IntentAnalysisResult = Field(default_factory=IntentAnalysisResult)
    strategy: StrategySelectionResult = Field(default_factory=StrategySelectionResult)
    goal: GoalExtractionResult = Field(default_factory=GoalExtractionResult)
    constraints: ConstraintAnalysisResult = Field(default_factory=ConstraintAnalysisResult)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ReasoningContextBuilderConfig(BaseModel):
    """Configuration options for ReasoningContextBuilder behavior."""

    include_metadata: bool = True
    validate_components: bool = True
    strict_building: bool = True


class ReasoningContextBuilder:
    """Thread-safe engine for building immutable ReasoningContext objects."""

    def __init__(self, config: Optional[ReasoningContextBuilderConfig] = None) -> None:
        """Initializes the ReasoningContextBuilder with optional configuration and thread lock."""
        self.config = config or ReasoningContextBuilderConfig()
        self._context_hooks: List[Dict[str, Any]] = []
        self._lock = threading.RLock()

    def register_context_hook(
        self,
        hook_id: str,
        hook_func: Callable[[Dict[str, Any]], Dict[str, Any]],
        priority: int = 10,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Registers a context metadata transformation hook."""
        with self._lock:
            # Remove duplicate hook if present
            self._context_hooks = [h for h in self._context_hooks if h["hook_id"] != hook_id]

            hook_entry = {
                "hook_id": hook_id,
                "hook_func": hook_func,
                "priority": priority,
                "metadata": metadata or {},
            }
            self._context_hooks.append(hook_entry)
            logger.info("Context Hook Registered: hook_id=%s", hook_id)
            return True

    def remove_context_hook(self, hook_id: str) -> bool:
        """Removes a registered context hook by hook_id."""
        with self._lock:
            initial_count = len(self._context_hooks)
            self._context_hooks = [h for h in self._context_hooks if h["hook_id"] != hook_id]
            removed = len(self._context_hooks) < initial_count

            if removed:
                logger.info("Context Hook Removed: hook_id=%s", hook_id)
                return True
            return False

    def clear_context_hooks(self) -> None:
        """Clears all context hooks from the registry."""
        with self._lock:
            self._context_hooks.clear()
            logger.info("Context Hooks Cleared")

    def build_context(
        self,
        request: Any = "",
        intent_result: Optional[IntentAnalysisResult] = None,
        strategy_result: Optional[StrategySelectionResult] = None,
        goal_result: Optional[GoalExtractionResult] = None,
        constraint_result: Optional[ConstraintAnalysisResult] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ReasoningContext:
        """Constructs an immutable ReasoningContext combining all stage reasoning outputs."""
        with self._lock:
            req_str = request if isinstance(request, str) else ""

            intent_val = intent_result if isinstance(intent_result, IntentAnalysisResult) else IntentAnalysisResult()
            strategy_val = strategy_result if isinstance(strategy_result, StrategySelectionResult) else StrategySelectionResult()
            goal_val = goal_result if isinstance(goal_result, GoalExtractionResult) else GoalExtractionResult()
            constraint_val = constraint_result if isinstance(constraint_result, ConstraintAnalysisResult) else ConstraintAnalysisResult()

            ctx_metadata = dict(metadata or {})

            # Execute registered context hooks sorted by priority descending
            if self.config.include_metadata and self._context_hooks:
                sorted_hooks = sorted(self._context_hooks, key=lambda h: h.get("priority", 10), reverse=True)
                for hook in sorted_hooks:
                    try:
                        func = hook["hook_func"]
                        updated = func(dict(ctx_metadata))
                        if isinstance(updated, dict):
                            ctx_metadata = updated
                    except Exception as e:
                        logger.warning("Context hook '%s' raised exception: %s", hook.get("hook_id"), e)

            now = datetime.now(timezone.utc)
            context = ReasoningContext(
                request=req_str,
                intent=intent_val,
                strategy=strategy_val,
                goal=goal_val,
                constraints=constraint_val,
                created_at=now,
                metadata=ctx_metadata,
            )

            logger.info("Reasoning Context Built")
            return context

    def list_context_hooks(self) -> List[Dict[str, Any]]:
        """Lists registered context hooks."""
        with self._lock:
            return [
                {
                    "hook_id": h["hook_id"],
                    "priority": h["priority"],
                    "metadata": dict(h.get("metadata", {})),
                }
                for h in self._context_hooks
            ]
