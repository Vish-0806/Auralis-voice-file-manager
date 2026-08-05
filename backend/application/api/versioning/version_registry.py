"""API Version Registry Implementation (Phase 15.6).

Thread-safe in-memory registry for managing API versions, release channels,
latest version resolution, and deprecation metadata.
"""

import logging
from threading import RLock

from typing import Dict, Optional, Tuple

from backend.application.api.versioning.exceptions import (
    VersionRegistrationException,
)
from backend.application.api.versioning.interfaces import IVersionRegistry
from backend.application.api.versioning.models import (
    ApiVersion,
    ReleaseChannel,
)

logger = logging.getLogger(__name__)


class VersionRegistry(IVersionRegistry):
    """Thread-safe registry for storing and querying API versions."""

    def __init__(self) -> None:
        """Initialize VersionRegistry using Constructor Dependency Injection."""
        self._lock = RLock()
        self._versions: Dict[str, ApiVersion] = {}
        self._version_numbers: Dict[str, str] = {}

        self._total_registrations = 0
        self._total_unregistrations = 0
        self._total_clears = 0

    def register_version(self, version: ApiVersion) -> ApiVersion:
        """Register a new API version definition.

        Args:
            version: Immutable ApiVersion instance.

        Returns:
            ApiVersion: Registered version.

        Raises:
            VersionRegistrationException: If version_id or version_number is already registered.
        """
        with self._lock:
            if version.version_id in self._versions:
                raise VersionRegistrationException(
                    f"API version with ID '{version.version_id}' is already registered."
                )

            if version.version_number in self._version_numbers:
                existing_id = self._version_numbers[version.version_number]
                raise VersionRegistrationException(
                    f"API version number '{version.version_number}' is already registered by version ID '{existing_id}'."
                )

            self._versions[version.version_id] = version
            self._version_numbers[version.version_number] = version.version_id
            self._total_registrations += 1
            logger.info(
                "Registered API version ID '%s' (%s) in channel '%s'.",
                version.version_id,
                version.version_number,
                version.channel.value,
            )
            return version

    def unregister_version(self, version_id: str) -> Optional[ApiVersion]:
        """Unregister an API version by version ID.

        Args:
            version_id: Unique version identifier.

        Returns:
            Optional[ApiVersion]: Removed version if present, else None.
        """
        with self._lock:
            version = self._versions.pop(version_id, None)
            if version is not None:
                self._version_numbers.pop(version.version_number, None)
                self._total_unregistrations += 1
                logger.info("Unregistered API version ID '%s'.", version_id)
            return version

    def lookup_version(self, version_id: str) -> Optional[ApiVersion]:
        """Look up an API version by version ID or version number string.

        Args:
            version_id: Version ID or version number string (e.g. '1.0.0').

        Returns:
            Optional[ApiVersion]: ApiVersion model if found, else None.
        """
        with self._lock:
            if version_id in self._versions:
                return self._versions[version_id]
            if version_id in self._version_numbers:
                mapped_id = self._version_numbers[version_id]
                return self._versions.get(mapped_id)
            return None

    def get_latest_version(
        self, channel: Optional[ReleaseChannel] = None
    ) -> Optional[ApiVersion]:
        """Get the latest registered API version, optionally filtered by release channel.

        Args:
            channel: Optional ReleaseChannel filter.

        Returns:
            Optional[ApiVersion]: Latest version if found, else None.
        """
        with self._lock:
            versions = list(self._versions.values())
            if channel is not None:
                versions = [v for v in versions if v.channel == channel]

            if not versions:
                return None

            # Helper to parse semver tuples
            def _parse_semver(ver_str: str) -> Tuple[int, ...]:
                parts = []
                for p in ver_str.lstrip("v").split("."):
                    clean = "".join(filter(str.isdigit, p))
                    parts.append(int(clean) if clean else 0)
                return tuple(parts)

            versions.sort(key=lambda v: _parse_semver(v.version_number), reverse=True)
            return versions[0]

    def list_versions(
        self, channel: Optional[ReleaseChannel] = None
    ) -> Tuple[ApiVersion, ...]:
        """List registered versions, optionally filtered by channel and sorted by version number.

        Args:
            channel: Optional ReleaseChannel filter.

        Returns:
            Tuple[ApiVersion, ...]: Immutable tuple of versions.
        """
        with self._lock:
            versions = list(self._versions.values())
            if channel is not None:
                versions = [v for v in versions if v.channel == channel]
            return tuple(versions)

    def count_versions(self) -> int:
        """Get total count of registered API versions.

        Returns:
            int: Number of versions.
        """
        with self._lock:
            return len(self._versions)

    def clear(self) -> None:
        """Clear all registered versions from the registry."""
        with self._lock:
            self._versions.clear()
            self._version_numbers.clear()
            self._total_clears += 1
            logger.info("VersionRegistry cleared.")

    def get_registry_telemetry(self) -> Dict[str, int]:
        """Get internal registry telemetry counters under lock."""
        with self._lock:
            return {
                "total_registrations": self._total_registrations,
                "total_unregistrations": self._total_unregistrations,
                "total_clears": self._total_clears,
                "current_versions_count": len(self._versions),
            }
