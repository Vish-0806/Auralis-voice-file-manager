"""Unit tests for the unified WorkspaceAnalysis domain model."""

import json
from datetime import datetime, timezone
# pyrefly: ignore [missing-import]
from pydantic import ValidationError
from memory.workspace import WorkspaceAnalysis


def test_field_population_and_helpers() -> None:
    """Verify that all WorkspaceAnalysis fields are instantiated and helpers return correct classifications."""
    now = datetime.now(timezone.utc)
    analysis = WorkspaceAnalysis(
        workspace_path="/my/workspace/root",
        project_name="root",
        project_type="python",
        repository_type="git",
        dominant_language="Python",
        language_statistics={"Python": 0.8, "Markdown": 0.2},
        language_counts={"Python": 3, "Markdown": 1},
        build_system="pip",
        recommended_build_command="pip install -r requirements.txt",
        git_branch="feature/analysis",
        git_remote_available=True,
        git_dirty=True,
        git_has_unpushed_commits=True,
        total_files=4,
        total_directories=2,
        maximum_depth=2,
        total_size=1024,
        last_indexed=now,
        analysis_timestamp=now,
    )

    # Assert basic fields
    assert analysis.workspace_path == "/my/workspace/root"
    assert analysis.project_name == "root"
    assert analysis.total_size == 1024

    # Assert helper categorizations
    assert analysis.is_git_repository() is True
    assert analysis.is_python_project() is True
    assert analysis.is_node_project() is False
    assert analysis.is_java_project() is False


def test_workspace_analysis_summary_generation() -> None:
    """Verify formatting of the summary() output string."""
    now = datetime.now(timezone.utc)
    analysis = WorkspaceAnalysis(
        workspace_path="/test/path",
        project_name="path",
        project_type="node",
        repository_type="none",
        dominant_language="JavaScript",
        language_statistics={"JavaScript": 1.0},
        language_counts={"JavaScript": 2},
        build_system="npm",
        recommended_build_command="npm run build",
        git_branch=None,
        git_remote_available=False,
        git_dirty=False,
        git_has_unpushed_commits=False,
        total_files=2,
        total_directories=0,
        maximum_depth=1,
        total_size=500,
        last_indexed=now,
        analysis_timestamp=now,
    )

    summary = analysis.summary()
    assert "/test/path" in summary
    assert "NODE" in summary
    assert "Dominant Language: JavaScript" in summary
    assert "Build System: npm" in summary
    assert "Git: N/A" in summary
    assert "Size: 500 bytes" in summary


def test_serialization_and_json_parsing() -> None:
    """Verify model dumps to dict and loads back correctly via JSON serialization."""
    now = datetime.now(timezone.utc)
    analysis = WorkspaceAnalysis(
        workspace_path="/serialize/path",
        project_name="path",
        project_type="rust",
        repository_type="git",
        dominant_language="Rust",
        language_statistics={"Rust": 1.0},
        language_counts={"Rust": 5},
        build_system="cargo",
        recommended_build_command="cargo build",
        git_branch="main",
        git_remote_available=True,
        git_dirty=False,
        git_has_unpushed_commits=False,
        total_files=5,
        total_directories=1,
        maximum_depth=2,
        total_size=900,
        last_indexed=now,
        analysis_timestamp=now,
    )

    # Dump model to JSON string
    json_str = analysis.model_dump_json()
    assert "/serialize/path" in json_str

    # Parse back from JSON dict
    parsed_dict = json.loads(json_str)
    reconstructed = WorkspaceAnalysis.model_validate(parsed_dict)
    assert reconstructed.workspace_path == "/serialize/path"
    assert reconstructed.dominant_language == "Rust"
    assert reconstructed.is_git_repository() is True
    # Verify timestamp parse alignment
    assert abs((reconstructed.analysis_timestamp - now).total_seconds()) < 1.0


def test_backward_compatibility_defaults() -> None:
    """Verify default values map properly to support legacy configurations."""
    now = datetime.now(timezone.utc)
    analysis = WorkspaceAnalysis(
        workspace_path="/compat/path",
        project_name="path",
        project_type="none",
        repository_type="none",
        dominant_language="Other",
        language_statistics={},
        language_counts={},
        total_files=0,
        total_directories=0,
        maximum_depth=0,
        total_size=0,
        last_indexed=now,
        analysis_timestamp=now,
    )

    # Defaults check
    assert analysis.git_remote_available is False
    assert analysis.git_dirty is False
    assert analysis.git_has_unpushed_commits is False
    assert analysis.build_system is None
    assert analysis.recommended_build_command is None
    assert analysis.git_branch is None
