"""Service Collection (Phase 14.2.2).

Thread-safe collection managing service descriptors with O(1) lookups by service type
and alias. Enforces registration validation rules, alias conflict detection, and statistics tracking.
Zero resolution or service instantiation logic.
"""

import logging
from threading import RLock
from typing import Any, Callable, Dict, List, Optional, Tuple

from backend.application.di.exceptions import ServiceRegistrationException
from backend.application.di.interfaces import IServiceCollection, IServiceDescriptor
from backend.application.di.models import ServiceDescriptorModel, ServiceLifetime
from backend.application.di.service_descriptor import ServiceDescriptor

logger = logging.getLogger(__name__)


class ServiceCollection(IServiceCollection):
    """Thread-safe production builder collection for registering and managing service descriptors."""

    def __init__(self) -> None:
        """Initialize ServiceCollection with lock protection, O(1) index maps, and statistics."""
        self._lock = RLock()
        self._descriptors: List[ServiceDescriptor] = []
        self._service_map: Dict[Any, List[ServiceDescriptor]] = {}
        self._alias_map: Dict[str, ServiceDescriptor] = {}

        # Registration Statistics Counters
        self.total_registrations: int = 0
        self.singleton_registrations: int = 0
        self.transient_registrations: int = 0
        self.scoped_registrations: int = 0
        self.replacements: int = 0
        self.removals: int = 0
        self.duplicates_rejected: int = 0
        self.aliases_registered: int = 0

    def _validate_descriptor(self, descriptor: IServiceDescriptor) -> None:
        """Validate service descriptor fields prior to registration.

        Raises:
            ServiceRegistrationException: If descriptor validation fails.
        """
        if not descriptor or descriptor.service_type is None:
            raise ServiceRegistrationException("Cannot register descriptor with None service_type.")

        if not isinstance(descriptor.lifetime, ServiceLifetime):
            raise ServiceRegistrationException(
                f"Invalid lifetime '{descriptor.lifetime}' on descriptor for {descriptor.service_type}."
            )

        for alias in descriptor.aliases:
            if not alias or not isinstance(alias, str) or not alias.strip():
                raise ServiceRegistrationException(f"Invalid empty string alias in descriptor for {descriptor.service_type}.")
            if alias in self._alias_map:
                existing = self._alias_map[alias]
                if existing.service_type != descriptor.service_type:
                    raise ServiceRegistrationException(
                        f"Alias conflict: '{alias}' is already registered for service {existing.service_type}."
                    )

    def register(self, descriptor: IServiceDescriptor) -> bool:
        """Register a ServiceDescriptor instance enforcing unique duplicate rules.

        Args:
            descriptor: ServiceDescriptor instance.

        Returns:
            bool: True if registration succeeded.

        Raises:
            ServiceRegistrationException: If validation fails or duplicate service is detected.
        """
        with self._lock:
            self._validate_descriptor(descriptor)

            if descriptor.service_type in self._service_map:
                self.duplicates_rejected += 1
                raise ServiceRegistrationException(
                    f"Duplicate service registration detected for service_type: {descriptor.service_type}."
                )

            ConcreteDescriptor = (
                descriptor
                if isinstance(descriptor, ServiceDescriptor)
                else ServiceDescriptor(
                    service_type=descriptor.service_type,
                    implementation_type=descriptor.implementation_type,
                    lifetime=descriptor.lifetime,
                    aliases=descriptor.aliases,
                    tags=descriptor.tags,
                )
            )

            self._descriptors.append(ConcreteDescriptor)
            self._service_map[descriptor.service_type] = [ConcreteDescriptor]

            for alias in descriptor.aliases:
                self._alias_map[alias] = ConcreteDescriptor
                self.aliases_registered += 1

            # Update Statistics Counters
            self.total_registrations += 1
            if descriptor.lifetime == ServiceLifetime.SINGLETON:
                self.singleton_registrations += 1
            elif descriptor.lifetime == ServiceLifetime.TRANSIENT:
                self.transient_registrations += 1
            elif descriptor.lifetime == ServiceLifetime.SCOPED:
                self.scoped_registrations += 1

            logger.info("Registered service descriptor for: %s [%s]", descriptor.service_type, descriptor.lifetime.value)
            return True

    def replace(self, descriptor: IServiceDescriptor) -> bool:
        """Replace existing registration for service_type with a new descriptor.

        Args:
            descriptor: ServiceDescriptor instance.

        Returns:
            bool: True if replaced.
        """
        with self._lock:
            self._validate_descriptor(descriptor)

            ConcreteDescriptor = (
                descriptor
                if isinstance(descriptor, ServiceDescriptor)
                else ServiceDescriptor(
                    service_type=descriptor.service_type,
                    implementation_type=descriptor.implementation_type,
                    lifetime=descriptor.lifetime,
                    aliases=descriptor.aliases,
                    tags=descriptor.tags,
                )
            )

            if descriptor.service_type in self._service_map:
                self.remove(descriptor.service_type)
                self.replacements += 1

            return self.register(ConcreteDescriptor)

    def try_add(self, descriptor: IServiceDescriptor) -> bool:
        """Add descriptor only if service_type is not already registered.

        Args:
            descriptor: ServiceDescriptor instance.

        Returns:
            bool: True if added, False if already registered.
        """
        with self._lock:
            if descriptor.service_type in self._service_map:
                self.duplicates_rejected += 1
                logger.info("try_add skipped existing service: %s", descriptor.service_type)
                return False

            try:
                return self.register(descriptor)
            except ServiceRegistrationException:
                return False

    def add_singleton(
        self,
        service_type: Any,
        implementation_type: Optional[Any] = None,
        factory: Optional[Callable[..., Any]] = None,
        instance: Optional[Any] = None,
        aliases: Optional[Tuple[str, ...]] = None,
        tags: Optional[Tuple[str, ...]] = None,
    ) -> bool:
        """Register a SINGLETON service descriptor.

        Returns:
            bool: True if registered.
        """
        descriptor = ServiceDescriptor(
            service_type=service_type,
            implementation_type=implementation_type,
            factory=factory,
            lifetime=ServiceLifetime.SINGLETON,
            instance=instance,
            aliases=aliases,
            tags=tags,
        )
        return self.register(descriptor)

    def add_transient(
        self,
        service_type: Any,
        implementation_type: Optional[Any] = None,
        factory: Optional[Callable[..., Any]] = None,
        aliases: Optional[Tuple[str, ...]] = None,
        tags: Optional[Tuple[str, ...]] = None,
    ) -> bool:
        """Register a TRANSIENT service descriptor.

        Returns:
            bool: True if registered.
        """
        descriptor = ServiceDescriptor(
            service_type=service_type,
            implementation_type=implementation_type,
            factory=factory,
            lifetime=ServiceLifetime.TRANSIENT,
            aliases=aliases,
            tags=tags,
        )
        return self.register(descriptor)

    def add_scoped(
        self,
        service_type: Any,
        implementation_type: Optional[Any] = None,
        factory: Optional[Callable[..., Any]] = None,
        aliases: Optional[Tuple[str, ...]] = None,
        tags: Optional[Tuple[str, ...]] = None,
    ) -> bool:
        """Register a SCOPED service descriptor.

        Returns:
            bool: True if registered.
        """
        descriptor = ServiceDescriptor(
            service_type=service_type,
            implementation_type=implementation_type,
            factory=factory,
            lifetime=ServiceLifetime.SCOPED,
            aliases=aliases,
            tags=tags,
        )
        return self.register(descriptor)

    def remove(self, service_type: Any) -> bool:
        """Remove descriptor registration matching service_type.

        Args:
            service_type: Target service type to remove.

        Returns:
            bool: True if at least one matching descriptor was removed.
        """
        with self._lock:
            if service_type not in self._service_map:
                return False

            descriptors_to_remove = self._service_map[service_type]
            for desc in descriptors_to_remove:
                for alias in desc.aliases:
                    if alias in self._alias_map:
                        del self._alias_map[alias]
                if desc in self._descriptors:
                    self._descriptors.remove(desc)

            del self._service_map[service_type]
            self.removals += 1
            logger.info("Removed service descriptors for: %s", service_type)
            return True

    def remove_all(self) -> None:
        """Remove all registered services from collection."""
        self.clear()

    def contains(self, service_type: Any) -> bool:
        """Check if service_type is registered with O(1) complexity.

        Args:
            service_type: Target service type.

        Returns:
            bool: True if registered.
        """
        with self._lock:
            return service_type in self._service_map

    def contains_alias(self, alias: str) -> bool:
        """Check if an alias string is registered with O(1) complexity.

        Args:
            alias: Target alias string.

        Returns:
            bool: True if alias is present.
        """
        with self._lock:
            return alias in self._alias_map

    def get_descriptor(self, service_type: Any) -> Optional[ServiceDescriptor]:
        """Get registered ServiceDescriptor by service_type with O(1) complexity.

        Args:
            service_type: Target service type.

        Returns:
            Optional[ServiceDescriptor]: Descriptor if registered.
        """
        with self._lock:
            descriptors = self._service_map.get(service_type)
            return descriptors[0] if descriptors else None

    def get_descriptor_by_alias(self, alias: str) -> Optional[ServiceDescriptor]:
        """Get registered ServiceDescriptor by alias string with O(1) complexity.

        Args:
            alias: Target alias string.

        Returns:
            Optional[ServiceDescriptor]: Descriptor if found.
        """
        with self._lock:
            return self._alias_map.get(alias)

    def count(self) -> int:
        """Get total count of registered descriptors.

        Returns:
            int: Number of descriptors.
        """
        with self._lock:
            return len(self._descriptors)

    def clear(self) -> None:
        """Clear all descriptors, index maps, and aliases."""
        with self._lock:
            self._descriptors.clear()
            self._service_map.clear()
            self._alias_map.clear()
            logger.info("Cleared ServiceCollection descriptors and alias mappings.")

    def list_services(self) -> Tuple[ServiceDescriptorModel, ...]:
        """List all registered service descriptors in registration order.

        Returns:
            Tuple[ServiceDescriptorModel, ...]: Immutable tuple of models.
        """
        with self._lock:
            return tuple(desc.to_model() for desc in self._descriptors)

    def list_by_lifetime(self, lifetime: ServiceLifetime) -> Tuple[ServiceDescriptorModel, ...]:
        """List service descriptors filtered by lifetime scope.

        Args:
            lifetime: ServiceLifetime enum filter.

        Returns:
            Tuple[ServiceDescriptorModel, ...]: Filtered tuple of models.
        """
        with self._lock:
            return tuple(
                desc.to_model()
                for desc in self._descriptors
                if desc.lifetime == lifetime
            )

    def list_aliases(self) -> Tuple[str, ...]:
        """List all registered service aliases.

        Returns:
            Tuple[str, ...]: Immutable tuple of registered alias strings.
        """
        with self._lock:
            return tuple(self._alias_map.keys())

    def get_descriptors(self) -> Tuple[ServiceDescriptor, ...]:
        """Get raw ServiceDescriptor instances.

        Returns:
            Tuple[ServiceDescriptor, ...]: Immutable tuple of descriptors.
        """
        with self._lock:
            return tuple(self._descriptors)
