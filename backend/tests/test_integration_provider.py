"""Unit tests for IntegrationProvider (Phase 11.9)."""

# pyrefly: ignore [missing-import]
import pytest
from brain.os.integration import (
    ExecutionStatistics,
    ICapabilityRegistry,
    IExecutionPipeline,
    IOperationDispatcher,
    IRequestRouter,
    IntegrationHealth,
    IntegrationProvider,
    OperationRequest,
    OperationResponse,
    OperationTarget,
)


def test_integration_provider_execute_and_health() -> None:
    provider = IntegrationProvider()

    assert isinstance(provider.get_capability_registry(), ICapabilityRegistry)
    assert isinstance(provider.get_request_router(), IRequestRouter)
    assert isinstance(provider.get_dispatcher(), IOperationDispatcher)
    assert isinstance(provider.get_execution_pipeline(), IExecutionPipeline)

    req = OperationRequest(
        request_id="ip1",
        target=OperationTarget.FILESYSTEM,
        capability="filesystem.open",
    )

    resp = provider.execute(req)
    assert isinstance(resp, OperationResponse)
    assert resp.success is True

    health = provider.get_health()
    assert isinstance(health, IntegrationHealth)
    assert health.healthy is True

    stats = provider.get_statistics()
    assert isinstance(stats, ExecutionStatistics)
    assert stats.total_operations == 1
    assert stats.successful_operations == 1

    caps = provider.get_capabilities()
    assert isinstance(caps, list)
    assert len(caps) > 0

    diag = provider.get_diagnostics()
    assert isinstance(diag, dict)
    assert diag["provider_type"] == "IntegrationProvider"
