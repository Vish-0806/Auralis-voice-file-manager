"""Comprehensive unit tests for Phase 14.2.4 Scoped Lifetime & Child Container Management."""

import concurrent.futures
from typing import Optional, Tuple
# pyrefly: ignore [missing-import]
import pytest
# pyrefly: ignore [missing-import]
from pydantic import ValidationError

from backend.application.di.dependency_container import DependencyContainer
from backend.application.di.exceptions import (
    CircularDependencyException,
    DependencyInjectionException,
    ServiceRegistrationException,
    ServiceResolutionException,
    ServiceValidationException,
)
from backend.application.di.interfaces import (
    IDependencyContainer,
    IServiceCollection,
    IServiceDescriptor,
    IServiceProvider,
)
from backend.application.di.models import (
    ContainerCapabilities,
    ContainerConfiguration,
    ContainerContext,
    ContainerDiagnostics,
    ContainerHealth,
    ContainerState,
    ContainerStatistics,
    DependencyGraphNode,
    ServiceDescriptorModel,
    ServiceLifetime,
    ServiceRegistration,
)
from backend.application.di.runtime import (
    get_dependency_container,
    get_service_provider,
    reset_dependency_container,
    reset_service_provider,
    set_dependency_container,
    set_service_provider,
)
from backend.application.di.service_collection import ServiceCollection
from backend.application.di.service_descriptor import ServiceDescriptor
from backend.application.di.service_provider import ServiceProvider


# Dummy service types & implementation classes for testing
class IServiceA:
    pass


class ServiceA(IServiceA):
    pass


class IServiceB:
    pass


class ServiceB(IServiceB):
    def __init__(self, service_a: IServiceA) -> None:
        self.service_a = service_a


class IServiceC:
    pass


class ServiceC(IServiceC):
    def __init__(self, service_b: IServiceB) -> None:
        self.service_b = service_b


class ServiceScoped:
    pass


class ServiceScopedWithDependencies:
    def __init__(self, service_a: IServiceA) -> None:
        self.service_a = service_a


class ServiceWithOptional:
    def __init__(self, service_a: Optional[IServiceA] = None) -> None:
        self.service_a = service_a


class ServiceWithOptionalNoDefault:
    def __init__(self, service_a: Optional[IServiceA]) -> None:
        self.service_a = service_a


class ServiceWithDefault:
    def __init__(self, value: int = 42) -> None:
        self.value = value


class CircularA:
    def __init__(self, b: "CircularB") -> None:
        self.b = b


class CircularB:
    def __init__(self, a: CircularA) -> None:
        self.a = a


class CircularThreeA:
    def __init__(self, b: "CircularThreeB") -> None:
        self.b = b


class CircularThreeB:
    def __init__(self, c: "CircularThreeC") -> None:
        self.c = c


class CircularThreeC:
    def __init__(self, a: CircularThreeA) -> None:
        self.a = a


# ============================================================================
# 1. Models & Enum Tests
# ============================================================================


def test_service_lifetime_enum():
    """Verify ServiceLifetime enum values."""
    assert ServiceLifetime.SINGLETON.value == "SINGLETON"
    assert ServiceLifetime.TRANSIENT.value == "TRANSIENT"
    assert ServiceLifetime.SCOPED.value == "SCOPED"


def test_container_state_enum():
    """Verify ContainerState enum values."""
    assert ContainerState.UNINITIALIZED.value == "UNINITIALIZED"
    assert ContainerState.READY.value == "READY"
    assert ContainerState.STOPPED.value == "STOPPED"


def test_service_descriptor_model_immutability():
    """Verify ServiceDescriptorModel immutability."""
    model = ServiceDescriptorModel(service_type="IServiceA")
    assert model.service_type == "IServiceA"
    assert model.lifetime == ServiceLifetime.SINGLETON

    with pytest.raises(ValidationError):
        model.service_type = "Modified"  # type: ignore[misc]


def test_container_capabilities_model():
    """Verify ContainerCapabilities defaults."""
    caps = ContainerCapabilities()
    assert caps.supports_singleton is True
    assert caps.supports_transient is True
    assert caps.supports_scoped is True
    assert caps.supports_aliases is True
    assert caps.supports_tags is True


def test_container_statistics_and_health_models():
    """Verify ContainerStatistics and ContainerHealth models."""
    stats = ContainerStatistics(registered_services_count=5)
    assert stats.registered_services_count == 5

    health = ContainerHealth(is_healthy=True, state=ContainerState.READY)
    assert health.is_healthy is True
    assert health.state == ContainerState.READY


def test_container_diagnostics_model():
    """Verify ContainerDiagnostics model fields."""
    diag = ContainerDiagnostics(
        registered_services_count=10,
        resolved_services_count=5,
        cached_singleton_count=2,
    )
    assert diag.registered_services_count == 10
    assert diag.resolved_services_count == 5
    assert diag.cached_singleton_count == 2


def test_service_registration_model():
    """Verify ServiceRegistration model."""
    desc_model = ServiceDescriptorModel(service_type="IServiceA")
    reg = ServiceRegistration(service_name="IServiceA", descriptor=desc_model)
    assert reg.service_name == "IServiceA"
    assert reg.descriptor.service_type == "IServiceA"


def test_dependency_graph_node_model():
    """Verify DependencyGraphNode model."""
    node = DependencyGraphNode(
        node_id="node_a",
        service_type="IServiceA",
        dependencies=("IServiceB",),
        lifetime=ServiceLifetime.SINGLETON,
    )
    assert node.node_id == "node_a"
    assert node.dependencies == ("IServiceB",)


