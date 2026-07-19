"""Unit tests for the Auralis Memory Subsystem.

Tests all CRUD operations, search, filters, listing, and dependency injection
capabilities of the modular Memory subsystem.
"""

import uuid
# pyrefly: ignore [missing-import]
import pytest
from memory import (
    MemoryEntry,
    MemoryMetadata,
    MemoryQuery,
    MemoryService,
    MemoryType,
)
from memory.providers.base_provider import InMemoryProvider
from memory.repository.memory_repository import MemoryRepository
from memory.manager.memory_manager import MemoryManager


@pytest.fixture
def memory_service() -> MemoryService:
    """Fixture to provide a clean MemoryService instance for each test."""
    return MemoryService()


@pytest.mark.anyio
async def test_save_and_get_memory(memory_service: MemoryService) -> None:
    """Test saving a memory entry and retrieving it back by ID."""
    entry_id = str(uuid.uuid4())
    content = "User preference: Default text editor is VS Code."
    metadata = MemoryMetadata(
        tags=["preference", "editor"],
        source="unit_test",
        additional_info={"editor_name": "vscode"}
    )
    entry = MemoryEntry(
        id=entry_id,
        content=content,
        memory_type=MemoryType.PREFERENCE,
        metadata=metadata
    )

    # Save
    saved_entry = await memory_service.save(entry)
    assert saved_entry.id == entry_id
    assert saved_entry.content == content
    assert saved_entry.memory_type == MemoryType.PREFERENCE
    assert saved_entry.metadata.source == "unit_test"

    # Get
    retrieved_entry = await memory_service.get(entry_id)
    assert retrieved_entry is not None
    assert retrieved_entry.id == entry_id
    assert retrieved_entry.content == content
    assert retrieved_entry.metadata.additional_info["editor_name"] == "vscode"


@pytest.mark.anyio
async def test_get_nonexistent_memory(memory_service: MemoryService) -> None:
    """Test retrieving a non-existent memory entry returns None."""
    retrieved = await memory_service.get("nonexistent_id")
    assert retrieved is None


@pytest.mark.anyio
async def test_update_memory(memory_service: MemoryService) -> None:
    """Test updating an existing memory entry."""
    entry_id = str(uuid.uuid4())
    entry = MemoryEntry(
        id=entry_id,
        content="Original content.",
        memory_type=MemoryType.SESSION
    )

    await memory_service.save(entry)

    # Update content
    entry.content = "Updated content."
    entry.metadata.tags = ["updated"]
    
    updated_entry = await memory_service.update(entry_id, entry)
    assert updated_entry.content == "Updated content."
    assert "updated" in updated_entry.metadata.tags

    # Verify retrieval
    retrieved = await memory_service.get(entry_id)
    assert retrieved is not None
    assert retrieved.content == "Updated content."


@pytest.mark.anyio
async def test_update_nonexistent_memory_raises_keyerror(memory_service: MemoryService) -> None:
    """Test updating a non-existent entry raises a KeyError."""
    entry = MemoryEntry(
        id="nonexistent",
        content="Some content",
        memory_type=MemoryType.SESSION
    )
    with pytest.raises(KeyError):
        await memory_service.update("nonexistent", entry)


@pytest.mark.anyio
async def test_delete_memory(memory_service: MemoryService) -> None:
    """Test deleting a memory entry."""
    entry_id = str(uuid.uuid4())
    entry = MemoryEntry(
        id=entry_id,
        content="To be deleted.",
        memory_type=MemoryType.ACTIVITY
    )

    await memory_service.save(entry)
    
    # Confirm it exists
    assert await memory_service.get(entry_id) is not None

    # Delete
    await memory_service.delete(entry_id)

    # Confirm it is gone
    assert await memory_service.get(entry_id) is None


@pytest.mark.anyio
async def test_list_memories(memory_service: MemoryService) -> None:
    """Test listing memory entries, with and without filtering by type."""
    entry1 = MemoryEntry(
        id="1",
        content="Session log 1",
        memory_type=MemoryType.SESSION
    )
    entry2 = MemoryEntry(
        id="2",
        content="Session log 2",
        memory_type=MemoryType.SESSION
    )
    entry3 = MemoryEntry(
        id="3",
        content="Workflow macro",
        memory_type=MemoryType.WORKFLOW
    )

    await memory_service.save(entry1)
    await memory_service.save(entry2)
    await memory_service.save(entry3)

    # List all
    all_memories = await memory_service.list()
    assert len(all_memories) == 3

    # List only session type
    session_memories = await memory_service.list(memory_type="session")
    assert len(session_memories) == 2
    ids = {m.id for m in session_memories}
    assert "1" in ids
    assert "2" in ids
    assert "3" not in ids


@pytest.mark.anyio
async def test_search_memories(memory_service: MemoryService) -> None:
    """Test searching memories using text content and filtering."""
    entry1 = MemoryEntry(
        id="1",
        content="Project Auralis setup completed.",
        memory_type=MemoryType.PROJECT,
        metadata=MemoryMetadata(tags=["auralis", "setup"], additional_info={"status": "done"})
    )
    entry2 = MemoryEntry(
        id="2",
        content="Project PyTorch model trained.",
        memory_type=MemoryType.PROJECT,
        metadata=MemoryMetadata(tags=["pytorch", "model"], additional_info={"status": "done"})
    )
    entry3 = MemoryEntry(
        id="3",
        content="Conversation about dinner recipes.",
        memory_type=MemoryType.CONVERSATION,
        metadata=MemoryMetadata(tags=["dinner"], additional_info={"status": "active"})
    )

    await memory_service.save(entry1)
    await memory_service.save(entry2)
    await memory_service.save(entry3)

    # Search text match
    query = MemoryQuery(text="Project")
    results = await memory_service.search(query)
    assert len(results) == 2
    assert results[0].score == 1.0

    # Search with type filter
    query_with_type = MemoryQuery(text="Project", memory_type=MemoryType.CONVERSATION)
    results_type = await memory_service.search(query_with_type)
    assert len(results_type) == 0

    # Search metadata field filters
    query_filters = MemoryQuery(text="", filters={"status": "done"})
    results_filters = await memory_service.search(query_filters)
    assert len(results_filters) == 2
    ids = {r.entry.id for r in results_filters}
    assert "1" in ids
    assert "2" in ids


@pytest.mark.anyio
async def test_dependency_injection() -> None:
    """Test initializing MemoryService with a custom/mock manager."""
    provider = InMemoryProvider()
    # pyrefly: ignore [bad-instantiation]
    repository = MemoryRepository(provider)
    manager = MemoryManager(repository)
    service = MemoryService(manager=manager)

    entry = MemoryEntry(
        id="inj-1",
        content="Injected memory test",
        memory_type=MemoryType.SESSION
    )
    await service.save(entry)
    retrieved = await service.get("inj-1")
    assert retrieved is not None
    assert retrieved.content == "Injected memory test"
