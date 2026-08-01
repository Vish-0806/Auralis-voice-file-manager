"""Unit tests for SecurityProvider (Phase 11.8)."""

# pyrefly: ignore [missing-import]
import pytest
from brain.os.security import (
    IAuditLogger,
    IConfirmationManager,
    IPermissionManager,
    IPolicyEngine,
    IRiskAnalyzer,
    OperationCategory,
    SecurityCapabilities,
    SecurityDecision,
    SecurityDecisionType,
    SecurityHealth,
    SecurityProvider,
    SecurityRequest,
    SecurityStatistics,
)


def test_security_provider_evaluate_request() -> None:
    provider = SecurityProvider()
    req = SecurityRequest(
        request_id="sp1",
        category=OperationCategory.FILESYSTEM,
        operation="read_file",
        target_resource="/data/test.json",
    )

    dec = provider.evaluate_request(req)
    assert isinstance(dec, SecurityDecision)
    assert dec.decision_type == SecurityDecisionType.ALLOW

    health = provider.get_health()
    assert isinstance(health, SecurityHealth)
    assert health.healthy is True

    stats = provider.get_statistics()
    assert isinstance(stats, SecurityStatistics)
    assert stats.total_requests_evaluated == 1
    assert stats.allowed_requests == 1

    caps = provider.get_capabilities()
    assert isinstance(caps, SecurityCapabilities)

    diag = provider.get_diagnostics()
    assert isinstance(diag, dict)
    assert diag["provider_type"] == "SecurityProvider"
