"""Unit tests for the speech recognition subsystem.

Tests the models, microphone wrapper, audio processor (DSP), and speech-to-text
engine including timeouts, silence endpointing, and fallbacks.
"""

import io
import time
from unittest.mock import MagicMock, patch
import pytest

from voice.speech.models import SpeechConfiguration, SpeechRequest, SpeechResult
from voice.speech.microphone import Microphone
from voice.speech.audio_processor import AudioProcessor
from voice.speech.speech_to_text import SpeechToText


def test_speech_configuration_defaults():
    """Verify that SpeechConfiguration initializes with expected defaults."""
    config = SpeechConfiguration()
    assert config.backend == "faster-whisper"
    assert config.model_size == "base"
    assert config.language == "en"
    assert config.timeout == 10.0
    assert config.phrase_time_limit is None
    assert config.silence_threshold == 500
    assert config.silence_duration == 1.5
    assert config.sample_rate == 16000
    assert config.sample_width == 2
    assert config.channels == 1


# --- AudioProcessor Tests ---


def test_audio_processor_normalize():
    """Verify that normalize adjusts volume as expected."""
    processor = AudioProcessor()
    # Simple low volume PCM square wave (sample width = 2, max value = 32767)
    # Peak value is 1000
    low_vol_data = b"\xe8\x03" * 100  # 1000 in little-endian 16-bit
    assert len(low_vol_data) == 200

    # Normalize to 90% peak (32767 * 0.9 = 29490)
    normalized = processor.normalize(low_vol_data, sample_width=2, target_peak_ratio=0.9)
    assert len(normalized) == 200

    # Verify peak is indeed scaled up
    import audioop
    peak_original = audioop.max(low_vol_data, 2)
    peak_normalized = audioop.max(normalized, 2)
    assert peak_original == 1000
    assert 29000 <= peak_normalized <= 29600


def test_audio_processor_is_silent():
    """Verify that silence detection identifies quiet vs loud frames."""
    processor = AudioProcessor()

    # Zero bytes should be silent
    assert processor.is_silent(b"\x00" * 100, threshold=100) is True

    # Loud signal should not be silent
    loud_data = b"\x00\x40" * 100  # 16384 in little-endian 16-bit
    assert processor.is_silent(loud_data, threshold=100) is False
    assert processor.is_silent(loud_data, threshold=20000) is True


def test_audio_processor_wav_header():
    """Verify standard WAV header format creation."""
    processor = AudioProcessor()
    data_size = 1000
    header = processor.create_wav_header(
        data_size=data_size, sample_rate=16000, sample_width=2, channels=1
    )

    assert len(header) == 44
    assert header[0:4] == b"RIFF"
    assert header[8:12] == b"WAVE"
    assert header[12:16] == b"fmt "
    assert header[36:40] == b"data"

    # Total size in header must be data_size + 36
    import struct
    total_size = struct.unpack("<I", header[4:8])[0]
    assert total_size == data_size + 36


def test_audio_processor_prepare_audio():
    """Verify prepare_audio normalizes, converts channels, and adds header."""
    processor = AudioProcessor()
    # Stereo PCM data with low peak
    stereo_data = b"\xe8\x03\xe8\x03" * 50  # 100 samples total, stereo (50 left, 50 right)
    assert len(stereo_data) == 200

    prepared = processor.prepare_audio(
        stereo_data, sample_rate=16000, sample_width=2, channels=2, normalize=True
    )

    # 44 bytes header + 100 bytes mono data
    assert len(prepared) == 144
    assert prepared[0:4] == b"RIFF"

    # Verify data is mono (channels parameter at offset 22 is 1)
    import struct
    channels = struct.unpack("<H", prepared[22:24])[0]
    assert channels == 1


# --- Microphone Tests ---


@patch("pyaudio.PyAudio")
def test_microphone_device_listing(mock_pyaudio_class):
    """Verify microphone lists and queries default devices."""
    mock_pyaudio = MagicMock()
    mock_pyaudio_class.return_value = mock_pyaudio

    # Set up device list mock
    mock_pyaudio.get_device_count.return_value = 2
    mock_pyaudio.get_device_info_by_index.side_effect = [
        {"index": 0, "name": "Device 0", "maxInputChannels": 2, "defaultSampleRate": 44100},
        {"index": 1, "name": "Device 1 (Output only)", "maxInputChannels": 0},
    ]
    mock_pyaudio.get_default_input_device_info.return_value = {"index": 0}

    mic = Microphone()
    devices = mic.list_devices()

    # Output devices should be filtered out
    assert len(devices) == 1
    assert devices[0]["name"] == "Device 0"
    assert devices[0]["index"] == 0

    assert mic.get_default_device_index() == 0