def test_container_configuration_and_context_models():
    """Verify ContainerConfiguration and ContainerContext models."""
    config = ContainerConfiguration(container_name="TestContainer")
    assert config.container_name == "TestContainer"

    context = ContainerContext(container_id="test-123")
    assert context.container_id == "test-123"


# ============================================================================
# 2. Exception Hierarchy Tests
# ============================================================================


def test_di_exception_hierarchy():
    """Verify DependencyInjectionException hierarchy subclassing."""
    assert issubclass(ServiceRegistrationException, DependencyInjectionException)
    assert issubclass(ServiceResolutionException, DependencyInjectionException)
    assert issubclass(CircularDependencyException, DependencyInjectionException)
    assert issubclass(ServiceValidationException, DependencyInjectionException)


# ============================================================================
# 3. ABC Interfaces Tests
# ============================================================================


def test_di_interface_instantiation_raises():
    """Verify ABC contracts raise TypeError when instantiated directly."""
    with pytest.raises(TypeError):
        IServiceDescriptor()  # type: ignore[abstract]
    with pytest.raises(TypeError):
        IServiceCollection()  # type: ignore[abstract]
    with pytest.raises(TypeError):
        IServiceProvider()  # type: ignore[abstract]
    with pytest.raises(TypeError):
        IDependencyContainer()  # type: ignore[abstract]


# ============================================================================
# 4. ServiceDescriptor Component Tests
# ============================================================================


def test_service_descriptor_initialization_and_to_model():
    """Verify ServiceDescriptor attributes and model conversion."""
    desc = ServiceDescriptor(
        service_type=IServiceA,
        implementation_type=ServiceA,
        lifetime=ServiceLifetime.SINGLETON,
        aliases=("alias_a",),
        tags=("core",),
        metadata={"tag": "core"},
    )
    assert desc.service_type is IServiceA
    assert desc.implementation_type is ServiceA
    assert desc.lifetime == ServiceLifetime.SINGLETON
    assert desc.aliases == ("alias_a",)
    assert desc.tags == ("core",)

    model = desc.to_model()
    assert model.service_type == "IServiceA"
    assert model.implementation_type == "ServiceA"
    assert model.aliases == ("alias_a",)
    assert model.tags == ("core",)


def test_service_descriptor_factory_and_instance():
    """Verify ServiceDescriptor with factory and pre-constructed instance."""
    dummy_factory = lambda provider: ServiceA()
    dummy_instance = ServiceA()

    desc_factory = ServiceDescriptor(service_type=IServiceA, factory=dummy_factory)
    assert desc_factory.factory is dummy_factory
    assert desc_factory.to_model().has_factory is True

    desc_instance = ServiceDescriptor(service_type=IServiceA, instance=dummy_instance)
    assert desc_instance.instance is dummy_instance
    assert desc_instance.to_model().has_instance is True


def test_service_descriptor_equality_and_hashing():
    """Verify ServiceDescriptor equality and hash functionality."""
    desc1 = ServiceDescriptor(
        service_type=IServiceA,
        implementation_type=ServiceA,
        lifetime=ServiceLifetime.SINGLETON,
        descriptor_id="id_1",
    )
    desc2 = ServiceDescriptor(
        service_type=IServiceA,
        implementation_type=ServiceA,
        lifetime=ServiceLifetime.SINGLETON,
        descriptor_id="id_1",
    )
    desc3 = ServiceDescriptor(
        service_type=IServiceB,
        implementation_type=ServiceB,
        lifetime=ServiceLifetime.TRANSIENT,
        descriptor_id="id_3",
    )

    assert desc1 == desc2
    assert desc1 != desc3
    assert hash(desc1) == hash(desc2)


def test_service_descriptor_hash_set_membership():
    """Verify using ServiceDescriptor in Python sets."""
    desc1 = ServiceDescriptor(service_type=IServiceA, descriptor_id="id_1")
    desc2 = ServiceDescriptor(service_type=IServiceB, descriptor_id="id_2")

    descriptor_set = {desc1, desc2}
    assert len(descriptor_set) == 2
    assert desc1 in descriptor_set


def test_service_descriptor_lifetime_validation():
    """Verify ServiceDescriptor validates lifetime value."""
    with pytest.raises(ServiceRegistrationException):
        ServiceDescriptor(service_type=IServiceA, lifetime="INVALID_LIFETIME")  # type: ignore[arg-type]


def test_service_descriptor_none_service_type_raises():
    """Verify ServiceDescriptor raises exception when service_type is None."""
    with pytest.raises(ServiceRegistrationException):
        ServiceDescriptor(service_type=None)


def test_service_descriptor_metadata_copy_immutability():
    """Verify modifying returned metadata copy does not mutate descriptor."""
    desc = ServiceDescriptor(service_type=IServiceA, metadata={"key": "val"})
    meta_copy = desc.metadata
    meta_copy["key"] = "modified"
    assert desc.metadata["key"] == "val"


# ============================================================================
# 5. ServiceCollection Component Tests
# ============================================================================


def test_service_collection_add_singleton():
    """Verify adding singleton descriptors to ServiceCollection."""
    services = ServiceCollection()
    assert services.add_singleton(IServiceA, ServiceA, aliases=("service_a",), tags=("core",)) is True
    assert services.contains(IServiceA) is True
    assert services.contains_alias("service_a") is True
    assert services.count() == 1


