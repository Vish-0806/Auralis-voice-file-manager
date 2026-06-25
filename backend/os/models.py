"""
Module: backend.os.models

Responsibility:
    Provides platform-neutral data models for OSAL transactions.

Future Expansion:
    Support binary streaming models for screen capture data.
"""

from typing import Dict, Any, List, Optional


class OSProcessInfo:
    """Represents a platform-neutral operating system process."""
    
    def __init__(self, pid: int, name: str, cpu_percent: float, memory_bytes: int) -> None:
        self.pid: int = pid
        self.name: str = name
        self.cpu_percent: float = cpu_percent
        self.memory_bytes: int = memory_bytes


class StorageDeviceMetrics:
    """Represents storage device capacity metrics."""
    
    def __init__(self, path: str, total_bytes: int, free_bytes: int) -> None:
        self.path: str = path
        self.total_bytes: int = total_bytes
        self.free_bytes: int = free_bytes
