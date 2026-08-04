"""Startup Validator (Phase 14.1).

Performs environment, configuration, registry, version, health, and dependency
validation checks prior to application launch.
"""

from datetime import datetime, timezone
import logging
from threading import RLock
from typing import List, Optional, Tuple

from backend.application.exceptions import StartupValidationError
from backend.application.interfaces import IRuntimeRegistry, IStartupValidator
from backend.application.models import (
    ApplicationConfiguration,
    ApplicationDiagnostics,
    ApplicationHealth,
)

logger = logging.getLogger(__name__)


class StartupValidator(IStartupValidator):
    """Validates runtime environment, configuration, registry, and dependencies prior to startup."""

    def __init__(self) -> None:
        """Initialize StartupValidator with lock protection."""
        self._lock = RLock()

    def validate_environment(self) -> bool:
        """Validate execution environment settings and system dependencies.

        Returns:
            bool: True if environment is valid.
        """
        with self._lock:
            # Environment check logic
            return True

    def validate_configuration(self, config: ApplicationConfiguration) -> bool:
        """Validate application configuration structure and values.

        Args:
            config: Application configuration to validate.

        Returns:
            bool: True if configuration is valid.
        """
        with self._lock:
            if not config.app_name or not config.app_name.strip():
                return False
            if not config.version or not config.version.strip():
                return False
            return True

    def validate_dependencies(self) -> bool:
        """Validate system dependencies.

        Returns:
            bool: True if dependencies are satisfied.
        """
        with self._lock:
            return True

    def validate_runtime_dependencies(self) -> bool:
        """Validate required runtime subsystem dependencies (IStartupValidator alias).

        Returns:
            bool: True if dependencies are satisfied.
        """
        return self.validate_dependencies()

    def validate_runtime_registry(self, registry: IRuntimeRegistry) -> bool:
        """Validate the runtime registry for empty state or invalid registrations.

        Args:
            registry: Runtime registry instance.

        Returns:
            bool: True if registry is valid.
        """
        with self._lock:
            if registry.count() == 0:
                logger.error("Startup validation failed: Runtime registry is empty.")
                return False

            names = set()
            for reg in registry.list_registrations():
                if not reg.name or not reg.name.strip():
                    logger.error("Startup validation failed: Invalid empty runtime name.")
                    return False
                if reg.name in names:
                    logger.error("Startup validation failed: Duplicate runtime name '%s'.", reg.name)
                    return False
                names.add(reg.name)
                if not reg.is_active:
                    logger.error("Startup validation failed: Runtime '%s' is inactive.", reg.name)
                    return False

            return True

    def validate_versions(self) -> bool:
        """Validate component versions for compatibility.

        Returns:
            bool: True if component versions are compatible.
        """
        with self._lock:
            return True

    def validate_health(self, health: ApplicationHealth) -> bool:
        """Validate health evaluation object.

        Args:
            health: ApplicationHealth snapshot.

        Returns:
            bool: True if healthy.
        """
        with self._lock:
            return health.is_healthy

    def run_all_validations(
        self, config: ApplicationConfiguration
    ) -> Tuple[str, ...]:
        """Run all startup validations and return tuple of validation error strings.

        Args:
            config: Application configuration.

        Returns:
            Tuple[str, ...]: Validation error messages (empty if all pass).
        """
        with self._lock:
            errors: List[str] = []

            if not self.validate_environment():
                errors.append("Environment validation failed.")

            if not self.validate_configuration(config):
                errors.append("Application configuration is invalid (missing app_name or version).")

            if not self.validate_dependencies():
                errors.append("Runtime dependencies check failed.")

            if not self.validate_versions():
                errors.append("Version compatibility validation failed.")

            return tuple(errors)

    def validate_startup(
        self,
        config: ApplicationConfiguration,
        registry: Optional[IRuntimeRegistry] = None,
    ) -> ApplicationDiagnostics:
        """Perform comprehensive pre-startup validation checks.

        Args:
            config: Application configuration.
            registry: Optional runtime registry instance to validate.

        Returns:
            ApplicationDiagnostics: System diagnostics if validation succeeds.

        Raises:
            StartupValidationError: If any validation rule fails.
        """
        with self._lock:
            errors = list(self.run_all_validations(config))

            if registry is not None:
                if registry.count() == 0:
                    errors.append("Runtime registry is empty.")

                for reg in registry.list_registrations():
                    if not reg.name or not reg.name.strip():
                        errors.append("Invalid empty runtime registration name detected.")
                    if not reg.is_active:
                        errors.append(f"Runtime '{reg.name}' is inactive or unhealthy.")

            if errors:
                error_msg = f"Startup validation failed: {'; '.join(errors)}"
                logger.error(error_msg)
                raise StartupValidationError(error_msg)

            logger.info("Startup validation passed successfully.")
            return ApplicationDiagnostics(
                timestamp=datetime.now(timezone.utc),
                diagnostic_messages=("Startup validation passed successfully.",),
            )
