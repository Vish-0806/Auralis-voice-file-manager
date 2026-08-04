"""Profile Manager (Phase 14.3.4).

Thread-safe manager for configuration profile registration, inheritance resolution,
safe runtime switching, value override merging, and diagnostics reporting.
"""

from datetime import datetime, timezone
import logging
from threading import RLock
from typing import Dict, List, Optional, Set, Tuple, Any

from backend.application.config.exceptions import ConfigurationProfileError
from backend.application.config.models import (
    ConfigurationProfileDefinition,
    ConfigurationProfileSnapshot,
    ConfigurationProfileType,
    ProfileHealth,
    ProfileStatistics,
)

logger = logging.getLogger(__name__)


class ProfileManager:
    """Production thread-safe runtime profile manager with inheritance resolution."""

    def __init__(self) -> None:
        """Initialize ProfileManager with default profiles."""
        self._lock = RLock()
        self._profiles: Dict[str, ConfigurationProfileDefinition] = {}
        self._active_profile_name: str = "development"

        # Statistics
        self._registered_profiles_count: int = 0
        self._active_profile_switches_count: int = 0
        self._inheritance_resolutions_count: int = 0

        # Register default profiles
        self._init_default_profiles()

    def _init_default_profiles(self) -> None:
        """Initialize default deployment profiles."""
        base_dev = ConfigurationProfileDefinition(
            profile_type=ConfigurationProfileType.DEVELOPMENT,
            profile_name="development",
            parent_profile_name=None,
            overrides={"debug": True, "log_level": "DEBUG"},
            active=True,
            priority=100,
        )
        base_test = ConfigurationProfileDefinition(
            profile_type=ConfigurationProfileType.TESTING,
            profile_name="testing",
            parent_profile_name="development",
            overrides={"debug": True, "log_level": "DEBUG", "testing": True},
            active=False,
            priority=100,
        )
        base_prod = ConfigurationProfileDefinition(
            profile_type=ConfigurationProfileType.PRODUCTION,
            profile_name="production",
            parent_profile_name=None,
            overrides={"debug": False, "log_level": "INFO"},
            active=False,
            priority=100,
        )
        self.register_profile(base_dev)
        self.register_profile(base_test)
        self.register_profile(base_prod)

    def register_profile(self, profile: ConfigurationProfileDefinition) -> bool:
        """Register a configuration profile.

        Args:
            profile: Target ConfigurationProfileDefinition model.

        Returns:
            bool: True if registered.

        Raises:
            ConfigurationProfileError: If profile is invalid or duplicate name.
        """
        if profile is None or not profile.profile_name:
            raise ConfigurationProfileError("Cannot register invalid or nameless configuration profile.")

        with self._lock:
            name = profile.profile_name
            if name in self._profiles and self._registered_profiles_count > 0:
                raise ConfigurationProfileError(f"Configuration profile '{name}' is already registered.")

            self._profiles[name] = profile
            self._registered_profiles_count = len(self._profiles)
            logger.info("Registered configuration profile '%s'.", name)
            return True

    def unregister_profile(self, profile_name: str) -> bool:
        """Unregister a configuration profile by name.

        Args:
            profile_name: Target profile name.

        Returns:
            bool: True if unregistered.

        Raises:
            ConfigurationProfileError: If trying to unregister the currently active profile.
        """
        with self._lock:
            if profile_name == self._active_profile_name:
                raise ConfigurationProfileError(f"Cannot unregister currently active profile '{profile_name}'.")

            if profile_name in self._profiles:
                del self._profiles[profile_name]
                self._registered_profiles_count = len(self._profiles)
                logger.info("Unregistered configuration profile '%s'.", profile_name)
                return True
            return False

    def activate_profile(self, profile_name: str) -> bool:
        """Switch active configuration profile at runtime safely.

        Args:
            profile_name: Name of target profile to activate.

        Returns:
            bool: True if activated.

        Raises:
            ConfigurationProfileError: If target profile is not registered.
        """
        with self._lock:
            if profile_name not in self._profiles:
                raise ConfigurationProfileError(f"Cannot activate unregistered profile '{profile_name}'.")

            if profile_name != self._active_profile_name:
                self._active_profile_name = profile_name
                self._active_profile_switches_count += 1
                logger.info("Activated configuration profile '%s'.", profile_name)
            return True

    def get_active_profile(self) -> ConfigurationProfileDefinition:
        """Get currently active profile model."""
        with self._lock:
            return self._profiles[self._active_profile_name]

    def list_profiles(self) -> Tuple[ConfigurationProfileDefinition, ...]:
        """List all registered configuration profiles."""
        with self._lock:
            return tuple(self._profiles.values())

    def resolve_profile(self, profile_name: Optional[str] = None) -> Dict[str, Any]:
        """Resolve merged overrides following inheritance chain (parent -> child).

        Args:
            profile_name: Target profile name (defaults to active profile).

        Returns:
            Dict[str, Any]: Merged overrides dictionary.
        """
        with self._lock:
            target_name = profile_name or self._active_profile_name
            if target_name not in self._profiles:
                raise ConfigurationProfileError(f"Cannot resolve unregistered profile '{target_name}'.")

            self._inheritance_resolutions_count += 1
            chain: List[ConfigurationProfileDefinition] = []
            visited: Set[str] = set()

            curr: Optional[str] = target_name
            while curr and curr in self._profiles:
                if curr in visited:
                    raise ConfigurationProfileError(f"Circular inheritance detected in profile '{curr}'.")
                visited.add(curr)
                p = self._profiles[curr]
                chain.append(p)
                curr = p.parent_profile_name

            # Merge from root parent to child
            chain.reverse()
            merged_overrides: Dict[str, Any] = {}
            for p in chain:
                merged_overrides.update(p.overrides)

            return merged_overrides

    def create_snapshot(self) -> ConfigurationProfileSnapshot:
        """Create an immutable snapshot of active profile and merged overrides."""
        with self._lock:
            active_p = self.get_active_profile()
            merged = self.resolve_profile()
            return ConfigurationProfileSnapshot(
                active_profile_name=active_p.profile_name,
                parent_profile_name=active_p.parent_profile_name,
                merged_values=merged,
                created_at=datetime.now(timezone.utc),
            )

    def health(self) -> ProfileHealth:
        """Get health status of profile subsystem."""
        with self._lock:
            is_healthy = self._active_profile_name in self._profiles
            issues = () if is_healthy else (f"Active profile '{self._active_profile_name}' missing from registry.",)
            return ProfileHealth(
                is_healthy=is_healthy,
                active_profile_name=self._active_profile_name,
                issues=issues,
                checked_at=datetime.now(timezone.utc),
            )

    def statistics(self) -> ProfileStatistics:
        """Get profile metrics."""
        with self._lock:
            return ProfileStatistics(
                registered_profiles_count=self._registered_profiles_count,
                active_profile_switches_count=self._active_profile_switches_count,
                inheritance_resolutions_count=self._inheritance_resolutions_count,
            )
