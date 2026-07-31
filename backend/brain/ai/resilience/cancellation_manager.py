"""DefaultCancellationManager implementation for tracking cancellation requests (Phase 10.7).

Records manual, timeout, and dependency cancellation requests and maintains propagation state.
"""

import uuid
import logging
from typing import Any, Dict, Optional

from brain.ai.resilience.interfaces import CancellationManagerInterface
from brain.ai.resilience.resilience_models import (
    CancellationReason,
    CancellationRequest,
)

logger = logging.getLogger(__name__)


class DefaultCancellationManager(CancellationManagerInterface):
    """Tracks and evaluates operation cancellation requests."""

    def __init__(self) -> None:
        self._requests: Dict[str, CancellationRequest] = {}

    def request_cancellation(
        self,
        target_id: str,
        requested_by: str,
        reason: CancellationReason,
        details: Optional[Dict[str, Any]] = None,
    ) -> CancellationRequest:
        """Issue a cancellation request for a target."""
        req_id = f"cancel-{uuid.uuid4().hex[:8]}"

        request = CancellationRequest(
            request_id=req_id,
            target_id=target_id,
            requested_by=requested_by,
            reason=reason,
            details=details or {},
        )
        self._requests[target_id] = request
        logger.info(f"Cancellation requested for target '{target_id}' by '{requested_by}' ({reason.value}).")
        return request

    def is_cancelled(self, target_id: str) -> bool:
        """Check if target is cancelled."""
        return target_id in self._requests

    def get_cancellation_request(self, target_id: str) -> Optional[CancellationRequest]:
        """Retrieve CancellationRequest details for a target."""
        return self._requests.get(target_id)
