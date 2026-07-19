"""Unit and Integration tests for Advanced Memory Retrieval APIs."""

# pyrefly: ignore [missing-import]
import pytest
import uuid
from datetime import datetime, timedelta, timezone
from memory import MemoryService, MemoryEntry, MemoryMetadata, MemoryType
from memory.providers.postgres_provider import PostgresProvider


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
async def test_in_memory_advanced_retrieval(mock_in_memory_service) -> None:
    """Verify retrieval operations function correctly on the InMemoryProvider."""
    service = mock_in_memory_service
    unique = f"_{uuid.uuid4().hex[:8]}"

    # Seed 3 conversations
    for i in range(3):
        entry = MemoryEntry(
            id=f"conv_{i}{unique}",
            content=f"Message {i}",
            memory_type=MemoryType.CONVERSATION,
            metadata=MemoryMetadata(
                created_at=datetime.now(timezone.utc) - timedelta(minutes=i),
                additional_info={"session_id": f"sess_{i % 2}{unique}", "user_id": 99}
            )
        )
        await service.save(entry)

    # Seed executions
    await service.save(MemoryEntry(
        id=f"exec_success{unique}",
        content="success log",
        memory_type=MemoryType.ACTIVITY,
        metadata=MemoryMetadata(additional_info={"status": "success", "user_id": 99})
    ))
    await service.save(MemoryEntry(
        id=f"exec_failed{unique}",
        content="failed log",
        memory_type=MemoryType.ACTIVITY,
        metadata=MemoryMetadata(additional_info={"status": "failed", "user_id": 99})
    ))

    # Seed contexts (using session_id as the primary MemoryEntry ID)
    await service.save(MemoryEntry(
        id=f"sess_active{unique}",
        content="workspace_a",
        memory_type=MemoryType.SESSION,
        metadata=MemoryMetadata(additional_info={"user_id": 99})
    ))

    # Seed preferences
    await service.save(MemoryEntry(
        id=f"pref_key{unique}",
        content="value_a",
        memory_type=MemoryType.PREFERENCE,
        metadata=MemoryMetadata(additional_info={"user_id": 99})
    ))

    # Seed events
    await service.save(MemoryEntry(
        id=f"event_item{unique}",
        content="event_payload",
        memory_type=MemoryType.LONG_TERM,
        metadata=MemoryMetadata(additional_info={"user_id": 99})
    ))

    # 1. Test Conversation retrieval
    recent_convs = await service.get_recent_conversations(2)
    assert len(recent_convs) == 2
    assert recent_convs[0].content == "Message 0"

    sess_convs = await service.get_conversations_by_session(f"sess_0{unique}", 5)
    assert len(sess_convs) == 2

    user_convs = await service.get_conversations_by_user(99, 5)
    assert len(user_convs) == 3

    # 2. Test Execution retrieval
    recent_execs = await service.get_recent_executions(5)
    assert len(recent_execs) == 2

    failed_execs = await service.get_failed_executions(5)
    assert len(failed_execs) == 1
    assert failed_execs[0].content == "failed log"

    success_execs = await service.get_successful_executions(5)
    assert len(success_execs) == 1
    assert success_execs[0].content == "success log"

    # 3. Test Context retrieval
    latest_ctx = await service.get_latest_context(99)
    assert latest_ctx is not None
    assert latest_ctx.content == "workspace_a"

    sess_ctx = await service.get_context_by_session(f"sess_active{unique}")
    assert sess_ctx is not None
    assert sess_ctx.content == "workspace_a"

    # 4. Test Preference retrieval
    pref = await service.get_preference_by_key(99, f"pref_key{unique}")
    assert pref is not None
    assert pref.content == "value_a"

    # 5. Test Event retrieval
    events = await service.get_recent_events(5)
    assert len(events) == 1
    assert events[0].id == f"event_item{unique}"