def test_service_collection_add_transient_and_scoped():
    """Verify adding transient and scoped descriptors."""
    services = ServiceCollection()
    assert services.add_transient(IServiceA, ServiceA) is True
    assert services.add_scoped(IServiceB, ServiceB) is True
    assert services.count() == 2


def test_service_collection_duplicate_detection_raises():
    """Verify registering a duplicate service type raises ServiceRegistrationException."""
    services = ServiceCollection()
    services.add_singleton(IServiceA, ServiceA)

    with pytest.raises(ServiceRegistrationException):
        services.add_singleton(IServiceA, ServiceA)


def test_service_collection_replace():
    """Verify replace overwrites an existing service descriptor."""
    services = ServiceCollection()
    services.add_singleton(IServiceA, ServiceA)
    assert services.count() == 1

    new_desc = ServiceDescriptor(service_type=IServiceA, implementation_type=ServiceB)
    assert services.replace(new_desc) is True
    assert services.count() == 1
    assert services.get_descriptor(IServiceA).implementation_type is ServiceB  # type: ignore[union-attr]


def test_service_collection_try_add():
    """Verify try_add adds if missing and returns False if already present."""
    services = ServiceCollection()
    desc1 = ServiceDescriptor(service_type=IServiceA, implementation_type=ServiceA)
    desc2 = ServiceDescriptor(service_type=IServiceA, implementation_type=ServiceB)

    assert services.try_add(desc1) is True
    assert services.try_add(desc2) is False
    assert services.count() == 1


def test_service_collection_alias_conflict_raises():
    """Verify registering duplicate alias for a different service raises ServiceRegistrationException."""
    services = ServiceCollection()
    services.add_singleton(IServiceA, ServiceA, aliases=("common_alias",))

    with pytest.raises(ServiceRegistrationException):
        services.add_singleton(IServiceB, ServiceB, aliases=("common_alias",))


def test_service_collection_register_none_descriptor_raises():
    """Verify register raises ServiceRegistrationException when descriptor is None."""
    services = ServiceCollection()
    with pytest.raises(ServiceRegistrationException):
        services.register(None)  # type: ignore[arg-type]


def test_service_collection_empty_alias_raises():
    """Verify empty string alias raises ServiceRegistrationException."""
    services = ServiceCollection()
    with pytest.raises(ServiceRegistrationException):
        services.add_singleton(IServiceA, ServiceA, aliases=("",))


def test_service_collection_get_descriptor_by_type_and_alias():
    """Verify O(1) descriptor lookup by service_type and alias."""
    services = ServiceCollection()
    services.add_singleton(IServiceA, ServiceA, aliases=("alias_a",))

    desc_by_type = services.get_descriptor(IServiceA)
    desc_by_alias = services.get_descriptor_by_alias("alias_a")

    assert desc_by_type is not None
    assert desc_by_alias is not None
    assert desc_by_type == desc_by_alias


def test_service_collection_get_descriptor_non_existent():
    """Verify get_descriptor returns None for non-existent service_type or alias."""
    services = ServiceCollection()
    assert services.get_descriptor(IServiceA) is None
    assert services.get_descriptor_by_alias("non_existent_alias") is None
    assert services.contains_alias("non_existent_alias") is False
    assert services.contains(IServiceA) is False


def test_service_collection_list_by_lifetime():
    """Verify list_by_lifetime filters service models by lifetime."""
    services = ServiceCollection()
    services.add_singleton(IServiceA, ServiceA)
    services.add_transient(IServiceB, ServiceB)
    services.add_scoped(IServiceC, ServiceC)

    singletons = services.list_by_lifetime(ServiceLifetime.SINGLETON)
    transients = services.list_by_lifetime(ServiceLifetime.TRANSIENT)
    scoped = services.list_by_lifetime(ServiceLifetime.SCOPED)

    assert len(singletons) == 1
    assert singletons[0].service_type == "IServiceA"
    assert len(transients) == 1
    assert transients[0].service_type == "IServiceB"
    assert len(scoped) == 1
    assert scoped[0].service_type == "IServiceC"


def test_service_collection_list_by_lifetime_empty():
    """Verify list_by_lifetime returns empty tuple when no descriptors match lifetime."""
    services = ServiceCollection()
    services.add_singleton(IServiceA, ServiceA)
    assert services.list_by_lifetime(ServiceLifetime.SCOPED) == ()


def test_service_collection_list_aliases():
    """Verify list_aliases returns all registered aliases."""
    services = ServiceCollection()
    services.add_singleton(IServiceA, ServiceA, aliases=("alias_a1", "alias_a2"))
    services.add_transient(IServiceB, ServiceB, aliases=("alias_b",))

    aliases = services.list_aliases()
    assert len(aliases) == 3
    assert set(aliases) == {"alias_a1", "alias_a2", "alias_b"}


def test_service_collection_tags_preservation():
    """Verify descriptor classification tags are preserved in service models."""
    services = ServiceCollection()
    services.add_singleton(IServiceA, ServiceA, tags=("core", "analytics"))
    models = services.list_services()

    assert models[0].tags == ("core", "analytics")


def test_service_collection_remove_and_remove_all():
    """Verify removing descriptors and removing all."""
    services = ServiceCollection()
    services.add_singleton(IServiceA, ServiceA, aliases=("alias_a",))
    services.add_singleton(IServiceB, ServiceB)

    assert services.remove(IServiceA) is True
    assert services.contains(IServiceA) is False
    assert services.contains_alias("alias_a") is False
    assert services.count() == 1
    assert services.remove(IServiceC) is False

    services.remove_all()
    assert services.count() == 0


