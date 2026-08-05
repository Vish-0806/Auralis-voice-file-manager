"""API Route Resolver Implementation (Phase 15.2).

Thread-safe route resolver locating API routes by path, method, alias, route ID,
and resolving immutable route metadata.
"""

import logging
from threading import RLock
from typing import Optional

from backend.application.api.routing.interfaces import (
    IRouteRegistry,
    IRouteResolver,
)
from backend.application.api.routing.models import (
    ApiRoute,
    RouteMetadata,
    RouteMethod,
)
from backend.application.api.routing.route_registry import RouteRegistry

logger = logging.getLogger(__name__)


class RouteResolver(IRouteResolver):
    """Thread-safe resolver looking up routes and metadata from IRouteRegistry."""

    def __init__(self, registry: Optional[IRouteRegistry] = None) -> None:
        """Initialize RouteResolver using Constructor Dependency Injection.

        Args:
            registry: Optional IRouteRegistry implementation instance.
        """
        self._lock = RLock()
        self._registry = registry or RouteRegistry()

    def resolve_by_path(
        self, path: str, method: RouteMethod = RouteMethod.GET
    ) -> Optional[ApiRoute]:
        """Resolve an API route by path and HTTP method.

        Args:
            path: Target path string.
            method: RouteMethod enum.

        Returns:
            Optional[ApiRoute]: Resolved ApiRoute model if found, else None.
        """
        with self._lock:
            if hasattr(self._registry, "get_route_by_path_method"):
                return getattr(self._registry, "get_route_by_path_method")(path, method)

            for route in self._registry.list_routes():
                if route.path == path and route.method == method:
                    return route
            return None

    def resolve_by_alias(self, alias: str) -> Optional[ApiRoute]:
        """Resolve an API route by its unique alias.

        Args:
            alias: Route alias string.

        Returns:
            Optional[ApiRoute]: Resolved ApiRoute model if found, else None.
        """
        with self._lock:
            if hasattr(self._registry, "get_route_by_alias"):
                return getattr(self._registry, "get_route_by_alias")(alias)

            for route in self._registry.list_routes():
                if route.alias == alias:
                    return route
            return None

    def resolve_by_id(self, route_id: str) -> Optional[ApiRoute]:
        """Resolve an API route by its route ID.

        Args:
            route_id: Unique route identifier.

        Returns:
            Optional[ApiRoute]: Resolved ApiRoute model if found, else None.
        """
        with self._lock:
            return self._registry.lookup(route_id)

    def resolve_metadata(self, route_id: str) -> Optional[RouteMetadata]:
        """Resolve immutable metadata attached to a route by route ID.

        Args:
            route_id: Unique route identifier.

        Returns:
            Optional[RouteMetadata]: RouteMetadata model if found, else None.
        """
        with self._lock:
            route = self._registry.lookup(route_id)
            if route:
                return route.metadata
            return None
