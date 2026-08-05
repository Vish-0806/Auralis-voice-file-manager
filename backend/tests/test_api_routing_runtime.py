"""Tests for API Request Routing Runtime (Phase 15.2).

Validates immutable models, enums, exception hierarchy, ABC interfaces,
route registry, route resolver, request dispatcher, routing provider,
routing runtime, lazy singletons, and multithreaded concurrency.
"""

from concurrent.futures import ThreadPoolExecutor
# pyrefly: ignore [missing-import]
import pytest
# pyrefly: ignore [missing-import]
from pydantic import ValidationError

from backend.application.api.routing import (
    ApiRoute,
    DispatchResult,
    DuplicateRouteException,
    IRequestDispatcher,
    IRouteRegistry,
    IRouteResolver,
    IRoutingProvider,
    IRoutingRuntime,
    RequestDispatcher,
    RouteCapabilities,
    RouteContext,
    RouteDiagnostics,
    RouteDispatchException,
    RouteGroup,
    RouteHealth,
    RouteMetadata,
    RouteMethod,
    RouteRegistrationException,
    RouteRegistry,
    RouteResolutionException,
    RouteResolver,
    RouteState,
    RouteStatistics,
    RoutingException,
    RoutingProvider,
    RoutingRuntime,
    RoutingRuntimeState,
    get_routing_provider,
    get_routing_runtime,
    reset_routing_provider,
    reset_routing_runtime,
    set_routing_provider,
    set_routing_runtime,
)


@pytest.fixture(autouse=True)
def _reset_routing_singletons():
    """Reset routing singletons before and after each test."""
    reset_routing_runtime()
    reset_routing_provider()
    yield
    reset_routing_runtime()
    reset_routing_provider()


# --- Enum Tests ---

def test_enum_route_method():
    """Verify RouteMethod enum string values."""
    assert RouteMethod.GET.value == "GET"
    assert RouteMethod.POST.value == "POST"
    assert RouteMethod.PUT.value == "PUT"
    assert RouteMethod.PATCH.value == "PATCH"
    assert RouteMethod.DELETE.value == "DELETE"
    assert RouteMethod.OPTIONS.value == "OPTIONS"
    assert RouteMethod.HEAD.value == "HEAD"
    assert len(RouteMethod) == 7


def test_enum_route_state():
    """Verify RouteState enum values."""
    assert RouteState.UNREGISTERED.value == "UNREGISTERED"
    assert RouteState.REGISTERED.value == "REGISTERED"
    assert RouteState.ACTIVE.value == "ACTIVE"
    assert RouteState.DISABLED.value == "DISABLED"
    assert len(RouteState) == 4


def test_enum_routing_runtime_state():
    """Verify RoutingRuntimeState enum values."""
    assert RoutingRuntimeState.UNINITIALIZED.value == "UNINITIALIZED"
    assert RoutingRuntimeState.INITIALIZING.value == "INITIALIZING"
    assert RoutingRuntimeState.READY.value == "READY"
    assert RoutingRuntimeState.STOPPING.value == "STOPPING"
    assert RoutingRuntimeState.STOPPED.value == "STOPPED"
    assert len(RoutingRuntimeState) == 5


# --- Model Immutability Tests ---

def test_model_immutability_api_route():
    """Verify ApiRoute defaults and immutability."""
    route = ApiRoute(route_id="r1", path="/v1/test", method=RouteMethod.GET)
    assert route.route_id == "r1"
    assert route.path == "/v1/test"
    assert route.state == RouteState.ACTIVE

    with pytest.raises(ValidationError):
        route.path = "/v1/new"  # type: ignore[attr-defined]


def test_model_immutability_route_metadata():
    """Verify RouteMetadata defaults and immutability."""
    meta = RouteMetadata(name="TestRoute", summary="Summary text")
    assert meta.name == "TestRoute"
    assert meta.deprecated is False

    with pytest.raises(ValidationError):
        meta.name = "Changed"  # type: ignore[attr-defined]


def test_model_immutability_route_group():
    """Verify RouteGroup defaults and immutability."""
    group = RouteGroup(group_id="g1", name="users")
    assert group.group_id == "g1"
    assert group.name == "users"

    with pytest.raises(ValidationError):
        group.name = "admin"  # type: ignore[attr-defined]


