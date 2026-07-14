"""Database Integration Tests for Auralis Memory Repositories."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import OperationalError, IntegrityError
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import JSONB

from memory.database import Base
from memory.database.config import db_config
from memory.models.domain_models import (
    UserDomain,
    PreferenceDomain,
    WorkspaceProfileDomain,
    ContextDomain,
    ConversationHistoryDomain,
    RoutineLearningDomain,
    ExecutionHistoryDomain,
    MemoryEventDomain,
)
from memory.repository.repository_factory import RepositoryFactory


@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(type_, compiler, **kw):
    """Compiles JSONB as JSON under SQLite to support test suites."""
    return "JSON"


@pytest.fixture(scope="module")
def db_engine():
    """Attempts to create a PostgreSQL connection. Falls back to in-memory SQLite if PostgreSQL is unavailable."""
    engine = None
    try:
        # Attempt to create PG engine and connect
        engine = create_engine(db_config.url, connect_args={"connect_timeout": 2})
        with engine.connect() as conn:
            pass
    except (OperationalError, Exception):
        # Fall back to SQLite in-memory
        engine = create_engine("sqlite:///:memory:")

    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(db_engine) -> Session:
    """Fixture providing a transaction-scoped database Session."""
    connection = db_engine.connect()
    transaction = connection.begin()
    session_local = sessionmaker(bind=connection)
    session = session_local()

    yield session

    session.close()
    if transaction.is_active:
        transaction.rollback()
    connection.close()


def test_independent_user_repository_crud(db_session: Session) -> None:
    """Verify independent CRUD operations for UserRepository."""
    factory = RepositoryFactory(db_session)
    repo = factory.get_user_repository()

    # 1. Create
    user = UserDomain(username="integration_user", email="integration@example.com")
    saved = repo.create(user)
    assert saved.id is not None
    assert saved.username == "integration_user"

    # 2. Read
    retrieved = repo.get_by_id(saved.id)
    assert retrieved is not None
    assert retrieved.email == "integration@example.com"

    # 3. Update
    saved.email = "new_integration@example.com"
    updated = repo.update(saved.id, saved)
    assert updated is not None
    assert updated.email == "new_integration@example.com"

    # 4. Search
    results = repo.search({"username": "integration_user"})
    assert len(results) == 1
    assert results[0].id == saved.id

    # 5. Delete
    deleted = repo.delete(saved.id)
    assert deleted is True
    assert repo.get_by_id(saved.id) is None


def test_preference_repository_crud(db_session: Session) -> None:
    """Verify CRUD on PreferenceRepository."""
    factory = RepositoryFactory(db_session)
    user_repo = factory.get_user_repository()
    pref_repo = factory.get_preference_repository()

    user = user_repo.create(UserDomain(username="pref_user"))

    # Create
    pref = PreferenceDomain(user_id=user.id, key="fontSize", value=14)
    saved = pref_repo.create(pref)
    assert saved.id is not None

    # Read / Search
    retrieved = pref_repo.get_by_user_and_key(user.id, "fontSize")
    assert retrieved is not None
    assert retrieved.value == 14

    # Update
    saved.value = 16
    updated = pref_repo.update(saved.id, saved)
    assert updated.value == 16

    # Delete
    assert pref_repo.delete(saved.id) is True


def test_workspace_repository_crud(db_session: Session) -> None:
    """Verify CRUD on WorkspaceRepository."""
    factory = RepositoryFactory(db_session)
    user_repo = factory.get_user_repository()
    work_repo = factory.get_workspace_repository()

    user = user_repo.create(UserDomain(username="work_user"))

    # Create
    profile = WorkspaceProfileDomain(user_id=user.id, name="default", path="/var/workspace", settings={"theme": "light"})
    saved = work_repo.create(profile)
    assert saved.id is not None

    # Read
    retrieved = work_repo.get_by_id(saved.id)
    assert retrieved.name == "default"
    assert retrieved.settings.get("theme") == "light"

    # Delete
    assert work_repo.delete(saved.id) is True


def test_context_repository_crud(db_session: Session) -> None:
    """Verify CRUD on ContextRepository."""
    factory = RepositoryFactory(db_session)
    user_repo = factory.get_user_repository()
    ctx_repo = factory.get_context_repository()

    user = user_repo.create(UserDomain(username="ctx_user"))

    # Create
    ctx = ContextDomain(user_id=user.id, session_id="sess_123", active_window="Browser", workspace_path="/path")
    saved = ctx_repo.create(ctx)
    assert saved.id is not None

    # Read
    retrieved = ctx_repo.get_by_id(saved.id)
    assert retrieved.session_id == "sess_123"

    # Delete
    assert ctx_repo.delete(saved.id) is True


def test_conversation_repository_crud(db_session: Session) -> None:
    """Verify CRUD on ConversationRepository."""
    factory = RepositoryFactory(db_session)
    user_repo = factory.get_user_repository()
    conv_repo = factory.get_conversation_repository()

    user = user_repo.create(UserDomain(username="conv_user"))

    # Create
    msg = ConversationHistoryDomain(user_id=user.id, session_id="chat_0", role="user", content="hello assistant")
    saved = conv_repo.create(msg)
    assert saved.id is not None

    # Read
    retrieved = conv_repo.get_by_id(saved.id)
    assert retrieved.content == "hello assistant"

    # Delete
    assert conv_repo.delete(saved.id) is True


def test_routine_repository_crud(db_session: Session) -> None:
    """Verify CRUD on RoutineRepository."""
    factory = RepositoryFactory(db_session)
    user_repo = factory.get_user_repository()
    routine_repo = factory.get_routine_repository()

    user = user_repo.create(UserDomain(username="routine_user"))

    # Create
    routine = RoutineLearningDomain(user_id=user.id, trigger_event="open_editor", action_sequence={"steps": ["a", "b"]})
    saved = routine_repo.create(routine)
    assert saved.id is not None

    # Read
    retrieved = routine_repo.get_by_id(saved.id)
    assert retrieved.trigger_event == "open_editor"

    # Delete
    assert routine_repo.delete(saved.id) is True


def test_execution_repository_crud(db_session: Session) -> None:
    """Verify CRUD on ExecutionRepository."""
    factory = RepositoryFactory(db_session)
    user_repo = factory.get_user_repository()
    exec_repo = factory.get_execution_repository()

    user = user_repo.create(UserDomain(username="exec_user"))

    # Create
    hist = ExecutionHistoryDomain(user_id=user.id, action="run_script", status="success", duration_ms=250)
    saved = exec_repo.create(hist)
    assert saved.id is not None

    # Read
    retrieved = exec_repo.get_by_id(saved.id)
    assert retrieved.action == "run_script"

    # Delete
    assert exec_repo.delete(saved.id) is True


def test_memory_event_repository_crud(db_session: Session) -> None:
    """Verify CRUD on MemoryEventRepository."""
    factory = RepositoryFactory(db_session)
    user_repo = factory.get_user_repository()
    event_repo = factory.get_memory_event_repository()

    user = user_repo.create(UserDomain(username="event_user"))

    # Create
    event = MemoryEventDomain(user_id=user.id, event_type="state_change", payload={"key": "val"})
    saved = event_repo.create(event)
    assert saved.id is not None

    # Read
    retrieved = event_repo.get_by_id(saved.id)
    assert retrieved.event_type == "state_change"

    # Delete
    assert event_repo.delete(saved.id) is True


def test_transaction_rollback_on_failed_operations(db_session: Session) -> None:
    """Verify that transactions successfully roll back when integrity or database constraints fail."""
    factory = RepositoryFactory(db_session)
    user_repo = factory.get_user_repository()

    # Create a user to set up a unique constraint test
    user = UserDomain(username="unique_username")
    user_repo.create(user)

    # Attempt to create another user with the duplicate username in a nested sub-transaction
    db_session.begin_nested()
    duplicate_user = UserDomain(username="unique_username")
    
    with pytest.raises(IntegrityError):
        # This will fail the database unique constraint on 'username'
        user_repo.create(duplicate_user)

    db_session.rollback()

    # Verify that the database session was rolled back successfully, and no changes persist
    assert user_repo.exists(username="unique_username") is False
    assert user_repo.count() == 0
