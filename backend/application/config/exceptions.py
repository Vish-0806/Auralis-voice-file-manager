"""Configuration Runtime Exception Hierarchy (Phase 14.3.1).

Defines custom exceptions for configuration runtime initialization, validation,
provider coordination, profile management, and source loading errors.
"""


class ConfigurationException(Exception):
    """Base exception for all Configuration Runtime errors."""

    pass


class ConfigurationInitializationError(ConfigurationException):
    """Raised when configuration runtime initialization fails."""

    pass


class ConfigurationValidationError(ConfigurationException):
    """Raised when configuration validation fails."""

    pass


class ConfigurationProviderError(ConfigurationException):
    """Raised when configuration provider encounters a runtime error."""

    pass


class ConfigurationProfileError(ConfigurationException):
    """Raised when configuration profile operations or activations fail."""

    pass


class ConfigurationSourceError(ConfigurationException):
    """Raised when loading or parsing a configuration source fails."""

    pass
