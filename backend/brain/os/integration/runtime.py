"""Singleton accessor for Integration Runtime (Phase 11.9).

Provides thread-safe singleton access for IntegrationRuntime coordinator.
"""

import threading
from typing import Optional

from brain.os.integration.integration_runtime import IntegrationRuntime

_integration_runtime_lock = threading.RLock()
_integration_instance: Optional[IntegrationRuntime] = None


def get_integration_runtime() -> IntegrationRuntime:
    """Get or initialize singleton IntegrationRuntime instance."""
    global _integration_instance
    with _integration_runtime_lock:
        if _integration_instance is None:
            _integration_instance = IntegrationRuntime()
            _integration_instance.initialize()
        return _integration_instance


def reset_integration_runtime() -> None:
    """Reset singleton instance (used for testing and teardown)."""
    global _integration_instance
    with _integration_runtime_lock:
        if _integration_instance is not None:
            _integration_instance.shutdown()
            _integration_instance = None
