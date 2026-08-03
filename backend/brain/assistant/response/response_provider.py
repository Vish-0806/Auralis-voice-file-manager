"""Response Provider implementation for Auralis (Phase 13.6).

Aggregates ResponseCoordinator, ResponseBuilder, ResponseFormatter, and StreamingManager into a unified provider.
Exposes health diagnostics, performance statistics, and capabilities using constructor dependency injection only.
"""

from datetime import datetime, timezone
import logging
import threading
import time
from typing import Any, Dict, List, Optional

from brain.assistant.response.interfaces import (
    IResponseBuilder,
    IResponseCoordinator,
    IResponseFormatter,
    IResponseProvider,
    IStreamingManager,
)
from brain.assistant.response.models import (
    AssistantResponse,
    ResponseFormat,
    ResponseHealth,
    ResponseMetadata,
    ResponseStatistics,
    ResponseStream,
    StreamingMode,
)
from brain.assistant.response.response_builder import ResponseBuilder
from brain.assistant.response.response_coordinator import ResponseCoordinator
from brain.assistant.response.response_formatter import ResponseFormatter
from brain.assistant.response.streaming_manager import StreamingManager

logger = logging.getLogger(__name__)


class ResponseProvider(IResponseProvider):
    """Aggregating provider for response coordination, assembly, formatting, and stream management."""

    def __init__(
        self,
        coordinator: Optional[IResponseCoordinator] = None,
        builder: Optional[IResponseBuilder] = None,
        formatter: Optional[IResponseFormatter] = None,
        streaming_manager: Optional[IStreamingManager] = None,
    ) -> None:
        """Initializes ResponseProvider using constructor dependency injection only."""
        self._lock = threading.RLock()
        self._formatter = formatter or ResponseFormatter(lock=self._lock)
        self._builder = builder or ResponseBuilder(formatter=self._formatter, lock=self._lock)
        self._coordinator = coordinator or ResponseCoordinator(lock=self._lock)
        self._streaming_manager = streaming_manager or StreamingManager(lock=self._lock)

        self._initialized = False
        self._start_time: Optional[float] = None

        # Performance metrics
        self._total_responses = 0
        self._total_streams = 0
        self._total_chunks = 0
        self._total_latency_ms = 0.0
        self._formats_rendered: Dict[str, int] = {
            ResponseFormat.MARKDOWN.value: 0,
            ResponseFormat.PLAIN_TEXT.value: 0,
            ResponseFormat.JSON.value: 0,
        }

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def coordinator(self) -> IResponseCoordinator:
        with self._lock:
            return self._coordinator

    @property
    def builder(self) -> IResponseBuilder:
        with self._lock:
            return self._builder

    @property
    def formatter(self) -> IResponseFormatter:
        with self._lock:
            return self._formatter

    @property
    def streaming_manager(self) -> IStreamingManager:
        with self._lock:
            return self._streaming_manager

    @property
    def is_initialized(self) -> bool:
        with self._lock:
            return self._initialized

    # ------------------------------------------------------------------
    # Core Operations
    # ------------------------------------------------------------------

    def build_response(
        self,
        request_id: str,
        content: str,
        format_type: ResponseFormat = ResponseFormat.MARKDOWN,
        confidence: float = 1.0,
        metadata: Optional[ResponseMetadata] = None,
    ) -> AssistantResponse:
        """Build response through builder while recording metrics."""
        t0 = time.time()
        res = self._builder.build_response(
            request_id=request_id,
            content=content,
            format_type=format_type,
            confidence=confidence,
            metadata=metadata,
        )
        latency = (time.time() - t0) * 1000.0

        with self._lock:
            self._total_responses += 1
            self._total_latency_ms += latency
            fmt_key = format_type.value if hasattr(format_type, "value") else str(format_type)
            self._formats_rendered[fmt_key] = self._formats_rendered.get(fmt_key, 0) + 1

        return res

    def create_stream(
        self,
        response: AssistantResponse,
        chunk_size: int = 16,
        mode: StreamingMode = StreamingMode.CHUNK_STREAM,
    ) -> ResponseStream:
        """Create stream through streaming manager while recording metrics."""
        stream = self._streaming_manager.create_stream(response, chunk_size=chunk_size, mode=mode)
        with self._lock:
            self._total_streams += 1
            self._total_chunks += stream.total_chunks
        return stream

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def initialize(self) -> None:
        """Initialize provider resources."""
        with self._lock:
            if self._initialized:
                return

            self._initialized = True
            self._start_time = time.time()
            logger.info("ResponseProvider initialized successfully")

    def shutdown(self) -> None:
        """Gracefully shut down provider resources."""
        with self._lock:
            if not self._initialized:
                return

            self._initialized = False
            self._start_time = None
            logger.info("ResponseProvider shutdown complete")

    def clear(self) -> None:
        """Reset provider statistics."""
        with self._lock:
            self._total_responses = 0
            self._total_streams = 0
            self._total_chunks = 0
            self._total_latency_ms = 0.0
            self._formats_rendered = {
                ResponseFormat.MARKDOWN.value: 0,
                ResponseFormat.PLAIN_TEXT.value: 0,
                ResponseFormat.JSON.value: 0,
            }

    # ------------------------------------------------------------------
    # Health & Statistics
    # ------------------------------------------------------------------

    def get_health(self) -> ResponseHealth:
        """Expose real-time diagnostic health snapshot."""
        with self._lock:
            subsystems = {
                "coordinator": self._coordinator is not None,
                "builder": self._builder is not None,
                "formatter": self._formatter is not None,
                "streaming_manager": self._streaming_manager is not None,
            }
            issues: List[str] = []
            if not self._initialized:
                issues.append("ResponseProvider is not initialized")

            healthy = self._initialized and len(issues) == 0

            return ResponseHealth(
                status="READY" if healthy else ("UNINITIALIZED" if not self._initialized else "DEGRADED"),
                healthy=healthy,
                subsystems=subsystems,
                statistics=self.get_statistics().model_dump(),
                detected_issues=issues,
                checked_at=datetime.now(timezone.utc),
                metadata={},
            )

    def get_statistics(self) -> ResponseStatistics:
        """Expose aggregated response performance metrics."""
        with self._lock:
            avg_latency = (self._total_latency_ms / self._total_responses) if self._total_responses > 0 else 0.0

            uptime = 0.0
            if self._start_time is not None and self._initialized:
                uptime = max(0.0, time.time() - self._start_time)

            return ResponseStatistics(
                total_responses_built=self._total_responses,
                total_streams_generated=self._total_streams,
                total_chunks_emitted=self._total_chunks,
                average_response_latency_ms=avg_latency,
                formats_rendered=dict(self._formats_rendered),
                uptime_seconds=uptime,
                metadata={},
            )
