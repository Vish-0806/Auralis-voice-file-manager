"""Unit tests for PermissionManager (Phase 11.8)."""

# pyrefly: ignore [missing-import]
import pytest
from brain.os.security import (
    OperationCategory,
    PermissionLevel,
    PermissionManager,
    PermissionResult,
    SecurityContext,
    SecurityRequest,
)


def test_permission_manager_user_permission() -> None:
    pm = PermissionManager()
    req = SecurityRequest(
        request_id="r1",
        category=OperationCategory.FILESYSTEM,
        operation="read_file",
        target_resource="/docs/test.txt",
        requested_permission=PermissionLevel.READ,
        context=SecurityContext(is_admin=False),
    )

    res = pm.validate_permission(req)
    assert isinstance(res, PermissionResult)
    assert res.granted is True
    assert res.is_admin_required is False


def test_permission_manager_admin_required() -> None:
    pm = PermissionManager()
    req = SecurityRequest(
        request_id="r2",
        category=OperationCategory.FILESYSTEM,
        operation="delete_file",
        target_resource="C:\\Windows\\System32\\driver.sys",
        requested_permission=PermissionLevel.ADMIN,
        context=SecurityContext(is_admin=False),
    )

    res = pm.validate_permission(req)
    assert res.granted is False
    assert res.is_admin_required is True
