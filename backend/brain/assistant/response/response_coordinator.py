"""Response Coordinator implementation for Auralis (Phase 13.6).

Coordinates response preparation between AI, Dialogue, Decision, and Assistant Memory runtimes.
Collects metadata and synthesizes ResponseContext without executing LLM inference.
Thread-safe using threading.RLock().
"""

import logging
import threading
from typing import Any, Dict, List, Optional

from brain.assistant.response.exceptions import ResponseValidationError
from brain.assistant.response.interfaces import IResponseCoordinator
from brain.assistant.response.models import (
    ResponseContext,
    ResponseFormat,
    ResponseMetadata,
    StreamingMode,
)

logger = logging.getLogger(__name__)


class ResponseCoordinator(IResponseCoordinator):
    """Thread-safe coordinator synthesizing ResponseContext from registered subsystem runtimes."""

    def __init__(self, lock: Optional[threading.RLock] = None) -> None:
        self._lock = lock or threading.RLock()

    def prepare_response_context(
        self,
        request_id: str,
        user_prompt: str,
        ai_runtime: Optional[Any] = None,
        dialogue_runtime: Optional[Any] = None,
        decision_runtime: Optional[Any] = None,
        memory_runtime: Optional[Any] = None,
    ) -> ResponseContext:
        """Synthesize ResponseContext by collecting state and metadata from available runtimes."""
        if not request_id:
            raise ResponseValidationError("request_id cannot be empty")

        with self._lock:
            variables: Dict[str, Any] = {}
            citations: List[str] = []
            exec_summary: Dict[str, Any] = {}

            session_id: Optional[str] = None
            conversation_id: Optional[str] = None
            turn_id: Optional[str] = None

            # 1. Inspect Dialogue Runtime
            if dialogue_runtime is not None:
                try:
                    health = dialogue_runtime.get_health()
                    variables["dialogue_status"] = health.status
                except Exception as exc:
                    logger.debug("Failed to inspect dialogue_runtime in response_coordinator: %s", exc)

            # 2. Inspect Decision Runtime
            if decision_runtime is not None:
                try:
                    stats = decision_runtime.get_statistics()
                    exec_summary["requests_evaluated"] = stats.total_requests_evaluated
                    exec_summary["direct_executions"] = stats.direct_executions_routed
                except Exception as exc:
                    logger.debug("Failed to inspect decision_runtime in response_coordinator: %s", exc)

            # 3. Inspect Assistant Memory Runtime
            if memory_runtime is not None:
                try:
                    stats = memory_runtime.get_statistics()
                    variables["snapshots_generated"] = stats.total_snapshots_generated
                except Exception as exc:
                    logger.debug("Failed to inspect memory_runtime in response_coordinator: %s", exc)

            meta = ResponseMetadata(
                session_id=session_id,
                conversation_id=conversation_id,
                turn_id=turn_id,
                citations=citations,
                execution_summary=exec_summary,
                custom_attributes=variables,
            )

            context = ResponseContext(
                request_id=request_id,
                prompt=user_prompt,
                format_type=ResponseFormat.MARKDOWN,
                streaming_mode=StreamingMode.FULL_RESPONSE,
                variables=variables,
                metadata=meta,
            )

            logger.info("Prepared ResponseContext for req_id=%s (vars=%d)", request_id, len(variables))
            return context
