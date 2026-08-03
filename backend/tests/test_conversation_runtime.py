"""Unit tests for Phase 13.2 – Conversation Runtime."""

import threading
# pyrefly: ignore [missing-import]
import pytest
# pyrefly: ignore [missing-import]
from pydantic import ValidationError

from brain.assistant.conversation import (
    ContextManager,
    Conversation,
    ConversationContext,
    ConversationException,
    ConversationHealth,
    ConversationHistory,
    ConversationManager,
    ConversationMessage,
    ConversationMetadata,
    ConversationNotFoundError,
    ConversationParticipant,
    ConversationProvider,
    ConversationRuntime,
    ConversationState,
    ConversationStateError,
    ConversationStatistics,
    ConversationType,
    HistoryManager,
    IConversationProvider,
    MessageRole,
    get_conversation_runtime,
    reset_conversation_runtime,
)


@pytest.fixture(autouse=True)
def cleanup_singleton():
    """Ensure clean singleton state before and after each test."""
    reset_conversation_runtime()
    yield
    reset_conversation_runtime()


# ---------------------------------------------------------------------------
# 1. Immutable Models
# ---------------------------------------------------------------------------

def test_immutable_models() -> None:
    """Verify all 8 Pydantic v2 models are frozen and immutable."""
    meta = ConversationMetadata()
    part = ConversationParticipant()
    msg = ConversationMessage()
    ctx = ConversationContext()
    hist = ConversationHistory()
    stats = ConversationStatistics()
    health = ConversationHealth()
    conv = Conversation()

    models = [meta, part, msg, ctx, hist, stats, health, conv]
    for m in models:
        with pytest.raises((ValidationError, TypeError, AttributeError)):
            m.conversation_id = "hacked"  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# 2. Lifecycle & Conversation Creation
# ---------------------------------------------------------------------------

def test_conversation_creation_and_retrieval() -> None:
    """Verify creating and retrieving conversations."""
    runtime = get_conversation_runtime()
    provider = runtime.get_provider()
    assert isinstance(provider, ConversationProvider)

    conv = provider.manager.create_conversation(
        conversation_type=ConversationType.VOICE,
        title="Voice Session",
        user_id="usr-123",
        workspace_id="ws-456",
    )

    assert conv.conversation_id.startswith("conv-")
    assert conv.conversation_type == ConversationType.VOICE
    assert conv.state == ConversationState.ACTIVE
    assert conv.metadata.title == "Voice Session"

    retrieved = provider.manager.get_conversation(conv.conversation_id)
    assert retrieved is not None
    assert retrieved.conversation_id == conv.conversation_id


# ---------------------------------------------------------------------------
# 3. State Transitions
# ---------------------------------------------------------------------------

def test_state_transitions() -> None:
    """Verify conversation state transitions (pause, close, archive)."""
    runtime = get_conversation_runtime()
    provider = runtime.get_provider()
    assert isinstance(provider, ConversationProvider)

    conv = provider.manager.create_conversation(title="State Test")
    conv_id = conv.conversation_id

    # Pause
    paused = provider.manager.update_state(conv_id, ConversationState.PAUSED)
    assert paused.state == ConversationState.PAUSED

    # Close
    closed = provider.manager.close_conversation(conv_id)
    assert closed.state == ConversationState.CLOSED
    assert closed.closed_at is not None

    # Archive
    archived = provider.manager.archive_conversation(conv_id)
    assert archived.state == ConversationState.ARCHIVED

    # Invalid transition from ARCHIVED to ACTIVE
    with pytest.raises(ConversationStateError):
        provider.manager.update_state(conv_id, ConversationState.ACTIVE)

    # Non-existent conversation
    with pytest.raises(ConversationNotFoundError):
        provider.manager.update_state("non-existent-id", ConversationState.CLOSED)


# ---------------------------------------------------------------------------
# 4. Message Append & History Retrieval
# ---------------------------------------------------------------------------

def test_message_append_and_history_retrieval() -> None:
    """Verify message appending, history retrieval, pagination, and trimming."""
    runtime = get_conversation_runtime()
    provider = runtime.get_provider()
    assert isinstance(provider, ConversationProvider)

    conv = provider.manager.create_conversation(title="History Test")
    cid = conv.conversation_id

    m1 = provider.history_manager.append_message(cid, MessageRole.USER, "Hello AI")
    m2 = provider.history_manager.append_message(cid, MessageRole.ASSISTANT, "Hello User")
    m3 = provider.history_manager.append_message(cid, MessageRole.USER, "How are you?")

    assert m1.content == "Hello AI"
    assert m2.role == MessageRole.ASSISTANT

    hist = provider.history_manager.get_history(cid)
    assert hist.total_messages == 3
    assert len(hist.messages) == 3

    # Pagination: limit=2, offset=1
    page = provider.history_manager.get_history(cid, limit=2, offset=1)
    assert len(page.messages) == 2
    assert page.messages[0].content == "Hello User"
    assert page.messages[1].content == "How are you?"

    # Trimming
    trimmed_hist = provider.history_manager.trim_history(cid, max_messages=2)
    assert trimmed_hist.trimmed is True
    assert len(trimmed_hist.messages) == 2
    assert trimmed_hist.messages[0].content == "Hello User"


