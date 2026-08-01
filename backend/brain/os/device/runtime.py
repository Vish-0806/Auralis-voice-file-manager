"""Singleton accessor for Device Runtime (Phase 11.7).

Provides thread-safe singleton access for DeviceRuntime coordinator.
"""

import threading
from typing import Optional

from brain.os.device.device_runtime import DeviceRuntime

_device_runtime_lock = threading.RLock()
_device_instance: Optional[DeviceRuntime] = None


def get_device_runtime() -> DeviceRuntime:
    """Get or initialize singleton DeviceRuntime instance."""
    global _device_instance
    with _device_runtime_lock:
        if _device_instance is None:
            _device_instance = DeviceRuntime()
            _device_instance.initialize()
        return _device_instance


def reset_device_runtime() -> None:
    """Reset singleton instance (used for testing and teardown)."""
    global _device_instance
    with _device_runtime_lock:
        if _device_instance is not None:
            _device_instance.shutdown()
            _device_instance = None
