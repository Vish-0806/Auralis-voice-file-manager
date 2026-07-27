"""Autonomous Decision Engine for pre-execution evaluation and validation."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field

from brain.execution.execution_state import ExecutionState, ExecutionStatus


class DecisionType(str, Enum):
    """Types of execution strategies determined by the DecisionEngine."""

    EXECUTE = "EXECUTE"
    SKIP = "SKIP"
    RETRY = "RETRY"
    WAIT = "WAIT"
    ASK_USER = "ASK_USER"
    USE_FALLBACK = "USE_FALLBACK"
    REUSE_RESOURCE = "REUSE_RESOURCE"
    CANCEL = "CANCEL"


class DecisionReason(str, Enum):
    """Categorized explanation reasons for a decision."""

    RESOURCE_ALREADY_AVAILABLE = "RESOURCE_ALREADY_AVAILABLE"
    APPLICATION_ALREADY_RUNNING = "APPLICATION_ALREADY_RUNNING"
    PREFERENCE_MATCH = "PREFERENCE_MATCH"
    WORKSPACE_CONTEXT = "WORKSPACE_CONTEXT"
    DEPENDENCY_NOT_MET = "DEPENDENCY_NOT_MET"
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    RECOVERABLE_FAILURE = "RECOVERABLE_FAILURE"
    USER_CONFIRMATION_REQUIRED = "USER_CONFIRMATION_REQUIRED"
    TIMEOUT = "TIMEOUT"
    UNKNOWN = "UNKNOWN"


class ExecutionDecision(BaseModel):
    """Encapsulates the pre-execution decision analysis results."""

    decision_type: DecisionType = Field(description="The determined decision strategy type")
    reason: DecisionReason = Field(description="The reasoning category behind the decision")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence of the decision scoring")
    message: str = Field(description="User-readable description explaining the rationale")
    recommended_action: Optional[str] = Field(default=None, description="Recommended remediation action sequence")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata parameters payload")


class DecisionContext(BaseModel):
    """Aggregates active context variables for evaluation by the DecisionEngine."""

    execution_state: Optional[ExecutionState] = Field(default=None, description="Current execution state")
    assistant_context: Optional[Any] = Field(default=None, description="Recent user activity and session context")
    workspace_analysis: Optional[Any] = Field(default=None, description="Workspace analysis results")
    resolved_preferences: Optional[Dict[str, Any]] = Field(default=None, description="Resolved user preferences")
    workflow_metadata: Optional[Dict[str, Any]] = Field(default=None, description="Workflow metadata details")
    capability_metadata: Optional[Dict[str, Any]] = Field(default=None, description="Capability environment metadata")


class DecisionEngine:
    """Evaluates context parameters to dynamically suggest safe and efficient task execution strategies."""

    def evaluate(self, context: Optional[DecisionContext]) -> ExecutionDecision:
        """Evaluates the context and returns the optimal execution strategy.

        Args:
            context: The DecisionContext to evaluate.

        Returns:
            The compiled ExecutionDecision.
        """
        if not context:
            return ExecutionDecision(
                decision_type=DecisionType.CANCEL,
                reason=DecisionReason.UNKNOWN,
                confidence=0.0,
                message="Invalid or empty context provided.",
            )

        # 1. Evaluate user confirmation (ASK_USER)
        confirm_dec = self.evaluate_confirmation(context)
        if confirm_dec:
            return confirm_dec

        # 2. Evaluate dependencies (WAIT/CANCEL)
        dep_dec = self.evaluate_dependency(context)
        if dep_dec:
            return dep_dec

        # 3. Evaluate resource reuse (REUSE_RESOURCE)
        reuse_dec = self.evaluate_resource_reuse(context)
        if reuse_dec:
            return reuse_dec

        # 4. Evaluate fallbacks (USE_FALLBACK)
        fallback_dec = self.evaluate_fallback(context)
        if fallback_dec:
            return fallback_dec

        # 5. Evaluate preferences (PREFERENCE_MATCH)
        pref_dec = self._evaluate_preferences(context)
        if pref_dec:
            return pref_dec

        # 6. Evaluate retries (RETRY)
        retry_dec = self._evaluate_retry_scenarios(context)
        if retry_dec:
            return retry_dec

        return ExecutionDecision(
            decision_type=DecisionType.EXECUTE,
            reason=DecisionReason.UNKNOWN,
            confidence=1.0,
            message="No specific block, fallback, or optimization detected. Execute directly.",
        )

    def evaluate_resource_reuse(self, context: DecisionContext) -> Optional[ExecutionDecision]:
        """Checks if resources/apps are already running to avoid duplication.

        Args:
            context: The DecisionContext.

        Returns:
            An ExecutionDecision recommending resource reuse, or None.
        """
        meta = context.capability_metadata or {}
        if meta.get("vscode_running") is True:
            return ExecutionDecision(
                decision_type=DecisionType.REUSE_RESOURCE,
                reason=DecisionReason.RESOURCE_ALREADY_AVAILABLE,
                confidence=1.0,
                message="VS Code editor is already open on this workspace.",
                recommended_action="Reuse active VS Code instance",
            )
        if meta.get("app_already_running") is True:
            app_name = meta.get("app_name", "Application")
            return ExecutionDecision(
                decision_type=DecisionType.REUSE_RESOURCE,
                reason=DecisionReason.APPLICATION_ALREADY_RUNNING,
                confidence=0.95,
                message=f"{app_name} is already active.",
                recommended_action=f"Focus active {app_name} window",
            )
        return None

    def evaluate_fallback(self, context: DecisionContext) -> Optional[ExecutionDecision]:
        """Determines fallback strategies for missing system programs.

        Args:
            context: The DecisionContext.

        Returns:
            An ExecutionDecision proposing a fallback executable, or None.
        """
        meta = context.capability_metadata or {}
        if meta.get("missing_executable") is True:
            fallback = meta.get("fallback_executable", "Edge")
            original = meta.get("original_executable", "Chrome")
            return ExecutionDecision(
                decision_type=DecisionType.USE_FALLBACK,
                reason=DecisionReason.RESOURCE_NOT_FOUND,
                confidence=0.9,
                message=f"{original} is missing on the host. Fallback to {fallback}.",
                recommended_action=f"Launch using {fallback}",
            )
        return None

    def evaluate_dependency(self, context: DecisionContext) -> Optional[ExecutionDecision]:
        """Checks if execution pre-requisites or connections are met.

        Args:
            context: The DecisionContext.

        Returns:
            An ExecutionDecision (WAIT/CANCEL) for dependency locks, or None.
        """
        meta = context.workflow_metadata or {}
        if meta.get("missing_dependency") is True:
            dep_name = meta.get("dependency_name", "Required package")
            return ExecutionDecision(
                decision_type=DecisionType.WAIT,
                reason=DecisionReason.DEPENDENCY_NOT_MET,
                confidence=0.95,
                message=f"Missing dependency: {dep_name}.",
                recommended_action=f"Wait for dependency {dep_name} compilation",
            )
        return None

    def evaluate_confirmation(self, context: DecisionContext) -> Optional[ExecutionDecision]:
        """Identifies risky steps requesting explicit user validation.

        Args:
            context: The DecisionContext.

        Returns:
            An ExecutionDecision requesting ASK_USER confirmation, or None.
        """
        meta = context.workflow_metadata or {}
        if meta.get("dangerous_operation") is True:
            op_description = meta.get("operation_description", "destructive changes")
            return ExecutionDecision(
                decision_type=DecisionType.ASK_USER,
                reason=DecisionReason.USER_CONFIRMATION_REQUIRED,
                confidence=1.0,
                message=f"Dangerous action detected: {op_description}. Requires explicit authorization.",
                recommended_action="Prompt user for confirmation before proceeding",
            )
        return None

    def _evaluate_preferences(self, context: DecisionContext) -> Optional[ExecutionDecision]:
        """Applies learned user habits to match default capabilities/parameters."""
        prefs = context.resolved_preferences or {}
        if "browser" in prefs:
            pref_browser = prefs["browser"]
            return ExecutionDecision(
                decision_type=DecisionType.EXECUTE,
                reason=DecisionReason.PREFERENCE_MATCH,
                confidence=0.95,
                message=f"Applying user default browser preference: {pref_browser}.",
                recommended_action=f"Use browser default {pref_browser}",
            )
        return None

    def _evaluate_retry_scenarios(self, context: DecisionContext) -> Optional[ExecutionDecision]:
        """Checks if a step failed but is recoverable within retry parameters."""
        state = context.execution_state
        if state and state.status == ExecutionStatus.FAILED:
            # Let's say max retry limits are 3
            if state.retry_count < 3:
                return ExecutionDecision(
                    decision_type=DecisionType.RETRY,
                    reason=DecisionReason.RECOVERABLE_FAILURE,
                    confidence=0.8,
                    message="Recoverable error encountered. Retry step.",
                    recommended_action="Execute retry attempt",
                )
        return None
