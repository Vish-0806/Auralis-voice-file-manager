"""Decision Coordinator implementation for Auralis (Phase 13.4).

Coordinates high-level decision routing between Assistant, Dialogue, AI, and Execution subsystems.
Synthesizes DecisionResult without executing LLM calls or OS commands. Thread-safe using threading.RLock().
"""

from datetime import datetime, timezone
import logging
import threading
from typing import Any, Dict, Optional

from brain.assistant.reasoning.decision_evaluator import DecisionEvaluator
from brain.assistant.reasoning.exceptions import DecisionValidationError
from brain.assistant.reasoning.interfaces import (
    IDecisionCoordinator,
    IDecisionEvaluator,
    IDecisionPolicyManager,
)
from brain.assistant.reasoning.models import (
    DecisionAction,
    DecisionOutcome,
    DecisionPolicy,
    DecisionRequest,
    DecisionResult,
)
from brain.assistant.reasoning.policy_manager import PolicyManager

logger = logging.getLogger(__name__)


class DecisionCoordinator(IDecisionCoordinator):
    """Thread-safe coordinator evaluating dialogue state, execution readiness, and decision routing."""

    def __init__(
        self,
        policy_manager: Optional[IDecisionPolicyManager] = None,
        evaluator: Optional[IDecisionEvaluator] = None,
        lock: Optional[threading.RLock] = None,
    ) -> None:
        self._lock = lock or threading.RLock()
        self._policy_manager = policy_manager or PolicyManager(lock=self._lock)
        self._evaluator = evaluator or DecisionEvaluator(lock=self._lock)

    def evaluate_request(
        self,
        request: DecisionRequest,
        policy: Optional[DecisionPolicy] = None,
    ) -> DecisionResult:
        """Evaluate a decision request and produce a deterministic DecisionResult."""
        if not isinstance(request, DecisionRequest):
            raise DecisionValidationError("request must be an instance of DecisionRequest")

        with self._lock:
            # 1. Evaluate policy rules to generate decision candidates
            candidates = self._policy_manager.evaluate_policy(request, policy)

            # 2. Evaluate and score candidates to resolve conflicts
            winner = self._evaluator.evaluate_candidates(candidates, request.context)

            # 3. Formulate clarification/confirmation prompts if required
            clarification_p: Optional[str] = None
            if winner.requires_clarification:
                clarification_p = f"Clarification required for request: '{request.user_prompt}'"

            confirmation_p: Optional[str] = None
            if winner.requires_confirmation:
                confirmation_p = f"Are you sure you want to execute action: '{request.user_prompt}'?"

            requires_planner = winner.action == DecisionAction.PLANNER_REQUIRED
            outcome = DecisionOutcome.ACCEPTED if winner.action != DecisionAction.REJECT else DecisionOutcome.REJECTED

            res = DecisionResult(
                request_id=request.request_id,
                recommended_action=winner.action,
                priority=winner.priority,
                outcome=outcome,
                confidence=winner.score,
                selected_candidate=winner,
                evaluated_candidates=candidates,
                requires_ai=winner.requires_ai,
                requires_planner=requires_planner,
                requires_clarification=winner.requires_clarification,
                requires_confirmation=winner.requires_confirmation,
                clarification_prompt=clarification_p,
                confirmation_prompt=confirmation_p,
                reason=winner.reason,
                evaluated_at=datetime.now(timezone.utc),
            )

            logger.info(
                "Decision evaluated for req_id=%s: action=%s priority=%s",
                request.request_id,
                res.recommended_action,
                res.priority,
            )
            return res
