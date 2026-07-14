"""User Context Expiration checks and policies."""

import time
from typing import Any, Dict


class ContextExpiration:
    """Manages context entry lifecycle policies, evaluating and purging expired records."""

    @staticmethod
    def is_expired(entry: Dict[str, Any]) -> bool:
        """Determines if a context record dictionary is expired.

        Args:
            entry: Context item dictionary containing value, expires_at, etc.

        Returns:
            True if the entry has expired, False otherwise.
        """
        expires_at = entry.get("expires_at")
        if expires_at is None:
            return False
        return time.time() > expires_at

    @classmethod
    def clear_expired_context(cls, metadata_bag: Dict[str, Any]) -> Dict[str, Any]:
        """Iterates through and filters out expired context items from metadata.

        Args:
            metadata_bag: Active context dictionary storage.

        Returns:
            A cleaned metadata dictionary containing only active (non-expired) records.
        """
        cleaned = {}
        for key, entry in metadata_bag.items():
            if isinstance(entry, dict) and "value" in entry:
                if not cls.is_expired(entry):
                    cleaned[key] = entry
            else:
                # Retain entries that don't match the standard ContextItem schema as a safeguard
                cleaned[key] = entry
        return cleaned
