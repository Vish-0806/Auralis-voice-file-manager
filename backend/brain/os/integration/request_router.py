"""Request Router implementation (Phase 11.9).

Resolves capability descriptors for operation requests and validates request parameters,
forwarding to the operation dispatcher without executing business logic.
"""

from typing import Optional

from brain.os.integration.capability_registry import CapabilityRegistry
from brain.os.integration.exceptions import (
    CapabilityNotFoundError,
    OperationValidationError,
)
from brain.os.integration.integration_models import (
    CapabilityDescriptor,
    OperationRequest,
)
from brain.os.integration.interfaces import ICapabilityRegistry, IRequestRouter


class RequestRouter(IRequestRouter):
    """Provides capability routing and request validation."""

    def __init__(self, registry: Optional[ICapabilityRegistry] = None) -> None:
        self._registry = registry or CapabilityRegistry()

    def route(self, request: OperationRequest) -> CapabilityDescriptor:
        """Resolve target capability for an operation request."""
        cap_name = request.capability
        if not cap_name:
            # Derive default capability name if omitted
            cap_name = f"{request.target.value}.{request.action or 'default'}"

        descriptor = self._registry.lookup(cap_name)
        if not descriptor:
            raise CapabilityNotFoundError(
                f"Capability '{cap_name}' not registered for target '{request.target.value}'",
                request_id=request.request_id,
            )

        if not descriptor.is_enabled:
            raise OperationValidationError(
                f"Capability '{cap_name}' is currently disabled",
                request_id=request.request_id,
            )

        return descriptor

    def validate_request(self, request: OperationRequest) -> bool:
        """Validate request parameters and targets against registered capability schema."""
        if not request.target:
            raise OperationValidationError("Operation request target cannot be empty", request_id=request.request_id)

        try:
            self.route(request)
            return True
        except Exception:
            return False
