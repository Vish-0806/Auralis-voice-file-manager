"""API Validation Exceptions (Phase 15.5).

Defines the exception hierarchy for schema registration, validation execution,
serialization, and deserialization operations.
"""


class ValidationException(Exception):
    """Base exception for all validation and serialization errors."""

    pass


class SchemaRegistrationException(ValidationException):
    """Raised when registering or looking up a validation schema fails."""

    pass


class ValidationFailureException(ValidationException):
    """Raised when data fails validation against a schema contract."""

    pass


class SerializationException(ValidationException):
    """Raised when object serialization encounters an unhandled error."""

    pass


class DeserializationException(ValidationException):
    """Raised when data deserialization fails."""

    pass
