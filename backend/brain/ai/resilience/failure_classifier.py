"""DefaultFailureClassifier implementation for exception classification (Phase 10.7).

Classifies runtime errors into FailureInfo models with FailureType categories
(TRANSIENT, PERMANENT, VALIDATION, PROVIDER, TOOL, TIMEOUT, CANCELLATION, UNKNOWN).
"""

import uuid
import logging
from typing import Any, Dict, Optional

from brain.ai.resilience.interfaces import FailureClassifierInterface
from brain.ai.resilience.resilience_models import FailureInfo, FailureType

logger = logging.getLogger(__name__)


class DefaultFailureClassifier(FailureClassifierInterface):
    """Classifies exceptions into structured FailureInfo categories."""

    def classify_failure(
        self,
        exception_or_message: Any,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> FailureInfo:
        """Classify failure into FailureInfo model.

        Args:
            exception_or_message: Exception instance or error message string.
            metadata: Optional contextual metadata dict.

        Returns:
            FailureInfo model.
        """
        meta = metadata or {}
        msg = str(exception_or_message)
        exc_class = type(exception_or_message).__name__ if isinstance(exception_or_message, Exception) else None

        failure_type, is_transient = self._determine_type(exception_or_message, msg)

        return FailureInfo(
            failure_id=f"fail-{uuid.uuid4().hex[:8]}",
            failure_type=failure_type,
            message=msg,
            exception_class=exc_class,
            is_transient=is_transient,
            metadata=meta,
        )

    def _determine_type(self, err: Any, msg: str) -> tuple[FailureType, bool]:
        """Determine FailureType and is_transient flag."""
        msg_lower = msg.lower()

        # 1. Timeout Errors
        if "timeout" in msg_lower or "timed out" in msg_lower or "Timeout" in str(type(err)):
            return FailureType.TIMEOUT, True

        # 2. Cancellation Errors
        if "cancell" in msg_lower:
            return FailureType.CANCELLATION, False

        # 3. Permanent / Authentication Errors
        if any(term in msg_lower for term in ["401", "403", "unauthorized", "invalid api key", "forbidden"]):
            return FailureType.PERMANENT, False

        # 4. Transient HTTP & Network Errors (429, 502, 503, 504, rate limit, connection reset)
        if any(term in msg_lower for term in ["rate limit", "429", "502", "503", "504", "connection reset", "network error", "retry later"]):
            return FailureType.TRANSIENT, True

        # 5. Tool Errors
        if "tool" in msg_lower:
            return FailureType.TOOL, False

        # 6. Validation Errors
        if any(term in msg_lower for term in ["validation", "invalid", "schema", "json"]):
            return FailureType.VALIDATION, False

        # 7. Provider Errors
        if any(term in msg_lower for term in ["provider", "groq", "llm"]):
            return FailureType.PROVIDER, True

        return FailureType.UNKNOWN, False
