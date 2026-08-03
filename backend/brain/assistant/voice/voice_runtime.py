"""Voice Runtime Coordinator for Auralis (Phase 13.7).

Manages voice orchestration runtime lifecycle, provider registration, restart mechanics,
health monitoring, statistics tracking, and thread-safe operations using threading.RLock().
"""

from datetime import datetime, timezone
import logging
import threading
import time
from typing import Optional

from brain.assistant.voice.interfaces import (
    IVoiceProvider,
    IVoiceRuntime,
)
from brain.assistant.voice.models import (
    VoiceCapabilities,
    VoiceHealth,
    VoiceStatistics,
)
from brain.assistant.voice.voice_provider import VoiceProvider

logger = logging.getLogger(__name__)


class VoiceRuntime(IVoiceRuntime):
    """Thread-safe top-level runtime coordinator for Voice Orchestration."""

    def __init__(self, provider: Optional[IVoiceProvider] = None) -> None:
        self._lock = threading.RLock()
        self._provider = provider
        self._initialized = False
        self._start_time: Optional[float] = None

    @property
    def is_initialized(self) -> bool:
        with self._lock:
            return self._initialized

    def get_provider(self) -> Optional[IVoiceProvider]:
        with self._lock:
            return self._provider

    def register_provider(self, provider: IVoiceProvider) -> None:
        """Register a voice provider instance thread-safely."""
        with self._lock:
            if not isinstance(provider, IVoiceProvider):
                raise TypeError("Provider must implement IVoiceProvider interface")
            self._provider = provider
            logger.debug("Registered voice provider: %s", provider)

    def initialize(self) -> None:
        """Initialize the Voice Runtime."""
        with self._lock:
            if self._initialized:
                return

            if self._provider is None:
                self._provider = VoiceProvider()

            if not self._provider.is_initialized:
                self._provider.initialize()

            self._initialized = True
            self._start_time = time.time()
            logger.info("VoiceRuntime initialized successfully")

    def shutdown(self) -> None:
        """Gracefully shut down the Voice Runtime."""
        with self._lock:
            if not self._initialized:
                return

            if self._provider is not None and self._provider.is_initialized:
                self._provider.shutdown()

            self._initialized = False
            self._start_time = None
            logger.info("VoiceRuntime shutdown complete")

    def restart(self) -> None:
        """Restart the Voice Runtime thread-safely."""
        with self._lock:
            logger.info("Restarting VoiceRuntime...")
            self.shutdown()
            self.clear()
            self.initialize()
            logger.info("VoiceRuntime restart complete")

    def clear(self) -> None:
        """Reset voice runtime state and statistics."""
        with self._lock:
            if self._provider is not None and hasattr(self._provider, "clear"):
                self._provider.clear()  # type: ignore[attr-defined]
            self._initialized = False
            self._start_time = None

    def get_health(self) -> VoiceHealth:
        """Return aggregated health status."""
        with self._lock:
            if self._provider is not None:
                return self._provider.get_health()

            healthy = self._initialized
            return VoiceHealth(
                status="READY" if healthy else "UNINITIALIZED",
                healthy=healthy,
                subsystems={"provider": False},
                statistics={},
                detected_issues=[] if healthy else ["No provider registered"],
                checked_at=datetime.now(timezone.utc),
                metadata={},
            )

    def get_statistics(self) -> VoiceStatistics:
        """Return performance and usage statistics."""
        with self._lock:
            if self._provider is not None:
                return self._provider.get_statistics()

            uptime = 0.0
            if self._start_time is not None and self._initialized:
                uptime = max(0.0, time.time() - self._start_time)

            return VoiceStatistics(
                total_sessions_created=0,
                active_sessions=0,
                total_interactions=0,
                speech_to_text_routed=0,
                text_to_speech_routed=0,
                wake_word_triggers=0,
                average_pipeline_latency_ms=0.0,
                uptime_seconds=uptime,
                metadata={},
            )

    def get_capabilities(self) -> VoiceCapabilities:
        """Return voice orchestration capabilities specifications."""
        with self._lock:
            if self._provider is not None:
                return self._provider.get_capabilities()
            return VoiceCapabilities()
