"""Unit tests for the ProjectIntelligenceEngine and its sub-detectors."""

from unittest.mock import MagicMock, patch
# pyrefly: ignore [missing-import]
import pytest
from datetime import datetime, timezone
from memory.workspace import (
    WorkspaceIndex,
    WorkspaceFileEntry,
    ProjectIntelligenceEngine,
    ProjectDetector,
    LanguageDetector,
    BuildSystemDetector,
    GitWorkspaceAnalyzer,
    WorkspaceAnalysis,
)


@pytest.fixture
def base_index() -> WorkspaceIndex:
    """Fixture providing a baseline WorkspaceIndex."""
    return WorkspaceIndex(
        workspace_path="/test/workspace",
        directories=[],
        files={},
        directory_count=0,
        file_count=0,
        total_size=0,
        maximum_depth=0,
        indexed_at=datetime.now(timezone.utc),
    )


def test_project_detector_categorization(base_index) -> None:
    """Verify that ProjectDetector classifies project types correctly based on files."""
    detector = ProjectDetector()

    # 1. Node check
    index_node = base_index.model_copy()
    index_node.files = {
        "package.json": WorkspaceFileEntry(
            relative_path="package.json",
            absolute_path="/test/workspace/package.json",
            filename="package.json",
            extension=".json",
            size=10,
            modified_time=datetime.now(timezone.utc),
            is_hidden=False,
            is_directory=False,
        )
    }
    assert detector.detect_project_type(index_node) == "node"

    # 2. Rust check
    index_rust = base_index.model_copy()
    index_rust.files = {
        "Cargo.toml": WorkspaceFileEntry(
            relative_path="Cargo.toml",
            absolute_path="/test/workspace/Cargo.toml",
            filename="Cargo.toml",
            extension=".toml",
            size=10,
            modified_time=datetime.now(timezone.utc),
            is_hidden=False,
            is_directory=False,
        )
    }
    assert detector.detect_project_type(index_rust) == "rust"

    # 3. Python check
    index_py = base_index.model_copy()
    index_py.files = {
        "requirements.txt": WorkspaceFileEntry(
            relative_path="requirements.txt",
            absolute_path="/test/workspace/requirements.txt",
            filename="requirements.txt",
            extension=".txt",
            size=10,
            modified_time=datetime.now(timezone.utc),
            is_hidden=False,
            is_directory=False,
        )
    }
    assert detector.detect_project_type(index_py) == "python"


def test_language_detector_weighting(base_index) -> None:
    """Verify LanguageDetector calculates dominant language and percentages based on size."""
    detector = LanguageDetector()

    index = base_index.model_copy()
    index.files = {
        "main.py": WorkspaceFileEntry(
            relative_path="main.py",
            absolute_path="/test/workspace/main.py",
            filename="main.py",
            extension=".py",
            size=80,  # 80% Python
            modified_time=datetime.now(timezone.utc),
            is_hidden=False,
            is_directory=False,
        ),
        "README.md": WorkspaceFileEntry(
            relative_path="README.md",
            absolute_path="/test/workspace/README.md",
            filename="README.md",
            extension=".md",
            size=20,  # 20% Markdown
            modified_time=datetime.now(timezone.utc),
            is_hidden=False,
            is_directory=False,
        ),
    }

    dominant, stats, counts = detector.analyze_languages(index)
    assert dominant == "Python"
    assert stats["Python"] == 0.8000
    assert stats["Markdown"] == 0.2000
    assert counts["Python"] == 1
    assert counts["Markdown"] == 1


