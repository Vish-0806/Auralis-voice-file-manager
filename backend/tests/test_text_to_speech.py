"""Unit tests for the Text-to-Speech engine subsystem."""

import sys
from unittest.mock import MagicMock, patch
# Mock edge_tts module since it is not installed in the test environment
sys.modules["edge_tts"] = MagicMock()

import time
import pytest

from voice.tts.models import TTSConfiguration, SpeechResponse
from voice.tts.voice_manager import VoiceManager
from voice.tts.audio_output import AudioOutput
from voice.tts.text_to_speech import TextToSpeech, HAS_EDGE_TTS


def test_tts_configuration_defaults():
    """Verify that TTSConfiguration initializes with correct defaults."""
    config = TTSConfiguration()
    assert config.engine == "edge-tts"
    assert config.voice_id is None
    assert config.rate == 150
    assert config.volume == 1.0
    assert config.language == "en"


def test_voice_manager_profiles_and_listing():
    """Verify listing voices and managing custom voice profiles."""
    vm = VoiceManager()

    # Verify default profile registrations
    profile_edge = vm.get_profile("default_edge")
    assert profile_edge is not None
    assert profile_edge["engine"] == "edge-tts"

    # Verify listing Edge-TTS neural voices (returns static list)
    voices = vm.list_voices("edge-tts")
    assert len(voices) > 0
    assert voices[0]["id"] == "en-US-AriaNeural"

    # Test custom profile registration
    vm.register_profile("custom_low", {"engine": "pyttsx3", "rate": 100})
    profile_custom = vm.get_profile("custom_low")
    assert profile_custom["rate"] == 100


@patch("pyttsx3.init")
def test_voice_manager_pyttsx3_listing(mock_pyttsx3_init):
    """Verify listing local voices queries pyttsx3 engine."""
    mock_engine = MagicMock()
    mock_pyttsx3_init.return_value = mock_engine

    mock_voice = MagicMock()
    mock_voice.id = "local_voice_0"
    mock_voice.name = "Local Voice"
    mock_voice.gender = "female"
    mock_voice.languages = ["en"]
    mock_engine.getProperty.return_value = [mock_voice]

    vm = VoiceManager()
    voices = vm.list_voices("pyttsx3")

    assert len(voices) == 1
    assert voices[0]["id"] == "local_voice_0"
    mock_engine.getProperty.assert_called_with("voices")


def test_audio_output_queue_and_interruption():
    """Verify queueing tasks and stop/interruption mechanisms on AudioOutput."""
    ao = AudioOutput()
    task_run_count = 0

    def mock_task():
        nonlocal task_run_count
        task_run_count += 1

    # Queue speech
    ao.queue_speech(mock_task)
    ao.wait_until_done()

    assert task_run_count == 1
    assert ao.is_interrupted() is False

    # Test interruption
    ao.queue_speech(mock_task)
    ao.stop()

    # After stop, queue is flushed and interrupted should be True
    assert ao.is_interrupted() is True
    # The worker might or might not have run the second task before stop,
    # but the queue is empty now
    assert ao._queue.empty() is True


@patch("pyttsx3.init")
def test_tts_synthesize_pyttsx3(mock_pyttsx3_init):
    """Verify pyttsx3 WAV synthesis writes to a temp file and returns bytes."""
    mock_engine = MagicMock()
    mock_pyttsx3_init.return_value = mock_engine

    # Mock file reading by patching open
    dummy_wav_bytes = b"RIFF" + b"\x00" * 40 + b"data" + b"\x01" * 10
    config = TTSConfiguration(engine="pyttsx3")
    tts = TextToSpeech(config)

    # We need to simulate that pyttsx3 actually created the temp file
    with patch("os.path.exists", return_value=True), \
         patch("os.remove") as mock_remove:
        
        # Direct byte reading mock helper
        import io
        original_open = open
        def mock_open_helper(file_path, mode="r"):
            if "wav" in str(file_path):
                return io.BytesIO(dummy_wav_bytes)
            return original_open(file_path, mode)

        with patch("builtins.open", side_effect=mock_open_helper):
            response = tts.synthesize("Hello")

            assert response.success is True
            assert response.audio_data == dummy_wav_bytes
            assert response.text == "Hello"
            assert response.latency > 0

            mock_engine.save_to_file.assert_called_once()
            mock_engine.runAndWait.assert_called_once()
            mock_remove.assert_called_once()


@patch("voice.tts.text_to_speech.HAS_EDGE_TTS", True)
@patch("edge_tts.Communicate")
def test_tts_synthesize_edge_tts(mock_communicate_class):
    """Verify Edge-TTS synthesis is called asynchronously and returns MP3 bytes."""
    # Mock Communicate stream
    mock_communicate = MagicMock()
    mock_communicate_class.return_value = mock_communicate

    # Set up async stream chunk
    async def mock_stream_helper():
        yield {"type": "audio", "data": b"MP3_DATA_CHUNK"}

    mock_communicate.stream = mock_stream_helper

    config = TTSConfiguration(engine="edge-tts", voice_id="en-US-AriaNeural")
    tts = TextToSpeech(config)

    response = tts.synthesize("Neural Voice output")

    assert response.success is True
    assert response.audio_data == b"MP3_DATA_CHUNK"
    assert response.text == "Neural Voice output"
    mock_communicate_class.assert_called_with("Neural Voice output", "en-US-AriaNeural")


def test_tts_speak_queues_correctly():
    """Verify that calling speak() queues task on AudioOutput."""
    ao = MagicMock()
    tts = TextToSpeech(audio_output=ao)

    # Mock synthesize to return fake audio bytes
    tts.synthesize = MagicMock(
        return_value=SpeechResponse(
            text="Greetings", audio_data=b"MP3_AUDIO", success=True
        )
    )

    success = tts.speak("Greetings", wait=False)

    assert success is True
    ao.queue_speech.assert_called_once()
    # Check that it waited only if wait is True
    ao.wait_until_done.assert_not_called()
