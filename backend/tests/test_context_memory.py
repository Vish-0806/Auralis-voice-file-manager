"""Unit tests for the User Context Memory subsystem."""

# pyrefly: ignore [missing-import]
import pytest
import time
# pyrefly: ignore [missing-import]
from sqlalchemy import create_engine
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import sessionmaker, Session
# pyrefly: ignore [missing-import]
from sqlalchemy.ext.compiler import compiles
# pyrefly: ignore [missing-import]
from sqlalchemy.dialects.postgresql import JSONB

from memory.database import Base
from memory.repository.context_repository import ContextRepository
from memory.context import (
    ContextService,
    ContextManager,
    ContextCache,
    ContextValidator,
    ContextExpiration,
    ContextType,
    InvalidContextError,
)


@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(type_, compiler, **kw):
    """Compiles JSONB as JSON under SQLite to support test suites."""
    return "JSON"


@pytest.fixture(scope="module")
def db_engine():
    """Provides a SQLite in-memory engine for context memory testing."""
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
def context_manager(db_session: Session) -> ContextManager:
    """Fixture providing a configured ContextManager."""
    repository = ContextRepository(db_session)
    cache = ContextCache()
    return ContextManager(repository=repository, cache=cache)


def test_validator_raises_on_invalid_inputs() -> None:
    """Verify that ContextValidator validates context types and structures correctly."""
    validator = ContextValidator()

    # Invalid Type Enum
    with pytest.raises(InvalidContextError) as exc:
        validator.validate("invalid_context_type", "value")
    assert "Invalid context type" in str(exc.value)

    # Invalid Type (recent_files expects list)
    with pytest.raises(InvalidContextError) as exc:
        validator.validate(ContextType.RECENT_FILES, "not_a_list")
    assert "must be a list" in str(exc.value)

    # Invalid Type (recent_files list items must be strings)
    with pytest.raises(InvalidContextError) as exc:
        validator.validate(ContextType.RECENT_FILES, ["file1.txt", 123])
    assert "must be strings" in str(exc.value)

    # Invalid Type (workspace path expects string)
    with pytest.raises(InvalidContextError) as exc:
        validator.validate(ContextType.ACTIVE_WORKSPACE, 100)
    assert "must be a string" in str(exc.value)


def test_context_cache_operations() -> None:
    """Verify cache sets, gets, invalidates, and clear logic."""
    cache = ContextCache()
    user_id = 1
    session_id = "sess_1"

    # Initially empty
    assert cache.get(user_id, session_id) is None

    # Set and Get
    cache.set(user_id, session_id, {"theme": {"value": "dark"}})
    assert cache.get(user_id, session_id) == {"theme": {"value": "dark"}}

    # Invalidate
    cache.invalidate(user_id, session_id)
    assert cache.get(user_id, session_id) is None

    # Clear user cache
    cache.set(user_id, "sess_1", {"k1": "v1"})
    cache.set(user_id, "sess_2", {"k2": "v2"})
    cache.clear(user_id)
    assert cache.get(user_id, "sess_1") is None
    assert cache.get(user_id, "sess_2") is None


def test_context_manager_crud(context_manager: ContextManager) -> None:
    """Verify context saving, loading, updating, and deletion flow."""
    user_id = 2
    session_id = "sess_crud"

    # Load empty context
    assert context_manager.load_context(user_id, session_id) == {}

    # Save context
    saved = context_manager.save_context(user_id, session_id, ContextType.CURRENT_PROJECT, "/path/to/project")
    assert saved.workspace_path == "/path/to/project"

    # Load and verify
    ctx = context_manager.load_context(user_id, session_id)
    assert ctx == {ContextType.CURRENT_PROJECT.value: "/path/to/project"}

    # Update context
    context_manager.save_context(user_id, session_id, ContextType.CURRENT_PROJECT, "/new/path")
    assert context_manager.load_context(user_id, session_id) == {ContextType.CURRENT_PROJECT.value: "/new/path"}

    # Delete specific type
    assert context_manager.delete_context(user_id, session_id, ContextType.CURRENT_PROJECT) is True
    assert context_manager.load_context(user_id, session_id) == {}

    # Re-save and delete entire context record
    context_manager.save_context(user_id, session_id, ContextType.CURRENT_PROJECT, "/path")
    assert context_manager.delete_context(user_id, session_id) is True
    assert context_manager.load_context(user_id, session_id) == {}


def test_temporary_context_expires(context_manager: ContextManager) -> None:
    """Verify that temporary context entries expire correctly according to TTL policies."""
    user_id = 3
    session_id = "sess_expiry"

    # Save temporary context with 1 second TTL
    context_manager.save_context(user_id, session_id, ContextType.TEMPORARY, "temp_data", ttl_seconds=1)

    # Active initially
    assert context_manager.load_context(user_id, session_id) == {ContextType.TEMPORARY.value: "temp_data"}

    # Wait for TTL to expire
    time.sleep(1.1)

    # Expired: Should be pruned automatically on load
    assert context_manager.load_context(user_id, session_id) == {}


def test_restore_context(context_manager: ContextManager) -> None:
    """Verify that restore fully overrides the user session context bag state."""
    user_id = 4
    session_id = "sess_restore"

    # Initial context state
    context_manager.save_context(user_id, session_id, ContextType.CURRENT_PROJECT, "/p1")

    # Restore context state override
    restored_bag = {
        ContextType.CLIPBOARD.value: "restored clipboard",
        ContextType.ACTIVE_WORKSPACE.value: "/p2",
    }
    saved = context_manager.restore_context(user_id, session_id, restored_bag)
    assert saved.workspace_path == "/p2"

    # Load and verify override
    active_ctx = context_manager.load_context(user_id, session_id)
    assert active_ctx == {
        ContextType.CLIPBOARD.value: "restored clipboard",
        ContextType.ACTIVE_WORKSPACE.value: "/p2",
    }


def test_context_service_delegates_successfully(db_session: Session) -> None:
    """Verify that ContextService public methods delegate to the manager correctly."""
    repository = ContextRepository(db_session)
    manager = ContextManager(repository)
    service = ContextService(manager)

    user_id = 5
    session_id = "sess_service"

    # Save
    saved = service.save(user_id, session_id, ContextType.CURRENT_PROJECT, "/path")
    assert saved.workspace_path == "/path"

    # Load
    assert service.load(user_id, session_id) == {ContextType.CURRENT_PROJECT.value: "/path"}

    # Delete specific type
    assert service.delete(user_id, session_id, ContextType.CURRENT_PROJECT) is True
    assert service.load(user_id, session_id) == {}
