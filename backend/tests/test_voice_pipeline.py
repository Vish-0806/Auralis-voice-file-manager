"""Unit tests for the Voice Integration Pipeline and Controller."""

import time
from unittest.mock import MagicMock, patch
import pytest

from core.exceptions import PlanningException, DispatchException
from core.models import AssistantResponse, ExecutionPlan, ExecutionResult
from core.intents import Intent
from voice.ux import AssistantStatus
from voice.speech import SpeechResult
from voice.context import ContextState, ResolutionResult
from voice.integration.event_router import EventRouter
from voice.integration.voice_pipeline import VoicePipeline
from voice.integration.pipeline_controller import PipelineController


def test_event_router_pub_sub():
    """Verify that EventRouter routes messages to subscribers and allows unsubscribing."""
    router = EventRouter()
    triggered = []

    def callback(data):
        triggered.append(data)

    router.subscribe("TEST_EVENT", callback)
    router.publish("TEST_EVENT", {"payload": "hello"})

    assert len(triggered) == 1
    assert triggered[0]["payload"] == "hello"

    router.unsubscribe("TEST_EVENT", callback)
    router.publish("TEST_EVENT", {"payload": "world"})
    assert len(triggered) == 1  # Still 1, since unsubscribed


def _create_mock_pipeline_stack():
    """Helper to build mocks for all voice pipeline collaborators."""
    mock_assistant = MagicMock()
    mock_detector = MagicMock()
    mock_sm = MagicMock()
    mock_stt = MagicMock()
    mock_cm = MagicMock()
    mock_tts = MagicMock()
    mock_ux = MagicMock()
    mock_router = MagicMock()
    mock_mic = MagicMock()

    pipeline = VoicePipeline(
        assistant=mock_assistant,
        wake_word_detector=mock_detector,
        conversation_manager=mock_sm,
        speech_to_text=mock_stt,
        context_manager=mock_cm,
        text_to_speech=mock_tts,
        feedback_manager=mock_ux,
        event_router=mock_router,
        microphone=mock_mic,
    )
    return pipeline, mock_assistant, mock_detector, mock_sm, mock_stt, mock_cm, mock_tts, mock_ux, mock_router


def test_pipeline_text_command_flow():
    """Verify successful end-to-end command execution in simulated text mode."""
    (
        pipeline,
        mock_assistant,
        mock_detector,
        mock_sm,
        _,
        mock_cm,
        mock_tts,
        mock_ux,
        mock_router,
    ) = _create_mock_pipeline_stack()

    # 1. Mock Wake Word detection
    mock_detector.detect_in_text.return_value = MagicMock(phrase="Hey Auralis")

    # 2. Mock Active Session
    mock_session = MagicMock(session_id="session_123")
    mock_sm.get_active_session.side_effect = [
        None,  # First check (wake phase check)
        mock_session,  # Second check (inside command processing check)
        mock_session,  # Any successive calls
    ]

    # 3. Mock Context resolver
    mock_cm.resolve_references.return_value = ResolutionResult(
        resolved_command="open file doc.txt", requires_clarification=False
    )
    mock_cm.state = ContextState()

    # 4. Mock Assistant execution
    mock_plan = ExecutionPlan(intent=Intent.OPEN_FILE, target="doc.txt", confidence=1.0)
    mock_result = ExecutionResult(success=True, response="File doc.txt opened", data={"filename": "doc.txt"}, execution_time=0.1)
    mock_assistant.process_request.return_value = AssistantResponse(
        response="I've opened the file doc.txt", plan=mock_plan, result=mock_result
    )

    # Run step simulation
    success = pipeline.process_step(text_input="Hey Auralis open file doc.txt")

    assert success is True

    # Check subsystem coordination
    mock_detector.detect_in_text.assert_called_with("Hey Auralis open file doc.txt")
    mock_sm.start_conversation.assert_called_once()
    mock_ux.transition_to.assert_any_call(AssistantStatus.WAKE_DETECTED)
    mock_ux.transition_to.assert_any_call(AssistantStatus.LISTENING)

    # Reference resolution and execution check
    mock_cm.resolve_references.assert_called_with("open file doc.txt")
    mock_assistant.process_request.assert_called_once()
    mock_cm.update.assert_called_once_with(
        current_file="doc.txt",
        current_folder=None,
        current_search_results=None,
        current_capability="OPEN_FILE",
        last_intent="OPEN_FILE",
        last_execution_result="I've opened the file doc.txt",
        pending_confirmation=None,
    )

    # Speech playbacks and alerts checks
    mock_tts.speak.assert_called_with("I've opened the file doc.txt")
    mock_ux.transition_to.assert_any_call(AssistantStatus.SPEAKING)
    mock_ux.transition_to.assert_any_call(AssistantStatus.WAITING)

    # Interruption triggered at start of command
    mock_tts.audio_output.stop.assert_called_once()