def test_service_collection_statistics_tracking():
    """Verify ServiceCollection registration statistics counters."""
    services = ServiceCollection()
    services.add_singleton(IServiceA, ServiceA, aliases=("alias_a",))
    services.add_transient(IServiceB, ServiceB)
    services.add_scoped(IServiceC, ServiceC)

    assert services.total_registrations == 3
    assert services.singleton_registrations == 1
    assert services.transient_registrations == 1
    assert services.scoped_registrations == 1
    assert services.aliases_registered == 1

    with pytest.raises(ServiceRegistrationException):
        services.add_singleton(IServiceA, ServiceA)
    assert services.duplicates_rejected == 1


def test_service_collection_get_descriptors_raw_tuple():
    """Verify get_descriptors returns raw ServiceDescriptor objects."""
    services = ServiceCollection()
    services.add_singleton(IServiceA, ServiceA)
    descriptors = services.get_descriptors()

    assert len(descriptors) == 1
    assert isinstance(descriptors[0], ServiceDescriptor)


def test_service_collection_concurrent_registrations():
    """Verify thread-safe concurrent registrations in ServiceCollection."""
    services = ServiceCollection()

    def do_add(i: int):
        services.add_singleton(f"ServiceType_{i}")

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(do_add, i) for i in range(50)]
        concurrent.futures.wait(futures)

    assert services.count() == 50


def test_service_collection_concurrent_removals():
    """Verify thread-safe concurrent removals in ServiceCollection."""
    services = ServiceCollection()
    for i in range(30):
        services.add_singleton(f"ServiceType_{i}")

    def do_remove(i: int):
        return services.remove(f"ServiceType_{i}")

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(do_remove, i) for i in range(30)]
        results = [f.result() for f in futures]

    assert all(results)
    assert services.count() == 0


# ============================================================================
# 6. ServiceProvider Resolution & Lifetime Tests
# ============================================================================


def test_service_provider_singleton_resolution_caching():
    """Verify SINGLETON lifetime services are constructed once and cached."""
    services = ServiceCollection()
    services.add_singleton(IServiceA, ServiceA)
    provider = ServiceProvider(services=services)

    instance1 = provider.resolve(IServiceA)
    instance2 = provider.resolve(IServiceA)

    assert isinstance(instance1, ServiceA)
    assert instance1 is instance2
    assert provider.singleton_hits == 1
    assert provider.singleton_creations == 1


def test_service_provider_transient_resolution_fresh_instances():
    """Verify TRANSIENT lifetime services create a new instance on every resolve."""
    services = ServiceCollection()
    services.add_transient(IServiceA, ServiceA)
    provider = ServiceProvider(services=services)

    instance1 = provider.resolve(IServiceA)
    instance2 = provider.resolve(IServiceA)

    assert isinstance(instance1, ServiceA)
    assert isinstance(instance2, ServiceA)
    assert instance1 is not instance2
    assert provider.transient_creations == 2


def test_service_provider_factory_resolution():
    """Verify factory callable resolution with ServiceProvider parameter."""
    services = ServiceCollection()
    services.add_singleton(IServiceA, ServiceA)
    services.add_singleton(
        IServiceB,
        factory=lambda p: ServiceB(service_a=p.resolve(IServiceA)),
    )
    provider = ServiceProvider(services=services)

    instance_b = provider.resolve(IServiceB)
    assert isinstance(instance_b, ServiceB)
    assert isinstance(instance_b.service_a, ServiceA)
    assert provider.factory_executions == 1


def test_service_provider_recursive_constructor_injection():
    """Verify 2-level and 3-level recursive constructor dependency injection."""
    services = ServiceCollection()
    services.add_singleton(IServiceA, ServiceA)
    services.add_singleton(IServiceB, ServiceB)
    services.add_singleton(IServiceC, ServiceC)
    provider = ServiceProvider(services=services)

    instance_c = provider.resolve(IServiceC)
    assert isinstance(instance_c, ServiceC)
    assert isinstance(instance_c.service_b, ServiceB)
    assert isinstance(instance_c.service_b.service_a, ServiceA)


def test_service_provider_optional_constructor_dependency():
    """Verify resolving constructor with Optional dependency when present and missing."""
    services = ServiceCollection()
    services.add_transient(ServiceWithOptional, ServiceWithOptional)
    provider = ServiceProvider(services=services)

    # Missing Optional dependency -> resolves with None
    obj1 = provider.resolve(ServiceWithOptional)
    assert obj1.service_a is None

    # Register Optional dependency -> resolves with instance
    services.add_singleton(IServiceA, ServiceA)
    obj2 = provider.resolve(ServiceWithOptional)
    assert isinstance(obj2.service_a, ServiceA)


def test_service_provider_resolve_missing_optional_parameter_default_none():
    """Verify resolving constructor with Optional[T] parameter without default value."""
    services = ServiceCollection()
    services.add_transient(ServiceWithOptionalNoDefault, ServiceWithOptionalNoDefault)
    provider = ServiceProvider(services=services)

    obj = provider.resolve(ServiceWithOptionalNoDefault)
    assert obj.service_a is None


