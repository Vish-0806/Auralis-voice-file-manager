"""Configuration Certifier (Phase 14.3.6).

Production dependency graph analysis, runtime validation, diagnostics aggregation,
subsystem health audit, and production certification engine.
"""

from datetime import datetime, timezone
import logging
from threading import RLock
from typing import List, Optional, Tuple

from backend.application.config.configuration_source_manager import ConfigurationSourceManager
from backend.application.config.models import (
    ConfigurationCertificationResult,
    ConfigurationDiagnostics,
    ConfigurationHealth,
    ConfigurationRuntimeState,
    ConfigurationStatistics,
)

logger = logging.getLogger(__name__)


class ConfigurationCertifier:
    """Production certification engine for Configuration Runtime."""

    def __init__(self, source_manager: Optional[ConfigurationSourceManager] = None) -> None:
        """Initialize ConfigurationCertifier using Constructor Dependency Injection.

        Args:
            source_manager: Optional ConfigurationSourceManager instance.
        """
        self._lock = RLock()
        self._source_manager = source_manager or ConfigurationSourceManager()

    def certify(self) -> ConfigurationCertificationResult:
        """Execute complete production certification audit across all runtime subsystems.

        Returns:
            ConfigurationCertificationResult: Certification result report.
        """
        with self._lock:
            passed = 0
            failed = 0
            issues: List[str] = []

            # 1. Source registry check
            sources = self._source_manager.registry.list_sources()
            if len(sources) > 0:
                passed += 1
            else:
                failed += 1
                issues.append("Certification Failure: No configuration sources registered in SourceRegistry.")

            # 2. Source priority uniqueness check
            priorities = [s.priority for s in sources]
            if len(priorities) == len(set(priorities)):
                passed += 1
            else:
                failed += 1
                issues.append("Certification Warning: Duplicate source priorities detected in SourceRegistry.")

            # 3. Active profile validity check
            try:
                active_profile = self._source_manager.get_active_profile()
                if active_profile is not None and active_profile.profile_name:
                    passed += 1
                else:
                    failed += 1
                    issues.append("Certification Failure: Active configuration profile is invalid or missing.")
            except Exception as e:
                failed += 1
                issues.append(f"Certification Failure: Error retrieving active profile: {str(e)}")

            # 4. Schema manager & Resolver check
            try:
                resolve_res = self._source_manager.resolve_all()
                if len(resolve_res.errors) == 0:
                    passed += 1
                else:
                    failed += 1
                    issues.append(f"Certification Failure: {len(resolve_res.errors)} errors encountered during schema resolution.")
            except Exception as e:
                failed += 1
                issues.append(f"Certification Failure: Resolver exception during certification: {str(e)}")

            # 5. Validator check
            try:
                val_res = self._source_manager.validate()
                if val_res.is_valid:
                    passed += 1
                else:
                    failed += 1
                    for err in val_res.errors:
                        issues.append(f"Certification Validation Error [{err.key}]: {err.message}")
            except Exception as e:
                failed += 1
                issues.append(f"Certification Failure: Validator exception during certification: {str(e)}")

            # 6. Feature flag subsystem health check
            feat_health = self._source_manager.feature_manager.health()
            if feat_health.is_healthy:
                passed += 1
            else:
                failed += 1
                issues.extend([f"Feature Flag Subsystem Issue: {i}" for i in feat_health.issues])

            # 7. Secret manager health check
            sec_health = self._source_manager.secret_manager.health()
            if sec_health.is_healthy:
                passed += 1
            else:
                failed += 1
                issues.extend([f"Secret Subsystem Issue: {i}" for i in sec_health.issues])

            # 8. Overall aggregate health check
            agg_health = self._source_manager.health()
            if agg_health.is_healthy:
                passed += 1
            else:
                failed += 1
                issues.extend(agg_health.issues)

            total_checks = passed + failed
            avail_pct = (passed / total_checks * 100.0) if total_checks > 0 else 0.0
            is_certified = failed == 0

            logger.info("Configuration certifier completed: certified=%s (passed=%d, failed=%d, avail=%.1f%%).", is_certified, passed, failed, avail_pct)

            return ConfigurationCertificationResult(
                is_certified=is_certified,
                checks_passed=passed,
                checks_failed=failed,
                issues=tuple(issues),
                availability_percentage=avail_pct,
                certified_at=datetime.now(timezone.utc),
            )

    def validate_runtime(self) -> bool:
        """Validate configuration runtime readiness."""
        cert = self.certify()
        return cert.is_certified

    def diagnostics(self) -> ConfigurationDiagnostics:
        """Get aggregate configuration diagnostics snapshot."""
        with self._lock:
            return self._source_manager.diagnostics()

    def health(self) -> ConfigurationHealth:
        """Get aggregate health snapshot."""
        with self._lock:
            return self._source_manager.health()

    def statistics(self) -> ConfigurationStatistics:
        """Get aggregate statistics metrics snapshot."""
        with self._lock:
            return self._source_manager.statistics()
