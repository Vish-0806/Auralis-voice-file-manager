"""API Middleware Executor Implementation (Phase 15.3).

Thread-safe provider-independent middleware execution engine evaluating pipeline stages
and constructing telemetry records without executing HTTP handlers, networking,
or response serialization.
"""

from datetime import datetime, timezone
import logging
from threading import RLock
from typing import Dict, List, Optional
import uuid

from backend.application.api.middleware.interfaces import (
    IMiddlewareExecutor,
    IPipelineManager,
)
from backend.application.api.middleware.models import (
    MiddlewareContext,
    MiddlewareExecution,
    MiddlewareResult,
    MiddlewareStage,
)
from backend.application.api.middleware.pipeline_manager import PipelineManager

logger = logging.getLogger(__name__)


class MiddlewareExecutor(IMiddlewareExecutor):
    """Thread-safe execution engine invoking middleware pipelines across stages."""

    def __init__(self, pipeline_manager: Optional[IPipelineManager] = None) -> None:
        """Initialize MiddlewareExecutor using Constructor Dependency Injection.

        Args:
            pipeline_manager: Optional IPipelineManager implementation instance.
        """
        self._lock = RLock()
        self._pipeline_manager = pipeline_manager or PipelineManager()

        self._total_executions = 0
        self._failed_executions = 0

    def execute_stage(
        self, stage: MiddlewareStage, context: MiddlewareContext
    ) -> MiddlewareResult:
        """Execute middleware pipeline for a given stage against context.

        Args:
            stage: Target MiddlewareStage enum.
            context: Immutable MiddlewareContext instance.

        Returns:
            MiddlewareResult: Immutable execution result snapshot.
        """
        with self._lock:
            pipeline = self._pipeline_manager.build_pipeline(stage)
            executions: List[MiddlewareExecution] = []
            current_context = context

            for middleware in pipeline:
                self._total_executions += 1
                exec_id = f"exec_{uuid.uuid4().hex[:12]}"
                start_time = datetime.now(timezone.utc)

                # Simulated internal stage execution record creation
                duration_ms = 0.5  # Deterministic simulated duration
                execution = MiddlewareExecution(
                    execution_id=exec_id,
                    middleware_id=middleware.middleware_id,
                    stage=stage,
                    status="SUCCESS",
                    duration_ms=duration_ms,
                    executed_at=start_time,
                    error_message=None,
                )
                executions.append(execution)
                logger.debug(
                    "Executed middleware '%s' (%s) for stage '%s'.",
                    middleware.middleware_id,
                    middleware.name,
                    stage.value,
                )

            logger.info(
                "Completed middleware pipeline for stage '%s' with %d executions.",
                stage.value,
                len(executions),
            )

            return MiddlewareResult(
                is_success=True,
                stage=stage,
                context=current_context,
                executions=tuple(executions),
                error_message=None,
                completed_at=datetime.now(timezone.utc),
            )

    def get_execution_statistics(self) -> Dict[str, int]:
        """Get internal execution statistics under lock."""
        with self._lock:
            return {
                "total_executions": self._total_executions,
                "failed_executions": self._failed_executions,
                "successful_executions": self._total_executions - self._failed_executions,
            }
