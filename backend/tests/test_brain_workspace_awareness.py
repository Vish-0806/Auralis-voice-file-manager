"""Unit and integration tests for BrainController workspace awareness."""

# pyrefly: ignore [missing-import]
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone
from memory import AssistantContext
from memory.workspace import WorkspaceAnalysis
from brain.controller.models import BrainRequest
from brain.controller.brain_controller import BrainController
from brain.controller.brain_pipeline import BrainPipeline


@pytest.fixture
def mock_analysis() -> WorkspaceAnalysis:
    """Fixture providing a mock WorkspaceAnalysis."""
    return WorkspaceAnalysis(
        workspace_path="/test/project",
        project_name="Auralis",
        project_type="python",
        repository_type="git",
        dominant_language="Python",
        language_statistics={"Python": 1.0},
        language_counts={"Python": 1},
        build_system="pip",
        recommended_build_command="pip install -r requirements.txt",
        git_branch="feature/memory",
        git_remote_available=True,
        git_dirty=False,
        git_has_unpushed_commits=False,
        total_files=1,
        total_directories=0,
        maximum_depth=1,
        total_size=100,
        last_indexed=datetime.now(timezone.utc),
        analysis_timestamp=datetime.now(timezone.utc),
    )


def test_brain_pipeline_summary_compilation(mock_analysis) -> None:
    """Verify that BrainPipeline compiles correct multi-line summary string format."""
    # Create fake pipeline configuration and deps
    pipeline = BrainPipeline(
        config=MagicMock(),
        interpreter=MagicMock(),
        reasoning_engine=MagicMock(),
        planner=MagicMock(),
        capability_selector=MagicMock(),
        execution_engine=MagicMock()
    )

    # 1. Summary present
    ctx_present = AssistantContext(workspace_analysis=mock_analysis)
    summary = pipeline.generate_workspace_summary(ctx_present)

    assert summary is not None
    assert "Workspace:" in summary
    assert "Project: Auralis" in summary
    assert "Project Type: python" in summary
    assert "Language: Python" in summary
    assert "Build: pip" in summary
    assert "Branch: feature/memory" in summary

    # 2. Summary absent
    ctx_absent = AssistantContext(workspace_analysis=None)
    assert pipeline.generate_workspace_summary(ctx_absent) is None


def test_brain_controller_workspace_attached_and_no_duplicate(mock_analysis) -> None:
    """Verify that when workspace_analysis is attached, the summary is returned and no duplicate scan occurs."""
    controller = BrainController()
    dispatcher = MagicMock()

    # Setup mocked context
    ctx = AssistantContext(workspace_analysis=mock_analysis)

    # Patch ContextBuilder and verify no Coordinator instantiations inside controller
    with patch("memory.manager.context_builder.ContextBuilder") as mock_builder_class, \
         patch("brain.controller.brain_pipeline.BrainPipeline.execute") as mock_execute, \
         patch("memory.workspace.workspace_coordinator.WorkspaceIntelligenceCoordinator") as mock_coord_class:

        mock_builder_instance = mock_builder_class.return_value
        async def mock_build_coro(*args, **kwargs):
            return ctx
        mock_builder_instance.build_context.side_effect = mock_build_coro

        # Mock execute return to populate summary
        summary = "Workspace:\nProject: Auralis\nLanguage: Python\nBuild: pip\nBranch: feature/memory"
        mock_execute.return_value = MagicMock(
            success=True,
            message="Pipeline completed successfully.",
            goal_name="START_CODING",
            workspace_summary=summary,
        )

        req = BrainRequest(
            message="start coding",
            correlation_id="test_workspace_run",
        )

        res = controller.process_request(req, dispatcher)

        # Assert summary is returned
        assert res.workspace_summary == summary
        assert "Project: Auralis" in res.workspace_summary

        # Assert no coordinator instantiation
        mock_coord_class.assert_not_called()



def test_brain_controller_workspace_absent() -> None:
    """Verify that when workspace_analysis is absent, no summary is attached."""
    controller = BrainController()
    dispatcher = MagicMock()

    ctx = AssistantContext(workspace_analysis=None)

    with patch("memory.manager.context_builder.ContextBuilder") as mock_builder_class, \
         patch("brain.controller.brain_pipeline.BrainPipeline.execute") as mock_execute:

        mock_builder_instance = mock_builder_class.return_value
        async def mock_build_coro(*args, **kwargs):
            return ctx
        mock_builder_instance.build_context.side_effect = mock_build_coro

        mock_execute.return_value = MagicMock(
            success=True,
            message="Pipeline completed successfully.",
            goal_name="START_CODING",
            workspace_summary=None,
        )

        req = BrainRequest(
            message="start coding",
            correlation_id="test_no_workspace_run",
        )

        res = controller.process_request(req, dispatcher)

        assert res.workspace_summary is None