def test_build_system_detector_commands(base_index) -> None:
    """Verify BuildSystemDetector matches tools and maps correct commands."""
    detector = BuildSystemDetector()

    # Cargo check
    index_cargo = base_index.model_copy()
    index_cargo.files = {
        "Cargo.toml": WorkspaceFileEntry(
            relative_path="Cargo.toml",
            absolute_path="/test/workspace/Cargo.toml",
            filename="Cargo.toml",
            extension=".toml",
            size=10,
            modified_time=datetime.now(timezone.utc),
            is_hidden=False,
            is_directory=False,
        )
    }
    build_cargo = detector.detect_build_system(index_cargo)
    assert build_cargo.build_system == "cargo"
    assert build_cargo.recommended_build_command == "cargo build"

    # PNPM check
    index_pnpm = base_index.model_copy()
    index_pnpm.files = {
        "package.json": WorkspaceFileEntry(
            relative_path="package.json",
            absolute_path="/test/workspace/package.json",
            filename="package.json",
            extension=".json",
            size=10,
            modified_time=datetime.now(timezone.utc),
            is_hidden=False,
            is_directory=False,
        ),
        "pnpm-lock.yaml": WorkspaceFileEntry(
            relative_path="pnpm-lock.yaml",
            absolute_path="/test/workspace/pnpm-lock.yaml",
            filename="pnpm-lock.yaml",
            extension=".yaml",
            size=10,
            modified_time=datetime.now(timezone.utc),
            is_hidden=False,
            is_directory=False,
        ),
    }
    build_pnpm = detector.detect_build_system(index_pnpm)
    assert build_pnpm.build_system == "pnpm"
    assert build_pnpm.recommended_build_command == "pnpm build"


def test_git_workspace_analyzer_mocked() -> None:
    """Verify GitWorkspaceAnalyzer queries git branch properties and handles clean/dirty states."""
    analyzer = GitWorkspaceAnalyzer()

    # Mock subprocess.run
    with patch("subprocess.run") as mock_run, patch("os.path.isdir") as mock_isdir:
        mock_isdir.return_value = True

        # Mock git commands sequentially: branch, remote, status, rev-list
        mock_branch = MagicMock()
        mock_branch.stdout = "main"
        mock_branch.returncode = 0

        mock_remote = MagicMock()
        mock_remote.stdout = "origin"
        mock_remote.returncode = 0

        mock_status = MagicMock()
        mock_status.stdout = " M file.py\n"
        mock_status.returncode = 0

        mock_revlist = MagicMock()
        mock_revlist.stdout = "2"
        mock_revlist.returncode = 0

        mock_run.side_effect = [mock_branch, mock_remote, mock_status, mock_revlist]

        summary = analyzer.analyze_git("/test/workspace")
        assert summary is not None
        assert summary.branch == "main"
        assert summary.remote_available is True
        assert summary.is_dirty is True
        assert summary.unpushed_commits == 2


@pytest.mark.anyio
async def test_project_intelligence_coordination(base_index) -> None:
    """Verify ProjectIntelligenceEngine correctly coordinates and populates WorkspaceAnalysis."""
    engine = ProjectIntelligenceEngine()

    index = base_index.model_copy()
    index.files = {
        "Cargo.toml": WorkspaceFileEntry(
            relative_path="Cargo.toml",
            absolute_path="/test/workspace/Cargo.toml",
            filename="Cargo.toml",
            extension=".toml",
            size=50,
            modified_time=datetime.now(timezone.utc),
            is_hidden=False,
            is_directory=False,
        ),
        "main.rs": WorkspaceFileEntry(
            relative_path="main.rs",
            absolute_path="/test/workspace/main.rs",
            filename="main.rs",
            extension=".rs",
            size=250,
            modified_time=datetime.now(timezone.utc),
            is_hidden=False,
            is_directory=False,
        ),
    }

    # Mock Git to verify GitSummary populates correctly
    with patch("os.path.isdir") as mock_isdir, patch.object(
        engine.git_analyzer, "analyze_git"
    ) as mock_analyze:
        mock_isdir.return_value = True
        mock_analyze.return_value = None

        analysis = await engine.analyze(index)

        assert isinstance(analysis, WorkspaceAnalysis)
        assert analysis.workspace_path == "/test/workspace"
        assert analysis.project_name == "workspace"
        assert analysis.project_type == "rust"
        assert analysis.dominant_language == "Rust"
        assert analysis.build_system == "cargo"
        assert analysis.recommended_build_command == "cargo build"
        assert analysis.git_branch is None
        assert analysis.repository_type == "none"
