"""API Request Routing Runtime Package (Phase 15.2).

Provider-independent Request Routing Runtime establishing route models, exceptions,
ABC interfaces, registry, resolver, request dispatcher, routing provider,
routing runtime coordinator, and singleton accessors.
"""

from backend.application.api.routing.exceptions import (
    DuplicateRouteException,
    RouteDispatchException,
    RouteRegistrationException,
    RouteResolutionException,
    RoutingException,
)
from backend.application.api.routing.interfaces import (
    IRequestDispatcher,
    IRouteRegistry,
    IRouteResolver,
    IRoutingProvider,
    IRoutingRuntime,
)
from backend.application.api.routing.models import (
    ApiRoute,
    DispatchResult,
    RouteCapabilities,
    RouteContext,
    RouteDiagnostics,
    RouteGroup,
    RouteHealth,
    RouteMetadata,
    RouteMethod,
    RouteState,
    RouteStatistics,
    RoutingRuntimeState,
)
from backend.application.api.routing.request_dispatcher import RequestDispatcher
from backend.application.api.routing.route_registry import RouteRegistry
from backend.application.api.routing.route_resolver import RouteResolver
from backend.application.api.routing.routing_provider import RoutingProvider
from backend.application.api.routing.routing_runtime import RoutingRuntime
from backend.application.api.routing.runtime import (
    get_routing_provider,
    get_routing_runtime,
    reset_routing_provider,
    reset_routing_runtime,
    set_routing_provider,
    set_routing_runtime,
)

__all__ = [
    # Models & Enums
    "RouteMethod",
    "RouteState",
    "RoutingRuntimeState",
    "RouteMetadata",
    "ApiRoute",
    "RouteGroup",
    "RouteContext",
    "DispatchResult",
    "RouteCapabilities",
    "RouteStatistics",
    "RouteHealth",
    "RouteDiagnostics",
    # Exceptions
    "RoutingException",
    "RouteRegistrationException",
    "RouteResolutionException",
    "RouteDispatchException",
    "DuplicateRouteException",
    # Interfaces
    "IRouteRegistry",
    "IRouteResolver",
    "IRequestDispatcher",
    "IRoutingProvider",
    "IRoutingRuntime",
    # Implementations
    "RouteRegistry",
    "RouteResolver",
    "RequestDispatcher",
    "RoutingProvider",
    "RoutingRuntime",
    # Runtime Helpers
    "get_routing_runtime",
    "set_routing_runtime",
    "reset_routing_runtime",
    "get_routing_provider",
    "set_routing_provider",
    "reset_routing_provider",
]
