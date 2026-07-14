"""Unit tests for the Workspace Profiles subsystem."""

from unittest.mock import MagicMock
# pyrefly: ignore [missing-import]
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import JSONB

from memory.database import Base
from memory.repository.workspace_repository import WorkspaceRepository
from memory.workspace import (
    WorkspaceService,
    WorkspaceManager,
    WorkspaceValidator,
    WorkspaceLauncher,
    WorkspaceSnapshot,
    InvalidWorkspaceError,
    WorkspaceError,
    WorkspaceNotFoundError,
)


@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(type_, compiler, **kw):
    """Compiles JSONB as JSON under SQLite to support test suites."""
    return "JSON"


@pytest.fixture(scope="module")
def db_engine():
    """Provides a SQLite in-memory engine for workspace profiles testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(db_engine) -> Session:
    """Provides a transactional database Session."""
    connection = db_engine.connect()
    transaction = connection.begin()
    session_local = sessionmaker(bind=connection)
    session = session_local()

    yield session

    session.close()
    if transaction.is_active:
        transaction.rollback()
    connection.close()


@pytest.fixture
def mock_desktop_capability():
    """Fixture providing a mock DesktopCapability."""
    cap = MagicMock()
    # Mock LIST_WINDOWS success
    cap.execute.return_value = {
        "success": True,
        "data": {
            "windows": [
                {"title": "Visual Studio Code", "owner": "VS Code"},
                {"title": "Windows Terminal", "owner": "Terminal"},
            ]
        },
    }
    return cap


@pytest.fixture
def workspace_service(db_session: Session, mock_desktop_capability) -> WorkspaceService:
    """Fixture providing a configured WorkspaceService with a mock DesktopCapability."""
    repository = WorkspaceRepository(db_session)
    manager = WorkspaceManager(repository)
    launcher = WorkspaceLauncher(mock_desktop_capability)
    return WorkspaceService(
        manager=manager,
        launcher=launcher,
        desktop_capability=mock_desktop_capability,
    )


def test_workspace_validator_catches_invalid_formats() -> None:
    """Verify WorkspaceValidator catches incorrect settings layouts."""
    validator = WorkspaceValidator()

    # Invalid applications (not list)
    with pytest.raises(InvalidWorkspaceError) as exc:
        validator.validate_settings({"applications": "VS Code"})
    assert "must be a list" in str(exc.value)

    # Invalid applications entry (missing name)
    with pytest.raises(InvalidWorkspaceError) as exc:
        validator.validate_settings({"applications": [{"args": []}]})
    assert "containing a 'name' string key" in str(exc.value)

    # Invalid projects
    with pytest.raises(InvalidWorkspaceError) as exc:
        validator.validate_settings({"projects": [123]})
    assert "must be a string" in str(exc.value)


def test_template_retrieval(workspace_service: WorkspaceService) -> None:
    """Verify built-in template loading."""
    tmpl = workspace_service.get_template("coding")
    assert tmpl["path"] == "/projects/code"
    assert "applications" in tmpl["settings"]

    with pytest.raises(WorkspaceNotFoundError):
        workspace_service.get_template("nonexistent_template_999")


def test_workspace_crud_operations(workspace_service: WorkspaceService) -> None:
    """Verify workspace profiles creation, read, update, list, duplication and delete flows."""
    user_id = 10
    settings = {
        "applications": [{"name": "VS Code", "args": []}],
        "projects": ["/projects/my_code"],
        "browser_tabs": [],
        "terminal_config": {},
        "env_vars": {},
        "startup_order": ["applications"],
    }

    # 1. Create Profile
    saved = workspace_service.create(user_id, "Coding Mode", "/projects/my_code", settings)
    assert saved.id is not None
    assert saved.name == "Coding Mode"

    # Duplicates check
    with pytest.raises(WorkspaceError):
        workspace_service.create(user_id, "Coding Mode", "/path", settings)

    # 2. Get Profile
    retrieved = workspace_service.get(user_id, saved.id)
    assert retrieved.name == "Coding Mode"
    assert retrieved.path == "/projects/my_code"

    # Get by name
    by_name = workspace_service.get_by_name(user_id, "Coding Mode")
    assert by_name.id == saved.id

    # 3. Update Profile
    settings_updated = dict(settings)
    settings_updated["env_vars"] = {"DEBUG": "true"}
    updated = workspace_service.update(user_id, saved.id, "/new/path", settings_updated)
    assert updated.path == "/new/path"
    assert updated.settings["env_vars"]["DEBUG"] == "true"

    # 4. Duplicate Profile
    dup = workspace_service.duplicate(user_id, saved.id, "Coding Mode Copied")
    assert dup.name == "Coding Mode Copied"
    assert dup.path == "/new/path"

    # 5. List Profiles
    all_profiles = workspace_service.list(user_id)
    assert len(all_profiles) == 2

    # 6. Delete Profiles
    assert workspace_service.delete(user_id, saved.id) is True
    assert workspace_service.delete(user_id, dup.id) is True
    assert len(workspace_service.list(user_id)) == 0


def test_launcher_executes_via_capability(workspace_service: WorkspaceService, mock_desktop_capability) -> None:
    """Verify that launching a profile routes commands to the injected DesktopCapability."""
    user_id = 11
    settings = {
        "applications": [{"name": "VS Code", "args": []}, {"name": "Terminal", "args": []}],
        "projects": [],
        "browser_tabs": ["https://github.com"],
        "env_vars": {"LAUNCH_TEST_VAR": "true"},
        "startup_order": ["applications", "browser_tabs"],
    }

    profile = workspace_service.create(user_id, "test_launch", "/launch_path", settings)

    # Execute restore
    success = workspace_service.restore(user_id, profile.id)
    assert success is True

    # Assert DesktopCapability.execute was called for apps and tabs
    assert mock_desktop_capability.execute.call_count >= 3
    mock_desktop_capability.execute.assert_any_call(
        "OPEN_APPLICATION",
        {"target": "VS Code", "arguments": []},
    )
    mock_desktop_capability.execute.assert_any_call(
        "OPEN_APPLICATION",
        {"target": "Terminal", "arguments": []},
    )
    mock_desktop_capability.execute.assert_any_call(
        "OPEN_APPLICATION",
        {"target": "Microsoft Edge", "arguments": ["https://github.com"]},
    )

    # Assert environment variable was set
    import os
    assert os.environ.get("LAUNCH_TEST_VAR") == "true"


def test_workspace_snapshot(workspace_service: WorkspaceService, mock_desktop_capability) -> None:
    """Verify capturing context active path and window titles generates a profile snapshot."""
    user_id = 12
    session_id = "sess_snap"

    # Mock context service loader
    mock_context_service = MagicMock()
    mock_context_service.load.return_value = {
        "active_workspace": "/active/path/on/disk",
    }

    # Execute snapshot save
    saved = workspace_service.snapshot(user_id, session_id, "My Snapshot Profile", mock_context_service)

    assert saved.name == "My Snapshot Profile"
    assert saved.path == "/active/path/on/disk"
    # Verify open windows were captured
    apps = saved.settings["applications"]
    assert len(apps) == 2
    assert apps[0]["name"] == "VS Code"
    assert apps[1]["name"] == "Terminal"
