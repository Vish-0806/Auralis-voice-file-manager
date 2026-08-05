"""API Runtime Exceptions (Phase 15.1).

Defines the exception hierarchy for API runtime operations, provider errors,
initialization failures, configuration issues, and validation errors.
"""


class ApiRuntimeException(Exception):
    """Base exception for all API runtime errors."""

    pass


class ApiInitializationException(ApiRuntimeException):
    """Raised when API runtime or provider initialization fails."""

    pass


class ApiConfigurationException(ApiRuntimeException):
    """Raised when API configuration is invalid or missing."""

    pass


class ApiProviderException(ApiRuntimeException):
    """Raised when API provider operations encounter an error."""

    pass


class ApiValidationException(ApiRuntimeException):
    """Raised when API runtime validation checks fail."""

    pass
