"""DefaultRecoveryManager implementation for computing recovery decisions (Phase 10.7).

Determines RecoveryDecision actions (RETRY, CONTINUE, SKIP, ABORT, ESCALATE) based on
classified FailureInfo and policy thresholds without executing recovery actions directly.
"""

import uuid
import logging

from brain.ai.resilience.interfaces import RecoveryManagerInterface
from brain.ai.resilience.resilience_models import (
    FailureInfo,
    FailureType,
    RecoveryAction,
    RecoveryDecision,
)

logger = logging.getLogger(__name__)


class DefaultRecoveryManager(RecoveryManagerInterface):
    """Computes recovery decisions based on failure classification."""

    def determine_recovery(
        self,
        failure_info: FailureInfo,
        attempt_number: int = 1,
        max_retries: int = 3,
    ) -> RecoveryDecision:
        """Determine recovery action (RETRY, CONTINUE, SKIP, ABORT, ESCALATE).

        Args:
            failure_info: Classified FailureInfo model.
            attempt_number: Current attempt count.
            max_retries: Maximum retries limit.

        Returns:
            RecoveryDecision model instance.
        """
        dec_id = f"dec-{uuid.uuid4().hex[:8]}"

        # 1. Cancellation -> ABORT
        if failure_info.failure_type == FailureType.CANCELLATION:
            return RecoveryDecision(
                decision_id=dec_id,
                action=RecoveryAction.ABORT,
                failure_info=failure_info,
                reason="Operation cancelled by user or system.",
            )

        # 2. Permanent Failure -> ESCALATE
        if failure_info.failure_type == FailureType.PERMANENT:
            return RecoveryDecision(
                decision_id=dec_id,
                action=RecoveryAction.ESCALATE,
                failure_info=failure_info,
                reason="Permanent failure detected (e.g. invalid auth credentials). Escalating to user.",
            )

        # 3. Transient Failure & Retries Remaining -> RETRY
        if failure_info.is_transient and attempt_number <= max_retries:
            return RecoveryDecision(
                decision_id=dec_id,
                action=RecoveryAction.RETRY,
                failure_info=failure_info,
                retry_delay_seconds=1.0 * (2 ** (attempt_number - 1)),
                reason=f"Transient failure (attempt {attempt_number}/{max_retries}). Scheduling retry.",
            )

        # 4. Tool Execution Failure -> SKIP
        if failure_info.failure_type == FailureType.TOOL:
            return RecoveryDecision(
                decision_id=dec_id,
                action=RecoveryAction.SKIP,
                failure_info=failure_info,
                reason="Tool execution failed. Skipping step to preserve pipeline continuity.",
            )

        # 5. Retries Exhausted -> ABORT
        if attempt_number > max_retries:
            return RecoveryDecision(
                decision_id=dec_id,
                action=RecoveryAction.ABORT,
                failure_info=failure_info,
                reason=f"Maximum retries ({max_retries}) exhausted. Aborting operation.",
            )

        # 6. Fallback -> ESCALATE
        return RecoveryDecision(
            decision_id=dec_id,
            action=RecoveryAction.ESCALATE,
            failure_info=failure_info,
            reason="Unclassified failure. Escalating for handling.",
        )
