"""Unit tests for CapabilityRegistry (Phase 11.9)."""

# pyrefly: ignore [missing-import]
import pytest
from brain.os.integration import (
    CapabilityDescriptor,
    CapabilityRegistry,
    OperationTarget,
)


def test_capability_registry_defaults_and_lookup() -> None:
    reg = CapabilityRegistry()

    caps = reg.get_capabilities()
    assert isinstance(caps, list)
    assert len(caps) > 0

    cap_fs = reg.lookup("filesystem.open")
    assert cap_fs is not None
    assert cap_fs.target == OperationTarget.FILESYSTEM

    cats = reg.list_categories()
    assert len(cats) > 0
    assert OperationTarget.FILESYSTEM in cats


def test_capability_registry_register_and_unregister() -> None:
    reg = CapabilityRegistry()
    desc = CapabilityDescriptor(
        capability_name="custom.test",
        target=OperationTarget.SYSTEM,
        description="Custom Test Capability",
    )

    reg.register(desc)
    assert reg.lookup("custom.test") is not None

    unregistered = reg.unregister("custom.test")
    assert unregistered is True
    assert reg.lookup("custom.test") is None
