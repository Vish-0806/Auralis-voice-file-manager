"""Backward compatibility wrapper delegating to backend/ai.

TODO: This legacy wrapper can be removed once all references to ai_engine are deleted.
"""

from ai.intent_classifier import classify_intent

__all__ = ["classify_intent"]
