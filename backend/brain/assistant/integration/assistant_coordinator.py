"""Assistant Coordinator implementation for Auralis (Phase 13.9).

Coordinates all Assistant runtimes, merges execution summaries, synchronizes lifecycle state,
and synthesizes unified AssistantIntegrationResponse models without performing LLM inference.
Thread-safe using threading.RLock().
"""

from datetime import datetime, timezone
import logging
import threading
import time
from typing import Optional

from brain.assistant.integration.exceptions import AssistantValidationException
from brain.assistant.integration.interfaces import (
    IAssistantCoordinator,
    IPipelineCoordinator,
    IRuntimeRegistry,
)
from brain.assistant.integration.models import (
    AssistantIntegrationRequest,
    AssistantIntegrationResponse,
    IntegrationStage,
    IntegrationStatus,
)

logger = logging.getLogger(__name__)


class AssistantCoordinator(IAssistantCoordinator):
    """Thread-safe coordinator managing top-level request execution across all sub-runtimes."""

    def __init__(self, lock: Optional[threading.RLock] = None) -> None:
        self._lock = lock or threading.RLock()
        self._request_count = 0

    @property
    def request_count(self) -> int:
        with self._lock:
            return self._request_count

    def handle_request(
        self,
        request: AssistantIntegrationRequest,
        registry: IRuntimeRegistry,
        pipeline_coordinator: IPipelineCoordinator,
    ) -> AssistantIntegrationResponse:
        """Handle integration request and synthesize unified AssistantIntegrationResponse."""
        if not isinstance(request, AssistantIntegrationRequest):
            raise AssistantValidationException("request must be an instance of AssistantIntegrationRequest")

        t0 = time.time()

        with self._lock:
            self._request_count += 1

            # 1. Execute pipeline stages
            summaries = pipeline_coordinator.execute_pipeline(request, registry)

            # 2. Check response_runtime for content generation if registered
            response_rt = registry.get_runtime("response_runtime")
            reply_text = f"Processed prompt: '{request.user_prompt}'" if request.user_prompt else "Assistant ready."
            formatted_text = f"**Assistant Response**\n\n{reply_text}"

            if response_rt is not None and hasattr(response_rt, "get_provider"):
                try:
                    provider = response_rt.get_provider()
                    if provider and hasattr(provider, "build_response"):
                        built_resp = provider.build_response(
                            request_id=request.request_id,
                            content=reply_text,
                        )
                        formatted_text = built_resp.formatted_content
                except Exception as exc:
                    logger.debug("Error invoking response_runtime in AssistantCoordinator: %s", exc)

            latency_ms = (time.time() - t0) * 1000.0

            response = AssistantIntegrationResponse(
                request_id=request.request_id,
                status=IntegrationStatus.SUCCESS,
                assistant_reply=reply_text,
                formatted_reply=formatted_text,
                current_stage=IntegrationStage.COMPLETED,
                execution_summaries=summaries,
                total_latency_ms=latency_ms,
                timestamp=datetime.now(timezone.utc),
            )

            logger.info("Handled AssistantIntegrationRequest id=%s status=%s latency=%.2fms", request.request_id, response.status, latency_ms)
            return response

    def clear(self) -> None:
        """Reset request counter."""
        with self._lock:
            self._request_count = 0
