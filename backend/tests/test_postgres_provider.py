"""Unit tests for the Auralis PostgreSQL Provider implementation."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import JSONB

from memory.database import Base
from memory.models.domain_models import MemoryEntry, MemoryMetadata, MemoryQuery, MemoryType
from memory.providers.postgres_provider import PostgresProvider
from memory.exceptions import DataIntegrityError, DatabaseConnectionError, DatabaseOperationError


@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(type_, compiler, **kw):
    """Compiles JSONB as JSON under SQLite to support test suites."""
    return "JSON"


@pytest.fixture
def mock_db_session(monkeypatch):
    """Fixture providing a transactional SQLite in-memory database session, patching SessionLocal."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session_local = sessionmaker(bind=engine)

    # Patch SessionLocal inside postgres_provider and session
    monkeypatch.setattr("memory.providers.postgres_provider.SessionLocal", session_local)
    monkeypatch.setattr("memory.database.session.SessionLocal", session_local)

    session = session_local()
    try:
        yield session
    finally:
        session.close()


@pytest.mark.anyio
async def test_provider_initialization(mock_db_session) -> None:
    """Verify provider initialization seeds a default user profile."""
    provider = PostgresProvider()
    await provider.initialize()

    assert provider._default_user_id is not None
    assert provider._default_user_id == 1


@pytest.mark.anyio
async def test_provider_save_and_get_preference(mock_db_session) -> None:
    """Verify saving and retrieving Preference memory type."""
    provider = PostgresProvider()
    await provider.initialize()

    entry = MemoryEntry(
        id="user_theme",
        content="dark_mode",
        memory_type=MemoryType.PREFERENCE,
        metadata=MemoryMetadata(additional_info={"source": "settings"}),
    )

    await provider.save(entry)
    retrieved = await provider.get("user_theme")

    assert retrieved is not None
    assert retrieved.id == "user_theme"
    assert retrieved.content == "dark_mode"
    assert retrieved.memory_type == MemoryType.PREFERENCE
    assert retrieved.metadata.additional_info.get("source") == "settings"


@pytest.mark.anyio
async def test_provider_save_and_get_session_context(mock_db_session) -> None:
    """Verify saving and retrieving Session context memory type."""
    provider = PostgresProvider()
    await provider.initialize()

    entry = MemoryEntry(
        id="session_xyz",
        content="c:/Users/Vishal/workspace",
        memory_type=MemoryType.SESSION,
        metadata=MemoryMetadata(additional_info={"active_window": "VSCode"}),
    )

    await provider.save(entry)
    retrieved = await provider.get("session_xyz")

    assert retrieved is not None
    assert retrieved.id == "session_xyz"
    assert retrieved.content == "c:/Users/Vishal/workspace"
    assert retrieved.metadata.additional_info.get("active_window") == "VSCode"


@pytest.mark.anyio
async def test_provider_search_and_list(mock_db_session) -> None:
    """Verify search filter capabilities on PostgresProvider."""
    provider = PostgresProvider()
    await provider.initialize()

    entry1 = MemoryEntry(
        id="pref_font",
        content="Roboto Mono font",
        memory_type=MemoryType.PREFERENCE,
    )
    entry2 = MemoryEntry(
        id="pref_size",
        content="14px font",
        memory_type=MemoryType.PREFERENCE,
    )

    await provider.save(entry1)
    await provider.save(entry2)

    # Search for "Roboto"
    results = await provider.search(MemoryQuery(text="Roboto"))
    assert len(results) == 1
    assert results[0].entry.id == "pref_font"

    # Search for general "font"
    all_fonts = await provider.search(MemoryQuery(text="font"))
    assert len(all_fonts) == 2

    # List entries
    listed = await provider.list_entries(memory_type=MemoryType.PREFERENCE.value)
    assert len(listed) == 2


@pytest.mark.anyio
async def test_provider_update_and_delete(mock_db_session) -> None:
    """Verify updates and deletions propagate to Postgres repositories."""
    provider = PostgresProvider()
    await provider.initialize()

    entry = MemoryEntry(
        id="workflow_deploy",
        content="git pull && npm run build",
        memory_type=MemoryType.WORKFLOW,
    )
    await provider.save(entry)

    # Update
    entry.content = "git pull && npm run dev"
    await provider.update("workflow_deploy", entry)

    updated = await provider.get("workflow_deploy")
    assert updated is not None
    assert updated.content == "git pull && npm run dev"

    # Delete
    await provider.delete("workflow_deploy")
    assert await provider.get("workflow_deploy") is None


@pytest.mark.anyio
async def test_provider_exception_translation(mock_db_session, monkeypatch) -> None:
    """Verify SQLAlchemy exceptions are successfully mapped into domain-specific exceptions."""
    from sqlalchemy.exc import IntegrityError
    provider = PostgresProvider()
    await provider.initialize()

    # Define a helper mock method that raises IntegrityError
    def mock_commit(*args, **kwargs):
        raise IntegrityError("mock_stmt", {}, Exception("Duplicate key value"))

    # Force IntegrityError inside _session_scope context block by patching session commit
    with pytest.raises(DataIntegrityError):
        with provider._session_scope() as session:
            monkeypatch.setattr(session, "commit", mock_commit)
            session.commit()
