"""API Identity Manager Implementation (Phase 15.4).

Thread-safe identity management store responsible for managing identities, principal resolution,
role assignments, and claim assertions without external identity providers or networking.
"""

import logging
from threading import RLock
from typing import Dict, Optional, Tuple

from backend.application.api.auth.exceptions import IdentityException
from backend.application.api.auth.interfaces import IIdentityManager
from backend.application.api.auth.models import (
    Claim,
    Identity,
    Principal,
    Role,
)

logger = logging.getLogger(__name__)


class IdentityManager(IIdentityManager):
    """Thread-safe identity store managing identities, roles, claims, and principals."""

    def __init__(self) -> None:
        """Initialize IdentityManager using Constructor Dependency Injection."""
        self._lock = RLock()
        self._identities: Dict[str, Identity] = {}
        self._principals: Dict[str, Principal] = {}

    def register_identity(self, identity: Identity) -> Identity:
        """Register a new identity and generate its corresponding Principal.

        Args:
            identity: Immutable Identity instance.

        Returns:
            Identity: Registered identity.

        Raises:
            IdentityException: If identity_id is already registered.
        """
        with self._lock:
            if identity.identity_id in self._identities:
                raise IdentityException(
                    f"Identity with ID '{identity.identity_id}' is already registered."
                )

            principal_id = f"principal_{identity.identity_id}"
            principal = Principal(
                principal_id=principal_id,
                identity=identity,
                active_roles=tuple(r.name for r in identity.roles),
            )

            self._identities[identity.identity_id] = identity
            self._principals[principal_id] = principal
            logger.info("Registered identity ID '%s' (%s).", identity.identity_id, identity.username)
            return identity

    def lookup_identity(self, identity_id: str) -> Optional[Identity]:
        """Look up an identity by identity ID.

        Args:
            identity_id: Unique identity identifier.

        Returns:
            Optional[Identity]: Identity if found, else None.
        """
        with self._lock:
            return self._identities.get(identity_id)

    def lookup_principal(self, principal_id: str) -> Optional[Principal]:
        """Look up a security principal by principal ID.

        Args:
            principal_id: Unique principal identifier.

        Returns:
            Optional[Principal]: Principal if found, else None.
        """
        with self._lock:
            return self._principals.get(principal_id)

    def assign_role(self, identity_id: str, role: Role) -> Optional[Identity]:
        """Assign a role to an existing identity.

        Args:
            identity_id: Target identity ID.
            role: Role instance to assign.

        Returns:
            Optional[Identity]: Updated identity if found, else None.
        """
        with self._lock:
            identity = self._identities.get(identity_id)
            if identity is None:
                return None

            # Check if role is already present
            existing_role_ids = {r.role_id for r in identity.roles}
            if role.role_id in existing_role_ids:
                return identity

            updated_roles = identity.roles + (role,)
            updated_identity = identity.model_copy(update={"roles": updated_roles})
            self._identities[identity_id] = updated_identity

            # Update principal mapping
            principal_id = f"principal_{identity_id}"
            if principal_id in self._principals:
                self._principals[principal_id] = Principal(
                    principal_id=principal_id,
                    identity=updated_identity,
                    active_roles=tuple(r.name for r in updated_roles),
                )

            logger.info("Assigned role '%s' to identity ID '%s'.", role.name, identity_id)
            return updated_identity

    def add_claim(self, identity_id: str, claim: Claim) -> Optional[Identity]:
        """Add a claim assertion to an existing identity.

        Args:
            identity_id: Target identity ID.
            claim: Claim instance.

        Returns:
            Optional[Identity]: Updated identity if found, else None.
        """
        with self._lock:
            identity = self._identities.get(identity_id)
            if identity is None:
                return None

            updated_claims = identity.claims + (claim,)
            updated_identity = identity.model_copy(update={"claims": updated_claims})
            self._identities[identity_id] = updated_identity

            principal_id = f"principal_{identity_id}"
            if principal_id in self._principals:
                self._principals[principal_id] = Principal(
                    principal_id=principal_id,
                    identity=updated_identity,
                    active_roles=tuple(r.name for r in updated_identity.roles),
                )

            logger.info("Added claim '%s' to identity ID '%s'.", claim.key, identity_id)
            return updated_identity

    def list_identities(self) -> Tuple[Identity, ...]:
        """List all registered identities.

        Returns:
            Tuple[Identity, ...]: Immutable tuple of identities.
        """
        with self._lock:
            return tuple(self._identities.values())

    def count_identities(self) -> int:
        """Get total count of registered identities.

        Returns:
            int: Number of identities.
        """
        with self._lock:
            return len(self._identities)
