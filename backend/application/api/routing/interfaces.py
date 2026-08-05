"""API Request Routing Interfaces (Phase 15.2).

Defines Abstract Base Classes (ABCs) establishing design contracts for the Route Registry,
Route Resolver, Request Dispatcher, Routing Provider, and Routing Runtime.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Tuple

from backend.application.api.routing.models import (
    ApiRoute,
    DispatchResult,
    RouteCapabilities,
    RouteDiagnostics,
    RouteGroup,
    RouteHealth,
    RouteMetadata,
    RouteMethod,
    RouteStatistics,
)


class IRouteRegistry(ABC):
    """Abstract interface for the API Route Registry."""

    @abstractmethod
    def register(self, route: ApiRoute) -> ApiRoute:
        """Register a new API route in the registry.

        Args:
            route: Immutable ApiRoute model.

        Returns:
            ApiRoute: Registered route.

        Raises:
            DuplicateRouteException: If a duplicate path/method, ID, or alias exists.
            RouteRegistrationException: If registration fails.
        """
        raise NotImplementedError

    @abstractmethod
    def unregister(self, route_id: str) -> Optional[ApiRoute]:
        """Unregister an API route by ID.

        Args:
            route_id: Unique route identifier.

        Returns:
            Optional[ApiRoute]: Removed route if present, else None.
        """
        raise NotImplementedError

    @abstractmethod
    def contains(self, route_id: str) -> bool:
        """Check if a route ID is registered.

        Args:
            route_id: Unique route identifier.

        Returns:
            bool: True if present, False otherwise.
        """
        raise NotImplementedError

    @abstractmethod
    def lookup(self, route_id: str) -> Optional[ApiRoute]:
        """Look up a route by its ID.

        Args:
            route_id: Unique route identifier.

        Returns:
            Optional[ApiRoute]: Route model if found, else None.
        """
        raise NotImplementedError

    @abstractmethod
    def list_routes(self) -> Tuple[ApiRoute, ...]:
        """List all currently registered routes.

        Returns:
            Tuple[ApiRoute, ...]: Immutable tuple of registered routes.
        """
        raise NotImplementedError

    @abstractmethod
    def list_groups(self) -> Tuple[RouteGroup, ...]:
        """List all logical route groups.

        Returns:
            Tuple[RouteGroup, ...]: Immutable tuple of route groups.
        """
        raise NotImplementedError

    @abstractmethod
    def count(self) -> int:
        """Get the total count of registered routes.

        Returns:
            int: Route count.
        """
        raise NotImplementedError

    @abstractmethod
    def clear(self) -> None:
        """Clear all registered routes and groups from the registry."""
        raise NotImplementedError


class IRouteResolver(ABC):
    """Abstract interface for the API Route Resolver."""

    @abstractmethod
    def resolve_by_path(
        self, path: str, method: RouteMethod = RouteMethod.GET
    ) -> Optional[ApiRoute]:
        """Resolve an API route by path and method.

        Args:
            path: Target route path.
            method: HTTP method.

        Returns:
            Optional[ApiRoute]: Resolved ApiRoute if found, else None.
        """
        raise NotImplementedError

    @abstractmethod
    def resolve_by_alias(self, alias: str) -> Optional[ApiRoute]:
        """Resolve an API route by alias string.

        Args:
            alias: Unique route alias.

        Returns:
            Optional[ApiRoute]: Resolved ApiRoute if found, else None.
        """
        raise NotImplementedError

    @abstractmethod
    def resolve_by_id(self, route_id: str) -> Optional[ApiRoute]:
        """Resolve an API route by route ID.

        Args:
            route_id: Target route ID.

        Returns:
            Optional[ApiRoute]: Resolved ApiRoute if found, else None.
        """
        raise NotImplementedError

    @abstractmethod
    def resolve_metadata(self, route_id: str) -> Optional[RouteMetadata]:
        """Resolve route metadata by route ID.

        Args:
            route_id: Target route ID.

        Returns:
            Optional[RouteMetadata]: Route metadata if found, else None.
        """
        raise NotImplementedError


class IRequestDispatcher(ABC):
    """Abstract interface for the Request Dispatcher."""

    @abstractmethod
    def dispatch(
        self,
        path: str,
        method: RouteMethod = RouteMethod.GET,
        path_params: Optional[Dict[str, Any]] = None,
        query_params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> DispatchResult:
        """Prepare execution context and dispatch result for a matching route.

        Args:
            path: Target route path.
            method: HTTP method.
            path_params: Optional extracted path parameters.
            query_params: Optional extracted query parameters.
            headers: Optional request headers.

        Returns:
            DispatchResult: Prepared dispatch result object.

        Raises:
            RouteResolutionException: If route cannot be found.
            RouteDispatchException: If route is disabled or invalid.
        """
        raise NotImplementedError


class IRoutingProvider(ABC):
    """Abstract interface for the Routing Provider."""

    @abstractmethod
    def initialize(self) -> RouteHealth:
        """Initialize the routing provider.

        Returns:
            RouteHealth: Updated health snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def shutdown(self) -> RouteHealth:
        """Shutdown the routing provider safely.

        Returns:
            RouteHealth: Updated health snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def restart(self) -> RouteHealth:
        """Restart the routing provider.

        Returns:
            RouteHealth: Updated health snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def health(self) -> RouteHealth:
        """Get health status evaluation snapshot.

        Returns:
            RouteHealth: Health evaluation.
        """
        raise NotImplementedError

    @abstractmethod
    def statistics(self) -> RouteStatistics:
        """Get aggregate metrics and statistics.

        Returns:
            RouteStatistics: Statistics snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def capabilities(self) -> RouteCapabilities:
        """Get declared routing capabilities.

        Returns:
            RouteCapabilities: Capabilities snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def diagnostics(self) -> RouteDiagnostics:
        """Get system diagnostics snapshot.

        Returns:
            RouteDiagnostics: Diagnostics snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def get_registry(self) -> IRouteRegistry:
        """Get encapsulated route registry instance.

        Returns:
            IRouteRegistry: Route registry instance.
        """
        raise NotImplementedError

    @abstractmethod
    def get_resolver(self) -> IRouteResolver:
        """Get encapsulated route resolver instance.

        Returns:
            IRouteResolver: Route resolver instance.
        """
        raise NotImplementedError

    @abstractmethod
    def get_dispatcher(self) -> IRequestDispatcher:
        """Get encapsulated request dispatcher instance.

        Returns:
            IRequestDispatcher: Request dispatcher instance.
        """
        raise NotImplementedError


class IRoutingRuntime(ABC):
    """Abstract interface for the Routing Runtime."""

    @abstractmethod
    def initialize(self) -> RouteHealth:
        """Initialize the routing runtime.

        Returns:
            RouteHealth: Updated health snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def shutdown(self) -> RouteHealth:
        """Shutdown the routing runtime safely.

        Returns:
            RouteHealth: Updated health snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def restart(self) -> RouteHealth:
        """Restart the routing runtime.

        Returns:
            RouteHealth: Updated health snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def health(self) -> RouteHealth:
        """Get health evaluation snapshot.

        Returns:
            RouteHealth: Health evaluation.
        """
        raise NotImplementedError

    @abstractmethod
    def statistics(self) -> RouteStatistics:
        """Get aggregate statistics.

        Returns:
            RouteStatistics: Statistics snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def capabilities(self) -> RouteCapabilities:
        """Get declared routing capabilities.

        Returns:
            RouteCapabilities: Capabilities snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def diagnostics(self) -> RouteDiagnostics:
        """Get system diagnostics snapshot.

        Returns:
            RouteDiagnostics: Diagnostics snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def get_provider(self) -> IRoutingProvider:
        """Get encapsulated routing provider instance.

        Returns:
            IRoutingProvider: Routing provider instance.
        """
        raise NotImplementedError
