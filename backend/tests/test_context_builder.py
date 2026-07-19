"""Unit and Integration tests for ContextBuilder."""

# pyrefly: ignore [missing-import]
import pytest
import uuid
from datetime import datetime, timezone
from memory import (
    MemoryService,
    MemoryEntry,
    MemoryMetadata,
    MemoryType,
    ContextBuilder,
)


@pytest.fixture
def mock_in_memory_service(monkeypatch):
    """Provides a MemoryService forced to use InMemoryProvider."""
    from memory.config import settings
    monkeypatch.setattr(settings, "provider_type", "in_memory")
    return MemoryService()


@pytest.fixture
def postgres_active_service(monkeypatch):
    """Provides a MemoryService forced to use PostgresProvider."""
    from memory.config import settings
    monkeypatch.setattr(settings, "provider_type", "postgres")
    return MemoryService()


@pytest.fixture(scope="module", autouse=True)
def setup_postgres_schema():
    """Ensures PostgreSQL tables exist for integration testing."""
    # pyrefly: ignore [missing-import]
    from sqlalchemy import create_engine
    from memory.database import Base
    from memory.database.config import db_config
    engine = create_engine(db_config.url)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.mark.anyio
async def test_context_builder_empty_scenarios(mock_in_memory_service) -> None:
    """Verify ContextBuilder handles empty database / empty provider cases without raising errors."""
    service = mock_in_memory_service
    builder = ContextBuilder(service)

    # Build context with no data seeded
    context = await builder.build_context(user_id=123)

    assert context.recent_conversations == []
    assert context.recent_executions == []
    assert context.current_context is None
    assert context.preferences == []
    assert context.workspace_context is None
    assert context.metadata == {"user_id": 123, "session_id": None}


@pytest.mark.anyio
async def test_context_builder_in_memory(mock_in_memory_service) -> None:
    """Verify ContextBuilder correctly aggregates and filters data using the InMemoryProvider."""
    service = mock_in_memory_service
    builder = ContextBuilder(service)
    unique = f"_{uuid.uuid4().hex[:8]}"

    # 1. Seed conversation
    await service.save(MemoryEntry(
        id=f"conv_1{unique}",
        content="Hello standard user",
        memory_type=MemoryType.CONVERSATION,
        metadata=MemoryMetadata(additional_info={"session_id": f"sess_1{unique}", "user_id": 123})
    ))

    # 2. Seed execution
    await service.save(MemoryEntry(
        id=f"exec_1{unique}",
        content="exec status logs",
        memory_type=MemoryType.ACTIVITY,
        metadata=MemoryMetadata(additional_info={"status": "success", "user_id": 123})
    ))

    # 3. Seed context
    await service.save(MemoryEntry(
        id=f"sess_1{unique}",
        content="/home/workspace_project",
        memory_type=MemoryType.SESSION,
        metadata=MemoryMetadata(additional_info={"user_id": 123})
    ))

    # 4. Seed preference
    await service.save(MemoryEntry(
        id=f"theme{unique}",
        content="dark",
        memory_type=MemoryType.PREFERENCE,
        metadata=MemoryMetadata(additional_info={"user_id": 123})
    ))

    # 5. Seed workspace project context
    await service.save(MemoryEntry(
        id=f"work_profile{unique}",
        content="/home/workspace_project",
        memory_type=MemoryType.PROJECT,
        metadata=MemoryMetadata(additional_info={"user_id": 123, "name": "project_a"})
    ))

    # Run the builder
    context = await builder.build_context(user_id=123, session_id=f"sess_1{unique}")

    assert len(context.recent_conversations) == 1
    assert context.recent_conversations[0].content == "Hello standard user"

    assert len(context.recent_executions) == 1
    assert context.recent_executions[0].content == "exec status logs"

    assert context.current_context is not None
    assert context.current_context.content == "/home/workspace_project"

    assert len(context.preferences) == 1
    assert context.preferences[0].content == "dark"

    assert context.workspace_context is not None
    assert context.workspace_context.metadata.additional_info.get("name") == "project_a"


