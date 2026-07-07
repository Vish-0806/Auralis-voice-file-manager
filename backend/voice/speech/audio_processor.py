"""Audio processor for normalizing, detecting silence, and formatting audio.

Uses the audioop library to manipulate raw PCM data, including calculating RMS
power, scaling volume, changing sample rates, and adding WAV containers.
"""

import audioop
import struct
from typing import Optional, Tuple
from utils.logger import get_logger

logger = get_logger(__name__)


class AudioProcessor:
    """Provides utility methods to process raw PCM audio signals."""

    def normalize(
        self,
        audio_data: bytes,
        sample_width: int = 2,
        target_peak_ratio: float = 0.9,
    ) -> bytes:
        """Normalizes raw PCM audio volume to a target peak amplitude ratio.

        Args:
            audio_data: Raw PCM audio bytes.
            sample_width: Bytes per sample (1, 2, or 4).
            target_peak_ratio: Target fraction of maximum amplitude (0.0 to 1.0).

        Returns:
            Normalized audio bytes.
        """
        if not audio_data:
            return audio_data

        try:
            max_val = audioop.max(audio_data, sample_width)
            if max_val == 0:
                return audio_data

            max_possible = (1 << (8 * sample_width - 1)) - 1
            target_peak = int(max_possible * target_peak_ratio)
            factor = target_peak / max_val

            logger.debug(
                "Normalizing audio: peak=%d, target=%d, factor=%.2f",
                max_val,
                target_peak,
                factor,
            )
            return audioop.mul(audio_data, sample_width, factor)
        except Exception as e:
            logger.error("Failed to normalize audio: %s", e)
            return audio_data

    def is_silent(
        self,
        audio_data: bytes,
        sample_width: int = 2,
        threshold: int = 500,
    ) -> bool:
        """Determines if an audio chunk consists of silence based on RMS.

        Args:
            audio_data: Raw PCM audio bytes.
            sample_width: Bytes per sample (1, 2, or 4).
            threshold: RMS amplitude threshold below which audio is silent.

        Returns:
            True if the audio RMS is below the threshold, False otherwise.
        """
        if not audio_data:
            return True

        try:
            rms = audioop.rms(audio_data, sample_width)
            return rms < threshold
        except Exception as e:
            logger.error("Failed to measure RMS for silence detection: %s", e)
            return True

    def convert_sample_rate(
        self,
        audio_data: bytes,
        from_rate: int,
        to_rate: int,
        sample_width: int = 2,
        channels: int = 1,
    ) -> bytes:
        """Converts the sample rate of raw PCM audio.

        Args:
            audio_data: Raw PCM audio bytes.
            from_rate: Original sample rate in Hz.
            to_rate: Target sample rate in Hz.
            sample_width: Bytes per sample.
            channels: Number of audio channels.

        Returns:
            Sample-rate converted audio bytes.
        """
        if from_rate == to_rate or not audio_data:
            return audio_data

        try:
            state = None
            converted, _ = audioop.ratecv(
                audio_data, sample_width, channels, from_rate, to_rate, state
            )
            return converted
        except Exception as e:
            logger.error("Failed to convert sample rate: %s", e)
            return audio_data

    def convert_sample_width(
        self,
        audio_data: bytes,
        from_width: int,
        to_width: int,
    ) -> bytes:
        """Converts the sample width (bit depth) of raw PCM audio.

        Args:
            audio_data: Raw PCM audio bytes.
            from_width: Original bytes per sample (1, 2, or 4).
            to_width: Target bytes per sample (1, 2, or 4).

        Returns:
            Sample-width converted audio bytes.
        """
        if from_width == to_width or not audio_data:
            return audio_data

        try:
            return audioop.lin2lin(audio_data, from_width, to_width)
        except Exception as e:
            logger.error("Failed to convert sample width: %s", e)
            return audio_data

    def convert_to_mono(
        self,
        audio_data: bytes,
        sample_width: int = 2,
        channels: int = 2,
    ) -> bytes:
        """Converts stereo PCM audio to mono.

        Args:
            audio_data: Raw PCM audio bytes.
            sample_width: Bytes per sample.
            channels: Original channel count.

        Returns:
            Mono audio bytes.
        """
        if channels == 1 or not audio_data:
            return audio_data

        try:
            if channels == 2:
                # Merge stereo to mono by averaging channels
                return audioop.tomono(audio_data, sample_width, 0.5, 0.5)
            else:
                logger.warning(
                    "tomono only supports stereo. Returning original audio for channels: %d",
                    channels,
                )
                return audio_data
        except Exception as e:
            logger.error("Failed to convert stereo to mono: %s", e)
            return audio_data

    def create_wav_header(
        self,
        data_size: int,
        sample_rate: int = 16000,
        sample_width: int = 2,
        channels: int = 1,
    ) -> bytes:
        """Creates a standard 44-byte WAV header for PCM data.

        Args:
            data_size: Size of raw PCM data in bytes.
            sample_rate: Sample rate in Hz.
            sample_width: Bytes per sample.
            channels: Number of channels.

        Returns:
            WAV header bytes.
        """
        byte_rate = sample_rate * channels * sample_width
        block_align = channels * sample_width
        bits_per_sample = sample_width * 8

        return struct.pack(
            "<4sI4s4sIHHIIHH4sI",
            b"RIFF",
            36 + data_size,
            b"WAVE",
            b"fmt ",
            16,  # Subchunk1Size (PCM = 16)
            1,  # AudioFormat (PCM = 1)
            channels,
            sample_rate,
            byte_rate,
            block_align,
            bits_per_sample,
            b"data",
            data_size,
        )

    def prepare_audio(
        self,
        audio_data: bytes,
        sample_rate: int = 16000,
        sample_width: int = 2,
        channels: int = 1,
        normalize: bool = True,
    ) -> bytes:
        """Prepares raw PCM audio for speech-to-text recognition.

        Ensures the audio is mono, optionally normalizes it, and wraps it in a WAV
        container with a proper header.

        Args:
            audio_data: Raw PCM audio bytes.
            sample_rate: Sample rate in Hz.
            sample_width: Bytes per sample.
            channels: Number of input channels.
            normalize: Whether to normalize volume peak levels.

        Returns:
            WAV formatted audio bytes.
        """
        processed_data = audio_data

        # 1. Convert to mono if multi-channel
        if channels > 1:
            processed_data = self.convert_to_mono(
                processed_data, sample_width, channels
            )

        # 2. Normalize peak volume
        if normalize:
            processed_data = self.normalize(processed_data, sample_width)

        # 3. Create WAV header and prepend it
        wav_header = self.create_wav_header(
            data_size=len(processed_data),
            sample_rate=sample_rate,
            sample_width=sample_width,
            channels=1,  # Now mono
        )

        return wav_header + processed_data
