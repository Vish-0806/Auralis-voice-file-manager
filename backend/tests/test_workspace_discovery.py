"""Unit tests for the WorkspaceDiscoveryEngine."""

import os
import time
# pyrefly: ignore [missing-import]
import pytest
from datetime import datetime, timezone
from memory.workspace import (
    WorkspaceDiscoveryEngine,
    WorkspaceDiscoveryConfig,
    WorkspaceDiscoveryResult,
)


@pytest.mark.anyio
async def test_discover_git_and_build_markers(tmp_path) -> None:
    """Verify that the engine discovers git folders and package managers correctly."""
    # Setup directories
    proj_a = tmp_path / "proj_git"
    proj_a.mkdir()
    (proj_a / ".git").mkdir()

    proj_b = tmp_path / "proj_npm"
    proj_b.mkdir()
    (proj_b / "package.json").write_text("{}")

    proj_c = tmp_path / "proj_cargo"
    proj_c.mkdir()
    (proj_c / "Cargo.toml").write_text("")

    engine = WorkspaceDiscoveryEngine()
    results = await engine.discover(str(tmp_path))

    assert len(results) == 3
    paths = {r.workspace_path for r in results}
    assert str(proj_a) in paths
    assert str(proj_b) in paths
    assert str(proj_c) in paths

    # Verify confidence and naming
    git_res = next(r for r in results if r.workspace_path == str(proj_a))
    assert git_res.project_name == "proj_git"
    assert git_res.confidence == 1.0
    assert "Git" in git_res.detection_reason

    npm_res = next(r for r in results if r.workspace_path == str(proj_b))
    assert npm_res.project_name == "proj_npm"
    assert npm_res.confidence == 0.9
    assert "package.json" in npm_res.detection_reason


@pytest.mark.anyio
async def test_ignored_folders_are_skipped(tmp_path) -> None:
    """Verify that ignored directory names are skipped completely during search recursion."""
    # node_modules directory containing a git marker (should be skipped entirely)
    ignored_dir = tmp_path / "node_modules"
    ignored_dir.mkdir()
    (ignored_dir / ".git").mkdir()

    # Valid directory
    proj = tmp_path / "my_project"
    proj.mkdir()
    (proj / "Cargo.toml").write_text("")

    engine = WorkspaceDiscoveryEngine()
    results = await engine.discover(str(tmp_path))

    assert len(results) == 1
    assert results[0].workspace_path == str(proj)


@pytest.mark.anyio
async def test_recursion_depth_limits(tmp_path) -> None:
    """Verify recursion traversal depth enforcement."""
    # Create deeply nested project root at depth 3
    deep_path = tmp_path / "d1" / "d2" / "d3"
    deep_path.mkdir(parents=True)
    (deep_path / "package.json").write_text("{}")

    # Depth limit 2 (should not find the project)
    config_shallow = WorkspaceDiscoveryConfig(max_depth=2)
    engine_shallow = WorkspaceDiscoveryEngine(config=config_shallow)
    results_shallow = await engine_shallow.discover(str(tmp_path))
    assert len(results_shallow) == 0

    # Depth limit 4 (should find it)
    config_deep = WorkspaceDiscoveryConfig(max_depth=4)
    engine_deep = WorkspaceDiscoveryEngine(config=config_deep)
    results_deep = await engine_deep.discover(str(tmp_path))
    assert len(results_deep) == 1
    assert results_deep[0].workspace_path == str(deep_path)


@pytest.mark.anyio
async def test_duplicate_and_nested_suppression(tmp_path) -> None:
    """Verify that subdirectories of detected project roots are not scanned further."""
    parent_project = tmp_path / "parent_project"
    parent_project.mkdir()
    (parent_project / "package.json").write_text("{}")

    # Nested project within parent
    nested_git = parent_project / "nested_git"
    nested_git.mkdir()
    (nested_git / ".git").mkdir()

    engine = WorkspaceDiscoveryEngine()
    results = await engine.discover(str(tmp_path))

    # Should only find the parent project and terminate further scanning in its child directories
    assert len(results) == 1
    assert results[0].workspace_path == str(parent_project)


@pytest.mark.anyio
async def test_allowed_roots_validation(tmp_path) -> None:
    """Verify whitelist checks for allowed search root directories."""
    proj = tmp_path / "whitelisted_project"
    proj.mkdir()
    (proj / ".git").mkdir()

    # Allowed roots contains tmp_path
    config = WorkspaceDiscoveryConfig(allowed_roots=[str(tmp_path)])
    engine = WorkspaceDiscoveryEngine(config=config)
    results = await engine.discover(str(tmp_path))
    assert len(results) == 1

    # Allowed roots does not contain tmp_path
    config_blocked = WorkspaceDiscoveryConfig(allowed_roots=["/other/path/whitelist"])
    engine_blocked = WorkspaceDiscoveryEngine(config=config_blocked)
    results_blocked = await engine_blocked.discover(str(tmp_path))
    assert len(results_blocked) == 0


@pytest.mark.anyio
async def test_scan_timeout(tmp_path) -> None:
    """Verify discovery engine timeout interruption."""
    # Tiny timeout
    config = WorkspaceDiscoveryConfig(scan_timeout=0.0001)
    engine = WorkspaceDiscoveryEngine(config=config)

    proj = tmp_path / "timeout_project"
    proj.mkdir()
    (proj / ".git").mkdir()

    results = await engine.discover(str(tmp_path))
    # Should exit immediately and return no matches due to quick timeout
    assert len(results) == 0
