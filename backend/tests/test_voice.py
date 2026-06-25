"""
Unit tests for the ContinuousListener module.
"""

import threading
import time
from unittest.mock import patch, MagicMock

import pytest
from voice.continuous_listener import ContinuousListener


def test_listener_start_stop_sync():
    """Verify sync start and stop using a mock listen side-effect to stop the loop."""
    listener = ContinuousListener()

    call_count = 0

    def mock_listen():
        nonlocal call_count
        call_count += 1
        # Stop the listener on first capture so the loop terminates
        listener.stop()
        return "hey auralis open downloads"

    with patch("voice.continuous_listener.listen", side_effect=mock_listen), \
         patch("voice.continuous_listener.detect_wake_word") as mock_detect, \
         patch("voice.continuous_listener.parse_command") as mock_parse, \
         patch("voice.continuous_listener.execute_action") as mock_exec, \
         patch("voice.continuous_listener.tts_speak") as mock_speak:

        mock_detect.return_value = {"activated": True, "cleaned_command": "open downloads"}
        mock_parse.return_value = {"action": "open", "target": "downloads"}
        mock_exec.return_value = "Opened downloads"

        # Run synchronously
        listener.start(run_in_thread=False)

        assert call_count == 1
        mock_detect.assert_called_once_with("hey auralis open downloads")
        mock_parse.assert_called_once_with("open downloads")
        mock_exec.assert_called_once_with({"action": "open", "target": "downloads"})
        mock_speak.assert_called_once_with("Opened downloads")


def test_listener_empty_input():
    """Verify empty input is ignored and does not trigger further processing."""
    listener = ContinuousListener()

    def mock_listen():
        listener.stop()
        return ""

    with patch("voice.continuous_listener.listen", side_effect=mock_listen), \
         patch("voice.continuous_listener.detect_wake_word") as mock_detect:

        listener.start(run_in_thread=False)

        # Empty inputs should not call detect_wake_word
        mock_detect.assert_not_called()


def test_listener_wake_word_not_activated():
    """Verify input is ignored if the wake word is not detected."""
    listener = ContinuousListener()

    def mock_listen():
        listener.stop()
        return "open downloads"

    with patch("voice.continuous_listener.listen", side_effect=mock_listen), \
         patch("voice.continuous_listener.detect_wake_word") as mock_detect, \
         patch("voice.continuous_listener.parse_command") as mock_parse:

        mock_detect.return_value = {"activated": False, "cleaned_command": ""}

        listener.start(run_in_thread=False)

        mock_detect.assert_called_once_with("open downloads")
        mock_parse.assert_not_called()



def test_listener_empty_command_after_wake():
    """Verify prompt is spoken if wake word is detected with no trailing command."""
    listener = ContinuousListener()

    def mock_listen():
        listener.stop()
        return "hey auralis"

    with patch("voice.continuous_listener.listen", side_effect=mock_listen), \
         patch("voice.continuous_listener.detect_wake_word") as mock_detect, \
         patch("voice.continuous_listener.tts_speak") as mock_speak, \
         patch("voice.continuous_listener.parse_command") as mock_parse:

        mock_detect.return_value = {"activated": True, "cleaned_command": ""}

        listener.start(run_in_thread=False)

        mock_detect.assert_called_once_with("hey auralis")
        mock_speak.assert_called_once_with("How can I help you?")
        mock_parse.assert_not_called()


def test_listener_graceful_exception_handling():
    """Verify exceptions in the loop are caught and do not crash the loop."""
    listener = ContinuousListener()
    call_count = 0

    def mock_listen():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise RuntimeError("Microphone failure")
        listener.stop()
        return "hey auralis open downloads"

    with patch("voice.continuous_listener.listen", side_effect=mock_listen), \
         patch("voice.continuous_listener.detect_wake_word") as mock_detect, \
         patch("time.sleep") as mock_sleep:

        mock_detect.return_value = {"activated": False, "cleaned_command": ""}

        listener.start(run_in_thread=False)

        # Should have run twice:
        # First: raised error, handled, slept
        # Second: set stop, returned string, exited loop
        assert call_count == 2
        mock_sleep.assert_called_once_with(0.5)


def test_listener_thread_execution():
    """Verify running the listener in a background thread."""
    listener = ContinuousListener()

    # Stub listen to block for a tiny bit and return empty
    def mock_listen():
        time.sleep(0.05)
        return ""

    with patch("voice.continuous_listener.listen", side_effect=mock_listen):
        listener.start(run_in_thread=True)
        assert listener._running is True
        assert listener._thread is not None
        assert listener._thread.is_alive()

        # Let it run for a brief moment
        time.sleep(0.1)

        listener.stop()
        assert listener._running is False

        # Wait for thread to finish
        listener._thread.join(timeout=1.0)
        assert not listener._thread.is_alive()
