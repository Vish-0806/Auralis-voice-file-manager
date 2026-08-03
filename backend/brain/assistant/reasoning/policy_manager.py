"""Policy Manager implementation for Auralis (Phase 13.4).

Applies deterministic routing policies, detects clarification/confirmation requirements,
evaluates execution eligibility, and assigns decision priority.
Rule-based only — does NOT invoke AI. Thread-safe using threading.RLock().
"""

import logging
import threading
from typing import List, Optional

from brain.assistant.reasoning.exceptions import DecisionValidationError
from brain.assistant.reasoning.interfaces import IDecisionPolicyManager
from brain.assistant.reasoning.models import (
    DecisionAction,
    DecisionCandidate,
    DecisionPolicy,
    DecisionPriority,
    DecisionRequest,
)

logger = logging.getLogger(__name__)

_DESTRUCTIVE_KEYWORDS = {"delete", "remove", "wipe", "format", "purge", "destroy"}
_DIRECT_EXECUTION_KEYWORDS = {"open", "list", "search", "create", "copy", "move"}
_PLANNING_KEYWORDS = {"organize", "pipeline", "workflow", "plan", "batch"}


class PolicyManager(IDecisionPolicyManager):
    """Thread-safe policy engine evaluating deterministic routing candidates."""

    def __init__(self, lock: Optional[threading.RLock] = None) -> None:
        self._lock = lock or threading.RLock()

    def evaluate_policy(
        self,
        request: DecisionRequest,
        policy: Optional[DecisionPolicy] = None,
    ) -> List[DecisionCandidate]:
        """Generate deterministic decision candidates based on policy rules."""
        if not isinstance(request, DecisionRequest):
            raise DecisionValidationError("request must be an instance of DecisionRequest")

        with self._lock:
            pol = policy or DecisionPolicy()
            prompt = (request.user_prompt or "").strip().lower()
            tokens = set(prompt.split())
            ctx = request.context

            candidates: List[DecisionCandidate] = []

            # 1. Clarification Requirement Rule
            if not prompt or ctx.dialogue_status == "WAITING_FOR_CLARIFICATION":
                candidates.append(
                    DecisionCandidate(
                        action=DecisionAction.CLARIFICATION_REQUIRED,
                        score=0.9,
                        priority=DecisionPriority.HIGH,
                        requires_clarification=True,
                        reason="User prompt is empty or awaiting clarification",
                    )
                )

            # 2. Confirmation Requirement Rule for Destructive Operations
            if pol.strict_execution_checks and (
                any(k in tokens for k in _DESTRUCTIVE_KEYWORDS)
                or ctx.dialogue_status == "WAITING_FOR_CONFIRMATION"
            ):
                candidates.append(
                    DecisionCandidate(
                        action=DecisionAction.CONFIRMATION_REQUIRED,
                        score=0.95,
                        priority=DecisionPriority.CRITICAL,
                        requires_confirmation=True,
                        reason="Destructive keyword detected requiring explicit confirmation",
                    )
                )

            # 3. Direct Execution Rule
            if ctx.execution_ready or any(k in tokens for k in _DIRECT_EXECUTION_KEYWORDS):
                candidates.append(
                    DecisionCandidate(
                        action=DecisionAction.DIRECT_EXECUTION,
                        score=0.85,
                        priority=DecisionPriority.HIGH,
                        reason="Direct command keyword or execution readiness satisfied",
                    )
                )

            # 4. Multi-step Planner Rule
            if any(k in tokens for k in _PLANNING_KEYWORDS):
                candidates.append(
                    DecisionCandidate(
                        action=DecisionAction.PLANNER_REQUIRED,
                        score=0.8,
                        priority=DecisionPriority.MEDIUM,
                        reason="Multi-step planning keyword detected",
                    )
                )

            # 5. AI Required Rule
            if ctx.ai_required or pol.auto_ai_fallback:
                candidates.append(
                    DecisionCandidate(
                        action=DecisionAction.AI_REQUIRED,
                        score=0.75,
                        priority=DecisionPriority.MEDIUM,
                        requires_ai=True,
                        reason="Complex query requires AI model assistance",
                    )
                )

            # 6. Fallback Rule
            if not candidates:
                candidates.append(
                    DecisionCandidate(
                        action=DecisionAction.NO_ACTION,
                        score=0.5,
                        priority=pol.default_priority,
                        reason="Default fallback candidate",
                    )
                )

            return candidates
