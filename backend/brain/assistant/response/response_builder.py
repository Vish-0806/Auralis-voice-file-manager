"""Response Builder implementation for Auralis (Phase 13.6).

Assembles complete AssistantResponse domain models with citations, confidence scores,
execution summaries, token metrics, response IDs, and timestamps.
Does NOT perform AI text generation. Thread-safe using threading.RLock().
"""

from datetime import datetime, timezone
import logging
import threading
from typing import Optional

from brain.assistant.response.exceptions import ResponseValidationError
from brain.assistant.response.interfaces import IResponseBuilder, IResponseFormatter
from brain.assistant.response.models import (
    AssistantResponse,
    ResponseFormat,
    ResponseMetadata,
    ResponseState,
)
from brain.assistant.response.response_formatter import ResponseFormatter

logger = logging.getLogger(__name__)


class ResponseBuilder(IResponseBuilder):
    """Thread-safe builder assembling immutable AssistantResponse models."""

    def __init__(
        self,
        formatter: Optional[IResponseFormatter] = None,
        lock: Optional[threading.RLock] = None,
    ) -> None:
        self._lock = lock or threading.RLock()
        self._formatter = formatter or ResponseFormatter(lock=self._lock)

    def build_response(
        self,
        request_id: str,
        content: str,
        format_type: ResponseFormat = ResponseFormat.MARKDOWN,
        confidence: float = 1.0,
        metadata: Optional[ResponseMetadata] = None,
    ) -> AssistantResponse:
        """Assemble an immutable AssistantResponse instance with metadata and formatting."""
        if not request_id:
            raise ResponseValidationError("request_id cannot be empty")

        with self._lock:
            meta = metadata or ResponseMetadata()
            formatted = self._formatter.format_content(content, format_type=format_type, metadata=meta)
            token_estimate = max(1, len(content) // 4)

            response = AssistantResponse(
                request_id=request_id,
                content=content,
                formatted_content=formatted,
                format_type=format_type,
                state=ResponseState.COMPLETED,
                confidence=confidence,
                tokens_used=token_estimate,
                latency_ms=0.0,
                metadata=meta,
                timestamp=datetime.now(timezone.utc),
            )

            logger.info("Built AssistantResponse id=%s for req_id=%s (tokens=%d)", response.response_id, request_id, token_estimate)
            return response
