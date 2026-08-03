"""Unit tests for Phase 13.6 – Assistant Response Generation & Streaming Runtime."""

import threading
# pyrefly: ignore [missing-import]
import pytest
# pyrefly: ignore [missing-import]
from pydantic import ValidationError

from brain.assistant.response import (
    AssistantResponse,
    IResponseProvider,
    ResponseBuilder,
    ResponseChunk,
    ResponseContext,
    ResponseCoordinator,
    ResponseException,
    ResponseFormat,
    ResponseFormatter,
    ResponseHealth,
    ResponseMetadata,
    ResponseProvider,
    ResponseRuntime,
    ResponseState,
    ResponseStatistics,
    ResponseStream,
    ResponseTemplate,
    StreamingManager,
    StreamingMode,
    get_response_runtime,
    reset_response_runtime,
)


@pytest.fixture(autouse=True)
def cleanup_singleton():
    """Ensure clean singleton state before and after each test."""
    reset_response_runtime()
    yield
    reset_response_runtime()


# ---------------------------------------------------------------------------
# 1. Immutable Models
# ---------------------------------------------------------------------------

def test_immutable_models() -> None:
    """Verify all 8 Pydantic v2 domain models are frozen and immutable."""
    meta = ResponseMetadata()
    ctx = ResponseContext()
    chunk = ResponseChunk()
    resp = AssistantResponse()
    stream = ResponseStream()
    tmpl = ResponseTemplate()
    stats = ResponseStatistics()
    health = ResponseHealth()

    models = [meta, ctx, chunk, resp, stream, tmpl, stats, health]
    for m in models:
        with pytest.raises((ValidationError, TypeError, AttributeError)):
            m.confidence = 0.5  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# 2. Response Building & Metadata Binding
# ---------------------------------------------------------------------------

def test_response_building() -> None:
    """Verify ResponseBuilder assembles AssistantResponse domain model with metadata."""
    runtime = get_response_runtime()
    provider = runtime.get_provider()
    assert isinstance(provider, ResponseProvider)

    meta = ResponseMetadata(
        citations=["https://docs.auralis.ai/v1"],
        execution_summary={"tasks_completed": 2},
    )

    response = provider.build_response(
        request_id="req-123",
        content="Operation completed successfully.",
        format_type=ResponseFormat.MARKDOWN,
        confidence=0.98,
        metadata=meta,
    )

    assert isinstance(response, AssistantResponse)
    assert response.request_id == "req-123"
    assert response.confidence == 0.98
    assert response.state == ResponseState.COMPLETED
    assert response.tokens_used >= 1
    assert "https://docs.auralis.ai/v1" in response.formatted_content


# ---------------------------------------------------------------------------
# 3. Stream Generation & Chunk Ordering
# ---------------------------------------------------------------------------

def test_stream_generation_and_chunk_ordering() -> None:
    """Verify StreamingManager chunks response content sequentially with is_final marking."""
    mgr = StreamingManager()

    resp = AssistantResponse(
        request_id="req-stream",
        content="Alpha Beta Gamma Delta Epsilon Zeta Eta Theta",
    )

    stream = mgr.create_stream(resp, chunk_size=10, mode=StreamingMode.CHUNK_STREAM)
    assert isinstance(stream, ResponseStream)
    assert stream.is_complete is True
    assert len(stream.chunks) > 1

    chunks = mgr.get_chunks(stream)
    for idx, c in enumerate(chunks):
        assert c.chunk_index == idx
        if idx == len(chunks) - 1:
            assert c.is_final is True
        else:
            assert c.is_final is False


# ---------------------------------------------------------------------------
# 4. Response Formatting (Markdown, Plain Text, JSON)
# ---------------------------------------------------------------------------

def test_response_formatting_variants() -> None:
    """Verify ResponseFormatter renders Markdown, Plain Text, and JSON."""
    formatter = ResponseFormatter()
    meta = ResponseMetadata(citations=["Ref 1"])

    # 1. Markdown
    md = formatter.format_content("### Title\nContent", ResponseFormat.MARKDOWN, meta)
    assert "References" in md
    assert "- Ref 1" in md

    # 2. Plain Text
    txt = formatter.format_content("### Title\nContent", ResponseFormat.PLAIN_TEXT, meta)
    assert "###" not in txt
    assert "Citations:" in txt

    # 3. JSON
    js = formatter.format_content("Hello World", ResponseFormat.JSON, meta)
    assert '"content": "Hello World"' in js