def test_service_provider_constructor_default_parameter_fallback():
    """Verify constructor parameters with default values fall back to default when unresolvable."""
    services = ServiceCollection()
    services.add_transient(ServiceWithDefault, ServiceWithDefault)
    provider = ServiceProvider(services=services)

    obj = provider.resolve(ServiceWithDefault)
    assert obj.value == 42


def test_service_provider_missing_dependency_raises():
    """Verify resolving unregistered service or missing required dependency raises ServiceResolutionException."""
    services = ServiceCollection()
    provider = ServiceProvider(services=services)

    with pytest.raises(ServiceResolutionException):
        provider.resolve(IServiceA)

    services.add_singleton(IServiceB, ServiceB)
    with pytest.raises(ServiceResolutionException):
        provider.resolve(IServiceB)


def test_service_provider_create_instance_non_class_raises():
    """Verify calling create_instance with non-class type raises ServiceResolutionException."""
    provider = ServiceProvider()
    with pytest.raises(ServiceResolutionException):
        provider.create_instance(123)  # type: ignore[arg-type]


def test_service_provider_resolve_instance_placeholder():
    """Verify descriptor with pre-constructed instance returns that exact instance."""
    services = ServiceCollection()
    pre_inst = ServiceA()
    services.add_singleton(IServiceA, instance=pre_inst)
    provider = ServiceProvider(services=services)

    assert provider.resolve(IServiceA) is pre_inst


def test_service_provider_circular_dependency_detection_two_nodes():
    """Verify circular dependency detection A -> B -> A raises CircularDependencyException."""
    services = ServiceCollection()
    services.add_transient(CircularA, CircularA)
    services.add_transient(CircularB, CircularB)
    provider = ServiceProvider(services=services)

    with pytest.raises(CircularDependencyException) as exc_info:
        provider.resolve(CircularA)

    assert "Circular dependency detected" in str(exc_info.value)
    assert "CircularA -> CircularB -> CircularA" in str(exc_info.value)


def test_service_provider_circular_dependency_detection_three_nodes():
    """Verify circular dependency detection A -> B -> C -> A raises CircularDependencyException."""
    services = ServiceCollection()
    services.add_transient(CircularThreeA, CircularThreeA)
    services.add_transient(CircularThreeB, CircularThreeB)
    services.add_transient(CircularThreeC, CircularThreeC)
    provider = ServiceProvider(services=services)

    with pytest.raises(CircularDependencyException) as exc_info:
        provider.resolve(CircularThreeA)

    assert "Circular dependency detected" in str(exc_info.value)
    assert "CircularThreeA -> CircularThreeB -> CircularThreeC -> CircularThreeA" in str(exc_info.value)


def test_service_provider_try_resolve():
    """Verify try_resolve returns instance on success and None on failure."""
    services = ServiceCollection()
    services.add_singleton(IServiceA, ServiceA)
    provider = ServiceProvider(services=services)

    assert isinstance(provider.try_resolve(IServiceA), ServiceA)
    assert provider.try_resolve(IServiceC) is None


def test_service_provider_resolve_required():
    """Verify resolve_required resolves service instance or raises exception."""
    services = ServiceCollection()
    services.add_singleton(IServiceA, ServiceA)
    provider = ServiceProvider(services=services)

    assert isinstance(provider.resolve_required(IServiceA), ServiceA)
    with pytest.raises(ServiceResolutionException):
        provider.resolve_required(IServiceB)


def test_service_provider_resolve_all():
    """Verify resolve_all returns tuple of resolved instances."""
    services = ServiceCollection()
    services.add_singleton(IServiceA, ServiceA)
    provider = ServiceProvider(services=services)

    res = provider.resolve_all(IServiceA)
    assert len(res) == 1
    assert isinstance(res[0], ServiceA)

    assert provider.resolve_all(IServiceB) == ()


def test_service_provider_create_instance():
    """Verify create_instance directly instantiates class with DI."""
    services = ServiceCollection()
    services.add_singleton(IServiceA, ServiceA)
    provider = ServiceProvider(services=services)

    instance_b = provider.create_instance(ServiceB)
    assert isinstance(instance_b, ServiceB)
    assert isinstance(instance_b.service_a, ServiceA)


def test_service_provider_resolve_by_alias():
    """Verify resolving services by registered alias string."""
    services = ServiceCollection()
    services.add_singleton(IServiceA, ServiceA, aliases=("service_a_alias",))
    provider = ServiceProvider(services=services)

    instance = provider.resolve("service_a_alias")
    assert isinstance(instance, ServiceA)


def test_service_provider_signature_caching():
    """Verify constructor parameter signatures are cached in _signature_cache."""
    services = ServiceCollection()
    services.add_singleton(IServiceA, ServiceA)
    provider = ServiceProvider(services=services)

    provider.create_instance(ServiceB)
    assert ServiceB in provider._signature_cache
    assert len(provider._signature_cache[ServiceB]) == 1


def test_service_provider_resolution_statistics_and_diagnostics():
    """Verify resolution statistics and detailed diagnostics snapshots."""
    services = ServiceCollection()
    services.add_singleton(IServiceA, ServiceA)
    provider = ServiceProvider(services=services)

    provider.resolve(IServiceA)
    provider.resolve(IServiceA)

    stats = provider.statistics()
    assert stats.resolved_services_count == 2
    assert stats.metrics["singleton_hits"] == 1.0

    diag = provider.diagnostics()
    assert diag.resolved_services_count == 2
    assert diag.cached_singleton_count == 1
    assert diag.active_resolution_stack == ()


