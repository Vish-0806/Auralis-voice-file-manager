"""Backward compatibility wrapper delegating to backend/ai.

TODO: This legacy wrapper can be removed once all references to ai_engine are deleted.
"""

from ai.command_parser import parse_command

__all__ = ["parse_command"]
