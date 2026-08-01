"""Unit tests for RequestRouter (Phase 11.9)."""

# pyrefly: ignore [missing-import]
import pytest
from brain.os.integration import (
    CapabilityNotFoundError,
    CapabilityDescriptor,
    OperationRequest,
    OperationTarget,
    OperationValidationError,
    RequestRouter,
)


def test_request_router_route_success() -> None:
    router = RequestRouter()
    req = OperationRequest(
        request_id="r1",
        target=OperationTarget.FILESYSTEM,
        capability="filesystem.open",
    )

    desc = router.route(req)
    assert isinstance(desc, CapabilityDescriptor)
    assert desc.capability_name == "filesystem.open"

    valid = router.validate_request(req)
    assert valid is True


def test_request_router_route_unregistered() -> None:
    router = RequestRouter()
    req = OperationRequest(
        request_id="r2",
        target=OperationTarget.SYSTEM,
        capability="unregistered.fake.capability",
    )

    with pytest.raises(CapabilityNotFoundError):
        router.route(req)
