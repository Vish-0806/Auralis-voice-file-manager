"""Failure Recovery Engine for analyzing runtime exceptions and planning strategy."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field, ConfigDict


class FailureCategory(str, Enum):
    """Categorized runtime failures analyzed by the FailureRecoveryEngine."""

    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    APPLICATION_NOT_AVAILABLE = "APPLICATION_NOT_AVAILABLE"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    TIMEOUT = "TIMEOUT"
    NETWORK_ERROR = "NETWORK_ERROR"
    FILESYSTEM_ERROR = "FILESYSTEM_ERROR"
    DEPENDENCY_FAILURE = "DEPENDENCY_FAILURE"
    INVALID_PARAMETERS = "INVALID_PARAMETERS"
    USER_CANCELLED = "USER_CANCELLED"
    UNKNOWN = "UNKNOWN"


class RecoveryStrategy(str, Enum):
    """Actionable strategies recommended by the FailureRecoveryEngine."""

    RETRY = "RETRY"
    WAIT = "WAIT"
    USE_FALLBACK = "USE_FALLBACK"
    SKIP = "SKIP"
    ASK_USER = "ASK_USER"
    ABORT = "ABORT"
    IGNORE = "IGNORE"


class FailureAnalysis(BaseModel):
    """Contains the details of failure analysis and classification."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    failure_category: FailureCategory = Field(description="Classified failure category type")
    original_exception: Optional[Any] = Field(default=None, description="The raw runtime exception observed")
    message: str = Field(description="User-readable description or warning message")
    recoverable: bool = Field(description="Whether a recovery plan is feasible for this failure type")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Analysis confidence score")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata parameters payload")


class RecoveryPlan(BaseModel):
    """Detailed recipe proposing deterministic actions to restore system continuity."""

    strategy: RecoveryStrategy = Field(description="The recommended recovery strategy type")
    reason: str = Field(description="Detailed rationale for choosing this recovery path")
    recommended_action: Optional[str] = Field(default=None, description="Actionable remediation sequence instructions")
    maximum_retry_count: int = Field(default=3, description="Maximum number of retries before aborting")
    wait_seconds: float = Field(default=0.0, description="Amount of time to wait before trying again")
    fallback_resource: Optional[str] = Field(default=None, description="Alternative target resource name if fallback strategy is used")
    requires_user_confirmation: bool = Field(default=False, description="Whether execution requires explicit authorization")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata parameters payload")


