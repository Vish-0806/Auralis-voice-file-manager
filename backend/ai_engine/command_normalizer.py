"""Backward compatibility wrapper delegating to backend/ai.

TODO: This legacy wrapper can be removed once all references to ai_engine are deleted.
"""

from ai.command_normalizer import normalize_command, normalize_target

__all__ = ["normalize_command", "normalize_target"]