def test_service_provider_failed_resolutions_counter():
    """Verify failed_resolutions counter increments on failure."""
    services = ServiceCollection()
    provider = ServiceProvider(services=services)

    with pytest.raises(ServiceResolutionException):
        provider.resolve(IServiceA)

    assert provider.failed_resolutions == 1


# ============================================================================
# 7. Scoped Lifetime & Child Scope Tests (Phase 14.2.4)
# ============================================================================


def test_scoped_service_resolution_same_scope():
    """Verify resolving a SCOPED service within the same child scope returns identical instance."""
    services = ServiceCollection()
    services.add_scoped(ServiceScoped, ServiceScoped)
    root_provider = ServiceProvider(services=services)

    scope1 = root_provider.create_scope()
    inst1 = scope1.resolve(ServiceScoped)
    inst2 = scope1.resolve(ServiceScoped)

    assert isinstance(inst1, ServiceScoped)
    assert inst1 is inst2


def test_scoped_service_resolution_different_scopes():
    """Verify resolving a SCOPED service across distinct child scopes returns different instances."""
    services = ServiceCollection()
    services.add_scoped(ServiceScoped, ServiceScoped)
    root_provider = ServiceProvider(services=services)

    scope1 = root_provider.create_scope()
    scope2 = root_provider.create_scope()

    inst1 = scope1.resolve(ServiceScoped)
    inst2 = scope2.resolve(ServiceScoped)

    assert isinstance(inst1, ServiceScoped)
    assert isinstance(inst2, ServiceScoped)
    assert inst1 is not inst2


def test_scoped_service_resolution_root_provider():
    """Verify resolving a SCOPED service on root provider caches instance in root's scoped cache."""
    services = ServiceCollection()
    services.add_scoped(ServiceScoped, ServiceScoped)
    root_provider = ServiceProvider(services=services)

    inst1 = root_provider.resolve(ServiceScoped)
    inst2 = root_provider.resolve(ServiceScoped)

    assert isinstance(inst1, ServiceScoped)
    assert inst1 is inst2


def test_scoped_service_factory_resolution():
    """Verify SCOPED service registered with factory function resolves scoped instance per scope."""
    services = ServiceCollection()
    services.add_scoped(ServiceScoped, factory=lambda p: ServiceScoped())
    root_provider = ServiceProvider(services=services)

    scope1 = root_provider.create_scope()
    scope2 = root_provider.create_scope()

    inst1 = scope1.resolve(ServiceScoped)
    inst2 = scope2.resolve(ServiceScoped)

    assert inst1 is not inst2
    assert scope1.resolve(ServiceScoped) is inst1


def test_scoped_service_with_constructor_dependencies():
    """Verify SCOPED service depending on SINGLETON and TRANSIENT services resolves correctly."""
    services = ServiceCollection()
    services.add_singleton(IServiceA, ServiceA)
    services.add_scoped(ServiceScopedWithDependencies, ServiceScopedWithDependencies)
    root_provider = ServiceProvider(services=services)

    scope1 = root_provider.create_scope()
    inst = scope1.resolve(ServiceScopedWithDependencies)

    assert isinstance(inst, ServiceScopedWithDependencies)
    assert isinstance(inst.service_a, ServiceA)


def test_child_scope_creation_properties():
    """Verify create_scope properties (scope_id, depth, is_disposed)."""
    root_provider = ServiceProvider()
    assert root_provider.depth == 0
    assert root_provider.scope_id == "root"

    child = root_provider.create_scope()
    assert child.depth == 1
    assert child.is_disposed is False
    assert child.scope_id.startswith("scope_")


def test_nested_scope_hierarchy():
    """Verify nested scope hierarchy Root (depth=0) -> Scope A (depth=1) -> Scope B (depth=2)."""
    root = ServiceProvider()
    scope_a = root.create_scope()
    scope_b = scope_a.create_scope()

    assert root.depth == 0
    assert scope_a.depth == 1
    assert scope_b.depth == 2


def test_shared_singleton_cache_across_nested_scopes():
    """Verify SINGLETON lifetime services resolved in Scope B return the exact same instance in Root and Scope A."""
    services = ServiceCollection()
    services.add_singleton(IServiceA, ServiceA)
    root = ServiceProvider(services=services)
    scope_a = root.create_scope()
    scope_b = scope_a.create_scope()

    inst_b = scope_b.resolve(IServiceA)
    inst_a = scope_a.resolve(IServiceA)
    inst_root = root.resolve(IServiceA)

    assert inst_b is inst_a
    assert inst_a is inst_root


def test_transient_lifetime_across_child_scopes():
    """Verify TRANSIENT lifetime services construct distinct instances across child scopes."""
    services = ServiceCollection()
    services.add_transient(IServiceA, ServiceA)
    root = ServiceProvider(services=services)
    scope_a = root.create_scope()

    inst_root = root.resolve(IServiceA)
    inst_scope = scope_a.resolve(IServiceA)

    assert inst_root is not inst_scope


def test_scope_disposal_clears_scoped_cache():
    """Verify scope disposal marks is_disposed=True and clears scoped cache."""
    services = ServiceCollection()
    services.add_scoped(ServiceScoped, ServiceScoped)
    root = ServiceProvider(services=services)
    scope = root.create_scope()

    inst = scope.resolve(ServiceScoped)
    assert scope._scoped_cache[ServiceScoped] is inst

    scope.dispose()
    assert scope.is_disposed is True
    assert len(scope._scoped_cache) == 0