class RecoveryContext(BaseModel):
    """Gathers context details required to compute the failure recovery plan."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    execution_state: Optional[Any] = Field(default=None, description="The active ExecutionState details")
    execution_step: Optional[Any] = Field(default=None, description="The specific failed workflow step ID/data")
    assistant_context: Optional[Any] = Field(default=None, description="The current assistant runtime state context")
    workspace_analysis: Optional[Any] = Field(default=None, description="Active workspace path/context metrics")
    resolved_preferences: Optional[Dict[str, Any]] = Field(default=None, description="Resolved default settings and parameters")
    exception: Optional[Any] = Field(default=None, description="The raw runtime exception thrown")
    retry_count: int = Field(default=0, description="Number of retries already performed")


class FailureRecoveryEngine:
    """Analyzes step/workflow failures and builds explainable, deterministic recovery plans."""

    def classify_exception(self, exception: Optional[Any]) -> FailureCategory:
        """Categorizes exception objects into FailureCategory.

        Args:
            exception: The exception instance or string representation.

        Returns:
            The matched FailureCategory.
        """
        if exception is None:
            return FailureCategory.UNKNOWN

        if isinstance(exception, FileNotFoundError):
            return FailureCategory.RESOURCE_NOT_FOUND
        if isinstance(exception, PermissionError):
            return FailureCategory.PERMISSION_DENIED
        if isinstance(exception, TimeoutError):
            return FailureCategory.TIMEOUT
        if isinstance(exception, (ConnectionError, ConnectionRefusedError)):
            return FailureCategory.NETWORK_ERROR

        # Handle exception passed as string
        exc_str = str(exception)
        if "FileNotFound" in exc_str or "No such file" in exc_str:
            return FailureCategory.RESOURCE_NOT_FOUND
        if "PermissionError" in exc_str or "Access denied" in exc_str or "Permission denied" in exc_str:
            return FailureCategory.PERMISSION_DENIED
        if "TimeoutError" in exc_str or "timed out" in exc_str:
            return FailureCategory.TIMEOUT
        if "ConnectionError" in exc_str or "network" in exc_str or "connection refused" in exc_str:
            return FailureCategory.NETWORK_ERROR

        return FailureCategory.UNKNOWN

    def recommend_strategy(self, analysis: FailureAnalysis) -> RecoveryStrategy:
        """Determines the optimal RecoveryStrategy based on failure classification.

        Args:
            analysis: The FailureAnalysis results.

        Returns:
            The recommended RecoveryStrategy.
        """
        cat = analysis.failure_category
        if cat == FailureCategory.RESOURCE_NOT_FOUND:
            return RecoveryStrategy.USE_FALLBACK
        elif cat == FailureCategory.PERMISSION_DENIED:
            return RecoveryStrategy.ASK_USER
        elif cat == FailureCategory.TIMEOUT:
            return RecoveryStrategy.RETRY
        elif cat == FailureCategory.NETWORK_ERROR:
            return RecoveryStrategy.WAIT
        else:
            return RecoveryStrategy.ABORT

    def analyse_failure(self, context: RecoveryContext) -> FailureAnalysis:
        """Analyzes a failure context and produces a detailed FailureAnalysis.

        Args:
            context: The RecoveryContext.

        Returns:
            The computed FailureAnalysis.
        """
        cat = self.classify_exception(context.exception)
        
        # Decide if recoverable
        recoverable = (cat in {
            FailureCategory.RESOURCE_NOT_FOUND,
            FailureCategory.PERMISSION_DENIED,
            FailureCategory.TIMEOUT,
            FailureCategory.NETWORK_ERROR,
        })

        # Confidence: High if matched correctly, lower for unknown/fallback types
        confidence = 1.0 if cat != FailureCategory.UNKNOWN else 0.5
        msg = str(context.exception) if context.exception else "Unknown execution error"

        return FailureAnalysis(
            failure_category=cat,
            original_exception=context.exception,
            message=msg,
            recoverable=recoverable,
            confidence=confidence,
            metadata={"retry_count": context.retry_count},
        )

    def build_recovery_plan(self, context: RecoveryContext) -> RecoveryPlan:
        """Produces a deterministic, explainable RecoveryPlan for a given failure context.

        Args:
            context: The RecoveryContext.

        Returns:
            The compiled RecoveryPlan.
        """
        if not context:
            return RecoveryPlan(
                strategy=RecoveryStrategy.ABORT,
                reason="Context is empty or invalid.",
                confidence=0.0,
            )

        analysis = self.analyse_failure(context)
        strategy = self.recommend_strategy(analysis)

        action = None
        wait_secs = 0.0
        req_confirm = False

        if strategy == RecoveryStrategy.USE_FALLBACK:
            action = "Launch alternative fallback browser/capability resource"
        elif strategy == RecoveryStrategy.ASK_USER:
            action = "Prompt user for elevated permission or credentials validation"
            req_confirm = True
        elif strategy == RecoveryStrategy.RETRY:
            action = "Re-execute step directly"
        elif strategy == RecoveryStrategy.WAIT:
            action = "Wait for network link stabilization"
            wait_secs = 10.0
        elif strategy == RecoveryStrategy.ABORT:
            action = "Clean up and cancel parent pipeline run"

        return RecoveryPlan(
            strategy=strategy,
            reason=f"Failure category {analysis.failure_category.value} resolved. Context: {analysis.message}",
            recommended_action=action,
            maximum_retry_count=3,
            wait_seconds=wait_secs,
            fallback_resource=context.resolved_preferences.get("fallback") if context.resolved_preferences else None,
            requires_user_confirmation=req_confirm,
            metadata=analysis.metadata,
        )
