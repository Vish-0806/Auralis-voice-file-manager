"""Health Aggregator implementation for Auralis (Phase 13.9).

Aggregates diagnostic health reports and capabilities across all 12 assistant and system runtimes:
Assistant, Conversation, Dialogue, Decision, Memory, Response, Voice, Proactive, Execution, Brain, AI, OS.
Calculates availability percentage and sub-runtime health statuses. Thread-safe using threading.RLock().
"""

from datetime import datetime, timezone
import logging
import threading
from typing import Dict, List, Optional

from brain.assistant.integration.interfaces import IHealthAggregator, IRuntimeRegistry
from brain.assistant.integration.models import AssistantIntegrationHealth

logger = logging.getLogger(__name__)

_KNOWN_RUNTIMES = [
    "assistant_runtime",
    "conversation_runtime",
    "dialogue_runtime",
    "decision_runtime",
    "memory_runtime",
    "response_runtime",
    "voice_runtime",
    "proactive_runtime",
    "execution_runtime",
    "brain_runtime",
    "ai_runtime",
    "os_runtime",
]


class HealthAggregator(IHealthAggregator):
    """Thread-safe health aggregator collecting diagnostics and computing system-wide availability."""

    def __init__(self, lock: Optional[threading.RLock] = None) -> None:
        self._lock = lock or threading.RLock()

    def aggregate_health(self, registry: IRuntimeRegistry) -> AssistantIntegrationHealth:
        """Collect diagnostic health snapshots across all registered runtimes and compute availability percentage."""
        with self._lock:
            subsystem_health: Dict[str, bool] = {}
            issues: List[str] = []

            healthy_count = 0
            total_runtimes = len(_KNOWN_RUNTIMES)

            for rt_name in _KNOWN_RUNTIMES:
                rt_inst = registry.get_runtime(rt_name)
                if rt_inst is None:
                    subsystem_health[rt_name] = False
                    issues.append(f"Subsystem runtime '{rt_name}' is not registered")
                    continue

                is_healthy = True
                if hasattr(rt_inst, "get_health"):
                    try:
                        h = rt_inst.get_health()
                        if hasattr(h, "healthy"):
                            is_healthy = bool(getattr(h, "healthy"))
                    except Exception as exc:
                        is_healthy = False
                        logger.debug("Failed to inspect health for %s: %s", rt_name, exc)

                subsystem_health[rt_name] = is_healthy
                if is_healthy:
                    healthy_count += 1
                else:
                    issues.append(f"Subsystem runtime '{rt_name}' reported unhealthy status")

            availability_pct = (healthy_count / float(total_runtimes)) * 100.0 if total_runtimes > 0 else 0.0

            if availability_pct >= 100.0:
                status_str = "READY"
            elif availability_pct >= 50.0:
                status_str = "DEGRADED"
            else:
                status_str = "UNHEALTHY"

            return AssistantIntegrationHealth(
                status=status_str,
                healthy=availability_pct >= 50.0,
                availability_percentage=availability_pct,
                subsystem_health=subsystem_health,
                detected_issues=issues,
                checked_at=datetime.now(timezone.utc),
                metadata={"healthy_count": healthy_count, "total_runtimes": total_runtimes},
            )