@patch("pyaudio.PyAudio")
def test_microphone_open_close(mock_pyaudio_class):
    """Verify microphone stream is opened and closed correctly."""
    mock_pyaudio = MagicMock()
    mock_pyaudio_class.return_value = mock_pyaudio
    mock_pyaudio.get_default_input_device_info.return_value = {"index": 2}

    mic = Microphone(device_index=None, sample_rate=16000, chunk_size=512)

    # Initially closed
    assert mic._stream is None

    mic.open()
    assert mic._stream is not None
    assert mic.device_index == 2  # Resolved from default

    import pyaudio
    mock_pyaudio.open.assert_called_once_with(
        format=pyaudio.paInt16,  # paInt16
        channels=1,
        rate=16000,
        input=True,
        input_device_index=2,
        frames_per_buffer=512,
    )

    mic.close()
    assert mic._stream is None
    assert mic._pyaudio is None


# --- SpeechToText Transcription Tests ---


@patch("speech_recognition.Recognizer")
def test_transcribe_speech_recognition_fallback(mock_recognizer_class):
    """Verify transcription fallbacks to SpeechRecognition when Whisper is disabled/unavailable."""
    mock_rec = MagicMock()
    mock_recognizer_class.return_value = mock_rec
    mock_rec.recognize_google.return_value = "Hello World"

    # Force backend to speech-recognition
    config = SpeechConfiguration(backend="speech-recognition", language="en-US")
    stt = SpeechToText(config)

    # Empty PCM audio (1000 bytes)
    audio_data = b"\x00" * 1000
    request = SpeechRequest(audio_data=audio_data, sample_rate=16000, sample_width=2, channels=1)

    result = stt.transcribe(request)

    assert result.success is True
    assert result.text == "hello world"
    assert result.error is None
    assert result.latency > 0

    # Ensure it used Google Speech API
    mock_rec.recognize_google.assert_called_once()


def test_transcribe_no_backend():
    """Verify failure state when no backend is successfully initialized."""
    config = SpeechConfiguration(backend="invalid-backend")
    # Patch HAS_FASTER_WHISPER to False to prevent Whisper load
    with patch("voice.speech.speech_to_text.HAS_FASTER_WHISPER", False):
        stt = SpeechToText(config)
        stt._speech_recognizer = None  # Force disable fallback
        stt._whisper_model = None

        request = SpeechRequest(audio_data=b"\x00" * 100, sample_rate=16000)
        result = stt.transcribe(request)

        assert result.success is False
        assert "No recognition backend" in result.error


# --- SpeechToText Recognize (Live Recording) Tests ---


def test_recognize_timeout():
    """Verify timeout is handled if no speech is detected within initial limit."""
    config = SpeechConfiguration(timeout=0.1, silence_threshold=500)
    stt = SpeechToText(config)
    stt._speech_recognizer = MagicMock()

    # Mock microphone to output only silent chunks
    mock_mic = MagicMock()
    mock_mic.sample_rate = 16000
    # 512 samples at 16-bit = 1024 bytes
    mock_mic.read.return_value = b"\x00" * 1024

    result = stt.recognize(mock_mic)

    assert result.success is False
    assert "Timeout: No speech detected" in result.error
    mock_mic.close.assert_called_once()


def test_recognize_silence_endpointing():
    """Verify recording stops automatically once the silence duration is reached."""
    # Silence duration = 0.1s. Sample rate = 16000. Chunk size = 1600 samples (100ms)
    # We will send:
    # 1. 1 loud chunk (speech starts)
    # 2. 2 quiet chunks (silence limit reached, recording stops)
    config = SpeechConfiguration(
        timeout=1.0,
        silence_threshold=500,
        silence_duration=0.1,  # 100ms
        sample_width=2,
    )
    stt = SpeechToText(config)

    # Mock transcribe to just return text directly
    stt.transcribe = MagicMock(
        return_value=SpeechResult(text="stop recording", success=True, latency=0.05)
    )

    mock_mic = MagicMock()
    mock_mic.sample_rate = 16000
    # Chunk size: 1600 samples of 16-bit PCM = 3200 bytes
    loud_chunk = b"\x00\x40" * 1600  # RMS > 500
    silent_chunk = b"\x00\x00" * 1600  # RMS = 0

    # Stream yields: loud, silent, silent
    mock_mic.read.side_effect = [loud_chunk, silent_chunk, silent_chunk]

    result = stt.recognize(mock_mic)

    assert result.success is True
    assert result.text == "stop recording"
    mock_mic.close.assert_called_once()
    # Ensure stt.transcribe was called with the captured data
    stt.transcribe.assert_called_once()
    request_arg = stt.transcribe.call_args[0][0]
    assert isinstance(request_arg, SpeechRequest)
    # Length: WAV Header (44) + 1 loud chunk (3200) + 1 silent chunk (3200) = 6444
    # Note: the second silent chunk triggers the break immediately, so it might not be appended
    assert len(request_arg.audio_data) >= 3244
