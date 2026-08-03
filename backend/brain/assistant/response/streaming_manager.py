"""Streaming Manager implementation for Auralis (Phase 13.6).

Splits AssistantResponse into ordered ResponseChunks, tracks stream state, and supports FULL_RESPONSE
and CHUNK_STREAM modes without networking calls. Thread-safe using threading.RLock().
"""

from datetime import datetime, timezone
import logging
import threading
from typing import List, Optional

from brain.assistant.response.exceptions import StreamingError
from brain.assistant.response.interfaces import IStreamingManager
from brain.assistant.response.models import (
    AssistantResponse,
    ResponseChunk,
    ResponseStream,
    StreamingMode,
)

logger = logging.getLogger(__name__)


class StreamingManager(IStreamingManager):
    """Thread-safe streaming manager partitioning responses into ordered streams."""

    def __init__(self, lock: Optional[threading.RLock] = None) -> None:
        self._lock = lock or threading.RLock()

    def create_stream(
        self,
        response: AssistantResponse,
        chunk_size: int = 16,
        mode: StreamingMode = StreamingMode.CHUNK_STREAM,
    ) -> ResponseStream:
        """Create a ResponseStream by partitioning an AssistantResponse into ordered ResponseChunks."""
        if not isinstance(response, AssistantResponse):
            raise StreamingError("response must be an instance of AssistantResponse")

        with self._lock:
            content = response.content or ""
            chunks: List[ResponseChunk] = []

            if mode == StreamingMode.FULL_RESPONSE or not content:
                # Emit entire content in a single chunk
                chunks.append(
                    ResponseChunk(
                        response_id=response.response_id,
                        chunk_index=0,
                        text=content,
                        is_final=True,
                        timestamp=datetime.now(timezone.utc),
                    )
                )
            else:
                # Partition content into chunks of chunk_size length
                step = max(1, chunk_size)
                parts = [content[i : i + step] for i in range(0, len(content), step)]

                for idx, part in enumerate(parts):
                    is_last = idx == len(parts) - 1
                    chunks.append(
                        ResponseChunk(
                            response_id=response.response_id,
                            chunk_index=idx,
                            text=part,
                            is_final=is_last,
                            timestamp=datetime.now(timezone.utc),
                        )
                    )

            stream = ResponseStream(
                response_id=response.response_id,
                mode=mode,
                chunks=chunks,
                total_chunks=len(chunks),
                is_complete=True,
                started_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc),
            )

            logger.info("Created ResponseStream id=%s mode=%s chunks=%d", stream.stream_id, mode, len(chunks))
            return stream

    def get_chunks(self, stream: ResponseStream) -> List[ResponseChunk]:
        """Retrieve ordered list of chunks from a ResponseStream."""
        if not isinstance(stream, ResponseStream):
            raise StreamingError("stream must be an instance of ResponseStream")

        with self._lock:
            return list(stream.chunks)
