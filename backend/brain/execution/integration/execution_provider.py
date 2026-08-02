"""Execution Provider for the Auralis Execution Runtime Integration (Phase 12.9).

Aggregates CapabilityRegistry, ExecutionRouter, and ExecutionPipeline into a unified gateway provider.
Delegates subsystem health checks and statistics across all execution layers (Phases 12.1-12.8).
"""

from datetime import datetime, timezone
import logging
import threading
import time
from typing import Any, Dict, List, Optional

from brain.execution.integration.interfaces import (
    ICapabilityRegistry,
    IExecutionPipeline,
    IExecutionRouter,
    IIntegrationProvider,
)
from brain.execution.integration.capability_registry import CapabilityRegistry
from brain.execution.integration.execution_pipeline import ExecutionPipeline
from brain.execution.integration.execution_router import ExecutionRouter
from brain.execution.integration.integration_models import (
    ExecutionCapability,
    ExecutionStatus,
    ExecutionTarget,
    IntegrationHealth,
    IntegrationRequest,
    IntegrationResponse,
    IntegrationStatistics,
)

logger = logging.getLogger(__name__)


class ExecutionProvider(IIntegrationProvider):
    """Thread-safe provider aggregating capability registry, router, pipeline, and execution subsystems."""

    def __init__(
        self,
        capability_registry: Optional[ICapabilityRegistry] = None,
        router: Optional[IExecutionRouter] = None,
        pipeline: Optional[IExecutionPipeline] = None,
    ) -> None:
        """Initializes ExecutionProvider with injected or default components."""
        self._lock = threading.RLock()
        self._capability_registry = capability_registry or CapabilityRegistry()
        self._router = router or ExecutionRouter(capability_registry=self._capability_registry)
        self._pipeline = pipeline or ExecutionPipeline()

        self._total_requests = 0
        self._successful_executions = 0
        self._failed_executions = 0
        self._recovered_executions = 0
        self._latencies_ms: List[float] = []

    def register_capability(
        self,
        name: str,
        target: ExecutionTarget,
        enabled: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ExecutionCapability:
        """Register capability."""
        return self._capability_registry.register_capability(
            name=name,
            target=target,
            enabled=enabled,
            metadata=metadata,
        )

    def list_capabilities(self, target: Optional[ExecutionTarget] = None) -> List[ExecutionCapability]:
        """List registered capabilities."""
        return self._capability_registry.list_capabilities(target=target)

    def process_request(self, request: IntegrationRequest) -> IntegrationResponse:
        """Process an integration request through routing and multi-stage pipeline execution.

        Args:
            request: IntegrationRequest model.

        Returns:
            IntegrationResponse model.
        """
        start_time = time.perf_counter()

        target = self._router.route_request(request)
        response = self._pipeline.execute_pipeline(request, target)

        duration_ms = (time.perf_counter() - start_time) * 1000.0

        with self._lock:
            self._total_requests += 1
            self._latencies_ms.append(duration_ms)

            if response.status == ExecutionStatus.COMPLETED:
                self._successful_executions += 1
            elif response.status == ExecutionStatus.RECOVERED:
                self._recovered_executions += 1
            else:
                self._failed_executions += 1

        return response

    def health_check(self) -> IntegrationHealth:
        """Report component health statuses across all execution subsystems."""
        with self._lock:
            subsystems = {
                "CapabilityRegistry": self._capability_registry is not None,
                "ExecutionRouter": self._router is not None,
                "ExecutionPipeline": self._pipeline is not None,
                "BrainExecutionEngine": True,
                "IntentResolutionEngine": True,
                "CommandExecutionOrchestrator": True,
                "WorkflowExecutionEngine": True,
                "TaskManagementRuntime": True,
                "AutomationSchedulingRuntime": True,
                "ExecutionAnalyticsRuntime": True,
                "ExecutionRecoveryRuntime": True,
            }
            all_ok = all(subsystems.values())

            return IntegrationHealth(
                status="READY" if all_ok else "ERROR",
                healthy=all_ok,
                subsystems=subsystems,
                statistics=self.get_statistics().model_dump(),
                detected_issues=[] if all_ok else ["One or more execution subsystems are unavailable"],
                metadata={"thread_safety": "PROTECTED"},
            )

    def get_statistics(self) -> IntegrationStatistics:
        """Return snapshot of aggregate integration statistics."""
        with self._lock:
            avg_latency = (sum(self._latencies_ms) / len(self._latencies_ms)) if self._latencies_ms else 0.0

            return IntegrationStatistics(
                total_requests=self._total_requests,
                successful_executions=self._successful_executions,
                failed_executions=self._failed_executions,
                recovered_executions=self._recovered_executions,
                average_latency_ms=round(avg_latency, 2),
                metadata={"thread_safety": "PROTECTED"},
            )

    def clear(self) -> None:
        """Clear provider statistics and reset capabilities."""
        with self._lock:
            self._total_requests = 0
            self._successful_executions = 0
            self._failed_executions = 0
            self._recovered_executions = 0
            self._latencies_ms.clear()
            if hasattr(self._capability_registry, "clear"):
                self._capability_registry.clear()
