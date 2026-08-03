"""Assistant Response Generation & Streaming Subsystem for Auralis (Phase 13.6).

Coordinates, prepares, assembles, formats, and streams assistant responses across AI, Dialogue, Decision,
and Memory runtimes without performing LLM inference or network streaming.
"""

from brain.assistant.response.exceptions import (
    FormattingError,
    ResponseException,
    ResponseGenerationError,
    ResponseValidationError,
    StreamingError,
)
from brain.assistant.response.interfaces import (
    IResponseBuilder,
    IResponseCoordinator,
    IResponseFormatter,
    IResponseProvider,
    IResponseRuntime,
    IStreamingManager,
)
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
    ResponseTemplate,
    StreamingMode,
)
from brain.assistant.response.response_builder import ResponseBuilder
from brain.assistant.response.response_coordinator import ResponseCoordinator
from brain.assistant.response.response_formatter import ResponseFormatter
from brain.assistant.response.response_provider import ResponseProvider
from brain.assistant.response.response_runtime import ResponseRuntime
from brain.assistant.response.runtime import (
    get_response_runtime,
    reset_response_runtime,
)
from brain.assistant.response.streaming_manager import StreamingManager

__all__ = [
    # Enums & Models
    "ResponseFormat",
    "ResponseState",
    "StreamingMode",
    "ResponseMetadata",
    "ResponseContext",
    "ResponseChunk",
    "AssistantResponse",
    "ResponseStream",
    "ResponseTemplate",
    "ResponseStatistics",
    "ResponseHealth",
    # Exceptions
    "ResponseException",
    "ResponseGenerationError",
    "StreamingError",
    "FormattingError",
    "ResponseValidationError",
    # Interfaces
    "IResponseBuilder",
    "IResponseFormatter",
    "IStreamingManager",
    "IResponseCoordinator",
    "IResponseProvider",
    "IResponseRuntime",
    # Components & Managers
    "ResponseCoordinator",
    "ResponseBuilder",
    "ResponseFormatter",
    "StreamingManager",
    "ResponseProvider",
    "ResponseRuntime",
    # Singleton accessors
    "get_response_runtime",
    "reset_response_runtime",
]
