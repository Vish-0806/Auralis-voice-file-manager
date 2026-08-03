"""Assistant Response Generation & Streaming Exception Hierarchy (Phase 13.6).

Defines custom exception classes for response preparation, formatting,
streaming, and validation errors.
"""


class ResponseException(Exception):
    """Base exception class for all Assistant Response Generation & Streaming errors."""

    pass


class ResponseGenerationError(ResponseException):
    """Raised when response coordination or building fails."""

    pass


class StreamingError(ResponseException):
    """Raised when stream initialization, chunk splitting, or sequence tracking fails."""

    pass


class FormattingError(ResponseException):
    """Raised when content formatting (Markdown, Plain Text, JSON) fails."""

    pass


class ResponseValidationError(ResponseException):
    """Raised when invalid parameters or models are supplied to the response subsystem."""

    pass
