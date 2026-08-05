"""API Request Routing Exceptions (Phase 15.2).

Defines the exception hierarchy for request routing operations, registration,
resolution, dispatching, and duplicate route detection.
"""


class RoutingException(Exception):
    """Base exception for all request routing errors."""

    pass


class RouteRegistrationException(RoutingException):
    """Raised when registering or unregistering a route fails."""

    pass


class RouteResolutionException(RoutingException):
    """Raised when looking up or resolving a route fails."""

    pass


class RouteDispatchException(RoutingException):
    """Raised when preparing or dispatching a request context fails."""

    pass


class DuplicateRouteException(RouteRegistrationException):
    """Raised when attempting to register a duplicate route or route alias."""

    pass
