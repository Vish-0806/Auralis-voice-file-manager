"""Integration tests for the Auralis PostgreSQL Memory Provider."""

# pyrefly: ignore [missing-import]
import pytest
import uuid
from memory import MemoryService, MemoryEntry, MemoryMetadata, MemoryQuery, MemoryType
from memory.providers.postgres_provider import PostgresProvider


@pytest.fixture(autouse=True)
def ensure_postgres_provider_active(monkeypatch):
    """Overrides conftest forced in-memory setting, activating postgres provider for this test file."""
    from memory.config import settings
    monkeypatch.setattr(settings, "provider_type", "postgres")


@pytest.fixture(scope="module", autouse=True)
def setup_postgres_tables():
    """Ensure PostgreSQL tables exist before running integration tests."""
    # pyrefly: ignore [missing-import]
    from sqlalchemy import create_engine
    from memory.database import Base
    from memory.database.config import db_config
    engine = create_engine(db_config.url)
    Base.metadata.create_all(bind=engine)
    yield
    # We do NOT drop tables here to preserve the schema for runtime application execution.


@pytest.fixture
async def postgres_service():
    """Provides a MemoryService initialized with the PostgresProvider."""
    service = MemoryService()
    # Explicitly check that we are using PostgresProvider
    assert service._manager._repository._provider.__class__.__name__ == "PostgresProvider"
    yield service


@pytest.mark.anyio
async def test_postgres_crud_integration(postgres_service) -> None:
    """Verify complete PostgreSQL CRUD lifecycle, persistence across sessions, and transactional commits."""
    # Generate unique keys to avoid test collisions and ease cleanup
    unique_suffix = f"_{uuid.uuid4().hex[:8]}"
    pref_key = f"pref_theme{unique_suffix}"
    session_key = f"sess_user{unique_suffix}"

    # Initialize PostgreSQL Provider
    provider = postgres_service._manager._repository._provider
    await provider.initialize()

    # 1. Verify save()
    pref_entry = MemoryEntry(
        id=pref_key,
        content="synthwave",
        memory_type=MemoryType.PREFERENCE,
        metadata=MemoryMetadata(additional_info={"editor": "cursor"}),
    )
    await postgres_service.save(pref_entry)

    session_entry = MemoryEntry(
        id=session_key,
        content="/home/workspace/project",
        memory_type=MemoryType.SESSION,
        metadata=MemoryMetadata(additional_info={"active_window": "terminal"}),
    )
    await postgres_service.save(session_entry)

    # 2. Verify get() and data persistence after reopening a database session
    # We instantiate a brand new provider instance to simulate reopening a database session / new connection
    fresh_provider = PostgresProvider()
    await fresh_provider.initialize()

    pref_retrieved = await fresh_provider.get(pref_key)
    assert pref_retrieved is not None
    assert pref_retrieved.id == pref_key
    assert pref_retrieved.content == "synthwave"
    assert pref_retrieved.metadata.additional_info.get("editor") == "cursor"

    session_retrieved = await fresh_provider.get(session_key)
    assert session_retrieved is not None
    assert session_retrieved.id == session_key
    assert session_retrieved.content == "/home/workspace/project"
    assert session_retrieved.metadata.additional_info.get("active_window") == "terminal"

    # 3. Verify update()
    pref_entry.content = "monokai"
    await postgres_service.update(pref_key, pref_entry)

    # Verify update persisted in fresh session
    pref_updated = await fresh_provider.get(pref_key)
    assert pref_updated is not None
    assert pref_updated.content == "monokai"

    # 4. Verify search()
    search_results = await postgres_service.search(MemoryQuery(text="monokai"))
    assert len(search_results) >= 1
    assert any(r.entry.id == pref_key for r in search_results)

    # 5. Verify list_entries()
    listed_entries = await postgres_service.list(memory_type="preference")
    assert len(listed_entries) >= 1
    assert any(e.id == pref_key for e in listed_entries)

    # 6. Verify delete()
    await postgres_service.delete(pref_key)
    await postgres_service.delete(session_key)

    # Verify deletions persisted in fresh session
    assert await fresh_provider.get(pref_key) is None
    assert await fresh_provider.get(session_key) is None
