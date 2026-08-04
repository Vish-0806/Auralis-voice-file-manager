"""Service Provider (Phase 14.2.4).

Thread-safe production service resolution engine implementing IServiceProvider.
Supports Singleton caching, Transient instantiation, Factory delegate execution,
Scoped lifetime management, Child container creation, nested scope hierarchies,
scope disposal, signature caching, recursive constructor injection, circular dependency
detection, scope statistics, and resolution diagnostics.
"""

from datetime import datetime, timezone
import inspect
import logging
from threading import RLock, local
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, get_args, get_origin
import uuid

from backend.application.di.exceptions import (
    CircularDependencyException,
    ServiceResolutionException,
)
from backend.application.di.interfaces import IServiceCollection, IServiceProvider
from backend.application.di.models import (
    ContainerDiagnostics,
    ContainerHealth,
    ContainerState,
    ContainerStatistics,
    ServiceLifetime,
)

logger = logging.getLogger(__name__)


class ServiceProvider(IServiceProvider):
    """Production ServiceProvider resolution engine supporting Scoped lifetime & child scopes."""

    def __init__(
        self,
        services: Optional[IServiceCollection] = None,
        singleton_cache: Optional[Dict[Any, Any]] = None,
        parent_scope: Optional["ServiceProvider"] = None,
        scope_id: Optional[str] = None,
        depth: int = 0,
    ) -> None:
        """Initialize ServiceProvider using Constructor Dependency Injection.

        Args:
            services: Optional ServiceCollection containing registered service descriptors.
            singleton_cache: Shared root singleton cache dictionary.
            parent_scope: Optional parent ServiceProvider instance.
            scope_id: Optional scope identifier string.
            depth: Hierarchy depth level (0 for root).
        """
        self._lock = RLock()
        self._services = services
        self._scope_id: str = scope_id or ("root" if depth == 0 else f"scope_{uuid.uuid4().hex[:12]}")
        self._depth: int = depth
        self._creation_time: datetime = datetime.now(timezone.utc)
        self._is_disposed: bool = False
        self._parent_scope: Optional[ServiceProvider] = parent_scope

        # Shared Root Singleton Cache
        self._singleton_cache: Dict[Any, Any] = singleton_cache if singleton_cache is not None else {}

        # Independent Scoped Cache & Signature Cache per scope instance
        self._scoped_cache: Dict[Any, Any] = {}
        self._signature_cache: Dict[Any, List[inspect.Parameter]] = {}
        self._child_scopes: List[ServiceProvider] = []
        self._thread_local = local()

        # Resolution & Scope Statistics Counters
        self.total_resolutions: int = 0
        self.singleton_hits: int = 0
        self.singleton_creations: int = 0
        self.transient_creations: int = 0
        self.scoped_resolutions: int = 0
        self.scoped_creations: int = 0
        self.factory_executions: int = 0
        self.failed_resolutions: int = 0
        self.circular_dependencies: int = 0
        self.cache_hits: int = 0

        # Scope Hierarchy Statistics
        self.scopes_created: int = 1 if depth == 0 else 0
        self.scopes_disposed: int = 0
        self.active_scopes_count: int = 1 if depth == 0 else 0
        self.nested_scopes: int = 0
        self.maximum_scope_depth: int = depth

    @property
    def scope_id(self) -> str:
        """Get scope identifier string."""
        with self._lock:
            return self._scope_id

    @property
    def depth(self) -> int:
        """Get depth of the scope hierarchy (0 for root)."""
        with self._lock:
            return self._depth

    @property
    def is_disposed(self) -> bool:
        """Check if the scope has been disposed."""
        with self._lock:
            return self._is_disposed

    def _get_resolution_stack(self) -> List[Any]:
        """Get thread-local resolution stack for tracking dependency chains."""
        if not hasattr(self._thread_local, "stack"):
            self._thread_local.stack = []
        return self._thread_local.stack

    def _type_name(self, target_type: Any) -> str:
        """Get string representation of a type or alias."""
        if isinstance(target_type, str):
            return target_type
        if hasattr(target_type, "__name__"):
            return target_type.__name__
        return str(target_type)

    def create_scope(self) -> IServiceProvider:
        """Create a new child ServiceProvider instance inheriting registrations and singleton cache.

        Returns:
            IServiceProvider: Scoped child service provider instance.

        Raises:
            ServiceResolutionException: If parent scope is disposed.
        """
        with self._lock:
            if self._is_disposed:
                raise ServiceResolutionException(
                    f"Cannot create child scope from disposed scope '{self._scope_id}'."
                )

            child = ServiceProvider(
                services=self._services,
                singleton_cache=self._singleton_cache,
                parent_scope=self,
                depth=self._depth + 1,
            )

            self._child_scopes.append(child)

            # Update scope hierarchy stats
            self.scopes_created += 1
            self.active_scopes_count += 1
            if self._depth + 1 > 0:
                self.nested_scopes += 1
            if self._depth + 1 > self.maximum_scope_depth:
                self.maximum_scope_depth = self._depth + 1

            logger.info("Created child scope '%s' at depth %d.", child.scope_id, child.depth)
            return child

    def resolve(self, service_type: Any) -> Any:
        """Resolve a service instance by service type.

        Args:
            service_type: Target registered service type or alias.

        Returns:
            Any: Resolved service instance.

        Raises:
            ServiceResolutionException: If scope is disposed, service is missing, or resolution fails.
            CircularDependencyException: If a circular dependency loop is detected.
        """
        with self._lock:
            if self._is_disposed:
                raise ServiceResolutionException(
                    f"Scope '{self._scope_id}' is disposed. Cannot resolve services."
                )
            self.total_resolutions += 1

        stack = self._get_resolution_stack()

        # Check for circular dependencies
        if service_type in stack:
            with self._lock:
                self.circular_dependencies += 1
            chain_str = " -> ".join([self._type_name(t) for t in stack] + [self._type_name(service_type)])
            msg = f"Circular dependency detected: {chain_str}"
            logger.error(msg)
            raise CircularDependencyException(msg)

        descriptor = None
        if self._services:
            if isinstance(service_type, str):
                descriptor = self._services.get_descriptor_by_alias(service_type)
                if not descriptor:
                    for desc in self._services.get_descriptors():
                        if hasattr(desc.service_type, "__name__") and desc.service_type.__name__ == service_type:
                            descriptor = desc
                            break
            else:
                descriptor = self._services.get_descriptor(service_type)

        if not descriptor:
            with self._lock:
                self.failed_resolutions += 1
            raise ServiceResolutionException(
                f"No service descriptor registered for service_type: '{self._type_name(service_type)}'."
            )

        # Check pre-constructed instance
        if descriptor.instance is not None:
            return descriptor.instance

        # Check SINGLETON cache (shared across all scopes)
        if descriptor.lifetime == ServiceLifetime.SINGLETON:
            with self._lock:
                if descriptor.service_type in self._singleton_cache:
                    self.singleton_hits += 1
                    self.cache_hits += 1
                    return self._singleton_cache[descriptor.service_type]

        # Check SCOPED cache (independent per scope instance)
        if descriptor.lifetime == ServiceLifetime.SCOPED:
            with self._lock:
                if descriptor.service_type in self._scoped_cache:
                    self.scoped_resolutions += 1
                    self.cache_hits += 1
                    return self._scoped_cache[descriptor.service_type]

        # Push to resolution stack
        stack.append(service_type)
        try:
            instance = None
            if descriptor.factory is not None:
                with self._lock:
                    self.factory_executions += 1
                instance = descriptor.factory(self)
            else:
                impl_type = descriptor.implementation_type or descriptor.service_type
                instance = self.create_instance(impl_type)

            with self._lock:
                if descriptor.lifetime == ServiceLifetime.SINGLETON:
                    self._singleton_cache[descriptor.service_type] = instance
                    self.singleton_creations += 1
                elif descriptor.lifetime == ServiceLifetime.SCOPED:
                    self._scoped_cache[descriptor.service_type] = instance
                    self.scoped_creations += 1
                    self.scoped_resolutions += 1
                elif descriptor.lifetime == ServiceLifetime.TRANSIENT:
                    self.transient_creations += 1

            return instance
        finally:
            stack.pop()

    def resolve_required(self, service_type: Any) -> Any:
        """Resolve a required service instance, raising exception if missing."""
        return self.resolve(service_type)

    def try_resolve(self, service_type: Any) -> Optional[Any]:
        """Try resolving a service instance, returning None if resolution fails."""
        try:
            return self.resolve(service_type)
        except ServiceResolutionException:
            return None

    def resolve_all(self, service_type: Any) -> Tuple[Any, ...]:
        """Resolve all registered instances for a service type."""
        if not self._services or not self._services.contains(service_type):
            return ()
        try:
            instance = self.resolve(service_type)
            return (instance,)
        except ServiceResolutionException:
            return ()

    def _unwrap_type(self, annotation: Any) -> Tuple[Any, bool]:
        """Unwrap Optional[T] or Union[T, None] annotations."""
        origin = get_origin(annotation)
        if origin is Union:
            args = get_args(annotation)
            non_none_args = [a for a in args if a is not type(None)]
            if len(non_none_args) == 1:
                return non_none_args[0], True
        return annotation, False

    def create_instance(self, implementation_type: Any) -> Any:
        """Construct an instance of implementation_type using recursive constructor DI."""
        if not isinstance(implementation_type, type):
            raise ServiceResolutionException(
                f"Cannot instantiate non-class type: '{implementation_type}'."
            )

        with self._lock:
            if implementation_type not in self._signature_cache:
                init_method = getattr(implementation_type, "__init__", None)
                if init_method is object.__init__:
                    params: List[inspect.Parameter] = []
                else:
                    sig = inspect.signature(init_method)
                    params = [
                        p for name, p in sig.parameters.items()
                        if name != "self" and p.kind not in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
                    ]
                self._signature_cache[implementation_type] = params

            parameters = self._signature_cache[implementation_type]

        kwargs: Dict[str, Any] = {}
        for param in parameters:
            param_type, is_optional = self._unwrap_type(param.annotation)

            target_type = param_type
            if isinstance(param_type, str) and self._services:
                if self._services.contains_alias(param_type):
                    target_type = param_type
                else:
                    for desc in self._services.get_descriptors():
                        if hasattr(desc.service_type, "__name__") and desc.service_type.__name__ == param_type:
                            target_type = desc.service_type
                            break

            resolved = None
            resolved_ok = False

            if target_type is not inspect.Parameter.empty and self._services:
                if self._services.contains(target_type) or (isinstance(target_type, str) and self._services.contains_alias(target_type)):
                    try:
                        resolved = self.resolve(target_type)
                        resolved_ok = True
                    except ServiceResolutionException:
                        resolved_ok = False

            if not resolved_ok:
                if param.default is not inspect.Parameter.empty:
                    kwargs[param.name] = param.default
                elif is_optional:
                    kwargs[param.name] = None
                else:
                    with self._lock:
                        self.failed_resolutions += 1
                    raise ServiceResolutionException(
                        f"Cannot resolve parameter '{param.name}' of type '{self._type_name(param_type)}' for '{implementation_type.__name__}'."
                    )
            else:
                kwargs[param.name] = resolved

        try:
            return implementation_type(**kwargs)
        except Exception as exc:
            with self._lock:
                self.failed_resolutions += 1
            raise ServiceResolutionException(
                f"Failed to instantiate '{implementation_type.__name__}': {exc}"
            ) from exc

    def dispose(self) -> None:
        """Dispose child scopes recursively, clear scoped instances, and mark scope as disposed.

        Leaves shared root singleton cache intact.
        """
        with self._lock:
            if self._is_disposed:
                return

            self._is_disposed = True

            # Recursively dispose child scopes
            for child in list(self._child_scopes):
                child.dispose()
            self._child_scopes.clear()

            # Clear scoped instances & signature cache
            self._scoped_cache.clear()
            self._signature_cache.clear()

            self.scopes_disposed += 1
            if self._parent_scope:
                with self._parent_scope._lock:
                    self._parent_scope.scopes_disposed += 1
                    if self._parent_scope.active_scopes_count > 0:
                        self._parent_scope.active_scopes_count -= 1
            if self.active_scopes_count > 0:
                self.active_scopes_count -= 1

            logger.info("Disposed ServiceProvider scope '%s'.", self._scope_id)

    def health(self) -> ContainerHealth:
        """Get health assessment of the provider."""
        with self._lock:
            is_healthy = not self._is_disposed
            issues = () if is_healthy else (f"Scope '{self._scope_id}' is disposed.",)
            return ContainerHealth(
                is_healthy=is_healthy,
                state=ContainerState.READY if is_healthy else ContainerState.STOPPED,
                issues=issues,
                checked_at=datetime.now(timezone.utc),
            )

    def statistics(self) -> ContainerStatistics:
        """Get resolution statistics of the provider."""
        with self._lock:
            registered = self._services.count() if self._services else 0
            return ContainerStatistics(
                registered_services_count=registered,
                resolved_services_count=self.total_resolutions,
                active_scopes_count=self.active_scopes_count,
                metrics={
                    "total_resolutions": float(self.total_resolutions),
                    "singleton_hits": float(self.singleton_hits),
                    "singleton_creations": float(self.singleton_creations),
                    "transient_creations": float(self.transient_creations),
                    "scoped_resolutions": float(self.scoped_resolutions),
                    "scoped_creations": float(self.scoped_creations),
                    "factory_executions": float(self.factory_executions),
                    "failed_resolutions": float(self.failed_resolutions),
                    "circular_dependencies": float(self.circular_dependencies),
                    "cache_hits": float(self.cache_hits),
                    "scopes_created": float(self.scopes_created),
                    "scopes_disposed": float(self.scopes_disposed),
                    "active_scopes": float(self.active_scopes_count),
                },
            )

    def diagnostics(self) -> ContainerDiagnostics:
        """Get resolution diagnostics snapshot."""
        with self._lock:
            stack = tuple(self._type_name(t) for t in self._get_resolution_stack())
            registered = self._services.count() if self._services else 0

            return ContainerDiagnostics(
                registered_services_count=registered,
                resolved_services_count=self.total_resolutions,
                cached_singleton_count=len(self._singleton_cache),
                active_resolution_stack=stack,
                failed_resolutions_count=self.failed_resolutions,
                circular_dependency_count=self.circular_dependencies,
                active_scope_count=self.active_scopes_count,
                disposed_scope_count=self.scopes_disposed,
                current_scope_id=self._scope_id,
                scope_depth=self._depth,
                scoped_cache_size=len(self._scoped_cache),
                singleton_cache_size=len(self._singleton_cache),
                metrics={
                    "singleton_hits": float(self.singleton_hits),
                    "scoped_hits": float(self.scoped_resolutions - self.scoped_creations),
                    "cache_hits": float(self.cache_hits),
                },
                timestamp=datetime.now(timezone.utc),
            )
