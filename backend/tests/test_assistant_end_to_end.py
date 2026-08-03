"""End-to-End Production Certification Test Suite for Phase 13.10 – Assistant Architecture."""

from concurrent.futures import ThreadPoolExecutor
import time
# pyrefly: ignore [missing-import]
import pytest

from brain.assistant import (
    get_assistant_runtime,
    reset_assistant_runtime,
)
from brain.assistant.conversation import (
    get_conversation_runtime,
    reset_conversation_runtime,
)
from brain.assistant.dialogue import (
    DialogueTurn,
    get_dialogue_runtime,
    reset_dialogue_runtime,
)
from brain.assistant.integration import (
    AssistantIntegrationRequest,
    AssistantIntegrationResponse,
    IntegrationStatus,
    get_assistant_integration_runtime,
    reset_assistant_integration_runtime,
)
from brain.assistant.memory import (
    get_assistant_memory_runtime,
    reset_assistant_memory_runtime,
)
from brain.assistant.proactive import (
    get_proactive_runtime,
    reset_proactive_runtime,
)
from brain.assistant.reasoning import (
    DecisionRequest,
    get_decision_runtime,
    reset_decision_runtime,
)
from brain.assistant.response import (
    get_response_runtime,
    reset_response_runtime,
)
from brain.assistant.voice import (
    get_voice_runtime,
    reset_voice_runtime,
)


@pytest.fixture(autouse=True)
def cleanup_all_singletons():
    """Reset all 9 Phase 13 singletons before and after each test."""
    reset_assistant_integration_runtime()
    reset_proactive_runtime()
    reset_voice_runtime()
    reset_response_runtime()
    reset_assistant_memory_runtime()
    reset_decision_runtime()
    reset_dialogue_runtime()
    reset_conversation_runtime()
    reset_assistant_runtime()

    yield

    reset_assistant_integration_runtime()
    reset_proactive_runtime()
    reset_voice_runtime()
    reset_response_runtime()
    reset_assistant_memory_runtime()
    reset_decision_runtime()
    reset_dialogue_runtime()
    reset_conversation_runtime()
    reset_assistant_runtime()


# ---------------------------------------------------------------------------
# 1. Multi-Runtime Initialization Sequence
# ---------------------------------------------------------------------------

def test_e2e_initialization_sequence() -> None:
    """Verify clean initialization sequence across all 9 Assistant architecture runtimes."""
    rt_13_1 = get_assistant_runtime()
    rt_13_2 = get_conversation_runtime()
    rt_13_3 = get_dialogue_runtime()
    rt_13_4 = get_decision_runtime()
    rt_13_5 = get_assistant_memory_runtime()
    rt_13_6 = get_response_runtime()
    rt_13_7 = get_voice_runtime()
    rt_13_8 = get_proactive_runtime()
    rt_13_9 = get_assistant_integration_runtime()

    runtimes = [
        ("Foundation", rt_13_1),
        ("Conversation", rt_13_2),
        ("Dialogue", rt_13_3),
        ("Decision", rt_13_4),
        ("Memory", rt_13_5),
        ("Response", rt_13_6),
        ("Voice", rt_13_7),
        ("Proactive", rt_13_8),
        ("Integration", rt_13_9),
    ]

    for name, rt in runtimes:
        assert rt.is_initialized is True, f"{name} runtime was not initialized"


# ---------------------------------------------------------------------------
# 2. Complete Assistant Request Lifecycle
# ---------------------------------------------------------------------------

def test_e2e_assistant_request_lifecycle() -> None:
    """Verify complete end-to-end request processing via the Assistant Integration Gateway."""
    integration_rt = get_assistant_integration_runtime()
    provider = integration_rt.get_provider()
    assert provider is not None

    req = AssistantIntegrationRequest(user_prompt="Analyze repository structure and summarize workspace status.")
    res = provider.handle_request(req)

    assert isinstance(res, AssistantIntegrationResponse)
    assert res.status == IntegrationStatus.SUCCESS
    assert res.request_id == req.request_id
    assert "Analyze repository structure" in res.assistant_reply
    assert len(res.execution_summaries) == 8


# ---------------------------------------------------------------------------
# 3. Conversation Session Creation & Message History
# ---------------------------------------------------------------------------

def test_e2e_conversation_lifecycle() -> None:
    """Verify Conversation Session creation, message recording, and history retrieval."""
    conv_rt = get_conversation_runtime()
    provider = conv_rt.get_provider()
    assert provider is not None

    conv = provider.manager.create_conversation(title="Session 1", user_id="user-123")
    assert conv.conversation_id is not None

    msg = provider.history_manager.append_message(conv.conversation_id, "USER", "Hello Assistant")
    assert msg.content == "Hello Assistant"

    history = provider.history_manager.get_history(conv.conversation_id)
    assert len(history.messages) == 1


# ---------------------------------------------------------------------------
# 4. Dialogue Turn Processing & State Machine Transitions
# ---------------------------------------------------------------------------

