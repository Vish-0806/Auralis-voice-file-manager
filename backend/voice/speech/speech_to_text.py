"""Speech-to-text recognition coordinator.

Orchestrates voice capture from a microphone, manages silence detection and timeouts,
processes audio via the AudioProcessor, and transcribes using the selected backend
(faster-whisper offline, or SpeechRecognition API fallback).
"""

import io
import time
from typing import Optional
from utils.logger import get_logger

# Import Speech Recognition packages
import speech_recognition as sr

# Try importing faster-whisper for offline speech-to-text
try:
    from faster_whisper import WhisperModel
    HAS_FASTER_WHISPER = True
except ImportError:
    HAS_FASTER_WHISPER = False

from voice.speech.models import SpeechConfiguration, SpeechRequest, SpeechResult
from voice.speech.microphone import Microphone
from voice.speech.audio_processor import AudioProcessor

logger = get_logger(__name__)


class SpeechToText:
    """Manages recording orchestration and transcribes voice input to text."""

    def __init__(self, config: Optional[SpeechConfiguration] = None) -> None:
        """Initializes the SpeechToText engine.

        Args:
            config: Subsystem configuration options. None uses defaults.
        """
        self.config = config or SpeechConfiguration()
        self.processor = AudioProcessor()

        self._whisper_model: Optional[WhisperModel] = None
        self._speech_recognizer: Optional[sr.Recognizer] = None

        self._init_backend()

    def _init_backend(self) -> None:
        """Initializes the configured speech recognition backend."""
        backend_choice = self.config.backend.lower()

        if backend_choice == "faster-whisper" and HAS_FASTER_WHISPER:
            try:
                logger.info(
                    "Initializing Faster-Whisper backend with model: %s",
                    self.config.model_size,
                )
                # Attempt to load model on CPU/GPU as appropriate
                self._whisper_model = WhisperModel(
                    self.config.model_size,
                    device="auto",
                    compute_type="default",
                )
                return
            except Exception as e:
                logger.warning(
                    "Failed to initialize Faster-Whisper. Falling back to SpeechRecognition: %s",
                    e,
                )

        # Fallback to standard SpeechRecognition
        logger.info("Initializing SpeechRecognition backend (Google API fallback)")
        self._speech_recognizer = sr.Recognizer()

    def transcribe(self, request: SpeechRequest) -> SpeechResult:
        """Transcribes raw or WAV audio bytes to lowercase text.

        Args:
            request: SpeechRequest containing audio bytes and parameters.

        Returns:
            SpeechResult wrapping transcription details.
        """
        start_time = time.time()
        audio_bytes = request.audio_data

        # Ensure the audio bytes have a WAV header. If it's short, it might be raw PCM.
        # Standard WAV headers are 44 bytes long and start with b'RIFF'.
        if not audio_bytes.startswith(b"RIFF"):
            logger.debug("Prepending WAV header to raw PCM data for transcription")
            audio_bytes = self.processor.prepare_audio(
                audio_bytes,
                sample_rate=request.sample_rate,
                sample_width=request.sample_width,
                channels=request.channels,
                normalize=True,
            )

        # 1. Faster-Whisper transcription
        if self._whisper_model is not None:
            try:
                logger.info("Transcribing using Faster-Whisper")
                wav_io = io.BytesIO(audio_bytes)
                segments, info = self._whisper_model.transcribe(
                    wav_io, language=self.config.language
                )
                text = " ".join([segment.text for segment in segments]).strip()
                latency = time.time() - start_time
                logger.info("Transcription completed in %.2fs", latency)
                return SpeechResult(
                    text=text.lower(),
                    success=True,
                    latency=latency,
                )
            except Exception as e:
                logger.error("Faster-Whisper transcription error: %s", e)
                # Fallback to SpeechRecognition if model failed mid-run
                if self._speech_recognizer is None:
                    self._speech_recognizer = sr.Recognizer()

        # 2. SpeechRecognition fallback
        if self._speech_recognizer is not None:
            try:
                logger.info("Transcribing using SpeechRecognition (Google API)")
                wav_io = io.BytesIO(audio_bytes)
                with sr.AudioFile(wav_io) as source:
                    audio = self._speech_recognizer.record(source)

                # Recognize using Google Web Speech API (free, no key required)
                text = self._speech_recognizer.recognize_google(
                    audio, language=self.config.language
                )
                latency = time.time() - start_time
                logger.info("Transcription completed in %.2fs", latency)
                return SpeechResult(
                    text=text.lower(),
                    success=True,
                    latency=latency,
                )
            except sr.UnknownValueError:
                latency = time.time() - start_time
                logger.warning("SpeechRecognition could not understand audio")
                return SpeechResult(
                    text="",
                    success=False,
                    error="Speech not understood",
                    latency=latency,
                )
            except sr.RequestError as e:
                latency = time.time() - start_time
                logger.error("SpeechRecognition service error: %s", e)
                return SpeechResult(
                    text=None,
                    success=False,
                    error=f"Service request error: {e}",
                    latency=latency,
                )
            except Exception as e:
                latency = time.time() - start_time
                logger.error("Unexpected SpeechRecognition error: %s", e)
                return SpeechResult(
                    text=None,
                    success=False,
                    error=f"Unexpected error: {e}",
                    latency=latency,
                )

        latency = time.time() - start_time
        return SpeechResult(
            text=None,
            success=False,
            error="No recognition backend initialized",
            latency=latency,
        )

    def recognize(
        self,
        microphone: Microphone,
        timeout: Optional[float] = None,
        phrase_time_limit: Optional[float] = None,
    ) -> SpeechResult:
        """Captures voice from microphone and transcribes it to text.

        Args:
            microphone: Microphone instance to capture audio.
            timeout: Maximum seconds to wait for initial speech. None uses config.
            phrase_time_limit: Maximum seconds for the phrase. None uses config.

        Returns:
            SpeechResult wrapping transcription details.
        """
        listen_timeout = timeout if timeout is not None else self.config.timeout
        listen_phrase_limit = (
            phrase_time_limit
            if phrase_time_limit is not None
            else self.config.phrase_time_limit
        )

        try:
            microphone.open()
        except Exception as e:
            logger.error("Could not open microphone for listening: %s", e)
            return SpeechResult(
                text=None,
                success=False,
                error=f"Failed to open microphone: {e}",
            )

        logger.info("Microphone opened. Listening...")
        recorded_chunks = []
        speech_started = False
        start_time = time.time()

        # Silence limits calculation
        bytes_per_second = microphone.sample_rate * self.config.sample_width
        silent_bytes_limit = self.config.silence_duration * bytes_per_second
        silent_bytes_acc = 0

        start_listen_time = time.time()

        try:
            while True:
                current_time = time.time()
                elapsed = current_time - start_listen_time

                # Check total phrase limit
                if listen_phrase_limit and elapsed > listen_phrase_limit:
                    logger.info("Phrase time limit reached (%.2fs)", elapsed)
                    break

                try:
                    chunk = microphone.read()
                except Exception as e:
                    logger.error("Error reading chunk: %s", e)
                    break

                if not chunk:
                    time.sleep(0.01)
                    continue

                recorded_chunks.append(chunk)

                # Check silence/speech status
                is_chunk_silent = self.processor.is_silent(
                    chunk,
                    sample_width=self.config.sample_width,
                    threshold=self.config.silence_threshold,
                )

                if not speech_started:
                    if not is_chunk_silent:
                        speech_started = True
                        logger.info("Speech detected. Recording...")
                    elif elapsed > listen_timeout:
                        logger.warning("Listening timeout: No speech detected")
                        return SpeechResult(
                            text=None,
                            success=False,
                            error="Timeout: No speech detected",
                            latency=time.time() - start_time,
                        )
                else:
                    if is_chunk_silent:
                        silent_bytes_acc += len(chunk)
                        if silent_bytes_acc >= silent_bytes_limit:
                            logger.info("Silence detected. Stopping capture.")
                            break
                    else:
                        silent_bytes_acc = 0

        except Exception as e:
            logger.error("Failure during live audio recording: %s", e)
            return SpeechResult(
                text=None,
                success=False,
                error=f"Recording failure: {e}",
                latency=time.time() - start_time,
            )
        finally:
            microphone.close()

        # Compile recorded audio bytes
        raw_pcm = b"".join(recorded_chunks)
        if not raw_pcm:
            return SpeechResult(
                text="",
                success=False,
                error="No audio data recorded",
                latency=time.time() - start_time,
            )

        # Prepare audio: mono, normalized, formatted as WAV
        wav_audio = self.processor.prepare_audio(
            raw_pcm,
            sample_rate=microphone.sample_rate,
            sample_width=self.config.sample_width,
            channels=1,  # PyAudio recording is mono
            normalize=True,
        )

        # Build and dispatch SpeechRequest
        request = SpeechRequest(
            audio_data=wav_audio,
            sample_rate=microphone.sample_rate,
            sample_width=self.config.sample_width,
            channels=1,
        )

        return self.transcribe(request)
