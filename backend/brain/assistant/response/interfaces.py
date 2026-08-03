"""Abstract Interfaces for Assistant Response Generation & Streaming (Phase 13.6).

Defines Python ABC abstract interfaces for response coordination, response building,
formatting, stream management, provider aggregation, and runtime orchestration.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from brain.assistant.response.models import (
    AssistantResponse,
    ResponseChunk,
    ResponseContext,
    ResponseFormat,
    ResponseHealth,
    ResponseMetadata,
    ResponseState,
    ResponseStatistics,
    ResponseStream,
    StreamingMode,
)


class IResponseBuilder(ABC):
    """Abstract interface for assembling AssistantResponse domain models."""

    @abstractmethod
    def build_response(
        self,
        request_id: str,
        content: str,
        format_type: ResponseFormat = ResponseFormat.MARKDOWN,
        confidence: float = 1.0,
        metadata: Optional[ResponseMetadata] = None,
    ) -> AssistantResponse:
        """Assemble an immutable AssistantResponse instance with metadata and formatting."""
        pass


class IResponseFormatter(ABC):
    """Abstract interface for formatting response text into Markdown, Plain Text, or JSON."""

    @abstractmethod
    def format_content(
        self,
        content: str,
        format_type: ResponseFormat = ResponseFormat.MARKDOWN,
        metadata: Optional[ResponseMetadata] = None,
    ) -> str:
        """Format raw text content into the specified output format."""
        pass


class IStreamingManager(ABC):
    """Abstract interface for chunking, streaming, and tracking stream state."""

    @abstractmethod
    def create_stream(
        self,
        response: AssistantResponse,
        chunk_size: int = 16,
        mode: StreamingMode = StreamingMode.CHUNK_STREAM,
    ) -> ResponseStream:
        """Create a ResponseStream by partitioning an AssistantResponse into ordered ResponseChunks."""
        pass

    @abstractmethod
    def get_chunks(self, stream: ResponseStream) -> List[ResponseChunk]:
        """Retrieve ordered list of chunks from a ResponseStream."""
        pass


class IResponseCoordinator(ABC):
    """Abstract interface for coordinating response preparation across AI, Dialogue, Decision, and Memory runtimes."""

    @abstractmethod
    def prepare_response_context(
        self,
        request_id: str,
        user_prompt: str,
        ai_runtime: Optional[Any] = None,
        dialogue_runtime: Optional[Any] = None,
        decision_runtime: Optional[Any] = None,
        memory_runtime: Optional[Any] = None,
    ) -> ResponseContext:
        """Synthesize a ResponseContext from registered subsystem runtimes."""
        pass


class IResponseProvider(ABC):
    """Abstract interface aggregating coordinator, builder, formatter, and streaming manager."""

    @property
    @abstractmethod
    def coordinator(self) -> IResponseCoordinator:
        """Get the response coordinator."""
        pass

    @property
    @abstractmethod
    def builder(self) -> IResponseBuilder:
        """Get the response builder."""
        pass

    @property
    @abstractmethod
    def formatter(self) -> IResponseFormatter:
        """Get the response formatter."""
        pass

    @property
    @abstractmethod
    def streaming_manager(self) -> IStreamingManager:
        """Get the streaming manager."""
        pass

    @abstractmethod
    def get_health(self) -> ResponseHealth:
        """Get diagnostic health report."""
        pass

    @abstractmethod
    def get_statistics(self) -> ResponseStatistics:
        """Get aggregated response performance metrics."""
        pass

    @abstractmethod
    def initialize(self) -> None:
        """Initialize provider resources."""
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown provider resources."""
        pass

    @property
    @abstractmethod
    def is_initialized(self) -> bool:
        """Check if provider is initialized."""
        pass


class IResponseRuntime(ABC):
    """Abstract interface for top-level Assistant Response Generation & Streaming Runtime orchestration."""

    @abstractmethod
    def initialize(self) -> None:
        """Initialize response runtime."""
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown response runtime."""
        pass

    @abstractmethod
    def get_health(self) -> ResponseHealth:
        """Get overall health status."""
        pass

    @abstractmethod
    def get_statistics(self) -> ResponseStatistics:
        """Get runtime performance statistics."""
        pass

    @property
    @abstractmethod
    def is_initialized(self) -> bool:
        """Check if runtime is initialized."""
        pass
