"""API Compatibility Manager Implementation (Phase 15.6).

Thread-safe compatibility manager evaluating semantic versioning rules,
backward/forward compatibility, breaking changes, and deprecation warnings
without HTTP or FastAPI dependencies.
"""

from datetime import datetime, timezone
import logging
from threading import RLock
from typing import Dict, List, Tuple

from backend.application.api.versioning.interfaces import ICompatibilityManager
from backend.application.api.versioning.models import (
    ApiVersion,
    CompatibilityReport,
    DeprecationState,
)

logger = logging.getLogger(__name__)


class CompatibilityManager(ICompatibilityManager):
    """Thread-safe compatibility manager evaluating version compatibility and breaking changes."""

    def __init__(self) -> None:
        """Initialize CompatibilityManager using Constructor Dependency Injection."""
        self._lock = RLock()
        self._total_compatibility_checks = 0

    def evaluate_compatibility(
        self, base_version: ApiVersion, target_version: ApiVersion
    ) -> CompatibilityReport:
        """Evaluate compatibility between two ApiVersion model instances.

        Args:
            base_version: Base/older ApiVersion model instance.
            target_version: Target/newer ApiVersion model instance.

        Returns:
            CompatibilityReport: Immutable compatibility evaluation report.
        """
        with self._lock:
            self._total_compatibility_checks += 1
            report = self.evaluate_version_strings(
                base_version.version_number, target_version.version_number
            )

            warnings_list = list(report.warnings)
            if (
                base_version.state == DeprecationState.DEPRECATED
                or target_version.state == DeprecationState.DEPRECATED
            ):
                warnings_list.append("One or both evaluated versions are marked DEPRECATED.")

            if base_version.deprecation_notice:
                warnings_list.append(
                    f"Base version notice: {base_version.deprecation_notice.reason}"
                )

            return CompatibilityReport(
                is_compatible=report.is_compatible,
                base_version=base_version.version_number,
                target_version=target_version.version_number,
                breaking_changes=report.breaking_changes,
                warnings=tuple(warnings_list),
                evaluated_at=datetime.now(timezone.utc),
            )

    def evaluate_version_strings(
        self, base_ver: str, target_ver: str
    ) -> CompatibilityReport:
        """Evaluate compatibility between two version string representations.

        Args:
            base_ver: Base version string (e.g. '1.0.0').
            target_ver: Target version string (e.g. '2.0.0').

        Returns:
            CompatibilityReport: Immutable compatibility evaluation report.
        """
        with self._lock:
            self._total_compatibility_checks += 1
            base_tuple = self._parse_semver(base_ver)
            target_tuple = self._parse_semver(target_ver)

            breaking_changes: List[str] = []
            warnings: List[str] = []
            is_compatible = True

            base_major, base_minor, _ = base_tuple
            target_major, target_minor, _ = target_tuple

            # Major version difference indicates breaking changes
            if target_major > base_major:
                is_compatible = False
                breaking_changes.append(
                    f"Major version upgrade from {base_ver} to {target_ver} contains breaking changes."
                )
            elif target_major < base_major:
                is_compatible = False
                breaking_changes.append(
                    f"Major version downgrade from {base_ver} to {target_ver} is unsupported."
                )

            # Minor version deprecation warnings
            if base_major == target_major and target_minor < base_minor:
                warnings.append(
                    f"Target minor version {target_ver} is older than base minor version {base_ver}."
                )

            logger.info(
                "Evaluated compatibility %s -> %s (compatible: %s, breaking: %d).",
                base_ver,
                target_ver,
                is_compatible,
                len(breaking_changes),
            )

            return CompatibilityReport(
                is_compatible=is_compatible,
                base_version=base_ver,
                target_version=target_ver,
                breaking_changes=tuple(breaking_changes),
                warnings=tuple(warnings),
                evaluated_at=datetime.now(timezone.utc),
            )

    def _parse_semver(self, ver_str: str) -> Tuple[int, int, int]:
        """Internal helper to parse semver tuple under lock."""
        parts = ver_str.lstrip("v").split(".")
        nums = []
        for p in parts[:3]:
            clean = "".join(filter(str.isdigit, p))
            nums.append(int(clean) if clean else 0)

        while len(nums) < 3:
            nums.append(0)

        return (nums[0], nums[1], nums[2])

    def get_compatibility_telemetry(self) -> Dict[str, int]:
        """Get internal compatibility evaluation counters under lock."""
        with self._lock:
            return {
                "total_compatibility_checks": self._total_compatibility_checks,
            }
