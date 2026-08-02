"""Global Singleton Accessors for the Execution Analytics & Observability Runtime (Phase 12.7).

Provides thread-safe accessors (get_analytics_runtime, reset_analytics_runtime) for the global AnalyticsRuntime instance.
"""

import logging
import threading
from typing import Optional

from brain.execution.analytics.analytics_provider import AnalyticsProvider
from brain.execution.analytics.analytics_runtime import AnalyticsRuntime

logger = logging.getLogger(__name__)

_global_analytics_lock = threading.RLock()
_global_analytics_runtime: Optional[AnalyticsRuntime] = None


def get_analytics_runtime(
    provider: Optional[AnalyticsProvider] = None,
    reset: bool = False,
) -> AnalyticsRuntime:
    """Singleton accessor for the global AnalyticsRuntime instance.

    Thread-safe. Automatically initializes on creation.

    Args:
        provider: Optional AnalyticsProvider instance.
        reset: If True, resets and creates a new runtime instance.

    Returns:
        AnalyticsRuntime singleton instance.
    """
    global _global_analytics_runtime
    with _global_analytics_lock:
        if reset or _global_analytics_runtime is None:
            if _global_analytics_runtime is not None:
                try:
                    _global_analytics_runtime.shutdown()
                except Exception:
                    pass
            _global_analytics_runtime = AnalyticsRuntime(provider=provider)
            _global_analytics_runtime.initialize()
        return _global_analytics_runtime


def reset_analytics_runtime() -> None:
    """Resets the global AnalyticsRuntime instance.

    Thread-safe. Gracefully shuts down active runtime and clears singleton instance.
    """
    global _global_analytics_runtime
    with _global_analytics_lock:
        if _global_analytics_runtime is not None:
            try:
                _global_analytics_runtime.shutdown()
                _global_analytics_runtime.clear()
            except Exception:
                pass
            _global_analytics_runtime = None
        logger.debug("Global AnalyticsRuntime reset")
