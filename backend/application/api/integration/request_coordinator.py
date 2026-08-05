"""API Request Coordinator Implementation (Phase 15.9).

Thread-safe request coordinator preparing immutable request contexts and validating
request metadata without transport or networking logic.
"""

import logging
from threading import RLock
from typing import Dict
import uuid

from backend.application.api.integration.exceptions import (
    RequestCoordinationException,
)
from backend.application.api.integration.interfaces import IRequestCoordinator
from backend.application.api.integration.models import (
    ApiIntegrationRequest,
    ApiRequestContext,
    PipelineStage,
)

logger = logging.getLogger(__name__)


class RequestCoordinator(IRequestCoordinator):
    """Thread-safe request coordinator preparing request contexts for gateway execution."""

    def __init__(self) -> None:
        """Initialize RequestCoordinator using Constructor Dependency Injection."""
        self._lock = RLock()
        self._total_requests_coordinated = 0

    def coordinate_request(
        self, request: ApiIntegrationRequest
    ) -> ApiRequestContext:
        """Prepare and validate an immutable request context for gateway execution.

        Args:
            request: Immutable ApiIntegrationRequest instance.

        Returns:
            ApiRequestContext: Prepared request context model.

        Raises:
            RequestCoordinationException: If request metadata validation fails.
        """
        with self._lock:
            if not self.validate_request_metadata(request):
                raise RequestCoordinationException(
                    f"Invalid request metadata for request ID '{request.request_id}'."
                )

            context_id = f"rctx_{uuid.uuid4().hex[:8]}"
            context = ApiRequestContext(
                context_id=context_id,
                request=request,
                current_stage=PipelineStage.ROUTING,
                attributes={"coordinated_at": request.received_at.isoformat()},
            )
            self._total_requests_coordinated += 1
            logger.info("Coordinated request ID '%s' (context: %s).", request.request_id, context_id)
            return context

    def validate_request_metadata(self, request: ApiIntegrationRequest) -> bool:
        """Validate metadata completeness of an incoming request.

        Args:
            request: Target request model.

        Returns:
            bool: True if metadata is valid, else False.
        """
        with self._lock:
            if not request.request_id or not request.request_id.strip():
                return False
            if not request.path or not request.path.strip():
                return False
            if not request.method or not request.method.strip():
                return False
            return True

    def get_coordinator_telemetry(self) -> Dict[str, int]:
        """Get internal coordinator telemetry counters under lock."""
        with self._lock:
            return {
                "total_requests_coordinated": self._total_requests_coordinated,
            }
