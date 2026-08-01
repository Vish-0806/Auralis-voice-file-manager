"""Integration Provider implementation (Phase 11.9).

Aggregates CapabilityRegistry, RequestRouter, OperationDispatcher, and ExecutionPipeline
into a unified provider. Reports health tracking, statistics, capabilities, and diagnostics.
"""

from datetime import datetime, timezone
import time
from typing import Any, Dict, List, Optional

from brain.os.integration.capability_registry import CapabilityRegistry
from brain.os.integration.execution_pipeline import ExecutionPipeline
from brain.os.integration.integration_models import (
    CapabilityDescriptor,
    ExecutionStatistics,
    IntegrationHealth,
    OperationRequest,
    OperationResponse,
)
from brain.os.integration.interfaces import (
    ICapabilityRegistry,
    IExecutionPipeline,
    IIntegrationProvider,
    IOperationDispatcher,
    IRequestRouter,
)
from brain.os.integration.operation_dispatcher import OperationDispatcher
from brain.os.integration.request_router import RequestRouter


class IntegrationProvider(IIntegrationProvider):
    """Canonical integration subsystem provider."""

    def __init__(
        self,
        registry: Optional[ICapabilityRegistry] = None,
        router: Optional[IRequestRouter] = None,
        dispatcher: Optional[IOperationDispatcher] = None,
        pipeline: Optional[IExecutionPipeline] = None,
    ) -> None:
        self._registry = registry or CapabilityRegistry()
        self._router = router or RequestRouter(registry=self._registry)
        self._dispatcher = dispatcher or OperationDispatcher()
        self._pipeline = pipeline or ExecutionPipeline(
            router=self._router, dispatcher=self._dispatcher
        )

        self._created_at = datetime.now(timezone.utc)
        self._start_time = time.time()
        self._healthy = True

        self._total_ops = 0
        self._successful_ops = 0
        self._failed_ops = 0
        self._security_denied = 0
        self._total_duration_ms = 0.0

    def get_capability_registry(self) -> ICapabilityRegistry:
        """Return capability registry."""
        return self._registry

    def get_request_router(self) -> IRequestRouter:
        """Return request router."""
        return self._router

    def get_dispatcher(self) -> IOperationDispatcher:
        """Return operation dispatcher."""
        return self._dispatcher

    def get_execution_pipeline(self) -> IExecutionPipeline:
        """Return execution pipeline."""
        return self._pipeline

    def execute(self, request: OperationRequest) -> OperationResponse:
        """Execute OS operation request through execution pipeline."""
        response = self._pipeline.execute_pipeline(request)

        self._total_ops += 1
        self._total_duration_ms += response.summary.duration_ms

        if response.success:
            self._successful_ops += 1
        else:
            self._failed_ops += 1
            if any("Security Policy Denied" in err for err in response.summary.errors):
                self._security_denied += 1

        return response

    def get_health(self) -> IntegrationHealth:
        """Return provider health status."""
        uptime = max(0.0, time.time() - self._start_time)
        caps_count = len(self._registry.get_capabilities())

        return IntegrationHealth(
            healthy=self._healthy,
            status="READY" if self._healthy else "DEGRADED",
            capabilities_count=caps_count,
            total_dispatches=self._total_ops,
            uptime_seconds=uptime,
            details={"provider_type": "IntegrationProvider"},
        )

    def get_statistics(self) -> ExecutionStatistics:
        """Return execution statistics."""
        avg_dur = (
            (self._total_duration_ms / self._total_ops)
            if self._total_ops > 0
            else 0.0
        )
        return ExecutionStatistics(
            total_operations=self._total_ops,
            successful_operations=self._successful_ops,
            failed_operations=self._failed_ops,
            security_denied=self._security_denied,
            average_duration_ms=avg_dur,
        )

    def get_capabilities(self) -> List[CapabilityDescriptor]:
        """Return registered capability descriptors."""
        return self._registry.get_capabilities()

    def get_diagnostics(self) -> Dict[str, Any]:
        """Return diagnostic information."""
        health = self.get_health()
        stats = self.get_statistics()

        return {
            "provider_type": "IntegrationProvider",
            "healthy": health.healthy,
            "capabilities_registered": health.capabilities_count,
            "total_operations": stats.total_operations,
            "successful_operations": stats.successful_operations,
            "failed_operations": stats.failed_operations,
            "security_denied": stats.security_denied,
            "average_duration_ms": stats.average_duration_ms,
            "uptime_seconds": health.uptime_seconds,
            "created_at": self._created_at.isoformat(),
        }
