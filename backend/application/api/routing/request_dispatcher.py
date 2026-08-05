"""API Request Dispatcher Implementation (Phase 15.2).

Thread-safe provider-independent dispatcher preparing execution contexts and
validating route states without executing HTTP handlers, networking, or serialization.
"""

from datetime import datetime, timezone
import logging
from threading import RLock
from typing import Any, Dict, Optional
import uuid

from backend.application.api.routing.exceptions import (
    RouteDispatchException,
    RouteResolutionException,
)
from backend.application.api.routing.interfaces import (
    IRequestDispatcher,
    IRouteResolver,
)
from backend.application.api.routing.models import (
    DispatchResult,
    RouteContext,
    RouteMethod,
    RouteState,
)
from backend.application.api.routing.route_resolver import RouteResolver

logger = logging.getLogger(__name__)


class RequestDispatcher(IRequestDispatcher):
    """Thread-safe dispatcher preparing route contexts for matching API routes."""

    def __init__(self, resolver: Optional[IRouteResolver] = None) -> None:
        """Initialize RequestDispatcher using Constructor Dependency Injection.

        Args:
            resolver: Optional IRouteResolver implementation instance.
        """
        self._lock = RLock()
        self._resolver = resolver or RouteResolver()
        self._total_dispatches = 0
        self._failed_dispatches = 0

    def dispatch(
        self,
        path: str,
        method: RouteMethod = RouteMethod.GET,
        path_params: Optional[Dict[str, Any]] = None,
        query_params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> DispatchResult:
        """Prepare route context and return dispatch result.

        Args:
            path: Target route path.
            method: HTTP method enum.
            path_params: Optional extracted path parameters.
            query_params: Optional extracted query parameters.
            headers: Optional request headers dictionary.

        Returns:
            DispatchResult: Prepared immutable dispatch result object.

        Raises:
            RouteResolutionException: If target route cannot be found.
            RouteDispatchException: If target route is disabled or inactive.
        """
        with self._lock:
            self._total_dispatches += 1

            route = self._resolver.resolve_by_path(path=path, method=method)
            if route is None:
                self._failed_dispatches += 1
                raise RouteResolutionException(
                    f"No route found matching path '{path}' and method '{method.value}'."
                )

            if route.state in (RouteState.DISABLED, RouteState.UNREGISTERED):
                self._failed_dispatches += 1
                raise RouteDispatchException(
                    f"Route ID '{route.route_id}' for path '{path}' is inactive (state: {route.state.value})."
                )

            context_id = f"ctx_{uuid.uuid4().hex[:12]}"
            context = RouteContext(
                context_id=context_id,
                route=route,
                path_params=path_params or {},
                query_params=query_params or {},
                headers=headers or {},
                metadata={"dispatched_at_iso": datetime.now(timezone.utc).isoformat()},
            )

            logger.info(
                "Prepared route context '%s' for route ID '%s' [%s].",
                context_id,
                route.route_id,
                method.value,
            )

            return DispatchResult(
                is_success=True,
                route_id=route.route_id,
                path=route.path,
                method=route.method,
                context=context,
                error_message=None,
            )

    def get_dispatch_statistics(self) -> Dict[str, int]:
        """Get internal dispatch counter statistics under lock."""
        with self._lock:
            return {
                "total_dispatches": self._total_dispatches,
                "failed_dispatches": self._failed_dispatches,
                "successful_dispatches": self._total_dispatches - self._failed_dispatches,
            }