@pytest.mark.anyio
async def test_context_builder_postgres(postgres_active_service) -> None:
    """Verify ContextBuilder correctly aggregates and filters data in PostgreSQL."""
    service = postgres_active_service
    builder = ContextBuilder(service)
    unique = f"_{uuid.uuid4().hex[:8]}"

    # Initialize Postgres Provider default profile
    provider = service._manager._repository._provider
    await provider.initialize()

    # Create isolated user for postgres
    with provider._session_scope() as session:
        from memory.repository.repository_factory import RepositoryFactory
        from memory.models.domain_models import UserDomain
        factory = RepositoryFactory(session)
        user_repo = factory.get_user_repository()
        user = UserDomain(username=f"test_ctx_{unique}", email=f"ctx_{unique}@auralis.local")
        user = user_repo.create(user)
        test_user_id = user.id

    try:
        # 1. Seed conversation
        await service.save(MemoryEntry(
            id=f"conv_1{unique}",
            content="Hello pg user",
            memory_type=MemoryType.CONVERSATION,
            metadata=MemoryMetadata(additional_info={"session_id": f"sess_1{unique}", "user_id": test_user_id})
        ))

        # 2. Seed execution
        await service.save(MemoryEntry(
            id=f"exec_1{unique}",
            content="exec status logs pg",
            memory_type=MemoryType.ACTIVITY,
            metadata=MemoryMetadata(additional_info={"status": "success", "user_id": test_user_id})
        ))

        # 3. Seed context
        await service.save(MemoryEntry(
            id=f"sess_1{unique}",
            content="/home/workspace_project_pg",
            memory_type=MemoryType.SESSION,
            metadata=MemoryMetadata(additional_info={"user_id": test_user_id})
        ))

        # 4. Seed preference
        await service.save(MemoryEntry(
            id=f"theme{unique}",
            content="dark_theme_pg",
            memory_type=MemoryType.PREFERENCE,
            metadata=MemoryMetadata(additional_info={"user_id": test_user_id})
        ))

        # 5. Seed workspace context
        # We write directly to the DB because there is no direct save() mapping to project/workspace in PostgresProvider
        with provider._session_scope() as session:
            from memory.repository.repository_factory import RepositoryFactory
            from memory.models.domain_models import WorkspaceProfileDomain
            factory = RepositoryFactory(session)
            work_repo = factory.get_workspace_repository()
            profile = WorkspaceProfileDomain(
                user_id=test_user_id,
                name="pg_project",
                path="/home/workspace_project_pg",
                settings={"editor": "VSCode"}
            )
            work_repo.create(profile)

        # Run builder
        context = await builder.build_context(user_id=test_user_id, session_id=f"sess_1{unique}")

        # Assertions
        # Filter returned objects to only match our isolated user_id
        conversations = [c for c in context.recent_conversations if c.metadata.additional_info.get("user_id") == test_user_id]
        assert len(conversations) == 1
        assert conversations[0].content == "Hello pg user"

        executions = [e for e in context.recent_executions if e.metadata.additional_info.get("user_id") == test_user_id]
        assert len(executions) == 1
        assert executions[0].content == "exec status logs pg"

        assert context.current_context is not None
        assert context.current_context.content == "/home/workspace_project_pg"

        preferences = [p for p in context.preferences if p.metadata.additional_info.get("user_id") == test_user_id]
        assert len(preferences) == 1
        assert preferences[0].content == "dark_theme_pg"

        assert context.workspace_context is not None
        assert context.workspace_context.metadata.additional_info.get("name") == "pg_project"

    finally:
        # Teardown dynamic test user and cascade-deleted data
        with provider._session_scope() as session:
            factory = RepositoryFactory(session)
            user_repo = factory.get_user_repository()
            user_repo.delete(test_user_id)


@pytest.mark.anyio
async def test_context_builder_exception_resilience(monkeypatch) -> None:
    """Verify ContextBuilder catches raised retrieval exceptions and defaults gracefully to empty objects."""
    # Create a broken memory service
    service = MemoryService()

    async def raise_err(*args, **kwargs):
        raise RuntimeError("DB connection dropped")

    # Monkeypatch service methods to raise exceptions
    monkeypatch.setattr(service, "get_recent_conversations", raise_err)
    monkeypatch.setattr(service, "get_conversations_by_session", raise_err)
    monkeypatch.setattr(service, "get_recent_executions", raise_err)
    monkeypatch.setattr(service, "get_latest_context", raise_err)
    monkeypatch.setattr(service, "get_user_preferences", raise_err)

    builder = ContextBuilder(service)
    context = await builder.build_context(user_id=456, session_id="broken_sess")

    # Assert gracefulness: empty lists and None returned instead of exception propagating
    assert context.recent_conversations == []
    assert context.recent_executions == []
    assert context.current_context is None
    assert context.preferences == []
    assert context.workspace_context is None
    assert context.metadata == {"user_id": 456, "session_id": "broken_sess"}