def test_dispose_child_scope_twice_is_idempotent():
    """Verify calling dispose on a scope multiple times is safe and idempotent."""
    root = ServiceProvider()
    scope = root.create_scope()
    scope.dispose()
    scope.dispose()
    assert scope.is_disposed is True


def test_scope_disposal_preserves_root_singletons():
    """Verify child scope disposal does NOT clear or mutate root singleton cache."""
    services = ServiceCollection()
    services.add_singleton(IServiceA, ServiceA)
    root = ServiceProvider(services=services)
    scope = root.create_scope()

    inst_singleton = scope.resolve(IServiceA)
    scope.dispose()

    assert scope.is_disposed is True
    assert root.resolve(IServiceA) is inst_singleton


def test_nested_scope_disposal_recursive():
    """Verify disposing parent scope recursively disposes all child scopes."""
    services = ServiceCollection()
    services.add_scoped(ServiceScoped, ServiceScoped)
    root = ServiceProvider(services=services)

    scope_a = root.create_scope()
    scope_b = scope_a.create_scope()

    inst_b = scope_b.resolve(ServiceScoped)
    scope_a.dispose()

    assert scope_a.is_disposed is True
    assert scope_b.is_disposed is True


def test_disposed_scope_resolution_raises_exception():
    """Verify attempting to resolve a service from a disposed scope raises ServiceResolutionException."""
    services = ServiceCollection()
    services.add_singleton(IServiceA, ServiceA)
    root = ServiceProvider(services=services)
    scope = root.create_scope()
    scope.dispose()

    with pytest.raises(ServiceResolutionException):
        scope.resolve(IServiceA)


def test_disposed_scope_resolve_required_raises():
    """Verify resolve_required on a disposed scope raises ServiceResolutionException."""
    services = ServiceCollection()
    services.add_singleton(IServiceA, ServiceA)
    root = ServiceProvider(services=services)
    scope = root.create_scope()
    scope.dispose()

    with pytest.raises(ServiceResolutionException):
        scope.resolve_required(IServiceA)


def test_disposed_scope_resolve_all_returns_empty_tuple():
    """Verify resolve_all on a disposed scope returns empty tuple."""
    services = ServiceCollection()
    services.add_singleton(IServiceA, ServiceA)
    root = ServiceProvider(services=services)
    scope = root.create_scope()
    scope.dispose()

    assert scope.resolve_all(IServiceA) == ()


def test_disposed_scope_create_scope_raises_exception():
    """Verify attempting to create a child scope from a disposed scope raises ServiceResolutionException."""
    root = ServiceProvider()
    scope = root.create_scope()
    scope.dispose()

    with pytest.raises(ServiceResolutionException):
        scope.create_scope()


def test_scope_health_reporting():
    """Verify health reporting for active (READY) and disposed (STOPPED) scopes."""
    root = ServiceProvider()
    scope = root.create_scope()

    assert scope.health().is_healthy is True
    assert scope.health().state == ContainerState.READY

    scope.dispose()
    assert scope.health().is_healthy is False
    assert scope.health().state == ContainerState.STOPPED
    assert "disposed" in scope.health().issues[0]


def test_scope_diagnostics_extended_fields():
    """Verify ContainerDiagnostics contains scope depth, scope ID, and scoped cache sizes."""
    services = ServiceCollection()
    services.add_scoped(ServiceScoped, ServiceScoped)
    root = ServiceProvider(services=services)
    scope = root.create_scope()
    scope.resolve(ServiceScoped)

    diag = scope.diagnostics()
    assert diag.current_scope_id == scope.scope_id
    assert diag.scope_depth == 1
    assert diag.scoped_cache_size == 1
    assert diag.timestamp is not None


# ============================================================================
# 8. DependencyContainer Scope Delegation Tests (Phase 14.2.4)
# ============================================================================


def test_dependency_container_create_and_dispose_scope():
    """Verify DependencyContainer create_scope, active_scopes, and dispose_scope."""
    container = DependencyContainer()
    container.add_scoped(ServiceScoped, ServiceScoped)

    scope1 = container.create_scope()
    scope2 = container.create_scope()

    active = container.active_scopes()
    assert len(active) == 2
    assert scope1.scope_id in active
    assert scope2.scope_id in active

    assert container.dispose_scope(scope1.scope_id) is True
    assert len(container.active_scopes()) == 1


def test_dependency_container_dispose_non_existent_scope():
    """Verify dispose_scope returns False when scope_id is not found."""
    container = DependencyContainer()
    assert container.dispose_scope("non_existent_scope_id") is False


def test_dependency_container_scope_statistics():
    """Verify DependencyContainer scope_statistics metric reporting."""
    container = DependencyContainer()
    scope1 = container.create_scope()
    scope2 = container.create_scope()

    stats = container.scope_statistics()
    assert stats["scopes_created"] == 3.0
    assert stats["active_scopes"] == 3.0  # Root + 2 scopes

    container.dispose_scope(scope1.scope_id)
    stats_after = container.scope_statistics()
    assert stats_after["scopes_disposed"] == 1.0


# ============================================================================
# 9. Concurrent Multithreaded Scope Tests
# ============================================================================


def test_concurrent_scope_creation():
    """Verify thread-safe concurrent scope creation using ThreadPoolExecutor."""
    container = DependencyContainer()

    def do_create():
        return container.create_scope()

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(do_create) for _ in range(30)]
        results = [f.result() for f in futures]

    assert len(results) == 30
    assert len(container.active_scopes()) == 30


