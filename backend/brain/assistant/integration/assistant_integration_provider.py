"""Assistant Integration Provider implementation for Auralis (Phase 13.9).

Aggregates RuntimeRegistry, PipelineCoordinator, AssistantCoordinator, and HealthAggregator into a unified provider.
Exposes health diagnostics, performance statistics, capabilities, and diagnostics using constructor dependency injection only.
Thread-safe using threading.RLock().
"""

from datetime import datetime, timezone
import logging
import threading
import time
from typing import Any, Dict, List, Optional

from brain.assistant.integration.assistant_coordinator import AssistantCoordinator
from brain.assistant.integration.health_aggregator import HealthAggregator
from brain.assistant.integration.interfaces import (
    IAssistantCoordinator,
    IAssistantIntegrationProvider,
    IHealthAggregator,
    IPipelineCoordinator,
    IRuntimeRegistry,
)
from brain.assistant.integration.models import (
    AssistantIntegrationCapabilities,
    AssistantIntegrationHealth,
    AssistantIntegrationRequest,
    AssistantIntegrationResponse,
    AssistantIntegrationStatistics,
)
from brain.assistant.integration.pipeline_coordinator import PipelineCoordinator
from brain.assistant.integration.runtime_registry import RuntimeRegistry

logger = logging.getLogger(__name__)