def test_pipeline_reference_clarification():
    """Verify that ambiguous commands trigger clarification requests and halt execution."""
    pipeline, _, mock_detector, mock_sm, _, mock_cm, mock_tts, mock_ux, _ = _create_mock_pipeline_stack()

    # Mock active session
    mock_session = MagicMock(session_id="session_123")
    mock_sm.get_active_session.return_value = mock_session

    # Mock resolution to require clarification
    mock_cm.resolve_references.return_value = ResolutionResult(
        resolved_command="",
        requires_clarification=True,
        clarification_prompt="Did you mean doc1.txt or doc2.txt?",
    )

    result = pipeline.process_command("delete it")

    assert result == "Did you mean doc1.txt or doc2.txt?"
    mock_tts.speak.assert_called_once_with("Did you mean doc1.txt or doc2.txt?")
    mock_ux.transition_to.assert_called_with(AssistantStatus.WAITING)


def test_controller_microphone_error_recovery():
    """Verify that controller handles microphone disconnect with backoff retry."""
    pipeline, _, _, _, _, _, _, mock_ux, _ = _create_mock_pipeline_stack()
    controller = PipelineController(pipeline)

    # Mock process_step to raise hardware disconnect error
    pipeline.process_step = MagicMock(side_effect=RuntimeError("PyAudio: No input devices found"))

    # Test error handler execution with sleep patch to keep it fast
    with patch("time.sleep") as mock_sleep:
        controller._loop()  # Will break immediately if _running is False. But we can trigger _handle_error directly:
        controller._handle_error(RuntimeError("PyAudio: No input devices found"))

        # Should transition status to ERROR and backoff 5 seconds
        mock_ux.transition_to.assert_called_once_with(
            AssistantStatus.ERROR, custom_message="Microphone disconnected. Retrying..."
        )
        mock_sleep.assert_called_once_with(5.0)


def test_controller_planner_error_recovery():
    """Verify that planner orchestration faults are caught and spoken to the user."""
    pipeline, _, _, mock_sm, _, _, mock_tts, mock_ux, _ = _create_mock_pipeline_stack()
    controller = PipelineController(pipeline)

    # Active session is set
    mock_sm.get_active_session.return_value = MagicMock()

    controller._handle_error(PlanningException("Planner failure"))

    mock_ux.transition_to.assert_any_call(AssistantStatus.ERROR)
    mock_tts.speak.assert_called_once_with(
        "I couldn't formulate a plan for that command. Please try again."
    )
    mock_ux.transition_to.assert_any_call(AssistantStatus.WAITING)


def test_controller_capability_error_recovery():
    """Verify that capability execution faults are caught and spoken to the user."""
    pipeline, _, _, mock_sm, _, _, mock_tts, mock_ux, _ = _create_mock_pipeline_stack()
    controller = PipelineController(pipeline)

    # Active session is set
    mock_sm.get_active_session.return_value = MagicMock()

    controller._handle_error(DispatchException("Capability target fail"))

    mock_ux.transition_to.assert_any_call(AssistantStatus.ERROR)
    mock_tts.speak.assert_called_once_with(
        "An error occurred while executing that operation. Please try again."
    )
    mock_ux.transition_to.assert_any_call(AssistantStatus.WAITING)