@pytest.mark.anyio
async def test_postgres_advanced_retrieval(postgres_active_service) -> None:
    """Verify retrieval operations function correctly on the PostgresProvider (integration)."""
    service = postgres_active_service
    unique = f"_{uuid.uuid4().hex[:8]}"

    # Initialize Postgres Provider default profile
    provider = service._manager._repository._provider
    await provider.initialize()

    # Create a dynamic test user in DB to keep this test completely isolated
    with provider._session_scope() as session:
        from memory.repository.repository_factory import RepositoryFactory
        from memory.models.domain_models import UserDomain
        factory = RepositoryFactory(session)
        user_repo = factory.get_user_repository()
        test_username = f"test_user{unique}"
        user = UserDomain(username=test_username, email=f"{test_username}@auralis.local")
        user = user_repo.create(user)
        test_user_id = user.id

    try:
        # Seed 3 conversations for the test user
        for i in range(3):
            entry = MemoryEntry(
                id=f"conv_{i}{unique}",
                content=f"Message {i}",
                memory_type=MemoryType.CONVERSATION,
                metadata=MemoryMetadata(
                    created_at=datetime.now(timezone.utc) - timedelta(minutes=i),
                    additional_info={"session_id": f"sess_{i % 2}{unique}", "user_id": test_user_id}
                )
            )
            await service.save(entry)

        # Seed executions
        await service.save(MemoryEntry(
            id=f"exec_success{unique}",
            content="success log",
            memory_type=MemoryType.ACTIVITY,
            metadata=MemoryMetadata(additional_info={"status": "success", "user_id": test_user_id})
        ))
        await service.save(MemoryEntry(
            id=f"exec_failed{unique}",
            content="failed log",
            memory_type=MemoryType.ACTIVITY,
            metadata=MemoryMetadata(additional_info={"status": "failed", "user_id": test_user_id})
        ))

        # Seed contexts (using session_id as primary MemoryEntry ID)
        await service.save(MemoryEntry(
            id=f"sess_active{unique}",
            content="workspace_a",
            memory_type=MemoryType.SESSION,
            metadata=MemoryMetadata(additional_info={"user_id": test_user_id})
        ))

        # Seed preferences
        await service.save(MemoryEntry(
            id=f"pref_key{unique}",
            content="value_a",
            memory_type=MemoryType.PREFERENCE,
            metadata=MemoryMetadata(additional_info={"user_id": test_user_id})
        ))

        # Seed events
        await service.save(MemoryEntry(
            id=f"event_item{unique}",
            content="event_payload",
            memory_type=MemoryType.LONG_TERM,
            metadata=MemoryMetadata(additional_info={"id": f"event_item{unique}", "user_id": test_user_id})
        ))

        # 1. Test Conversation retrieval
        recent_convs = await service.get_recent_conversations(2)
        # Filter to only our test user's convs
        recent_convs = [c for c in recent_convs if c.metadata.additional_info.get("user_id") == test_user_id]
        assert len(recent_convs) == 2
        assert recent_convs[0].content == "Message 2"

        sess_convs = await service.get_conversations_by_session(f"sess_0{unique}", 5)
        assert len(sess_convs) == 2

        user_convs = await service.get_conversations_by_user(test_user_id, 5)
        assert len(user_convs) == 3

        # 2. Test Execution retrieval
        recent_execs = await service.get_recent_executions(5)
        recent_execs = [e for e in recent_execs if e.metadata.additional_info.get("user_id") == test_user_id]
        assert len(recent_execs) == 2

        failed_execs = await service.get_failed_executions(5)
        failed_execs = [e for e in failed_execs if e.metadata.additional_info.get("user_id") == test_user_id]
        assert len(failed_execs) == 1
        assert failed_execs[0].content == "failed log"

        success_execs = await service.get_successful_executions(5)
        success_execs = [e for e in success_execs if e.metadata.additional_info.get("user_id") == test_user_id]
        assert len(success_execs) == 1
        assert success_execs[0].content == "success log"

        # 3. Test Context retrieval
        latest_ctx = await service.get_latest_context(test_user_id)
        assert latest_ctx is not None
        assert latest_ctx.content == "workspace_a"

        sess_ctx = await service.get_context_by_session(f"sess_active{unique}")
        assert sess_ctx is not None
        assert sess_ctx.content == "workspace_a"

        # 4. Test Preference retrieval
        pref = await service.get_preference_by_key(test_user_id, f"pref_key{unique}")
        assert pref is not None
        assert pref.content == "value_a"

        # 5. Test Event retrieval
        events = await service.get_recent_events(5)
        events = [e for e in events if e.metadata.additional_info.get("user_id") == test_user_id]
        assert len(events) == 1
        assert events[0].id == f"event_item{unique}"

    finally:
        # Cascade delete the test user, wiping all associated test records automatically
        with provider._session_scope() as session:
            factory = RepositoryFactory(session)
            user_repo = factory.get_user_repository()
            user_repo.delete(test_user_id)
