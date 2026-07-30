"""Assistant Runtime for the Auralis Brain Runtime (Phase 9.7).

Central assistant engine integrating registry, lifecycle, health, statistics, and integration pipeline.
"""

from datetime import datetime, timezone
import logging
import threading
import uuid
from typing import Any, Dict, List, Optional, Union

from brain.runtime.brain_models import (
    BrainRequest,
    BrainResponse,
    BrainRuntimeHealth,
    BrainRuntimeStatistics,
    PipelineStatus,
    RuntimeComponent,
)
from brain.runtime.dependency_registry import DependencyRegistry
from brain.runtime.health_monitor import HealthMonitor
from brain.runtime.integration_pipeline import IntegrationPipeline
from brain.runtime.lifecycle_manager import LifecycleManager
from brain.runtime.statistics_manager import StatisticsManager

logger = logging.getLogger(__name__)


class AssistantRuntime:
    """Thread-safe core assistant runtime orchestrating all Auralis Brain services.

    Responsibilities:
    - Manage subsystem dependency injection via DependencyRegistry.
    - Manage startup/shutdown lifecycle via LifecycleManager.
    - Monitor aggregated health via HealthMonitor.
    - Monitor aggregated statistics via StatisticsManager.
    - Execute end-to-end request pipeline via IntegrationPipeline.
    """

    def __init__(
        self,
        registry: Optional[DependencyRegistry] = None,
        lifecycle_manager: Optional[LifecycleManager] = None,
        health_monitor: Optional[HealthMonitor] = None,
        statistics_manager: Optional[StatisticsManager] = None,
        pipeline: Optional[IntegrationPipeline] = None,
    ) -> None:
        self._lock = threading.RLock()
        self._registry = registry or DependencyRegistry()
        self._lifecycle = lifecycle_manager or LifecycleManager(self._registry)
        self._health = health_monitor or HealthMonitor(self._registry)
        self._stats = statistics_manager or StatisticsManager(self._registry)
        self._pipeline = pipeline or IntegrationPipeline(self._registry)

        self._initialized = False
        self._is_shutdown = False
        self._runtime_id = f"ast-rt-{uuid.uuid4().hex[:6]}"
        logger.debug("AssistantRuntime constructed runtime_id=%s", self._runtime_id)

    # ------------------------------------------------------------------
    # Lifecycle Management
    # ------------------------------------------------------------------

    def initialize(self) -> bool:
        """Initialize all registered subsystem runtimes in startup order.

        Returns:
            True if all subsystems initialized cleanly, False otherwise.
        """
        with self._lock:
            try:
                self._is_shutdown = False
                ok = self._lifecycle.initialize_all()
                self._initialized = ok
                logger.info("Brain Initialized: runtime_id=%s success=%s", self._runtime_id, ok)
                return ok
            except Exception as exc:
                self._initialized = False
                logger.error("AssistantRuntime.initialize exception: %s", exc)
                return False

    def shutdown(self) -> bool:
        """Shutdown all registered subsystem runtimes in LIFO order.

        Returns:
            True always (graceful shutdown).
        """
        with self._lock:
            try:
                ok = self._lifecycle.shutdown_all()
                self._is_shutdown = True
                self._initialized = False
                logger.info("Brain Shutdown: runtime_id=%s", self._runtime_id)
                return ok
            except Exception as exc:
                self._is_shutdown = True
                self._initialized = False
                logger.error("AssistantRuntime.shutdown exception: %s", exc)
                return False

    def restart(self) -> bool:
        """Restart all subsystem runtimes.

        Returns:
            True if re-initialization succeeded.
        """
        with self._lock:
            logger.info("Brain Restarting: runtime_id=%s", self._runtime_id)
            return self._lifecycle.restart_all()

    def clear(self) -> None:
        """Clear all subsystem and brain runtime state/statistics."""
        with self._lock:
            self._stats.clear()
            self._lifecycle.clear_all()
            self._initialized = False
            self._is_shutdown = False
            logger.debug("AssistantRuntime cleared")

    # ------------------------------------------------------------------
    # Request Processing
    # ------------------------------------------------------------------

    def process_request(self, request: Union[BrainRequest, str]) -> BrainResponse:
        """Process an incoming user request through the full Brain pipeline.

        Args:
            request: :class:`BrainRequest` or raw user prompt string.

        Returns:
            Immutable :class:`BrainResponse`.
        """
        with self._lock:
            if not self._initialized and not self._is_shutdown:
                self.initialize()

        if isinstance(request, str):
            req_obj = BrainRequest(
                request_id=f"req-{uuid.uuid4().hex[:8]}",
                raw_text=request,
                session_id=f"sess-{uuid.uuid4().hex[:6]}",
            )
        else:
            req_obj = request

        self._stats.record_request_start()
        pipe_res = self._pipeline.execute(req_obj)
        self._stats.record_request_complete(pipe_res.pipeline_ms, success=pipe_res.success)

        text = self._build_response_text(req_obj, pipe_res)

        return BrainResponse(
            request_id=req_obj.request_id,
            session_id=req_obj.session_id,
            conversation_id=req_obj.conversation_id,
            success=pipe_res.success,
            text=text,
            voice_response=pipe_res.voice_result,
            execution_summary=pipe_res.execution_result,
            pipeline_status=pipe_res.status,
            duration_ms=pipe_res.pipeline_ms,
            error=pipe_res.error,
            timestamp=datetime.now(timezone.utc),
        )

    # ------------------------------------------------------------------
    # Health & Statistics
    # ------------------------------------------------------------------

    def health_check(self) -> BrainRuntimeHealth:
        """Query aggregated health across all subsystems.

        Returns:
            Immutable :class:`BrainRuntimeHealth` snapshot.
        """
        return self._health.check_health()

    def get_statistics(self) -> BrainRuntimeStatistics:
        """Query aggregated statistics across all subsystems.

        Returns:
            Immutable :class:`BrainRuntimeStatistics` snapshot.
        """
        return self._stats.get_statistics()

    def list_components(self) -> List[str]:
        """List all currently registered subsystem component names.

        Returns:
            List of component names.
        """
        return self._registry.list_components()

    # ------------------------------------------------------------------
    # Property Accessors
    # ------------------------------------------------------------------

    @property
    def is_initialized(self) -> bool:
        with self._lock:
            return self._initialized

    @property
    def registry(self) -> DependencyRegistry:
        return self._registry

    # ------------------------------------------------------------------
    # Internal Helpers
    # ------------------------------------------------------------------

    def _build_response_text(self, req: BrainRequest, res: Any) -> str:
        if not res.success:
            return f"Error processing request: {res.error}"
        if res.voice_result and isinstance(res.voice_result, dict):
            feedback = res.voice_result.get("feedback")
            if isinstance(feedback, dict) and feedback.get("text"):
                return feedback["text"]
        return f"Completed: {req.raw_text}"
