"""Unit tests for PermissionService (Phase 11.2)."""

import os
import pytest

from brain.os.filesystem import PermissionInfo, PermissionService
from brain.os.filesystem.exceptions import FileNotFoundError, PathSafetyError


def test_permission_service_check(tmp_path) -> None:
    test_file = tmp_path / "test.txt"
    test_file.write_text("hello")

    svc = PermissionService()
    info = svc.check_permissions(str(test_file))

    assert isinstance(info, PermissionInfo)
    assert info.can_read is True
    assert info.can_write is True
    assert info.can_delete is True
    assert len(info.owner) > 0


def test_permission_service_methods(tmp_path) -> None:
    test_file = tmp_path / "sample.txt"
    test_file.write_text("data")

    svc = PermissionService()

    assert svc.can_read(str(test_file)) is True
    assert svc.can_write(str(test_file)) is True
    assert svc.can_delete(str(test_file)) is True


def test_permission_service_file_not_found() -> None:
    svc = PermissionService()
    with pytest.raises(FileNotFoundError):
        svc.check_permissions("/non_existent_file_path_12345.txt")