class AssistantIntegrationProvider(IAssistantIntegrationProvider):
    """Aggregating provider for top-level assistant integration gateway operations."""

    def __init__(
        self,
        registry: Optional[IRuntimeRegistry] = None,
        pipeline_coordinator: Optional[IPipelineCoordinator] = None,
        assistant_coordinator: Optional[IAssistantCoordinator] = None,
        health_aggregator: Optional[IHealthAggregator] = None,
    ) -> None:
        """Initializes AssistantIntegrationProvider using constructor dependency injection only."""
        self._lock = threading.RLock()
        self._registry = registry or RuntimeRegistry(lock=self._lock)
        self._pipeline_coordinator = pipeline_coordinator or PipelineCoordinator(lock=self._lock)
        self._assistant_coordinator = assistant_coordinator or AssistantCoordinator(lock=self._lock)
        self._health_aggregator = health_aggregator or HealthAggregator(lock=self._lock)

        self._initialized = False
        self._start_time: Optional[float] = None

        # Statistics
        self._total_requests = 0
        self._successful_requests = 0
        self._failed_requests = 0
        self._pipeline_executions = 0
        self._total_latency_ms = 0.0

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def registry(self) -> IRuntimeRegistry:
        with self._lock:
            return self._registry

    @property
    def pipeline_coordinator(self) -> IPipelineCoordinator:
        with self._lock:
            return self._pipeline_coordinator

    @property
    def assistant_coordinator(self) -> IAssistantCoordinator:
        with self._lock:
            return self._assistant_coordinator

    @property
    def health_aggregator(self) -> IHealthAggregator:
        with self._lock:
            return self._health_aggregator

    @property
    def is_initialized(self) -> bool:
        with self._lock:
            return self._initialized

    # ------------------------------------------------------------------
    # Gateway Operations
    # ------------------------------------------------------------------

    def handle_request(self, request: AssistantIntegrationRequest) -> AssistantIntegrationResponse:
        """Process an integration request through the coordinator and pipeline."""
        t0 = time.time()
        res = self._assistant_coordinator.handle_request(
            request=request,
            registry=self._registry,
            pipeline_coordinator=self._pipeline_coordinator,
        )
        latency = (time.time() - t0) * 1000.0

        with self._lock:
            self._total_requests += 1
            self._pipeline_executions += 1
            self._total_latency_ms += latency

            if res.status.name == "SUCCESS":
                self._successful_requests += 1
            else:
                self._failed_requests += 1

        return res

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def initialize(self) -> None:
        """Initialize provider resources and register available sub-runtimes."""
        with self._lock:
            if self._initialized:
                return

            self._register_default_runtimes_locked()
            self._initialized = True
            self._start_time = time.time()
            logger.info("AssistantIntegrationProvider initialized successfully")

    def shutdown(self) -> None:
        """Gracefully shut down provider resources."""
        with self._lock:
            if not self._initialized:
                return

            self._initialized = False
            self._start_time = None
            logger.info("AssistantIntegrationProvider shutdown complete")

    def clear(self) -> None:
        """Reset sub-managers and performance metrics."""
        with self._lock:
            if hasattr(self._registry, "clear"):
                self._registry.clear()  # type: ignore[union-attr]
            if hasattr(self._assistant_coordinator, "clear"):
                self._assistant_coordinator.clear()  # type: ignore[union-attr]

            self._total_requests = 0
            self._successful_requests = 0
            self._failed_requests = 0
            self._pipeline_executions = 0
            self._total_latency_ms = 0.0

    # ------------------------------------------------------------------
    # Capabilities, Health & Statistics
    # ------------------------------------------------------------------

    def get_capabilities(self) -> AssistantIntegrationCapabilities:
        """Expose aggregated integration capabilities specification."""
        with self._lock:
            snapshots = self._registry.list_snapshots()
            names = [s.runtime_name for s in snapshots if s.is_available]

            return AssistantIntegrationCapabilities(
                supports_full_pipeline=True,
                supports_voice=True,
                supports_proactive=True,
                supports_multi_mode=True,
                available_runtimes=names,
                max_concurrent_requests=100,
            )

    def get_health(self) -> AssistantIntegrationHealth:
        """Expose unified health report across all registered runtimes."""
        return self._health_aggregator.aggregate_health(self._registry)

    def get_statistics(self) -> AssistantIntegrationStatistics:
        """Expose aggregated performance statistics metrics."""
        with self._lock:
            avg_latency = (self._total_latency_ms / self._total_requests) if self._total_requests > 0 else 0.0

            snapshots = self._registry.list_snapshots()

            uptime = 0.0
            if self._start_time is not None and self._initialized:
                uptime = max(0.0, time.time() - self._start_time)

            return AssistantIntegrationStatistics(
                total_requests_handled=self._total_requests,
                successful_requests=self._successful_requests,
                failed_requests=self._failed_requests,
                pipeline_executions=self._pipeline_executions,
                average_pipeline_latency_ms=avg_latency,
                registered_runtimes_count=len(snapshots),
                uptime_seconds=uptime,
                metadata={},
            )

    # ------------------------------------------------------------------
    # Internal Helpers
    # ------------------------------------------------------------------

    def _register_default_runtimes_locked(self) -> None:
        """Safely discover and register available Phase 13 and system runtimes."""
        runtimes_to_register = [
            ("assistant_runtime", "brain.assistant", "get_assistant_runtime"),
            ("conversation_runtime", "brain.assistant.conversation", "get_conversation_runtime"),
            ("dialogue_runtime", "brain.assistant.dialogue", "get_dialogue_runtime"),
            ("decision_runtime", "brain.assistant.reasoning", "get_decision_runtime"),
            ("memory_runtime", "brain.assistant.memory", "get_assistant_memory_runtime"),
            ("response_runtime", "brain.assistant.response", "get_response_runtime"),
            ("voice_runtime", "brain.assistant.voice", "get_voice_runtime"),
            ("proactive_runtime", "brain.assistant.proactive", "get_proactive_runtime"),
        ]

        import importlib
        for name, mod_path, getter_name in runtimes_to_register:
            try:
                mod = importlib.import_module(mod_path)
                getter = getattr(mod, getter_name, None)
                if getter and callable(getter):
                    inst = getter()
                    self._registry.register_runtime(name, inst, version="1.0.0", capabilities=["core"])
            except Exception as exc:
                logger.debug("Optional sub-runtime %s not auto-registered: %s", name, exc)
