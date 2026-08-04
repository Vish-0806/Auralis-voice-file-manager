"""Comprehensive unit tests for Phase 14.2.2 Service Registration Engine."""

import concurrent.futures
import pytest
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


# Dummy service types for testing
class IServiceA:
    pass


class ServiceA(IServiceA):
    pass


class IServiceB:
    pass


class ServiceB(IServiceB):
    pass


class IServiceC:
    pass


class ServiceC(IServiceC):
    pass


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
    dummy_factory = lambda: ServiceA()
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
# 6. ServiceProvider Component Tests
# ============================================================================


def test_service_provider_skeleton_raises_not_implemented():
    """Verify ServiceProvider resolution methods raise NotImplementedError in Phase 14.2.2."""
    provider = ServiceProvider()

    with pytest.raises(NotImplementedError):
        provider.resolve(IServiceA)

    with pytest.raises(NotImplementedError):
        provider.resolve_all(IServiceA)

    with pytest.raises(NotImplementedError):
        provider.create_scope()

    with pytest.raises(NotImplementedError):
        provider.dispose()


def test_service_provider_health_and_statistics():
    """Verify ServiceProvider health and statistics metrics."""
    services = ServiceCollection()
    services.add_singleton(IServiceA, ServiceA)
    provider = ServiceProvider(services=services)

    health = provider.health()
    assert health.is_healthy is True
    assert health.state == ContainerState.READY

    stats = provider.statistics()
    assert stats.registered_services_count == 1


# ============================================================================
# 7. DependencyContainer Component Tests
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


def test_dependency_container_registration_delegation():
    """Verify DependencyContainer registration delegation methods."""
    container = DependencyContainer()
    assert container.add_singleton(IServiceA, ServiceA, aliases=("alias_a",)) is True
    assert container.add_transient(IServiceB, ServiceB) is True
    assert container.add_scoped(IServiceC, ServiceC) is True
    assert container.contains(IServiceA) is True
    assert container.contains(IServiceB) is True
    assert len(container.list_services()) == 3

    desc = ServiceDescriptor(service_type=IServiceA, implementation_type=ServiceA)
    with pytest.raises(ServiceRegistrationException):
        container.register(desc)

    new_desc = ServiceDescriptor(service_type=IServiceA, implementation_type=ServiceC)
    assert container.replace(new_desc) is True
    assert container.remove(IServiceB) is True
    assert len(container.list_services()) == 2

    container.remove_all()
    assert len(container.list_services()) == 0


def test_dependency_container_try_add_delegation():
    """Verify DependencyContainer try_add delegation method."""
    container = DependencyContainer()
    desc1 = ServiceDescriptor(service_type=IServiceA, implementation_type=ServiceA)
    desc2 = ServiceDescriptor(service_type=IServiceA, implementation_type=ServiceB)

    assert container.try_add(desc1) is True
    assert container.try_add(desc2) is False
    assert len(container.list_services()) == 1


def test_dependency_container_statistics_aggregation():
    """Verify DependencyContainer statistics metric aggregation."""
    container = DependencyContainer()
    container.add_singleton(IServiceA, ServiceA)

    stats = container.statistics()
    assert stats.registered_services_count == 1
    assert "total_registrations" in stats.metrics
    assert stats.metrics["total_registrations"] == 1.0


def test_dependency_container_capabilities():
    """Verify DependencyContainer capability flags."""
    container = DependencyContainer()
    caps = container.capabilities()
    assert caps.supports_singleton is True
    assert caps.supports_transient is True
    assert caps.supports_scoped is True
    assert caps.supports_aliases is True
    assert caps.supports_tags is True
    assert caps.supports_replacement is True


def test_dependency_container_concurrent_lifecycle():
    """Verify thread-safe concurrent initialize and shutdown on DependencyContainer."""
    container = DependencyContainer()

    def do_init_shutdown():
        container.initialize()
        return container.shutdown()

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(do_init_shutdown) for _ in range(10)]
        results = [f.result() for f in futures]

    assert all(r == ContainerState.STOPPED for r in results)


# ============================================================================
# 8. Lazy Global Runtime Accessor Tests (runtime.py)
# ============================================================================


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
