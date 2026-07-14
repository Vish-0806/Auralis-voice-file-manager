"""Unit tests for the Memory Coordinator Platform."""

from unittest.mock import MagicMock
# pyrefly: ignore [missing-import]
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import JSONB

from memory.database import Base
from memory.repository.preference_repository import PreferenceRepository
from memory.repository.context_repository import ContextRepository
from memory.repository.workspace_repository import WorkspaceRepository
from memory.repository.routine_repository import RoutineRepository
from memory.repository.execution_repository import ExecutionRepository

from memory.preferences.preference_service import PreferenceService
from memory.context.context_service import ContextService
from memory.workspace.workspace_service import WorkspaceService
from memory.learning.routine_learning_service import RoutineLearningService

from memory import MemoryCoordinator
from memory.coordinator.memory_registry import MemoryRegistry
from memory.coordinator.memory_pipeline import MemoryPipeline
from memory.coordinator.memory_health import MemoryHealth


@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(type_, compiler, **kw):
    """Compiles JSONB as JSON under SQLite to support test suites."""
    return "JSON"


@pytest.fixture(scope="module")
def db_engine():
    """Provides a SQLite in-memory engine for coordinator platform testing."""
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
def memory_coordinator(db_session: Session) -> MemoryCoordinator:
    """Fixture providing an integrated MemoryCoordinator with custom repository database mappings."""
    pref_service = PreferenceService()
    pref_service._engine._repository = PreferenceRepository(db_session)

    ctx_service = ContextService()
    ctx_service._manager._repository = ContextRepository(db_session)

    ws_service = WorkspaceService()
    ws_service._manager._repository = WorkspaceRepository(db_session)

    lr_service = RoutineLearningService()
    lr_service._engine._routine_repository = RoutineRepository(db_session)
    lr_service._engine._execution_repository = ExecutionRepository(db_session)

    return MemoryCoordinator(
        preference_service=pref_service,
        context_service=ctx_service,
        workspace_service=ws_service,
        routine_service=lr_service,
        health_session_factory=lambda: db_session,
    )


def test_registry_registrations(memory_coordinator: MemoryCoordinator) -> None:
    """Verify that MemoryRegistry lists and registers services dynamically."""
    services = MemoryRegistry.list_services()
    assert "preferences" in services
    assert "context" in services
    assert "workspace" in services
    assert "learning" in services
    assert "personalization" in services

    # Register future plugin mock service
    mock_plugin = MagicMock()
    MemoryRegistry.register("email_service", mock_plugin)
    assert MemoryRegistry.get("email_service") == mock_plugin


def test_coordinator_delegates_successfully(memory_coordinator: MemoryCoordinator) -> None:
    """Verify delegation configurations across memory types."""
    user_id = 30
    session_id = "sess_coord"

    # 1. Preference
    memory_coordinator.set_preference(user_id, "ide", "theme", "dark")
    assert memory_coordinator.get_preference(user_id, "ide")["theme"] == "dark"

    # 2. Context
    saved_ctx = memory_coordinator.save_context(user_id, session_id, "current_project", "/home/proj")
    assert saved_ctx.workspace_path == "/home/proj"
    assert memory_coordinator.load_context(user_id, session_id) == {"current_project": "/home/proj"}

    # 3. Workspace
    settings = {
        "applications": [{"name": "Terminal", "args": []}],
        "projects": [],
        "browser_tabs": [],
        "terminal_config": {},
        "env_vars": {},
        "startup_order": ["applications"],
    }
    ws = memory_coordinator.create_workspace(user_id, "Coding", "/path", settings)
    assert ws.name == "Coding"
    assert len(memory_coordinator.list_workspaces(user_id)) == 1

    # 4. Learning
    ex = memory_coordinator.record_execution(user_id, "OPEN_APPLICATION", {"target": "Terminal"}, "success")
    assert ex.action == "OPEN_APPLICATION"
    assert len(memory_coordinator.list_routines(user_id)) == 0


def test_pipeline_personalization(memory_coordinator: MemoryCoordinator) -> None:
    """Verify pipeline executes and returns unified settings context overrides."""
    user_id = 31
    session_id = "sess_pipe"

    # Set up some database configurations
    memory_coordinator.set_preference(user_id, "ide", "theme", "dark")
    memory_coordinator.save_context(user_id, session_id, "current_project", "/my/editor/project")

    # Run pipeline
    ctx = memory_coordinator.run_pipeline(user_id, session_id)
    assert ctx.resolved_settings["theme"] == "dark"
    assert ctx.resolved_settings["workspace_path"] == "/my/editor/project"
    assert ctx.source_mapping["theme"] == "User Preferences"
    assert ctx.source_mapping["workspace_path"] == "Current Context"

    # Run pipeline with overrides
    ctx_overriden = memory_coordinator.run_pipeline(user_id, session_id, user_overrides={"theme": "purple"})
    assert ctx_overriden.resolved_settings["theme"] == "purple"
    assert ctx_overriden.source_mapping["theme"] == "Explicit User Command"


def test_diagnostics_health_checks(memory_coordinator: MemoryCoordinator) -> None:
    """Verify health and metrics checkpoints diagnostics reports."""
    user_id = 32
    session_id = "sess_health"

    # Health Check
    health = memory_coordinator.check_health()
    assert health["status"] == "healthy"
    assert health["database"] == "healthy"
    assert health["cache"] == "healthy"

    # Setup some dummy counts
    memory_coordinator.set_preference(user_id, "ide", "theme", "light")
    memory_coordinator.create_workspace(
        user_id,
        "presentation",
        "/path",
        {
            "applications": [],
            "projects": [],
            "browser_tabs": [],
            "terminal_config": {},
            "env_vars": {},
            "startup_order": [],
        },
    )

    # Metrics
    metrics = memory_coordinator.get_metrics(user_id)
    assert metrics["preferences_count"] >= 1
    assert metrics["workspace_profiles_count"] == 1
