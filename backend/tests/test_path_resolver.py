"""Unit tests for PathResolver (Phase 9.5)."""

import os
import tempfile
from pathlib import Path

# pyrefly: ignore [missing-import]
import pytest

from brain.filesystem import PathResolver


@pytest.fixture
def tmp_dir(tmp_path: Path) -> str:
    return str(tmp_path)


@pytest.fixture
def resolver(tmp_dir: str) -> PathResolver:
    return PathResolver(base_path=tmp_dir)


# ---------------------------------------------------------------------------
# Basic Resolution
# ---------------------------------------------------------------------------

def test_resolve_absolute_path(resolver: PathResolver, tmp_dir: str) -> None:
    result = resolver.resolve(tmp_dir)
    assert os.path.isabs(result)


def test_resolve_relative_path(resolver: PathResolver, tmp_dir: str) -> None:
    result = resolver.resolve("subdir/file.txt")
    assert os.path.isabs(result)
    assert "subdir" in result


def test_resolve_tilde_expansion() -> None:
    r = PathResolver()
    result = r.resolve("~/test_file.txt")
    assert "~" not in result
    assert os.path.isabs(result)


def test_resolve_env_variable(resolver: PathResolver, tmp_dir: str) -> None:
    os.environ["_TEST_FSPATH"] = tmp_dir
    result = resolver.resolve("$_TEST_FSPATH/file.txt")
    del os.environ["_TEST_FSPATH"]
    assert tmp_dir in result


def test_resolve_double_dots_normalized(resolver: PathResolver, tmp_dir: str) -> None:
    """Resolved path should not contain traversal components."""
    result = resolver.resolve(tmp_dir + "/a/../b")
    assert ".." not in result


# ---------------------------------------------------------------------------
# Safety / Traversal Prevention
# ---------------------------------------------------------------------------

def test_is_safe_within_base(resolver: PathResolver, tmp_dir: str) -> None:
    assert resolver.is_safe(os.path.join(tmp_dir, "file.txt")) is True


def test_is_safe_escape_base(resolver: PathResolver, tmp_dir: str) -> None:
    parent = str(Path(tmp_dir).parent)
    assert resolver.is_safe(parent + "/evil.txt") is False


def test_is_safe_traversal_attempt(resolver: PathResolver, tmp_dir: str) -> None:
    malicious = tmp_dir + "/../../etc/passwd"
    assert resolver.is_safe(malicious) is False


def test_is_safe_with_explicit_base(resolver: PathResolver, tmp_dir: str) -> None:
    sub = os.path.join(tmp_dir, "sub")
    # path is inside tmp_dir but outside sub
    assert resolver.is_safe(tmp_dir + "/outside.txt", base=sub) is False


def test_is_safe_valid_subdir(resolver: PathResolver, tmp_dir: str) -> None:
    sub = os.path.join(tmp_dir, "sub", "file.txt")
    assert resolver.is_safe(sub) is True


# ---------------------------------------------------------------------------
# Canonicalize
# ---------------------------------------------------------------------------

def test_canonicalize_existing_path(tmp_path: Path) -> None:
    f = tmp_path / "real.txt"
    f.write_text("hi")
    r = PathResolver(str(tmp_path))
    canon = r.canonicalize(str(f))
    assert "real.txt" in canon


def test_canonicalize_nonexistent_returns_normalized(resolver: PathResolver, tmp_dir: str) -> None:
    result = resolver.canonicalize(tmp_dir + "/nonexistent.txt")
    assert isinstance(result, str)
    assert len(result) > 0


# ---------------------------------------------------------------------------
# Utility Methods
# ---------------------------------------------------------------------------

def test_normalize_path(resolver: PathResolver, tmp_dir: str) -> None:
    messy = tmp_dir + "/a//b/../c"
    result = resolver.normalize(messy)
    assert ".." not in result
    assert "//" not in result


def test_join_paths(resolver: PathResolver, tmp_dir: str) -> None:
    result = resolver.join(tmp_dir, "subdir", "file.txt")
    assert "subdir" in result
    assert "file.txt" in result


def test_parent_of_path(resolver: PathResolver, tmp_dir: str) -> None:
    result = resolver.parent(os.path.join(tmp_dir, "file.txt"))
    assert result == resolver.resolve(tmp_dir)


def test_name_extraction(resolver: PathResolver) -> None:
    assert resolver.name("/some/path/to/file.txt") == "file.txt"


def test_stem_extraction(resolver: PathResolver) -> None:
    assert resolver.stem("/some/path/to/file.txt") == "file"


def test_suffix_extraction(resolver: PathResolver) -> None:
    assert resolver.suffix("/some/path/to/file.txt") == ".txt"


def test_suffix_no_extension(resolver: PathResolver) -> None:
    assert resolver.suffix("/some/path/to/README") == ""


# ---------------------------------------------------------------------------
# Base Path Management
# ---------------------------------------------------------------------------

def test_get_base_path(resolver: PathResolver, tmp_dir: str) -> None:
    base = resolver.get_base_path()
    assert os.path.isabs(base)


def test_set_base_path(resolver: PathResolver, tmp_dir: str, tmp_path: Path) -> None:
    new_base = str(tmp_path / "new_base")
    resolver.set_base_path(new_base)
    assert resolver.get_base_path() == new_base or os.path.normpath(new_base) in resolver.get_base_path()


# ---------------------------------------------------------------------------
# Thread Safety
# ---------------------------------------------------------------------------

def test_resolver_thread_safety(resolver: PathResolver, tmp_dir: str) -> None:
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [
            executor.submit(resolver.resolve, os.path.join(tmp_dir, f"file{i}.txt"))
            for i in range(50)
        ]
        results = [f.result() for f in futures]
    assert len(results) == 50
    assert all(isinstance(r, str) for r in results)
