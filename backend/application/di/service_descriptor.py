"""Service Descriptor (Phase 14.2.2).

Stores service metadata, factory definitions, instance placeholders, tags, aliases,
and lifetime scopes. Includes descriptor equality, hashing, validation, and serialization.
Data holder with zero resolution logic.
"""

from datetime import datetime, timezone
import logging
from threading import RLock
from typing import Any, Callable, Dict, Optional, Tuple
import uuid

from backend.application.di.exceptions import ServiceRegistrationException
from backend.application.di.interfaces import IServiceDescriptor
from backend.application.di.models import ServiceDescriptorModel, ServiceLifetime

logger = logging.getLogger(__name__)


class ServiceDescriptor(IServiceDescriptor):
    """Thread-safe descriptor holding service metadata, tags, aliases, and lifetime definitions."""

    def __init__(
        self,
        service_type: Any,
        implementation_type: Optional[Any] = None,
        factory: Optional[Callable[..., Any]] = None,
        lifetime: ServiceLifetime = ServiceLifetime.SINGLETON,
        instance: Optional[Any] = None,
        aliases: Optional[Tuple[str, ...]] = None,
        tags: Optional[Tuple[str, ...]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        descriptor_id: Optional[str] = None,
    ) -> None:
        """Initialize ServiceDescriptor using Constructor Dependency Injection.

        Args:
            service_type: Required service interface or class type.
            implementation_type: Optional concrete implementation class type.
            factory: Optional factory callable for instantiation.
            lifetime: Lifetime scope (SINGLETON, TRANSIENT, SCOPED).
            instance: Optional pre-constructed singleton instance.
            aliases: Optional tuple of string aliases.
            tags: Optional tuple of classification tags.
            metadata: Optional dictionary of service metadata attributes.
            descriptor_id: Optional unique identifier string.

        Raises:
            ServiceRegistrationException: If validation fails for service_type or lifetime.
        """
        self._lock = RLock()

        if service_type is None:
            raise ServiceRegistrationException("service_type cannot be None.")

        if not isinstance(lifetime, ServiceLifetime):
            try:
                lifetime = ServiceLifetime(lifetime)
            except (ValueError, TypeError) as exc:
                raise ServiceRegistrationException(
                    f"Invalid ServiceLifetime value: {lifetime}"
                ) from exc

        self._descriptor_id = descriptor_id or f"desc_{uuid.uuid4().hex[:12]}"
        self._registered_at = datetime.now(timezone.utc)
        self._service_type = service_type
        self._implementation_type = implementation_type or (
            service_type if isinstance(service_type, type) else None
        )
        self._factory = factory
        self._lifetime = lifetime
        self._instance = instance
        self._aliases: Tuple[str, ...] = tuple(aliases) if aliases else ()
        self._tags: Tuple[str, ...] = tuple(tags) if tags else ()
        self._metadata: Dict[str, Any] = dict(metadata) if metadata else {}

    @property
    def descriptor_id(self) -> str:
        """Get unique descriptor identifier string."""
        with self._lock:
            return self._descriptor_id

    @property
    def registered_at(self) -> datetime:
        """Get registration timestamp."""
        with self._lock:
            return self._registered_at

    @property
    def service_type(self) -> Any:
        """Get registered service type."""
        with self._lock:
            return self._service_type

    @property
    def implementation_type(self) -> Optional[Any]:
        """Get implementation class type."""
        with self._lock:
            return self._implementation_type

    @property
    def factory(self) -> Optional[Callable[..., Any]]:
        """Get factory callable if registered."""
        with self._lock:
            return self._factory

    @property
    def lifetime(self) -> ServiceLifetime:
        """Get service lifetime scope."""
        with self._lock:
            return self._lifetime

    @property
    def instance(self) -> Optional[Any]:
        """Get pre-constructed instance placeholder."""
        with self._lock:
            return self._instance

    @property
    def aliases(self) -> Tuple[str, ...]:
        """Get descriptor registered aliases."""
        with self._lock:
            return self._aliases

    @property
    def tags(self) -> Tuple[str, ...]:
        """Get descriptor classification tags."""
        with self._lock:
            return self._tags

    @property
    def metadata(self) -> Dict[str, Any]:
        """Get copy of descriptor metadata."""
        with self._lock:
            return dict(self._metadata)

    def to_model(self) -> ServiceDescriptorModel:
        """Export descriptor metadata as an immutable Pydantic v2 model.

        Returns:
            ServiceDescriptorModel: Descriptor model snapshot.
        """
        with self._lock:
            service_str = (
                self._service_type.__name__
                if hasattr(self._service_type, "__name__")
                else str(self._service_type)
            )
            impl_str = (
                self._implementation_type.__name__
                if self._implementation_type and hasattr(self._implementation_type, "__name__")
                else str(self._implementation_type)
                if self._implementation_type
                else None
            )
            return ServiceDescriptorModel(
                descriptor_id=self._descriptor_id,
                service_type=service_str,
                implementation_type=impl_str,
                lifetime=self._lifetime,
                has_factory=self._factory is not None,
                has_instance=self._instance is not None,
                tags=self._tags,
                aliases=self._aliases,
                registered_at=self._registered_at,
                metadata=dict(self._metadata),
            )

    def __eq__(self, other: object) -> bool:
        """Check equality between two ServiceDescriptor instances."""
        if not isinstance(other, ServiceDescriptor):
            return False
        with self._lock:
            return (
                self._descriptor_id == other._descriptor_id
                or (
                    self._service_type == other._service_type
                    and self._implementation_type == other._implementation_type
                    and self._lifetime == other._lifetime
                )
            )

    def __hash__(self) -> int:
        """Get hash value for ServiceDescriptor based on descriptor_id."""
        with self._lock:
            return hash(self._descriptor_id)