# ---------------------------------------------------------------------------
# 5. Context Updates & Topic Management
# ---------------------------------------------------------------------------

def test_context_updates() -> None:
    """Verify context topic updates and context dictionary merges."""
    runtime = get_conversation_runtime()
    provider = runtime.get_provider()
    assert isinstance(provider, ConversationProvider)

    conv = provider.manager.create_conversation(title="Context Test")
    cid = conv.conversation_id

    # Topic
    ctx1 = provider.context_manager.set_topic(cid, "File Management")
    assert ctx1.current_topic == "File Management"

    # Execution context merge
    ctx2 = provider.context_manager.merge_execution_context(cid, {"task_id": "t-100", "step": 2})
    assert ctx2.execution_context["task_id"] == "t-100"

    # Assistant context merge
    ctx3 = provider.context_manager.merge_assistant_context(cid, {"model": "gemini-3.6"})
    assert ctx3.assistant_context["model"] == "gemini-3.6"

    # Variable update
    ctx4 = provider.context_manager.update_variables(cid, {"user_pref": "dark_mode"})
    assert ctx4.variables["user_pref"] == "dark_mode"


# ---------------------------------------------------------------------------
# 6. Statistics & Health Reporting
# ---------------------------------------------------------------------------

def test_statistics_and_health() -> None:
    """Verify real-time health checks and aggregate statistics."""
    runtime = get_conversation_runtime()
    provider = runtime.get_provider()
    assert isinstance(provider, ConversationProvider)

    c1 = provider.manager.create_conversation(title="Stats Conv 1")
    c2 = provider.manager.create_conversation(title="Stats Conv 2")
    provider.history_manager.append_message(c1.conversation_id, MessageRole.USER, "Test 1")
    provider.history_manager.append_message(c1.conversation_id, MessageRole.ASSISTANT, "Test 2")
    provider.manager.close_conversation(c2.conversation_id)

    stats = runtime.get_statistics()
    assert stats.total_conversations_created == 2
    assert stats.active_conversations == 1
    assert stats.closed_conversations == 1
    assert stats.total_messages_processed == 2

    health = runtime.get_health()
    assert health.healthy is True
    assert health.status == "READY"


# ---------------------------------------------------------------------------
# 7. Singleton Identity & Reset
# ---------------------------------------------------------------------------

def test_singleton_identity() -> None:
    """Verify get_conversation_runtime identity and reset_conversation_runtime."""
    rt1 = get_conversation_runtime()
    rt2 = get_conversation_runtime()
    assert rt1 is rt2
    assert rt1.is_initialized is True

    reset_conversation_runtime()
    rt3 = get_conversation_runtime()
    assert rt3 is not rt1
    assert rt3.is_initialized is True


# ---------------------------------------------------------------------------
# 8. Thread Safety
# ---------------------------------------------------------------------------

def test_thread_safety() -> None:
    """Verify thread-safe concurrent conversation creation and message appending."""
    runtime = get_conversation_runtime()
    provider = runtime.get_provider()
    assert isinstance(provider, ConversationProvider)

    errors = []

    def worker(idx: int) -> None:
        try:
            conv = provider.manager.create_conversation(title=f"Thread Conv {idx}")
            for i in range(10):
                provider.history_manager.append_message(
                    conv.conversation_id, MessageRole.USER, f"Msg {i} from thread {idx}"
                )
                provider.context_manager.update_variables(conv.conversation_id, {"idx": idx})
        except Exception as exc:
            errors.append(exc)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0
    stats = runtime.get_statistics()
    assert stats.total_conversations_created == 10
    assert stats.total_messages_processed == 100


# ---------------------------------------------------------------------------
# 9. Dependency Injection
# ---------------------------------------------------------------------------

def test_dependency_injection() -> None:
    """Verify constructor dependency injection for managers."""
    custom_manager = ConversationManager()
    custom_history = HistoryManager()
    custom_context = ContextManager()

    provider = ConversationProvider(
        manager=custom_manager,
        history_manager=custom_history,
        context_manager=custom_context,
    )
    runtime = ConversationRuntime(provider=provider)
    runtime.initialize()

    assert provider.manager is custom_manager
    assert provider.history_manager is custom_history
    assert provider.context_manager is custom_context


# ---------------------------------------------------------------------------
# 10. Backward Compatibility
# ---------------------------------------------------------------------------

def test_backward_compatibility() -> None:
    """Verify Phase 9 AssistantRuntime continues operating alongside ConversationRuntime."""
    from brain.runtime import AssistantRuntime as Phase9Runtime

    p9 = Phase9Runtime()
    assert p9.initialize() is True
    res = p9.process_request("hello world")
    assert res.success is True
    assert p9.shutdown() is True
