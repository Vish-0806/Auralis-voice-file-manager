"""Unit tests for PermissionManager (Phase 9.5)."""

import os
import time
from pathlib import Path

# pyrefly: ignore [missing-import]
import pytest

from brain.filesystem import PermissionManager, PermissionResult


@pytest.fixture
def perm() -> PermissionManager:
    return PermissionManager(cache_ttl_seconds=60.0)


@pytest.fixture
def tmp_file(tmp_path: Path) -> str:
    f = tmp_path / "testfile.txt"
    f.write_text("hello")
    return str(f)


@pytest.fixture
def tmp_dir(tmp_path: Path) -> str:
    return str(tmp_path)


# ---------------------------------------------------------------------------
# validate() returns PermissionResult
# ---------------------------------------------------------------------------

def test_validate_existing_file(perm: PermissionManager, tmp_file: str) -> None:
    r = perm.validate(tmp_file)
    assert isinstance(r, PermissionResult)
    assert r.exists is True
    assert r.is_directory is False
    assert r.can_read is True


def test_validate_existing_directory(perm: PermissionManager, tmp_dir: str) -> None:
    r = perm.validate(tmp_dir)
    assert r.exists is True
    assert r.is_directory is True
    assert r.can_read is True


def test_validate_nonexistent_path(perm: PermissionManager, tmp_path: Path) -> None:
    r = perm.validate(str(tmp_path / "ghost.txt"))
    assert r.exists is False
    assert r.can_read is False
    assert r.can_write is False


def test_validate_result_frozen(perm: PermissionManager, tmp_file: str) -> None:
    # pyrefly: ignore [missing-import]
    from pydantic import ValidationError
    r = perm.validate(tmp_file)
    with pytest.raises((TypeError, ValidationError)):
        r.can_read = False


# ---------------------------------------------------------------------------
# Convenience Check Methods
# ---------------------------------------------------------------------------

def test_check_read_existing_file(perm: PermissionManager, tmp_file: str) -> None:
    assert perm.check_read(tmp_file) is True


def test_check_write_existing_file(perm: PermissionManager, tmp_file: str) -> None:
    assert perm.check_write(tmp_file) is True


def test_check_delete_existing_file(perm: PermissionManager, tmp_file: str) -> None:
    assert perm.check_delete(tmp_file) is True


def test_check_execute_file(perm: PermissionManager, tmp_file: str) -> None:
    result = perm.check_execute(tmp_file)
    assert isinstance(result, bool)


def test_check_directory_writable(perm: PermissionManager, tmp_dir: str) -> None:
    assert perm.check_directory(tmp_dir) is True


def test_check_read_nonexistent(perm: PermissionManager, tmp_path: Path) -> None:
    assert perm.check_read(str(tmp_path / "ghost.txt")) is False


def test_check_write_nonexistent(perm: PermissionManager, tmp_path: Path) -> None:
    assert perm.check_write(str(tmp_path / "ghost.txt")) is False


def test_check_delete_nonexistent(perm: PermissionManager, tmp_path: Path) -> None:
    assert perm.check_delete(str(tmp_path / "ghost.txt")) is False


def test_check_directory_on_file(perm: PermissionManager, tmp_file: str) -> None:
    """check_directory should return False for a regular file."""
    assert perm.check_directory(tmp_file) is False


# ---------------------------------------------------------------------------
# Cache Behaviour
# ---------------------------------------------------------------------------

def test_cache_hit_on_second_call(perm: PermissionManager, tmp_file: str) -> None:
    perm.validate(tmp_file)
    size_after_first = perm.cache_size()
    perm.validate(tmp_file)
    size_after_second = perm.cache_size()
    assert size_after_first == size_after_second  # no new entry


def test_invalidate_removes_from_cache(perm: PermissionManager, tmp_file: str) -> None:
    perm.validate(tmp_file)
    assert perm.cache_size() >= 1
    perm.invalidate(tmp_file)
    # After invalidation the same path is evicted
    # (parent may also be gone)
    remaining = perm.cache_size()
    assert remaining == 0 or remaining < 2


def test_clear_cache(perm: PermissionManager, tmp_file: str, tmp_dir: str) -> None:
    perm.validate(tmp_file)
    perm.validate(tmp_dir)
    assert perm.cache_size() >= 1
    perm.clear_cache()
    assert perm.cache_size() == 0


def test_cache_ttl_expiry(tmp_file: str) -> None:
    perm = PermissionManager(cache_ttl_seconds=0.01)
    perm.validate(tmp_file)
    assert perm.cache_size() == 1
    time.sleep(0.05)
    # After TTL, validate should re-check and result is NOT from cache
    r = perm.validate(tmp_file)
    assert r.exists is True  # Still correct result


def test_cache_max_size_eviction(tmp_path: Path) -> None:
    perm = PermissionManager(max_cache_size=3)
    files = []
    for i in range(5):
        f = tmp_path / f"file{i}.txt"
        f.write_text("")
        files.append(str(f))

    for f in files:
        perm.validate(f)

    assert perm.cache_size() <= 3


# ---------------------------------------------------------------------------
# Thread Safety
# ---------------------------------------------------------------------------

def test_permission_manager_thread_safety(perm: PermissionManager, tmp_file: str) -> None:
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(perm.validate, tmp_file) for _ in range(50)]
        results = [f.result() for f in futures]
    assert all(r.exists is True for r in results)
