"""Autonomous Decision Engine for pre-execution evaluation and validation (Phase 12.1).

Responsible for deciding:
- direct execution (DIRECT_EXECUTION)
- planner required (PLANNER_REQUIRED)
- AI required (AI_REQUIRED)
- clarification required (CLARIFICATION_REQUIRED)
- security review required (SECURITY_REVIEW_REQUIRED)

Must only produce ExecutionDecision objects. Performs zero execution.
Maintains 100% backward compatibility for legacy DecisionContext evaluations.
"""

from __future__ import annotations

from enum import Enum
import logging
from typing import Any, Dict, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field

from brain.execution.execution_models import (
    DecisionType,
    ExecutionDecision,
    ExecutionMode,
    ExecutionRequest,
)
from brain.execution.execution_state import ExecutionState, ExecutionStatus
from brain.execution.interfaces import IDecisionEngine

logger = logging.getLogger(__name__)


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
    DANGEROUS_OPERATION = "DANGEROUS_OPERATION"
    MULTI_STEP_WORKFLOW = "MULTI_STEP_WORKFLOW"
    AI_REASONING_REQUIRED = "AI_REASONING_REQUIRED"
    AMBIGUOUS_PROMPT = "AMBIGUOUS_PROMPT"
    DIRECT_SYSTEM_ACTION = "DIRECT_SYSTEM_ACTION"


class DecisionContext(BaseModel):
    """Aggregates active context variables for evaluation by the DecisionEngine (legacy support)."""

    execution_state: Optional[ExecutionState] = Field(default=None, description="Current execution state")
    assistant_context: Optional[Any] = Field(default=None, description="Recent user activity and session context")
    workspace_analysis: Optional[Any] = Field(default=None, description="Workspace analysis results")
    resolved_preferences: Optional[Dict[str, Any]] = Field(default=None, description="Resolved user preferences")
    workflow_metadata: Optional[Dict[str, Any]] = Field(default=None, description="Workflow metadata details")
    capability_metadata: Optional[Dict[str, Any]] = Field(default=None, description="Capability environment metadata")


