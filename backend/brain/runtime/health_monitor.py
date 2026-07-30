"""Health Monitor for the Auralis Brain Runtime (Phase 9.7).

Aggregates health checks across all 6 subsystem runtimes into a unified BrainRuntimeHealth snapshot.
"""

from datetime import datetime, timezone
import logging
import threading
from typing import Any, Dict, List, Optional

from brain.runtime.brain_models import (
    BrainRuntimeHealth,
    RuntimeComponent,
    SubsystemHealth,
)
from brain.runtime.dependency_registry import DependencyRegistry

logger = logging.getLogger(__name__)


class HealthMonitor:
    """Thread-safe health monitoring aggregator for the Auralis Brain architecture.

    Responsibilities:
    - Query health snapshots from Voice, Conversation, Reasoning, Planning, Execution, and Filesystem runtimes.
    - Produce unified BrainRuntimeHealth report with issue detection.
    """

    def __init__(
        self,
        registry: Optional[DependencyRegistry] = None,
        started_at: Optional[datetime] = None,
    ) -> None:
        self._lock = threading.RLock()
        self._registry = registry or DependencyRegistry()
        self._started_at = started_at or datetime.now(timezone.utc)
        logger.debug("HealthMonitor initialized")

    def check_health(self) -> BrainRuntimeHealth:
        """Perform a complete health check across all registered subsystems.

        Returns:
            Immutable :class:`BrainRuntimeHealth` snapshot.
        """
        with self._lock:
            subsystems: Dict[str, SubsystemHealth] = {}
            overall_healthy = True
            issues: List[str] = []

            for comp in RuntimeComponent:
                if comp == RuntimeComponent.BRAIN:
                    continue
                name = comp.value
                sub_health = self.check_subsystem(comp)
                subsystems[name] = sub_health
                if not sub_health.healthy:
                    overall_healthy = False
                    issues.append(f"Subsystem {name} is unhealthy ({sub_health.status})")

            uptime = (datetime.now(timezone.utc) - self._started_at).total_seconds()
            status_str = "READY" if overall_healthy else "DEGRADED"

            health = BrainRuntimeHealth(
                healthy=overall_healthy,
                status=status_str,
                subsystems=subsystems,
                active_requests=0,
                uptime_seconds=round(uptime, 2),
                checked_at=datetime.now(timezone.utc),
                metadata={"issues_detected": len(issues), "issues": issues},
            )
            logger.info("Health Check: healthy=%s status=%s subsystems=%d", overall_healthy, status_str, len(subsystems))
            return health

    def check_subsystem(self, component: RuntimeComponent) -> SubsystemHealth:
        """Query health snapshot from a single subsystem.

        Args:
            component: Target subsystem component.

        Returns:
            Immutable :class:`SubsystemHealth`.
        """
        name = component.value
        with self._lock:
            instance = self._registry.get(component)
            if instance is None:
                return SubsystemHealth(
                    subsystem_name=name,
                    healthy=False,
                    status="MISSING",
                    issues=["Subsystem instance not registered"],
                )

            try:
                if hasattr(instance, "health_check") and callable(instance.health_check):
                    raw = instance.health_check()
                    return self._map_to_subsystem_health(name, raw)
                elif hasattr(instance, "status"):
                    st = getattr(instance, "status")
                    st_val = st.value if hasattr(st, "value") else str(st)
                    is_ok = st_val in ("READY", "OK", "HEALTHY", "LISTENING")
                    return SubsystemHealth(
                        subsystem_name=name,
                        healthy=is_ok,
                        status=st_val,
                    )
                else:
                    return SubsystemHealth(
                        subsystem_name=name,
                        healthy=True,
                        status="READY",
                    )
            except Exception as exc:
                logger.error("HealthMonitor: Exception checking %s health: %s", name, exc)
                return SubsystemHealth(
                    subsystem_name=name,
                    healthy=False,
                    status="ERROR",
                    issues=[f"Health check failed with error: {exc}"],
                )

    def is_healthy(self) -> bool:
        """Quick boolean health query.

        Returns:
            True if all subsystems are healthy.
        """
        return self.check_health().healthy

    # ------------------------------------------------------------------
    # Internal Helpers
    # ------------------------------------------------------------------

    def _map_to_subsystem_health(self, name: str, raw: Any) -> SubsystemHealth:
        healthy = getattr(raw, "healthy", True)
        status = getattr(raw, "status", "READY")
        if hasattr(status, "value"):
            status = status.value
        components = getattr(raw, "components", {})
        if isinstance(components, list):
            components = {c: True for c in components}
        issues = getattr(raw, "issues", [])
        if not isinstance(issues, list):
            issues = [str(issues)]

        return SubsystemHealth(
            subsystem_name=name,
            healthy=bool(healthy),
            status=str(status),
            components=components if isinstance(components, dict) else {},
            issues=list(issues),
        )
