"""Unit tests for the MemoryRanker and its integration with ContextBuilder."""

# pyrefly: ignore [missing-import]
import pytest
from datetime import datetime, timezone, timedelta
from memory import (
    MemoryService,
    MemoryEntry,
    MemoryMetadata,
    MemoryType,
    ContextBuilder,
    MemoryRanker,
    MemoryRankerConfig,
)


@pytest.fixture
def mock_in_memory_service(monkeypatch):
    """Provides a MemoryService forced to use InMemoryProvider."""
    from memory.config import settings
    monkeypatch.setattr(settings, "provider_type", "in_memory")
    return MemoryService()


def test_ranker_scoring_calculation() -> None:
    """Verify that different criteria (session, workspace, entity, command) increase the relevance score."""
    ranker = MemoryRanker()
    now = datetime.now(timezone.utc)

    # 1. Base entry (recency only, created 1 hour ago)
    base_entry = MemoryEntry(
        id="base",
        content="some random description",
        memory_type=MemoryType.CONVERSATION,
        metadata=MemoryMetadata(created_at=now - timedelta(hours=1))
    )

    # 2. Entry matching session
    session_entry = MemoryEntry(
        id="session",
        content="some random description",
        memory_type=MemoryType.CONVERSATION,
        metadata=MemoryMetadata(
            created_at=now - timedelta(hours=1),
            additional_info={"session_id": "current_sess"}
        )
    )

    # 3. Entry matching workspace path
    workspace_entry = MemoryEntry(
        id="workspace",
        content="C:\\workspace",
        memory_type=MemoryType.CONVERSATION,
        metadata=MemoryMetadata(
            created_at=now - timedelta(hours=1),
            additional_info={"workspace_path": "C:\\workspace"}
        )
    )

    # 4. Entry matching command keywords
    command_entry = MemoryEntry(
        id="command",
        content="please open chrome web browser",
        memory_type=MemoryType.CONVERSATION,
        metadata=MemoryMetadata(created_at=now - timedelta(hours=1))
    )

    base_score = ranker.score_entry(base_entry)
    session_score = ranker.score_entry(session_entry, session_id="current_sess")
    workspace_score = ranker.score_entry(workspace_entry, workspace_path="C:\\workspace")
    command_score = ranker.score_entry(command_entry, query_text="open app")

    assert session_score > base_score
    assert workspace_score > base_score
    assert command_score > base_score


def test_ranker_config_overrides() -> None:
    """Verify that overriding weights in MemoryRankerConfig adjusts the calculated scores."""
    custom_config = MemoryRankerConfig(
        recency_weight=0.0,
        session_weight=1.0,
        workspace_weight=0.0,
        entity_weight=0.0,
        command_weight=0.0,
    )
    ranker = MemoryRanker(config=custom_config)
    now = datetime.now(timezone.utc)

    matching_entry = MemoryEntry(
        id="match",
        content="hello world",
        memory_type=MemoryType.CONVERSATION,
        metadata=MemoryMetadata(
            created_at=now - timedelta(days=10),
            additional_info={"session_id": "sess_x"}
        )
    )

    score = ranker.score_entry(matching_entry, session_id="sess_x")
    # Score should be exactly 1.0 because session matches and session weight is 1.0 (others are 0.0)
    assert abs(score - 1.0) < 1e-5


@pytest.mark.anyio
async def test_ranker_context_builder_integration(mock_in_memory_service) -> None:
    """Verify ContextBuilder invokes the ranker and honors the configured limits."""
    service = mock_in_memory_service
    unique = "_lim"

    # Seed 6 conversation entries (limit is 5 by default in MemoryRankerConfig)
    for i in range(6):
        await service.save(MemoryEntry(
            id=f"conv_{i}{unique}",
            content=f"conversation message {i}",
            memory_type=MemoryType.CONVERSATION,
            metadata=MemoryMetadata(additional_info={"user_id": 123})
        ))

    # Initialize ContextBuilder with standard config
    config = MemoryRankerConfig(max_conversations=3)
    builder = ContextBuilder(service, ranker_config=config)

    context = await builder.build_context(user_id=123)

    # Max conversations slice limit of 3 should be respected
    assert len(context.recent_conversations) == 3