def test_model_immutability_route_context():
    """Verify RouteContext immutability."""
    route = ApiRoute(route_id="r1", path="/v1/users")
    ctx = RouteContext(context_id="ctx_1", route=route)
    assert ctx.context_id == "ctx_1"
    assert ctx.route.route_id == "r1"

    with pytest.raises(ValidationError):
        ctx.context_id = "ctx_2"  # type: ignore[attr-defined]


def test_model_immutability_dispatch_result():
    """Verify DispatchResult defaults and immutability."""
    res = DispatchResult(is_success=True, route_id="r1", path="/v1/test")
    assert res.is_success is True
    assert res.route_id == "r1"

    with pytest.raises(ValidationError):
        res.is_success = False  # type: ignore[attr-defined]


def test_model_immutability_route_capabilities():
    """Verify RouteCapabilities defaults and immutability."""
    caps = RouteCapabilities()
    assert caps.supports_alias is True
    assert caps.supports_groups is True

    with pytest.raises(ValidationError):
        caps.supports_alias = False  # type: ignore[attr-defined]


def test_model_immutability_route_statistics():
    """Verify RouteStatistics defaults and immutability."""
    stats = RouteStatistics()
    assert stats.total_routes == 0

    with pytest.raises(ValidationError):
        stats.total_routes = 5  # type: ignore[attr-defined]


def test_model_immutability_route_health():
    """Verify RouteHealth defaults and immutability."""
    health = RouteHealth()
    assert health.is_healthy is True

    with pytest.raises(ValidationError):
        health.is_healthy = False  # type: ignore[attr-defined]


def test_model_immutability_route_diagnostics():
    """Verify RouteDiagnostics defaults and immutability."""
    diag = RouteDiagnostics()
    assert diag.registered_routes_count == 0

    with pytest.raises(ValidationError):
        diag.registered_routes_count = 10  # type: ignore[attr-defined]


# --- Exception Hierarchy Tests ---

def test_exception_hierarchy():
    """Verify routing exception hierarchy inheritance."""
    assert issubclass(DuplicateRouteException, RouteRegistrationException)
    assert issubclass(RouteRegistrationException, RoutingException)
    assert issubclass(RouteResolutionException, RoutingException)
    assert issubclass(RouteDispatchException, RoutingException)
    assert issubclass(RoutingException, Exception)


# --- Interface Abstraction Tests ---

def test_interfaces_cannot_be_instantiated():
    """Verify abstract base classes raise TypeError on instantiation."""
    with pytest.raises(TypeError):
        IRouteRegistry()  # type: ignore[abstract]

    with pytest.raises(TypeError):
        IRouteResolver()  # type: ignore[abstract]

    with pytest.raises(TypeError):
        IRequestDispatcher()  # type: ignore[abstract]

    with pytest.raises(TypeError):
        IRoutingProvider()  # type: ignore[abstract]

    with pytest.raises(TypeError):
        IRoutingRuntime()  # type: ignore[abstract]


# --- RouteRegistry Tests ---

def test_registry_register_and_lookup():
    """Verify route registration and lookup by ID."""
    registry = RouteRegistry()
    route = ApiRoute(route_id="r1", path="/api/v1/health", method=RouteMethod.GET)
    registered = registry.register(route)

    assert registered.route_id == "r1"
    assert registry.lookup("r1") == route
    assert registry.count() == 1


def test_registry_unregister():
    """Verify route unregistration."""
    registry = RouteRegistry()
    route = ApiRoute(route_id="r1", path="/api/v1/health")
    registry.register(route)

    removed = registry.unregister("r1")
    assert removed == route
    assert registry.lookup("r1") is None
    assert registry.count() == 0


def test_registry_contains_and_count():
    """Verify registry contains check and count tracking."""
    registry = RouteRegistry()
    assert registry.contains("r1") is False
    assert registry.count() == 0

    registry.register(ApiRoute(route_id="r1", path="/p1"))
    assert registry.contains("r1") is True
    assert registry.count() == 1


def test_registry_list_routes_and_groups():
    """Verify list_routes and group aggregation in list_groups."""
    registry = RouteRegistry()
    r1 = ApiRoute(route_id="r1", path="/users", group_name="users")
    r2 = ApiRoute(route_id="r2", path="/users/1", group_name="users")
    r3 = ApiRoute(route_id="r3", path="/files", group_name="files")

    registry.register(r1)
    registry.register(r2)
    registry.register(r3)

    all_routes = registry.list_routes()
    assert len(all_routes) == 3

    groups = registry.list_groups()
    assert len(groups) == 2
    group_names = [g.name for g in groups]
    assert "users" in group_names
    assert "files" in group_names