def test_concurrent_scope_disposal():
    """Verify thread-safe parallel disposal of child scopes."""
    container = DependencyContainer()
    scopes = [container.create_scope() for _ in range(20)]

    def do_dispose(s: IServiceProvider):
        return container.dispose_scope(s.scope_id)

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(do_dispose, s) for s in scopes]
        results = [f.result() for f in futures]

    assert all(results)
    assert len(container.active_scopes()) == 0


def test_concurrent_scoped_resolution_same_scope():
    """Verify parallel resolution of SCOPED service within the same scope returns identical instance."""
    services = ServiceCollection()
    services.add_scoped(ServiceScoped, ServiceScoped)
    root = ServiceProvider(services=services)
    scope = root.create_scope()

    def do_resolve():
        return scope.resolve(ServiceScoped)

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(do_resolve) for _ in range(50)]
        results = [f.result() for f in futures]

    first_inst = results[0]
    assert all(inst is first_inst for inst in results)


def test_concurrent_parallel_scopes_resolution():
    """Verify parallel resolution of SCOPED service across distinct child scopes returns distinct instances."""
    services = ServiceCollection()
    services.add_scoped(ServiceScoped, ServiceScoped)
    root = ServiceProvider(services=services)

    def do_scoped_work():
        s = root.create_scope()
        return s.resolve(ServiceScoped)

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(do_scoped_work) for _ in range(30)]
        results = [f.result() for f in futures]

    assert len(set(results)) == 30


# ============================================================================
# 10. Existing Lifecycle & Runtime Tests
# ============================================================================


def test_dependency_container_lifecycle():
    """Verify DependencyContainer lifecycle state transitions."""
    container = DependencyContainer()
    assert container.health().state == ContainerState.UNINITIALIZED

    state = container.initialize()
    assert state == ContainerState.READY
    assert container.health().is_healthy is True

    restart_state = container.restart()
    assert restart_state == ContainerState.READY

    shutdown_state = container.shutdown()
    assert shutdown_state == ContainerState.STOPPED


def test_dependency_container_resolution_delegation():
    """Verify DependencyContainer resolution delegation APIs."""
    container = DependencyContainer()
    container.add_singleton(IServiceA, ServiceA)
    container.add_singleton(IServiceB, ServiceB)

    instance_b = container.resolve(IServiceB)
    assert isinstance(instance_b, ServiceB)

    req_instance = container.resolve_required(IServiceA)
    assert isinstance(req_instance, ServiceA)

    try_instance = container.try_resolve(IServiceA)
    assert isinstance(try_instance, ServiceA)

    all_instances = container.resolve_all(IServiceA)
    assert len(all_instances) == 1


def test_scoped_instance_creation_count_metric():
    """Verify scoped_creations metric increments on constructing scoped instance."""
    services = ServiceCollection()
    services.add_scoped(ServiceScoped, ServiceScoped)
    root = ServiceProvider(services=services)
    scope = root.create_scope()

    scope.resolve(ServiceScoped)
    stats = scope.statistics()
    assert stats.metrics["scoped_creations"] == 1.0


def test_scoped_instance_hit_count_metric():
    """Verify scoped_hits metric in diagnostics increments on accessing cached scoped instance."""
    services = ServiceCollection()
    services.add_scoped(ServiceScoped, ServiceScoped)
    root = ServiceProvider(services=services)
    scope = root.create_scope()

    scope.resolve(ServiceScoped)
    scope.resolve(ServiceScoped)
    diag = scope.diagnostics()
    assert diag.metrics["scoped_hits"] == 1.0


def test_scoped_factory_execution_count_metric():
    """Verify factory_executions counter increments when factory produces scoped instance."""
    services = ServiceCollection()
    services.add_scoped(ServiceScoped, factory=lambda p: ServiceScoped())
    root = ServiceProvider(services=services)
    scope = root.create_scope()

    scope.resolve(ServiceScoped)
    assert scope.factory_executions == 1


def test_child_scope_creation_increments_parent_active_scopes():
    """Verify creating child scope updates active_scopes_count."""
    root = ServiceProvider()
    child1 = root.create_scope()
    child2 = root.create_scope()

    assert root.active_scopes_count == 3  # Root + 2 children


def test_dispose_scope_decrements_parent_active_scopes():
    """Verify disposing child scope decrements active_scopes_count."""
    root = ServiceProvider()
    child = root.create_scope()
    assert root.active_scopes_count == 2

    child.dispose()
    assert root.active_scopes_count == 1


def test_dependency_container_list_services_and_lifetimes():
    """Verify listing registered services and filtering by ServiceLifetime.SCOPED."""
    container = DependencyContainer()
    container.add_singleton(IServiceA, ServiceA)
    container.add_scoped(ServiceScoped, ServiceScoped)

    scoped_models = container.list_by_lifetime(ServiceLifetime.SCOPED)
    assert len(scoped_models) == 1
    assert scoped_models[0].service_type == "ServiceScoped"


def test_di_runtime_lazy_singleton_accessors():
    """Verify lazy singleton accessors in di/runtime.py."""
    reset_dependency_container()
    reset_service_provider()

    container = get_dependency_container()
    assert isinstance(container, IDependencyContainer)

    provider = get_service_provider()
    assert isinstance(provider, IServiceProvider)

    custom_container = DependencyContainer()
    set_dependency_container(custom_container)
    assert get_dependency_container() is custom_container

    reset_dependency_container()
    reset_service_provider()
