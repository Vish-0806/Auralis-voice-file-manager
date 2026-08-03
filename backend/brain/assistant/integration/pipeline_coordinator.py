"""Pipeline Coordinator implementation for Auralis (Phase 13.9).

Coordinates stage execution ordering across the complete assistant pipeline:
Conversation -> Dialogue -> Decision -> Memory -> Execution -> Response -> Voice -> Proactive.
Tracks pipeline stages and collects execution summaries without executing core AI logic.
Thread-safe using threading.RLock().
"""

from datetime import datetime, timezone
import logging
import threading
import time
from typing import List, Optional

from brain.assistant.integration.interfaces import IPipelineCoordinator, IRuntimeRegistry
from brain.assistant.integration.models import (
    AssistantExecutionSummary,
    AssistantIntegrationRequest,
    IntegrationStage,
)

logger = logging.getLogger(__name__)

_PIPELINE_STAGES = [
    (IntegrationStage.CONVERSATION, "conversation_runtime"),
    (IntegrationStage.DIALOGUE, "dialogue_runtime"),
    (IntegrationStage.DECISION, "decision_runtime"),
    (IntegrationStage.MEMORY, "memory_runtime"),
    (IntegrationStage.EXECUTION, "execution_runtime"),
    (IntegrationStage.RESPONSE, "response_runtime"),
    (IntegrationStage.VOICE, "voice_runtime"),
    (IntegrationStage.PROACTIVE, "proactive_runtime"),
]


class PipelineCoordinator(IPipelineCoordinator):
    """Thread-safe pipeline coordinator executing stage sequencing and collecting stage summaries."""

    def __init__(self, lock: Optional[threading.RLock] = None) -> None:
        self._lock = lock or threading.RLock()

    def execute_pipeline(
        self,
        request: AssistantIntegrationRequest,
        registry: IRuntimeRegistry,
    ) -> List[AssistantExecutionSummary]:
        """Execute the assistant pipeline and collect stage execution summaries."""
        with self._lock:
            summaries: List[AssistantExecutionSummary] = []

            for stage, runtime_name in _PIPELINE_STAGES:
                t0 = time.time()
                is_avail = registry.is_available(runtime_name)
                rt_inst = registry.get_runtime(runtime_name)

                stage_data = {
                    "runtime_name": runtime_name,
                    "available": is_avail,
                    "request_id": request.request_id,
                }

                if is_avail and rt_inst is not None:
                    if hasattr(rt_inst, "get_health"):
                        try:
                            h = rt_inst.get_health()
                            stage_data["status"] = getattr(h, "status", "READY")
                        except Exception as exc:
                            logger.debug("Failed health check for stage %s: %s", stage, exc)

                duration_ms = (time.time() - t0) * 1000.0

                summary = AssistantExecutionSummary(
                    stage=stage,
                    duration_ms=duration_ms,
                    success=is_avail or (rt_inst is None),
                    summary_data=stage_data,
                    timestamp=datetime.now(timezone.utc),
                )
                summaries.append(summary)

                logger.debug("Pipeline stage %s completed in %.2fms (success=%s)", stage, duration_ms, summary.success)

            return summaries
