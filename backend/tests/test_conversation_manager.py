"""Unit tests for the conversation management subsystem."""

from unittest.mock import MagicMock
import pytest

from voice.conversation.conversation_state import ConversationState
from voice.conversation.context import ConversationContext
from voice.conversation.session_manager import SessionManager, CONVERSATION_EXIT_COMMANDS
from voice.speech.models import SpeechResult


def _create_mock_manager() -> tuple[SessionManager, MagicMock, MagicMock, MagicMock, MagicMock]:
    """Helper to instantiate a mocked SessionManager."""
    mock_wake = MagicMock(return_value={"activated": False, "cleaned_command": ""})
    mock_rec = MagicMock(return_value=SpeechResult(text="", success=False))
    mock_exec = MagicMock(return_value=("Command executed", {}))
    mock_speak = MagicMock()

    manager = SessionManager(
        wake_word_detector=mock_wake,
        speech_recognizer=mock_rec,
        command_executor=mock_exec,
        tts_speaker=mock_speak,
        timeout_seconds=5.0,
    )
    return manager, mock_wake, mock_rec, mock_exec, mock_speak


def test_session_lifecycle():
    """Verify start and end transitions of conversation sessions."""
    manager, _, _, _, mock_speak = _create_mock_manager()

    assert manager.get_active_session() is None

    # 1. Start session
    session = manager.start_conversation()
    assert session is not None
    assert session.is_active is True
    assert session.state == ConversationState.LISTENING
    assert manager.get_active_session() == session
    mock_speak.assert_called_once_with("How can I help you?")

    # 2. End session
    manager.end_conversation()
    assert manager.get_active_session() is None
    assert session.is_active is False
    assert session.state == ConversationState.SLEEPING


def test_exit_commands_terminate_session():
    """Verify that any exit command terminates the active session with sign-off."""
    for exit_cmd in CONVERSATION_EXIT_COMMANDS:
        manager, _, _, _, mock_speak = _create_mock_manager()

        # Start active session
        manager.start_conversation()
        mock_speak.reset_mock()

        # Input exit command
        response = manager.handle_input(exit_cmd)

        assert response == "Goodbye."
        assert manager.get_active_session() is None
        mock_speak.assert_called_once_with("Goodbye.")


def test_handle_input_wake_word_activation():
    """Verify that a wake word activates a session and handles trailing command."""
    manager, mock_wake, _, mock_exec, mock_speak = _create_mock_manager()

    # Trigger wake word check
    mock_wake.return_value = {"activated": True, "cleaned_command": "show reports"}
    mock_exec.return_value = ("Showing reports", {"current_folder": "reports"})

    response = manager.handle_input("hey auralis show reports")

    assert response == "Showing reports"
    active_session = manager.get_active_session()
    assert active_session is not None
    assert active_session.state == ConversationState.WAITING_FOR_RESPONSE
    assert active_session.context.current_folder == "reports"
    assert active_session.context.last_command == "show reports"

    # Ensure greetings and responses were spoken
    mock_speak.assert_any_call("How can I help you?")
    mock_speak.assert_any_call("Showing reports")


def test_handle_input_wake_word_no_command():
    """Verify that a wake word with no command starts the session and prompts the user."""
    manager, mock_wake, _, _, mock_speak = _create_mock_manager()

    mock_wake.return_value = {"activated": True, "cleaned_command": ""}

    response = manager.handle_input("hey auralis")

    assert response == "Conversation started."
    active_session = manager.get_active_session()
    assert active_session is not None
    assert active_session.state == ConversationState.LISTENING

    mock_speak.assert_called_once_with("How can I help you?")


def test_standard_command_processing():
    """Verify context storage and state changes during standard command processing."""
    manager, _, _, mock_exec, mock_speak = _create_mock_manager()

    # Start session
    session = manager.start_conversation()
    mock_speak.reset_mock()

    mock_exec.return_value = ("file index.txt created", {"current_file": "index.txt"})

    response = manager.handle_input("create file index.txt")

    assert response == "file index.txt created"
    assert session.context.last_command == "create file index.txt"
    assert session.context.last_response == "file index.txt created"
    assert session.context.current_file == "index.txt"
    assert session.state == ConversationState.WAITING_FOR_RESPONSE

    mock_speak.assert_called_once_with("file index.txt created")


def test_inactivity_timeout():
    """Verify that session ends automatically when inactivity callback is triggered."""
    manager, _, _, _, mock_speak = _create_mock_manager()

    # Start session
    manager.start_conversation()
    mock_speak.reset_mock()

    # Trigger timeout callback manually
    manager.handle_session_timeout()

    assert manager.get_active_session() is None
    mock_speak.assert_called_once_with("Goodbye.")


def test_run_conversation_step_speech_success():
    """Verify run_conversation_step handles a successful transcribed command."""
    manager, _, mock_rec, mock_exec, _ = _create_mock_manager()

    # Start session
    manager.start_conversation()

    mock_rec.return_value = SpeechResult(text="list directories", success=True)
    mock_exec.return_value = ("listed folders", {"current_folder": "root"})

    success = manager.run_conversation_step()

    assert success is True
    session = manager.get_active_session()
    assert session is not None
    assert session.context.last_command == "list directories"
    assert session.context.current_folder == "root"


def test_run_conversation_step_timeout():
    """Verify run_conversation_step terminates session when recording times out."""
    manager, _, mock_rec, _, mock_speak = _create_mock_manager()

    # Start session
    manager.start_conversation()
    mock_speak.reset_mock()

    # Yield timeout error result
    mock_rec.return_value = SpeechResult(
        text=None, success=False, error="Timeout: No speech detected"
    )

    success = manager.run_conversation_step()

    assert success is False
    assert manager.get_active_session() is None
    mock_speak.assert_called_once_with("Goodbye.")
