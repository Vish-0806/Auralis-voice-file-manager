"""Self-Correction & Recovery subsystem package for Auralis."""

from __future__ import annotations

from .models import FailureType, FallbackOption, RecoveryStrategy, RecoveryResult
from .fallback_registry import FallbackRegistry
from .failure_analyzer import FailureAnalyzer
from .recovery_strategy import RecoveryStrategyBuilder
from .recovery_engine import RecoveryEngine

__all__ = [
    "FailureType",
    "FallbackOption",
    "RecoveryStrategy",
    "RecoveryResult",
    "FallbackRegistry",
    "FailureAnalyzer",
    "RecoveryStrategyBuilder",
    "RecoveryEngine",
]