def test_registry_clear():
    """Verify clearing registry wipes all routes."""
    registry = RouteRegistry()
    registry.register(ApiRoute(route_id="r1", path="/p1"))
    registry.register(ApiRoute(route_id="r2", path="/p2"))
    assert registry.count() == 2

    registry.clear()
    assert registry.count() == 0
    assert len(registry.list_routes()) == 0


def test_registry_duplicate_route_id():
    """Verify DuplicateRouteException on duplicate route_id."""
    registry = RouteRegistry()
    registry.register(ApiRoute(route_id="r1", path="/p1"))

    with pytest.raises(DuplicateRouteException):
        registry.register(ApiRoute(route_id="r1", path="/p2"))


def test_registry_duplicate_path_and_method():
    """Verify DuplicateRouteException on duplicate path + method."""
    registry = RouteRegistry()
    registry.register(ApiRoute(route_id="r1", path="/api/test", method=RouteMethod.GET))

    with pytest.raises(DuplicateRouteException):
        registry.register(ApiRoute(route_id="r2", path="/api/test", method=RouteMethod.GET))


def test_registry_duplicate_alias():
    """Verify DuplicateRouteException on duplicate route alias."""
    registry = RouteRegistry()
    registry.register(ApiRoute(route_id="r1", path="/p1", alias="get_test"))

    with pytest.raises(DuplicateRouteException):
        registry.register(ApiRoute(route_id="r2", path="/p2", alias="get_test"))


# --- RouteResolver Tests ---

def test_resolver_resolve_by_path():
    """Verify RouteResolver lookup by path and method."""
    registry = RouteRegistry()
    route = ApiRoute(route_id="r1", path="/v1/status", method=RouteMethod.GET)
    registry.register(route)

    resolver = RouteResolver(registry=registry)
    resolved = resolver.resolve_by_path("/v1/status", RouteMethod.GET)
    assert resolved == route

    unresolved = resolver.resolve_by_path("/v1/missing", RouteMethod.GET)
    assert unresolved is None


def test_resolver_resolve_by_alias():
    """Verify RouteResolver lookup by alias."""
    registry = RouteRegistry()
    route = ApiRoute(route_id="r1", path="/v1/status", alias="status_route")
    registry.register(route)

    resolver = RouteResolver(registry=registry)
    resolved = resolver.resolve_by_alias("status_route")
    assert resolved == route


def test_resolver_resolve_by_id():
    """Verify RouteResolver lookup by route ID."""
    registry = RouteRegistry()
    route = ApiRoute(route_id="r1", path="/v1/status")
    registry.register(route)

    resolver = RouteResolver(registry=registry)
    assert resolver.resolve_by_id("r1") == route


def test_resolver_resolve_metadata():
    """Verify RouteResolver metadata retrieval."""
    registry = RouteRegistry()
    meta = RouteMetadata(name="StatusApi", summary="Status endpoint")
    route = ApiRoute(route_id="r1", path="/v1/status", metadata=meta)
    registry.register(route)

    resolver = RouteResolver(registry=registry)
    retrieved = resolver.resolve_metadata("r1")
    assert retrieved == meta


# --- RequestDispatcher Tests ---

def test_dispatcher_successful_dispatch():
    """Verify RequestDispatcher context preparation on valid route."""
    registry = RouteRegistry()
    route = ApiRoute(route_id="r1", path="/users/{id}", method=RouteMethod.GET)
    registry.register(route)

    resolver = RouteResolver(registry=registry)
    dispatcher = RequestDispatcher(resolver=resolver)

    result = dispatcher.dispatch(
        path="/users/{id}",
        method=RouteMethod.GET,
        path_params={"id": "42"},
        query_params={"verbose": True},
        headers={"Accept": "application/json"},
    )

    assert result.is_success is True
    assert result.route_id == "r1"
    assert result.context is not None
    assert result.context.path_params == {"id": "42"}
    assert result.context.query_params == {"verbose": True}


def test_dispatcher_unresolved_route_exception():
    """Verify RouteResolutionException when route is missing."""
    dispatcher = RequestDispatcher()
    with pytest.raises(RouteResolutionException):
        dispatcher.dispatch(path="/missing/route", method=RouteMethod.GET)


