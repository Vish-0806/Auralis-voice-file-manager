"""Unit tests for the new modular Wake Word Subsystem."""

import time
from unittest.mock import MagicMock, patch
import pytest
from voice.wake_word.models import WakeWordConfiguration, WakeWordState, WakeWordEvent
from voice.wake_word.detector import WakeWordDetector
from voice.wake_word.listener import WakeWordListener


def test_models_initialization():
    """Verify that wake word models initialize with default values."""
    config = WakeWordConfiguration()
    assert "hey auralis" in config.wake_phrases
    assert config.sample_rate == 16000

    state = WakeWordState()
    assert state.is_listening is False
    assert state.status_message == "idle"

    event = WakeWordEvent(phrase="auralis")
    assert event.phrase == "auralis"
    assert event.confidence == 1.0


def test_detector_text_matching():
    """Verify that detector correctly matches wake phrases in text input."""
    detector = WakeWordDetector()
    
    # Matching cases
    event1 = detector.detect_in_text("Hey Auralis, open downloads")
    assert event1 is not None
    assert event1.phrase == "hey auralis"
    
    event2 = detector.detect_in_text("auralis show files")
    assert event2 is not None
    assert event2.phrase == "auralis"

    # Non-matching cases
    event3 = detector.detect_in_text("open downloads")
    assert event3 is None


def test_detector_simulation():
    """Verify that detector can queue and trigger a simulated wake word."""
    detector = WakeWordDetector()
    detector.simulate_wake_word("hello auralis")
    
    # First chunk should trigger simulated event
    event = detector.process_audio_chunk(b"\x00" * 2048)
    assert event is not None
    assert event.phrase == "hello auralis"

    # Subsequent chunk should not trigger (simulation consumed)
    event2 = detector.process_audio_chunk(b"\x00" * 2048)
    assert event2 is None


def test_detector_callbacks():
    """Verify that registered callbacks are invoked upon wake word detection."""
    detector = WakeWordDetector()
    callback_mock = MagicMock()
    detector.register_callback(callback_mock)

    detector.simulate_wake_word("hey auralis")
    detector.process_audio_chunk(b"\x00" * 2048)

    callback_mock.assert_called_once()
    event = callback_mock.call_args[0][0]
    assert event.phrase == "hey auralis"


def test_detector_event_bus_publication():
    """Verify that detector publishes event to EventBus when configured."""
    mock_bus = MagicMock()
    detector = WakeWordDetector(event_bus=mock_bus)

    detector.simulate_wake_word("auralis")
    detector.process_audio_chunk(b"\x00" * 2048)

    mock_bus.publish_envelope.assert_called_once()
    envelope = mock_bus.publish_envelope.call_args[0][0]
    assert envelope.event_type == "voice.wake_word_detected"
    assert envelope.payload["phrase"] == "auralis"


def test_listener_start_stop_simulated():
    """Verify listener start, execution, and stop in simulated mode (no PyAudio)."""
    detector = WakeWordDetector()
    
    # Force mock pyaudio import failure to test simulated fallback
    with patch("builtins.__import__", side_effect=ImportError):
        listener = WakeWordListener(detector=detector)
        assert listener.is_running is False
        
        listener.start(run_in_thread=True)
        assert listener.is_running is True
        
        # Let loop execute briefly
        time.sleep(0.1)
        
        listener.stop()
        assert listener.is_running is False


def test_listener_with_pyaudio_mock():
    """Verify listener works with pyaudio mock."""
    detector = WakeWordDetector()
    mock_pyaudio = MagicMock()
    mock_stream = MagicMock()
    mock_pyaudio.return_value.open.return_value = mock_stream
    mock_stream.read.return_value = b"\x00" * 2048

    with patch("pyaudio.PyAudio", mock_pyaudio):
        listener = WakeWordListener(detector=detector)
        listener.start(run_in_thread=True)
        assert listener.is_running is True
        
        time.sleep(0.1)
        
        listener.stop()
        assert listener.is_running is False
        
        mock_pyaudio.return_value.open.assert_called_once()
        mock_stream.read.assert_called()
