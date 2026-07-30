"""Unit tests for CommandDispatcher (Phase 9.6)."""

# pyrefly: ignore [missing-import]
import pytest
from brain.voice import CommandDispatcher, VoiceCommand, VoiceCommandStatus


def mock_successful_pipeline(text: str, session_id: str, metadata: dict) -> dict:
    return {
        "success": True,
        "processed_text": text,
        "session_id": session_id,
        "metadata": metadata,
    }


def mock_failing_pipeline(text: str, session_id: str, metadata: dict) -> dict:
    return {
        "success": False,
        "error": "Pipeline failure",
    }


def mock_exception_pipeline(text: str, session_id: str, metadata: dict) -> dict:
    raise RuntimeError("Brain pipeline crashed")


# ---------------------------------------------------------------------------
# Dispatching
# ---------------------------------------------------------------------------

def test_dispatch_default_noop_pipeline() -> None:
    dispatcher = CommandDispatcher()
    cmd = VoiceCommand(command_id="c1", session_id="s1", raw_text="hello")
    res = dispatcher.dispatch(cmd)
    assert res.success is True
    assert res.status == VoiceCommandStatus.COMPLETED
    assert res.command_id == "c1"


def test_dispatch_successful_pipeline() -> None:
    dispatcher = CommandDispatcher(pipeline=mock_successful_pipeline)
    cmd = VoiceCommand(command_id="c1", session_id="s1", raw_text="delete all")
    res = dispatcher.dispatch(cmd, conversation_id="conv-123")
    assert res.success is True
    assert res.status == VoiceCommandStatus.COMPLETED
    assert res.pipeline_ms >= 0.0
    assert res.metadata["pipeline_output"]["processed_text"] == "delete all"


def test_dispatch_failing_pipeline() -> None:
    dispatcher = CommandDispatcher(pipeline=mock_failing_pipeline)
    cmd = VoiceCommand(command_id="c1", session_id="s1", raw_text="delete all")
    res = dispatcher.dispatch(cmd)
    assert res.success is False
    assert res.status == VoiceCommandStatus.FAILED
    assert res.error == "Pipeline failure"


def test_dispatch_exception_handling() -> None:
    dispatcher = CommandDispatcher(pipeline=mock_exception_pipeline)
    cmd = VoiceCommand(command_id="c1", session_id="s1", raw_text="crash")
    res = dispatcher.dispatch(cmd)
    assert res.success is False
    assert res.status == VoiceCommandStatus.FAILED
    assert "Brain pipeline crashed" in res.error


# ---------------------------------------------------------------------------
# Pipeline Hot-Swapping & Logging
# ---------------------------------------------------------------------------

def test_set_pipeline() -> None:
    dispatcher = CommandDispatcher(pipeline=mock_failing_pipeline)
    cmd = VoiceCommand(command_id="c1", session_id="s1")
    res1 = dispatcher.dispatch(cmd)
    assert res1.success is False

    dispatcher.set_pipeline(mock_successful_pipeline)
    res2 = dispatcher.dispatch(cmd)
    assert res2.success is True


def test_dispatch_log() -> None:
    dispatcher = CommandDispatcher(pipeline=mock_successful_pipeline)
    cmd1 = VoiceCommand(command_id="c1", session_id="s1")
    cmd2 = VoiceCommand(command_id="c2", session_id="s1")
    dispatcher.dispatch(cmd1)
    dispatcher.dispatch(cmd2)

    log = dispatcher.get_dispatch_log()
    assert len(log) == 2
    assert log[0]["command_id"] == "c1"
    assert log[1]["command_id"] == "c2"

    dispatcher.clear_log()
    assert len(dispatcher.get_dispatch_log()) == 0


# ---------------------------------------------------------------------------
# Thread Safety
# ---------------------------------------------------------------------------

def test_command_dispatcher_thread_safety() -> None:
    import threading
    dispatcher = CommandDispatcher(pipeline=mock_successful_pipeline)
    results = []

    def run_dispatch(i: int) -> None:
        cmd = VoiceCommand(command_id=f"cmd-{i}", session_id="s-concur")
        res = dispatcher.dispatch(cmd)
        results.append(res)

    threads = [threading.Thread(target=run_dispatch, args=(i,)) for i in range(30)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(results) == 30
    assert all(r.success for r in results)
    assert len(dispatcher.get_dispatch_log()) == 30