def test_dispatcher_disabled_route_exception():
    """Verify RouteDispatchException when route state is DISABLED."""
    registry = RouteRegistry()
    route = ApiRoute(
        route_id="r1",
        path="/v1/disabled",
        method=RouteMethod.GET,
        state=RouteState.DISABLED,
    )
    registry.register(route)

    resolver = RouteResolver(registry=registry)
    dispatcher = RequestDispatcher(resolver=resolver)

    with pytest.raises(RouteDispatchException):
        dispatcher.dispatch(path="/v1/disabled", method=RouteMethod.GET)


# --- RoutingProvider Tests ---

def test_provider_lifecycle():
    """Verify RoutingProvider initialize and shutdown transitions."""
    provider = RoutingProvider()
    assert provider.health().state == RoutingRuntimeState.UNINITIALIZED

    health1 = provider.initialize()
    assert health1.state == RoutingRuntimeState.READY
    assert health1.is_healthy is True

    health2 = provider.shutdown()
    assert health2.state == RoutingRuntimeState.STOPPED
    assert health2.is_healthy is False


def test_provider_restart():
    """Verify RoutingProvider restart cycle."""
    provider = RoutingProvider()
    provider.initialize()

    health = provider.restart()
    assert health.state == RoutingRuntimeState.READY
    assert provider.statistics().metrics.get("total_restarts") == 1.0


def test_provider_health_stats_caps_diag():
    """Verify RoutingProvider health, statistics, capabilities, and diagnostics."""
    registry = RouteRegistry()
    registry.register(ApiRoute(route_id="r1", path="/p1"))

    provider = RoutingProvider(registry=registry)
    provider.initialize()

    assert provider.health().is_healthy is True
    assert provider.statistics().total_routes == 1
    assert provider.capabilities().supports_alias is True
    assert provider.diagnostics().registered_routes_count == 1


# --- RoutingRuntime Tests ---

def test_runtime_lifecycle_delegation():
    """Verify RoutingRuntime delegates lifecycle methods to provider."""
    runtime = RoutingRuntime()
    assert runtime.health().state == RoutingRuntimeState.UNINITIALIZED

    runtime.initialize()
    assert runtime.health().state == RoutingRuntimeState.READY

    runtime.shutdown()
    assert runtime.health().state == RoutingRuntimeState.STOPPED


# --- Lazy Singleton Helper Tests ---

def test_lazy_singleton_routing_runtime():
    """Verify get_routing_runtime, set_routing_runtime, and reset_routing_runtime."""
    r1 = get_routing_runtime()
    r2 = get_routing_runtime()
    assert r1 is r2
    assert isinstance(r1, RoutingRuntime)

    custom = RoutingRuntime()
    set_routing_runtime(custom)
    assert get_routing_runtime() is custom

    reset_routing_runtime()
    r3 = get_routing_runtime()
    assert r3 is not custom


def test_lazy_singleton_routing_provider():
    """Verify get_routing_provider, set_routing_provider, and reset_routing_provider."""
    p1 = get_routing_provider()
    p2 = get_routing_provider()
    assert p1 is p2
    assert isinstance(p1, RoutingProvider)

    custom = RoutingProvider()
    set_routing_provider(custom)
    assert get_routing_provider() is custom

    reset_routing_provider()
    p3 = get_routing_provider()
    assert p3 is not custom


# --- Concurrency Tests ---

def test_concurrent_registry_operations():
    """Verify thread-safety of RouteRegistry under concurrent registration."""
    registry = RouteRegistry()

    def register_worker(idx: int):
        registry.register(
            ApiRoute(
                route_id=f"r_{idx}",
                path=f"/path_{idx}",
                method=RouteMethod.GET,
            )
        )

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(register_worker, i) for i in range(40)]
        for f in futures:
            f.result()

    assert registry.count() == 40


def test_concurrent_dispatcher_operations():
    """Verify thread-safety of RequestDispatcher under concurrent dispatches."""
    registry = RouteRegistry()
    registry.register(ApiRoute(route_id="r1", path="/shared/path", method=RouteMethod.GET))

    resolver = RouteResolver(registry=registry)
    dispatcher = RequestDispatcher(resolver=resolver)

    def dispatch_worker(idx: int):
        return dispatcher.dispatch(path="/shared/path", method=RouteMethod.GET)

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(dispatch_worker, i) for i in range(50)]
        results = [f.result() for f in futures]

    assert len(results) == 50
    assert all(r.is_success for r in results)