# ---------------------------------------------------------------------------
# 5. Coordinator Context Preparation
# ---------------------------------------------------------------------------

def test_response_coordinator() -> None:
    """Verify ResponseCoordinator prepares ResponseContext across subsystem runtimes."""
    coord = ResponseCoordinator()

    class DummyDialogueRuntime:
        def get_health(self):
            class DummyHealth:
                status = "ACTIVE"
            return DummyHealth()

    ctx = coord.prepare_response_context(
        request_id="req-coord",
        user_prompt="list files",
        dialogue_runtime=DummyDialogueRuntime(),
    )

    assert isinstance(ctx, ResponseContext)
    assert ctx.request_id == "req-coord"
    assert ctx.variables.get("dialogue_status") == "ACTIVE"


# ---------------------------------------------------------------------------
# 6. Statistics & Health Reporting
# ---------------------------------------------------------------------------

def test_statistics_and_health() -> None:
    """Verify response runtime statistics and diagnostic health snapshot."""
    runtime = get_response_runtime()
    provider = runtime.get_provider()
    assert isinstance(provider, ResponseProvider)

    resp = provider.build_response("req-1", "Test response 1")
    _ = provider.create_stream(resp)

    stats = runtime.get_statistics()
    assert stats.total_responses_built == 1
    assert stats.total_streams_generated == 1
    assert stats.total_chunks_emitted >= 1

    health = runtime.get_health()
    assert health.healthy is True
    assert health.status == "READY"


# ---------------------------------------------------------------------------
# 7. Singleton Identity & Reset
# ---------------------------------------------------------------------------

def test_singleton_identity() -> None:
    """Verify get_response_runtime singleton identity and reset_response_runtime mechanics."""
    rt1 = get_response_runtime()
    rt2 = get_response_runtime()
    assert rt1 is rt2
    assert rt1.is_initialized is True

    reset_response_runtime()
    rt3 = get_response_runtime()
    assert rt3 is not rt1
    assert rt3.is_initialized is True


# ---------------------------------------------------------------------------
# 8. Thread Safety
# ---------------------------------------------------------------------------

def test_thread_safety() -> None:
    """Verify thread safety under concurrent response building and streaming."""
    runtime = get_response_runtime()
    provider = runtime.get_provider()
    assert isinstance(provider, ResponseProvider)

    errors = []

    def worker(idx: int) -> None:
        try:
            for i in range(10):
                resp = provider.build_response(
                    request_id=f"req-{idx}-{i}",
                    content=f"Thread content {idx} iteration {i}",
                )
                _ = provider.create_stream(resp, chunk_size=8)
        except Exception as exc:
            errors.append(exc)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0
    stats = runtime.get_statistics()
    assert stats.total_responses_built == 100
    assert stats.total_streams_generated == 100


# ---------------------------------------------------------------------------
# 9. Dependency Injection & Backward Compatibility
# ---------------------------------------------------------------------------

def test_dependency_injection_and_compatibility() -> None:
    """Verify constructor dependency injection and backward compatibility with Phase 10 & Phases 13.1–13.5."""
    from brain.assistant import get_assistant_runtime
    from brain.assistant.conversation import get_conversation_runtime
    from brain.assistant.dialogue import get_dialogue_runtime
    from brain.assistant.memory import get_assistant_memory_runtime
    from brain.assistant.reasoning import get_decision_runtime

    ast_rt = get_assistant_runtime()
    conv_rt = get_conversation_runtime()
    dial_rt = get_dialogue_runtime()
    dec_rt = get_decision_runtime()
    mem_rt = get_assistant_memory_runtime()

    assert ast_rt.is_initialized is True
    assert conv_rt.is_initialized is True
    assert dial_rt.is_initialized is True
    assert dec_rt.is_initialized is True
    assert mem_rt.is_initialized is True

    custom_coord = ResponseCoordinator()
    custom_formatter = ResponseFormatter()
    custom_builder = ResponseBuilder(formatter=custom_formatter)
    custom_stream = StreamingManager()

    provider = ResponseProvider(
        coordinator=custom_coord,
        builder=custom_builder,
        formatter=custom_formatter,
        streaming_manager=custom_stream,
    )

    resp_rt = ResponseRuntime(provider=provider)
    resp_rt.initialize()
    assert resp_rt.is_initialized is True