class DecisionEngine(IDecisionEngine):
    """Evaluates request context to decide execution routing strategy without executing logic."""

    def __init__(self, clarification_engine: Any | None = None) -> None:
        """Initialize DecisionEngine with optional clarification engine dependency."""
        self._clarification_engine = clarification_engine

    def evaluate(self, request_or_context: Any) -> ExecutionDecision:
        """Formulate an ExecutionDecision for an analyzed request or DecisionContext.

        Args:
            request_or_context: ExecutionRequest, DecisionContext, dict, or prompt string.

        Returns:
            ExecutionDecision object detailing routing requirements.
        """
        if request_or_context is None:
            return ExecutionDecision(
                decision_type=DecisionType.CANCEL,
                reason=DecisionReason.UNKNOWN.value,
                confidence=0.0,
                reason_code=DecisionReason.UNKNOWN if hasattr(DecisionReason, "UNKNOWN") else None,
                message="Invalid or empty context provided.",
            )

        # Handle legacy DecisionContext object
        if isinstance(request_or_context, DecisionContext):
            return self._evaluate_legacy_context(request_or_context)

        # Ensure request is an ExecutionRequest
        if isinstance(request_or_context, ExecutionRequest):
            req = request_or_context
        elif isinstance(request_or_context, dict):
            req = ExecutionRequest(
                prompt=str(request_or_context.get("prompt", "")),
                category=request_or_context.get("category"),
                metadata=request_or_context.get("metadata", {}),
            )
        elif isinstance(request_or_context, str):
            req = ExecutionRequest(prompt=request_or_context)
        else:
            # Check if it has DecisionContext-like attributes
            if hasattr(request_or_context, "workflow_metadata") or hasattr(request_or_context, "capability_metadata"):
                return self._evaluate_legacy_context(request_or_context)
            req = ExecutionRequest(prompt=str(request_or_context))

        return self.evaluate_request(req)

    def evaluate_request(self, request: ExecutionRequest) -> ExecutionDecision:
        """Evaluate an analyzed ExecutionRequest to formulate a Phase 12.1 ExecutionDecision.

        Decision precedence:
        1. Security Review Required (destructive actions, dangerous operation flag)
        2. Clarification Required (ambiguous prompt, missing parameters)
        3. Planner Required (workflow category, high complexity, multi-step)
        4. AI Required (AI generation category, open-ended reasoning)
        5. Direct Execution (default)
        """
        prompt_lower = request.prompt.lower()
        meta = request.metadata or {}

        # 1. Security Review Check
        if meta.get("is_potentially_destructive") is True or any(
            kw in prompt_lower for kw in ["format drive", "delete system", "drop database", "sudo rm -rf", "kill -9"]
        ):
            return ExecutionDecision(
                decision_type=DecisionType.SECURITY_REVIEW_REQUIRED,
                requires_security_review=True,
                mode=ExecutionMode.CRITICAL,
                confidence=1.0,
                reason="Potentially destructive operation detected requiring security authorization.",
                recommended_action="Prompt user for security confirmation before proceeding",
                metadata={"category": request.category, "risk_level": "HIGH"},
            )

        # 2. Clarification Required Check
        if meta.get("requires_clarification") is True or (not request.prompt.strip() and not meta):
            return ExecutionDecision(
                decision_type=DecisionType.CLARIFICATION_REQUIRED,
                requires_clarification=True,
                mode=ExecutionMode.INTERACTIVE,
                confidence=0.95,
                reason="Ambiguous or incomplete request requires user clarification.",
                recommended_action="Ask user for additional parameters",
                metadata={"category": request.category},
            )

        # 3. Planner Required Check
        if (
            request.category == "WORKFLOW_PLANNING"
            or meta.get("complexity") in ("HIGH", "CRITICAL")
            or meta.get("estimated_step_count", 1) > 2
            or request.mode == ExecutionMode.PLANNED
        ):
            return ExecutionDecision(
                decision_type=DecisionType.PLANNER_REQUIRED,
                requires_planner=True,
                mode=ExecutionMode.PLANNED,
                confidence=0.95,
                reason="Multi-step workflow or high complexity request requires action planning.",
                recommended_action="Invoke ActionPlanner pipeline",
                metadata={"category": request.category, "step_count": meta.get("estimated_step_count", 1)},
            )

        # 4. AI Required Check
        if request.category == "AI_GENERATION" or request.mode == ExecutionMode.AI_GUIDED or any(
            kw in prompt_lower for kw in ["generate", "summarize", "explain", "code", "draft essay", "translate"]
        ):
            return ExecutionDecision(
                decision_type=DecisionType.AI_REQUIRED,
                requires_ai=True,
                mode=ExecutionMode.AI_GUIDED,
                confidence=0.9,
                reason="Open-ended reasoning or generation request requires AI Orchestrator.",
                recommended_action="Route request through AI Runtime",
                metadata={"category": request.category},
            )

        # 5. Direct Execution (Default)
        return ExecutionDecision(
            decision_type=DecisionType.DIRECT_EXECUTION,
            mode=ExecutionMode.DIRECT,
            confidence=1.0,
            reason="Request can be executed directly without planner or AI reasoning.",
            recommended_action="Execute directly via OS Runtime",
            metadata={"category": request.category},
        )

    # ------------------------------------------------------------------
    # Legacy DecisionContext Evaluators (Backward Compatibility)
    # ------------------------------------------------------------------

    def _evaluate_legacy_context(self, context: Any) -> ExecutionDecision:
        """Internal helper handling legacy DecisionContext evaluation."""
        if self._clarification_engine is None:
            try:
                from brain.execution.clarification_engine import ClarificationEngine
                self._clarification_engine = ClarificationEngine()
            except Exception:
                pass

        if self._clarification_engine is not None:
            try:
                step_obj = None
                wf_meta = getattr(context, "workflow_metadata", None) or {}
                ex_state = getattr(context, "execution_state", None)

                if wf_meta or ex_state:
                    from core.intents import Intent
                    target_val = wf_meta.get("target")
                    if not target_val and ex_state:
                        target_val = getattr(ex_state, "metadata", {}).get("target") or getattr(ex_state, "current_step_id", None)

                    intent_val = wf_meta.get("intent")
                    if not intent_val and ex_state:
                        intent_val = getattr(ex_state, "metadata", {}).get("intent")

                    intent_enum = Intent(intent_val) if intent_val and (intent_val in Intent.__members__ or intent_val in [v.value for v in Intent]) else None

                    class HelperStep:
                        def __init__(self, target, intent, parameters):
                            self.target = target
                            self.intent = intent
                            self.parameters = parameters or {}

                    step_obj = HelperStep(target_val, intent_enum, wf_meta.get("parameters") or (getattr(ex_state, "metadata", {}) if ex_state else {}))

                from brain.execution.clarification_engine import ClarificationContext as ClarCtx
                clar_context = ClarCtx(
                    assistant_context=getattr(context, "assistant_context", None) if isinstance(getattr(context, "assistant_context", None), dict) else None,
                    execution_step=step_obj,
                    workspace_analysis=getattr(context, "workspace_analysis", None) if isinstance(getattr(context, "workspace_analysis", None), dict) else None,
                    resolved_preferences=getattr(context, "resolved_preferences", None),
                    metadata=getattr(ex_state, "metadata", {}) if ex_state else {},
                )

                if self._clarification_engine.detect_clarification(clar_context):
                    return ExecutionDecision(
                        decision_type=DecisionType.ASK_USER,
                        requires_clarification=True,
                        reason=DecisionReason.USER_CONFIRMATION_REQUIRED.value,
                        confidence=1.0,
                        reason_code=DecisionReason.USER_CONFIRMATION_REQUIRED,
                        message="Clarification required before task execution.",
                        recommended_action="Ask user for clarification",
                    )
            except Exception as exc:
                logger.debug("Clarification check skipped in DecisionEngine: %s", exc)

        # 1. Evaluate confirmation
        confirm_dec = self.evaluate_confirmation(context)
        if confirm_dec:
            return confirm_dec

        # 2. Evaluate dependency
        dep_dec = self.evaluate_dependency(context)
        if dep_dec:
            return dep_dec

        # 3. Evaluate resource reuse
        reuse_dec = self.evaluate_resource_reuse(context)
        if reuse_dec:
            return reuse_dec

        # 4. Evaluate fallback
        fallback_dec = self.evaluate_fallback(context)
        if fallback_dec:
            return fallback_dec

        # 5. Evaluate preferences
        pref_dec = self._evaluate_preferences(context)
        if pref_dec:
            return pref_dec

        # 6. Evaluate retries
        retry_dec = self._evaluate_retry_scenarios(context)
        if retry_dec:
            return retry_dec

        return ExecutionDecision(
            decision_type=DecisionType.EXECUTE,
            reason=DecisionReason.UNKNOWN.value,
            confidence=1.0,
            reason_code=DecisionReason.UNKNOWN,
            message="No specific block, fallback, or optimization detected. Execute directly.",
        )

    def evaluate_resource_reuse(self, context: Any) -> Optional[ExecutionDecision]:
        """Checks if resources/apps are already running to avoid duplication."""
        meta = getattr(context, "capability_metadata", None) or {}
        if meta.get("vscode_running") is True:
            return ExecutionDecision(
                decision_type=DecisionType.REUSE_RESOURCE,
                reason=DecisionReason.RESOURCE_ALREADY_AVAILABLE.value,
                confidence=1.0,
                reason_code=DecisionReason.RESOURCE_ALREADY_AVAILABLE,
                message="VS Code editor is already open on this workspace.",
                recommended_action="Reuse active VS Code instance",
            )
        if meta.get("app_already_running") is True:
            app_name = meta.get("app_name", "Application")
            return ExecutionDecision(
                decision_type=DecisionType.REUSE_RESOURCE,
                reason=DecisionReason.APPLICATION_ALREADY_RUNNING.value,
                confidence=0.95,
                reason_code=DecisionReason.APPLICATION_ALREADY_RUNNING,
                message=f"{app_name} is already active.",
                recommended_action=f"Focus active {app_name} window",
            )
        return None

    def evaluate_fallback(self, context: Any) -> Optional[ExecutionDecision]:
        """Determines fallback strategies for missing system programs."""
        meta = getattr(context, "capability_metadata", None) or {}
        if meta.get("missing_executable") is True:
            fallback = meta.get("fallback_executable", "Edge")
            original = meta.get("original_executable", "Chrome")
            return ExecutionDecision(
                decision_type=DecisionType.USE_FALLBACK,
                reason=DecisionReason.RESOURCE_NOT_FOUND.value,
                confidence=0.9,
                reason_code=DecisionReason.RESOURCE_NOT_FOUND,
                message=f"{original} is missing on the host. Fallback to {fallback}.",
                recommended_action=f"Launch using {fallback}",
            )
        return None

    def evaluate_dependency(self, context: Any) -> Optional[ExecutionDecision]:
        """Checks if execution pre-requisites or connections are met."""
        meta = getattr(context, "workflow_metadata", None) or {}
        if meta.get("missing_dependency") is True:
            dep_name = meta.get("dependency_name", "Required package")
            return ExecutionDecision(
                decision_type=DecisionType.WAIT,
                reason=DecisionReason.DEPENDENCY_NOT_MET.value,
                confidence=0.95,
                reason_code=DecisionReason.DEPENDENCY_NOT_MET,
                message=f"Missing dependency: {dep_name}.",
                recommended_action=f"Wait for dependency {dep_name} compilation",
            )
        return None

    def evaluate_confirmation(self, context: Any) -> Optional[ExecutionDecision]:
        """Identifies risky steps requesting explicit user validation."""
        meta = getattr(context, "workflow_metadata", None) or {}
        if meta.get("dangerous_operation") is True:
            op_description = meta.get("operation_description", "destructive changes")
            return ExecutionDecision(
                decision_type=DecisionType.ASK_USER,
                requires_security_review=True,
                reason=DecisionReason.USER_CONFIRMATION_REQUIRED.value,
                confidence=1.0,
                reason_code=DecisionReason.USER_CONFIRMATION_REQUIRED,
                message=f"Dangerous action detected: {op_description}. Requires explicit authorization.",
                recommended_action="Prompt user for confirmation before proceeding",
            )
        return None

    def _evaluate_preferences(self, context: Any) -> Optional[ExecutionDecision]:
        """Applies learned user habits to match default capabilities/parameters."""
        prefs = getattr(context, "resolved_preferences", None) or {}
        if "browser" in prefs:
            pref_browser = prefs["browser"]
            return ExecutionDecision(
                decision_type=DecisionType.EXECUTE,
                reason=DecisionReason.PREFERENCE_MATCH.value,
                confidence=0.95,
                reason_code=DecisionReason.PREFERENCE_MATCH,
                message=f"Applying user default browser preference: {pref_browser}.",
                recommended_action=f"Use browser default {pref_browser}",
            )
        return None

    def _evaluate_retry_scenarios(self, context: Any) -> Optional[ExecutionDecision]:
        """Checks if a step failed but is recoverable within retry parameters."""
        state = getattr(context, "execution_state", None)
        if state and getattr(state, "status", None) == ExecutionStatus.FAILED:
            if getattr(state, "retry_count", 0) < 3:
                return ExecutionDecision(
                    decision_type=DecisionType.RETRY,
                    reason=DecisionReason.RECOVERABLE_FAILURE.value,
                    confidence=0.8,
                    reason_code=DecisionReason.RECOVERABLE_FAILURE,
                    message="Recoverable error encountered. Retry step.",
                    recommended_action="Execute retry attempt",
                )
        return None
