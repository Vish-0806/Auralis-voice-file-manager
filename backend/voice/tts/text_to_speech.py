"""Coordinates speech synthesis from text and triggers audio playback."""

import asyncio
import os
import tempfile
import time
from typing import Any, Optional
from utils.logger import get_logger

# Try importing edge-tts
try:
    import edge_tts
    HAS_EDGE_TTS = True
except ImportError:
    HAS_EDGE_TTS = False

from voice.tts.models import TTSConfiguration, SpeechResponse
from voice.tts.voice_manager import VoiceManager
from voice.tts.audio_output import AudioOutput

logger = get_logger(__name__)


class TextToSpeech:
    """Orchestrates Text-to-Speech synthesis and controls audio play queue."""

    def __init__(
        self,
        config: Optional[TTSConfiguration] = None,
        voice_manager: Optional[VoiceManager] = None,
        audio_output: Optional[AudioOutput] = None,
    ) -> None:
        """Initializes the TextToSpeech coordinator.

        Args:
            config: Subsystem configurations. None uses defaults.
            voice_manager: Voice profile manager. None instantiates default.
            audio_output: Playback audio output controller. None instantiates default.
        """
        self.config = config or TTSConfiguration()
        self.voice_manager = voice_manager or VoiceManager()
        self.audio_output = audio_output or AudioOutput()

    def synthesize(self, text: str) -> SpeechResponse:
        """Converts text into speech, returning a SpeechResponse with audio bytes.

        Args:
            text: Plain text to convert.

        Returns:
            SpeechResponse enclosing audio data and synthesis details.
        """
        if not text or not text.strip():
            return SpeechResponse(
                text="", success=False, error="Text input is empty"
            )

        text_to_speak = text.strip()
        start_time = time.time()
        engine_choice = self.config.engine.lower().strip()

        # 1. Primary: Microsoft Edge TTS
        if engine_choice == "edge-tts" and HAS_EDGE_TTS:
            try:
                voice_id = self.config.voice_id or self.voice_manager.get_default_voice("edge-tts")
                logger.info("Synthesizing text via Edge-TTS (voice ID: %s)", voice_id)

                # Execute Edge-TTS stream asynchronously in a helper event loop
                audio_bytes = self._run_async(self._synthesize_edge(text_to_speak, voice_id))
                latency = time.time() - start_time

                return SpeechResponse(
                    text=text_to_speak,
                    audio_data=audio_bytes,
                    success=True,
                    latency=latency,
                )
            except Exception as e:
                logger.warning(
                    "Edge-TTS synthesis failed, falling back to pyttsx3: %s", e
                )

        # 2. Fallback: pyttsx3 local library
        try:
            logger.info("Synthesizing text via pyttsx3 local engine")
            import pyttsx3

            temp_engine = pyttsx3.init()

            # Set configurations on temporary engine
            if self.config.rate:
                temp_engine.setProperty("rate", self.config.rate)
            if self.config.volume:
                temp_engine.setProperty("volume", self.config.volume)

            voice_id = self.config.voice_id
            if voice_id:
                temp_engine.setProperty("voice", voice_id)

            # Try generating WAV bytes via a temporary file
            fd, temp_file_path = tempfile.mkstemp(suffix=".wav")
            os.close(fd)
            try:
                temp_engine.save_to_file(text_to_speak, temp_file_path)
                temp_engine.runAndWait()

                with open(temp_file_path, "rb") as f:
                    wav_bytes = f.read()

                latency = time.time() - start_time
                return SpeechResponse(
                    text=text_to_speak,
                    audio_data=wav_bytes,
                    success=True,
                    latency=latency,
                )
            finally:
                if os.path.exists(temp_file_path):
                    try:
                        os.remove(temp_file_path)
                    except Exception:
                        pass
        except Exception as e:
            logger.error("pyttsx3 synthesis failed: %s", e)
            latency = time.time() - start_time

            # Return success with no audio bytes as a absolute fallback,
            # letting us attempt direct pyttsx3.say() on audio output.
            return SpeechResponse(
                text=text_to_speak,
                audio_data=None,
                success=False,
                error=f"Local synthesis failed: {e}",
                latency=latency,
            )

    async def _synthesize_edge(self, text: str, voice: str) -> bytes:
        """Helper to call edge_tts Communicate stream asynchronously."""
        communicate = edge_tts.Communicate(text, voice)
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
        return audio_data

    def _run_async(self, coro) -> Any:
        """Runs an async coroutine synchronously on a safe event loop."""
        return asyncio.run(coro)

    def speak(self, text: str, wait: bool = True) -> bool:
        """Synthesizes text and queues it for playback.

        Args:
            text: Plain text to speak.
            wait: If True, blocks the calling thread until playback finishes.

        Returns:
            True if synthesis was queued successfully, False otherwise.
        """
        response = self.synthesize(text)

        # Case A: We successfully generated audio bytes (MP3 or WAV)
        if response.success and response.audio_data:
            audio_format = "wav" if response.audio_data.startswith(b"RIFF") else "mp3"

            def play_task():
                self.audio_output.play_bytes(response.audio_data, format=audio_format)

            self.audio_output.queue_speech(play_task)

        # Case B: Local file synthesis failed, fallback to native pyttsx3 loop
        else:
            logger.warning(
                "No audio bytes generated. Playing via pyttsx3 native queue fallback."
            )

            def play_native_task():
                try:
                    import pyttsx3

                    engine = pyttsx3.init()
                    if self.config.rate:
                        engine.setProperty("rate", self.config.rate)
                    if self.config.volume:
                        engine.setProperty("volume", self.config.volume)
                    if self.config.voice_id:
                        engine.setProperty("voice", self.config.voice_id)

                    self.audio_output.set_active_pyttsx3_engine(engine)
                    # Directly speak to system sound device
                    engine.say(text)
                    engine.runAndWait()
                except Exception as e:
                    logger.error("Native pyttsx3 fallback playback failed: %s", e)
                finally:
                    self.audio_output.clear_active_pyttsx3_engine()

            self.audio_output.queue_speech(play_native_task)

        if wait:
            self.audio_output.wait_until_done()

        return response.success