def test_e2e_dialogue_turn_processing() -> None:
    """Verify Dialogue turn processing and state machine transitions."""
    dial_rt = get_dialogue_runtime()
    provider = dial_rt.get_provider()
    assert provider is not None

    session = provider.manager.create_session("conv-456")
    turn = provider.manager.create_turn(session.session_id, "Organize files")
    assert isinstance(turn, DialogueTurn)
    assert turn.turn_id is not None

    completed_turn = provider.manager.complete_turn(session.session_id, turn.turn_id, "Files organized")
    assert completed_turn.system_response == "Files organized"


# ---------------------------------------------------------------------------
# 5. Decision & Reasoning Routing
# ---------------------------------------------------------------------------

def test_e2e_decision_routing() -> None:
    """Verify Decision Coordinator request routing and policy evaluation."""
    dec_rt = get_decision_runtime()
    provider = dec_rt.get_provider()
    assert provider is not None

    req = DecisionRequest(user_prompt="search_file", confidence=0.92)
    res = provider.coordinator.evaluate_request(req)

    assert res.request_id == req.request_id
    assert res.recommended_action is not None


# ---------------------------------------------------------------------------
# 6. Assistant Memory Snapshot Generation
# ---------------------------------------------------------------------------

def test_e2e_assistant_memory_context() -> None:
    """Verify Assistant Memory context merging and working context creation."""
    mem_rt = get_assistant_memory_runtime()
    provider = mem_rt.get_provider()
    assert provider is not None

    snapshot = provider.create_snapshot(session_id="conv-789")
    assert snapshot.snapshot_id is not None


# ---------------------------------------------------------------------------
# 7. Response Generation & Stream Formatting
# ---------------------------------------------------------------------------

def test_e2e_response_generation() -> None:
    """Verify Response Generation assembly and Markdown formatting."""
    resp_rt = get_response_runtime()
    provider = resp_rt.get_provider()
    assert provider is not None

    resp = provider.build_response(request_id="req-1", content="Hello user!")
    assert resp.content == "Hello user!"
    assert resp.formatted_content != ""


# ---------------------------------------------------------------------------
# 8. Voice Interaction Coordination
# ---------------------------------------------------------------------------

def test_e2e_voice_coordination() -> None:
    """Verify Voice Orchestration session lifecycle management."""
    voice_rt = get_voice_runtime()
    provider = voice_rt.get_provider()
    assert provider is not None

    session = provider.session_manager.create_session("user-voice-1")
    assert session.session_id is not None

    closed = provider.session_manager.close_session(session.session_id)
    assert closed.state.name == "CLOSED"


# ---------------------------------------------------------------------------
# 9. Proactive Recommendation & Notification Management
# ---------------------------------------------------------------------------

def test_e2e_proactive_behavior() -> None:
    """Verify Proactive recommendation generation and assistant-level notification lifecycle."""
    pro_rt = get_proactive_runtime()
    provider = pro_rt.get_provider()
    assert provider is not None

    eval_report = provider.coordinator.evaluate_proactive_behavior()
    assert eval_report.evaluation_id is not None

    notif = provider.notification_manager.create_notification("Alert Title", "Alert Body")
    assert notif.notification_id is not None
    assert provider.notification_manager.dismiss_notification(notif.notification_id) is True


# ---------------------------------------------------------------------------
# 10. 12-Subsystem Health & System Capability Aggregation
# ---------------------------------------------------------------------------

def test_e2e_health_capabilities_and_statistics() -> None:
    """Verify system-wide health aggregation, capability reporting, and stats."""
    integration_rt = get_assistant_integration_runtime()

    health = integration_rt.get_health()
    assert health.healthy is True
    assert health.availability_percentage >= 0.0
    assert len(health.subsystem_health) == 12

    caps = integration_rt.get_capabilities()
    assert caps.supports_full_pipeline is True

    stats = integration_rt.get_statistics()
    assert stats.uptime_seconds >= 0.0


# ---------------------------------------------------------------------------
# 11. Multi-Threaded Concurrency Certification using ThreadPoolExecutor
# ---------------------------------------------------------------------------

def test_e2e_concurrent_execution() -> None:
    """Certify thread safety under heavy concurrent load using ThreadPoolExecutor across all 9 runtimes."""
    integration_rt = get_assistant_integration_runtime()
    provider = integration_rt.get_provider()
    assert provider is not None

    def worker(idx: int) -> bool:
        req = AssistantIntegrationRequest(user_prompt=f"Concurrent request #{idx}")
        res = provider.handle_request(req)
        return res.status == IntegrationStatus.SUCCESS

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(worker, i) for i in range(25)]
        results = [f.result() for f in futures]

    assert all(results)
    stats = integration_rt.get_statistics()
    assert stats.total_requests_handled == 25


# ---------------------------------------------------------------------------
# 12. Singleton Identity, Restart & Shutdown Mechanics
# ---------------------------------------------------------------------------

def test_e2e_singleton_restart_shutdown() -> None:
    """Verify singleton identity, restart mechanics, and graceful shutdown across runtimes."""
    r1 = get_assistant_integration_runtime()
    r2 = get_assistant_integration_runtime()
    assert r1 is r2

    r1.restart()
    assert r1.is_initialized is True

    r1.shutdown()
    assert r1.is_initialized is False
