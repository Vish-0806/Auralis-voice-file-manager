"""Secret Manager (Phase 14.3.5).

Thread-safe manager for secret registration, access policy enforcement, value redaction algorithms,
audit access records tracking, and secure diagnostics snapshots. Never logs raw secret values.
"""

from datetime import datetime, timezone
import logging
import re
from threading import RLock
from typing import Dict, List, Optional, Tuple

from backend.application.config.exceptions import ConfigurationSourceError
from backend.application.config.models import (
    SecretAccessRecord,
    SecretDefinition,
    SecretEntry,
    SecretHealth,
    SecretPolicy,
    SecretReference,
    SecretSnapshot,
    SecretStatistics,
    SecretType,
)
from backend.application.config.secret_store import SecretStore

logger = logging.getLogger(__name__)


class SecretManager:
    """Production thread-safe secret manager enforcing access policies and value redaction."""

    def __init__(self, store: Optional[SecretStore] = None) -> None:
        """Initialize SecretManager.

        Args:
            store: Optional SecretStore instance.
        """
        self._lock = RLock()
        self._store = store or SecretStore()

        # Audit logs & Metrics
        self._access_records: List[SecretAccessRecord] = []
        self._access_count: int = 0
        self._modification_count: int = 0
        self._redaction_count: int = 0
        self._policy_violations_count: int = 0

    @property
    def store(self) -> SecretStore:
        """Get underlying SecretStore."""
        with self._lock:
            return self._store

    def redact(self, value: str, secret_type: SecretType = SecretType.PASSWORD) -> str:
        """Apply type-specific redaction to obscure secret values for logs and exports.

        Args:
            value: Input raw secret value string.
            secret_type: SecretType enum.

        Returns:
            str: Masked/redacted string representation.
        """
        with self._lock:
            self._redaction_count += 1

        if not value:
            return "********"

        if secret_type == SecretType.PASSWORD:
            return "********"

        elif secret_type == SecretType.TOKEN:
            prefix = value[:3] if len(value) >= 3 else "tok"
            return f"{prefix}********"

        elif secret_type == SecretType.API_KEY:
            prefix = value[:3] if len(value) >= 3 else "sk-"
            return f"{prefix}************"

        elif secret_type in (SecretType.CERTIFICATE, SecretType.PRIVATE_KEY):
            header = "-----BEGIN CERTIFICATE-----" if secret_type == SecretType.CERTIFICATE else "-----BEGIN PRIVATE KEY-----"
            footer = "-----END CERTIFICATE-----" if secret_type == SecretType.CERTIFICATE else "-----END PRIVATE KEY-----"
            return f"{header}\n...\n{footer}"

        elif secret_type == SecretType.CONNECTION_STRING:
            # Mask password in URI (e.g. postgresql://user:password@host:5432/db -> postgresql://user:****@host:5432/db)
            return re.sub(r":([^/@]+)@", r":****@", value)

        else:  # CUSTOM
            mask_len = min(len(value), 12)
            return "*" * max(mask_len, 8)

    def _record_access(self, secret_name: str, operation: str, allowed: bool) -> None:
        """Log access record without raw values."""
        record = SecretAccessRecord(
            secret_name=secret_name,
            operation=operation,
            timestamp=datetime.now(timezone.utc),
            allowed=allowed,
        )
        self._access_records.append(record)
        if len(self._access_records) > 500:
            self._access_records.pop(0)

    def register_secret(
        self,
        secret_name: str,
        raw_value: str,
        secret_type: SecretType = SecretType.PASSWORD,
        policy: Optional[SecretPolicy] = None,
    ) -> bool:
        """Register a new secret safely.

        Args:
            secret_name: Unique secret name string.
            raw_value: Raw sensitive secret value string.
            secret_type: Target SecretType.
            policy: Optional SecretPolicy instance.

        Returns:
            bool: True if registered.
        """
        with self._lock:
            effective_policy = policy or SecretPolicy()
            redacted = self.redact(raw_value, secret_type)
            entry = SecretEntry(
                secret_name=secret_name,
                secret_type=secret_type,
                raw_value=raw_value,
                redacted_value=redacted,
                policy=effective_policy,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            res = self._store.register_secret(entry)
            if res:
                self._modification_count += 1
                self._record_access(secret_name, "REGISTER", True)
            return res

    def update_secret(
        self,
        secret_name: str,
        raw_value: str,
        secret_type: SecretType = SecretType.PASSWORD,
        policy: Optional[SecretPolicy] = None,
    ) -> bool:
        """Update an existing secret value or policy safely.

        Args:
            secret_name: Target secret name.
            raw_value: Updated sensitive raw value.
            secret_type: Updated SecretType.
            policy: Optional updated SecretPolicy.

        Returns:
            bool: True if updated.
        """
        with self._lock:
            existing = self._store.get_secret(secret_name)
            if existing is None:
                return False

            if not existing.policy.allow_write:
                self._policy_violations_count += 1
                self._record_access(secret_name, "UPDATE", False)
                logger.warning("Secret policy violation: Write denied for secret '%s'.", secret_name)
                return False

            effective_policy = policy or existing.policy
            redacted = self.redact(raw_value, secret_type)
            updated_entry = SecretEntry(
                secret_name=secret_name,
                secret_type=secret_type,
                raw_value=raw_value,
                redacted_value=redacted,
                policy=effective_policy,
                created_at=existing.created_at,
                updated_at=datetime.now(timezone.utc),
            )
            res = self._store.update_secret(updated_entry)
            if res:
                self._modification_count += 1
                self._record_access(secret_name, "UPDATE", True)
            return res

    def remove_secret(self, secret_name: str) -> bool:
        """Remove a registered secret.

        Args:
            secret_name: Target secret name.

        Returns:
            bool: True if removed.
        """
        with self._lock:
            res = self._store.remove_secret(secret_name)
            if res:
                self._modification_count += 1
                self._record_access(secret_name, "REMOVE", True)
            return res

    def get_secret(self, secret_name: str) -> Optional[str]:
        """Get raw secret value if policy allows.

        Args:
            secret_name: Target secret name string.

        Returns:
            Optional[str]: Raw secret string or None if missing/denied.
        """
        with self._lock:
            self._access_count += 1
            entry = self._store.get_secret(secret_name)
            if entry is None:
                self._record_access(secret_name, "READ", False)
                return None

            if not entry.policy.allow_read:
                self._policy_violations_count += 1
                self._record_access(secret_name, "READ", False)
                logger.warning("Secret policy violation: Read denied for secret '%s'.", secret_name)
                return None

            self._record_access(secret_name, "READ", True)
            return entry.raw_value

    def get_redacted_secret(self, secret_name: str) -> Optional[str]:
        """Get redacted masked string representation for safe display.

        Args:
            secret_name: Target secret name.

        Returns:
            Optional[str]: Redacted string or None.
        """
        with self._lock:
            entry = self._store.get_secret(secret_name)
            if entry is None:
                return None
            return entry.redacted_value

    def list_secret_references(self) -> Tuple[SecretReference, ...]:
        """List safe metadata references for all registered secrets."""
        with self._lock:
            refs: List[SecretReference] = []
            for name in self._store.list_secret_names():
                entry = self._store.get_secret(name)
                if entry:
                    refs.append(
                        SecretReference(
                            secret_name=entry.secret_name,
                            secret_type=entry.secret_type,
                            redacted_value=entry.redacted_value,
                            policy=entry.policy,
                        )
                    )
            return tuple(refs)

    def create_snapshot(self) -> SecretSnapshot:
        """Create an immutable snapshot with redacted values only."""
        with self._lock:
            return self._store.create_snapshot()

    def health(self) -> SecretHealth:
        """Get health status of secret management subsystem."""
        with self._lock:
            return SecretHealth(
                is_healthy=True,
                issues=(),
                checked_at=datetime.now(timezone.utc),
            )

    def statistics(self) -> SecretStatistics:
        """Get secret management metrics."""
        with self._lock:
            return SecretStatistics(
                registered_secret_count=len(self._store.list_secret_names()),
                access_count=self._access_count,
                modification_count=self._modification_count,
                redaction_count=self._redaction_count,
                policy_violations_count=self._policy_violations_count,
            )
