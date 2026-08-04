"""Dependency Injection Exceptions (Phase 14.2.1).

Defines exception hierarchy for service registration, resolution, circular dependencies,
and validation errors.
"""


class DependencyInjectionException(Exception):
    """Base exception for dependency injection container errors."""

    pass


class ServiceRegistrationException(DependencyInjectionException):
    """Raised when registering a service descriptor fails."""

    pass


class ServiceResolutionException(DependencyInjectionException):
    """Raised when resolving a service fails."""

    pass


class CircularDependencyException(DependencyInjectionException):
    """Raised when a circular dependency chain is detected."""

    pass


class ServiceValidationException(DependencyInjectionException):
    """Raised when service validation rules fail."""

    pass
