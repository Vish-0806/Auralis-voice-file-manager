"""API Route Registry Implementation (Phase 15.2).

Thread-safe in-memory route registry supporting route registration, alias indexing,
group aggregation, duplicate detection, and registration statistics.
"""

import logging
from threading import RLock
from typing import Dict, Optional, Set, Tuple

from backend.application.api.routing.exceptions import (
    DuplicateRouteException,
)
from backend.application.api.routing.interfaces import IRouteRegistry
from backend.application.api.routing.models import (
    ApiRoute,
    RouteGroup,
    RouteMethod,
)

logger = logging.getLogger(__name__)


class RouteRegistry(IRouteRegistry):
    """Thread-safe registry for storing and querying API route definitions."""

    def __init__(self) -> None:
        """Initialize RouteRegistry using Constructor Dependency Injection."""
        self._lock = RLock()
        self._routes: Dict[str, ApiRoute] = {}
        self._path_methods: Dict[Tuple[str, RouteMethod], str] = {}
        self._aliases: Dict[str, str] = {}

        # Registration Statistics Counters
        self._total_registrations = 0
        self._total_unregistrations = 0
        self._total_clears = 0

    def register(self, route: ApiRoute) -> ApiRoute:
        """Register a new API route in the registry.

        Args:
            route: Immutable ApiRoute instance.

        Returns:
            ApiRoute: Registered route.

        Raises:
            DuplicateRouteException: If route_id, (path, method), or alias already exists.
        """
        with self._lock:
            # Check duplicate route ID
            if route.route_id in self._routes:
                raise DuplicateRouteException(
                    f"Route with ID '{route.route_id}' is already registered."
                )

            # Check duplicate (path, method)
            pm_key = (route.path, route.method)
            if pm_key in self._path_methods:
                existing_id = self._path_methods[pm_key]
                raise DuplicateRouteException(
                    f"Route for path '{route.path}' and method '{route.method.value}' "
                    f"is already registered by route ID '{existing_id}'."
                )

            # Check duplicate alias if provided
            if route.alias:
                if route.alias in self._aliases:
                    existing_id = self._aliases[route.alias]
                    raise DuplicateRouteException(
                        f"Route alias '{route.alias}' is already registered by route ID '{existing_id}'."
                    )

            # Store in internal maps
            self._routes[route.route_id] = route
            self._path_methods[pm_key] = route.route_id
            if route.alias:
                self._aliases[route.alias] = route.route_id

            self._total_registrations += 1
            logger.info(
                "Registered route ID '%s' for path '%s' [%s].",
                route.route_id,
                route.path,
                route.method.value,
            )
            return route

    def unregister(self, route_id: str) -> Optional[ApiRoute]:
        """Unregister an API route by ID.

        Args:
            route_id: Unique route identifier.

        Returns:
            Optional[ApiRoute]: Unregistered route if present, else None.
        """
        with self._lock:
            route = self._routes.pop(route_id, None)
            if route is None:
                return None

            pm_key = (route.path, route.method)
            self._path_methods.pop(pm_key, None)

            if route.alias:
                self._aliases.pop(route.alias, None)

            self._total_unregistrations += 1
            logger.info("Unregistered route ID '%s'.", route_id)
            return route

    def contains(self, route_id: str) -> bool:
        """Check if a route ID is registered.

        Args:
            route_id: Unique route identifier.

        Returns:
            bool: True if present, False otherwise.
        """
        with self._lock:
            return route_id in self._routes

    def lookup(self, route_id: str) -> Optional[ApiRoute]:
        """Look up a route by its ID.

        Args:
            route_id: Unique route identifier.

        Returns:
            Optional[ApiRoute]: Route model if found, else None.
        """
        with self._lock:
            return self._routes.get(route_id)

    def list_routes(self) -> Tuple[ApiRoute, ...]:
        """List all currently registered routes.

        Returns:
            Tuple[ApiRoute, ...]: Immutable tuple of registered routes.
        """
        with self._lock:
            return tuple(self._routes.values())

    def list_groups(self) -> Tuple[RouteGroup, ...]:
        """List all logical route groups, aggregated by group_name.

        Returns:
            Tuple[RouteGroup, ...]: Immutable tuple of route groups.
        """
        with self._lock:
            groups_map: Dict[str, Dict[str, ApiRoute]] = {}
            for route in self._routes.values():
                g_name = route.group_name or "default"
                if g_name not in groups_map:
                    groups_map[g_name] = {}
                groups_map[g_name][route.route_id] = route

            groups = []
            for g_name, r_dict in sorted(groups_map.items()):
                group_routes = tuple(sorted(r_dict.values(), key=lambda r: r.route_id))
                prefix = ""
                if group_routes:
                    prefix = group_routes[0].path
                groups.append(
                    RouteGroup(
                        group_id=f"group_{g_name}",
                        prefix=prefix,
                        name=g_name,
                        routes=group_routes,
                    )
                )

            return tuple(groups)

    def count(self) -> int:
        """Get total count of registered routes.

        Returns:
            int: Number of registered routes.
        """
        with self._lock:
            return len(self._routes)

    def clear(self) -> None:
        """Clear all registered routes and aliases."""
        with self._lock:
            self._routes.clear()
            self._path_methods.clear()
            self._aliases.clear()
            self._total_clears += 1
            logger.info("RouteRegistry cleared.")

    def get_route_by_path_method(
        self, path: str, method: RouteMethod = RouteMethod.GET
    ) -> Optional[ApiRoute]:
        """Internal helper method to query route by path and method under lock."""
        with self._lock:
            route_id = self._path_methods.get((path, method))
            if route_id:
                return self._routes.get(route_id)
            return None

    def get_route_by_alias(self, alias: str) -> Optional[ApiRoute]:
        """Internal helper method to query route by alias under lock."""
        with self._lock:
            route_id = self._aliases.get(alias)
            if route_id:
                return self._routes.get(route_id)
            return None

    def get_statistics_data(self) -> Dict[str, int]:
        """Get internal registration statistics snapshot."""
        with self._lock:
            return {
                "total_registrations": self._total_registrations,
                "total_unregistrations": self._total_unregistrations,
                "total_clears": self._total_clears,
                "current_count": len(self._routes),
                "alias_count": len(self._aliases),
            }
