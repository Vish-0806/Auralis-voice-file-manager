"""API Rate Limiter Implementation (Phase 15.8).

Thread-safe rate limiter managing rate limit rules, sliding window counters,
and token bucket accounting algorithms without Redis or network dependencies.
"""

from datetime import datetime, timezone
import logging
from threading import RLock
from typing import Dict, List, Optional, Tuple
import uuid

from backend.application.api.protection.exceptions import RateLimitException
from backend.application.api.protection.interfaces import IRateLimiter
from backend.application.api.protection.models import (
    RateLimitAlgorithm,
    RateLimitDecision,
    RateLimitRule,
    TokenBucket,
)

logger = logging.getLogger(__name__)


class RateLimiter(IRateLimiter):
    """Thread-safe in-memory rate limiter supporting sliding window and token bucket algorithms."""

    def __init__(self) -> None:
        """Initialize RateLimiter using Constructor Dependency Injection."""
        self._lock = RLock()
        self._rules: Dict[str, RateLimitRule] = {}

        # Sliding window state: map of (client_id, rule_id) -> list of timestamp floats
        self._window_history: Dict[Tuple[str, str], List[float]] = {}

        # Token bucket state: map of (client_id, rule_id) -> TokenBucket
        self._token_buckets: Dict[Tuple[str, str], TokenBucket] = {}

        self._total_evaluations = 0
        self._total_allowed = 0
        self._total_rejected = 0

    def register_rule(self, rule: RateLimitRule) -> RateLimitRule:
        """Register a new rate limit rule.

        Args:
            rule: Immutable RateLimitRule instance.

        Returns:
            RateLimitRule: Registered rule model.

        Raises:
            RateLimitException: If rule_id is already registered.
        """
        with self._lock:
            if rule.rule_id in self._rules:
                raise RateLimitException(
                    f"Rate limit rule with ID '{rule.rule_id}' is already registered."
                )

            self._rules[rule.rule_id] = rule
            logger.info("Registered rate limit rule ID '%s' (%s).", rule.rule_id, rule.name)
            return rule

    def unregister_rule(self, rule_id: str) -> Optional[RateLimitRule]:
        """Unregister a rate limit rule by rule ID.

        Args:
            rule_id: Unique rule identifier.

        Returns:
            Optional[RateLimitRule]: Removed rule if present, else None.
        """
        with self._lock:
            rule = self._rules.pop(rule_id, None)
            if rule is not None:
                logger.info("Unregistered rate limit rule ID '%s'.", rule_id)
            return rule

    def lookup_rule(self, rule_id: str) -> Optional[RateLimitRule]:
        """Look up a rate limit rule by ID.

        Args:
            rule_id: Unique rule identifier.

        Returns:
            Optional[RateLimitRule]: Rule model if found, else None.
        """
        with self._lock:
            return self._rules.get(rule_id)

    def evaluate_rate_limit(
        self, client_id: str, rule_id: str
    ) -> RateLimitDecision:
        """Evaluate rate limit quota for a client against a registered rule ID.

        Args:
            client_id: Target client identifier.
            rule_id: Target registered rule ID.

        Returns:
            RateLimitDecision: Result snapshot of rate limit evaluation.

        Raises:
            RateLimitException: If target rule_id is not registered.
        """
        with self._lock:
            self._total_evaluations += 1
            rule = self._rules.get(rule_id)
            if rule is None:
                raise RateLimitException(
                    f"Rate limit rule ID '{rule_id}' not found for evaluation."
                )

            decision_id = f"dec_{uuid.uuid4().hex[:8]}"
            now = datetime.now(timezone.utc)
            now_ts = now.timestamp()

            if rule.algorithm == RateLimitAlgorithm.TOKEN_BUCKET:
                return self._evaluate_token_bucket(client_id, rule, decision_id, now)

            # Default to SLIDING_WINDOW / FIXED_WINDOW
            return self._evaluate_sliding_window(client_id, rule, decision_id, now_ts, now)

    def _evaluate_sliding_window(
        self,
        client_id: str,
        rule: RateLimitRule,
        decision_id: str,
        now_ts: float,
        now: datetime,
    ) -> RateLimitDecision:
        """Internal helper for sliding window rate limit evaluation."""
        key = (client_id, rule.rule_id)
        history = self._window_history.get(key, [])

        # Purge timestamps outside window
        cutoff = now_ts - float(rule.window_seconds)
        active_history = [ts for ts in history if ts > cutoff]

        if len(active_history) >= rule.max_requests:
            self._total_rejected += 1
            self._window_history[key] = active_history
            retry_after = float(rule.window_seconds)
            if active_history:
                oldest = active_history[0]
                retry_after = max(0.1, (oldest + rule.window_seconds) - now_ts)

            logger.info("Rate limit EXCEEDED for client '%s' on rule '%s'.", client_id, rule.rule_id)
            return RateLimitDecision(
                decision_id=decision_id,
                is_allowed=False,
                remaining_tokens=0,
                retry_after_seconds=retry_after,
                reset_at=datetime.fromtimestamp(now_ts + retry_after, tz=timezone.utc),
                rule_id=rule.rule_id,
            )

        active_history.append(now_ts)
        self._window_history[key] = active_history
        self._total_allowed += 1
        remaining = max(0, rule.max_requests - len(active_history))

        logger.debug("Rate limit ALLOWED for client '%s' on rule '%s' (%d remaining).", client_id, rule.rule_id, remaining)
        return RateLimitDecision(
            decision_id=decision_id,
            is_allowed=True,
            remaining_tokens=remaining,
            retry_after_seconds=0.0,
            reset_at=datetime.fromtimestamp(now_ts + float(rule.window_seconds), tz=timezone.utc),
            rule_id=rule.rule_id,
        )

    def _evaluate_token_bucket(
        self,
        client_id: str,
        rule: RateLimitRule,
        decision_id: str,
        now: datetime,
    ) -> RateLimitDecision:
        """Internal helper for token bucket rate limit evaluation."""
        key = (client_id, rule.rule_id)
        bucket = self._token_buckets.get(key)

        capacity = rule.burst_capacity if rule.burst_capacity > 0 else rule.max_requests
        refill_rate = rule.refill_rate if rule.refill_rate > 0.0 else (rule.max_requests / float(rule.window_seconds))

        if bucket is None:
            bucket = TokenBucket(
                bucket_id=f"tb_{uuid.uuid4().hex[:8]}",
                client_id=client_id,
                capacity=capacity,
                current_tokens=float(capacity),
                refill_rate=refill_rate,
                last_refill_at=now,
            )

        # Calculate refilled tokens based on elapsed time
        elapsed = max(0.0, (now - bucket.last_refill_at).total_seconds())
        refilled_tokens = min(float(capacity), bucket.current_tokens + (elapsed * refill_rate))

        if refilled_tokens >= 1.0:
            remaining = refilled_tokens - 1.0
            updated_bucket = TokenBucket(
                bucket_id=bucket.bucket_id,
                client_id=client_id,
                capacity=capacity,
                current_tokens=remaining,
                refill_rate=refill_rate,
                last_refill_at=now,
            )
            self._token_buckets[key] = updated_bucket
            self._total_allowed += 1

            return RateLimitDecision(
                decision_id=decision_id,
                is_allowed=True,
                remaining_tokens=int(remaining),
                retry_after_seconds=0.0,
                reset_at=now,
                rule_id=rule.rule_id,
            )

        # Not enough tokens
        retry_after = (1.0 - refilled_tokens) / refill_rate if refill_rate > 0 else 1.0
        updated_bucket = TokenBucket(
            bucket_id=bucket.bucket_id,
            client_id=client_id,
            capacity=capacity,
            current_tokens=refilled_tokens,
            refill_rate=refill_rate,
            last_refill_at=now,
        )
        self._token_buckets[key] = updated_bucket
        self._total_rejected += 1

        return RateLimitDecision(
            decision_id=decision_id,
            is_allowed=False,
            remaining_tokens=0,
            retry_after_seconds=retry_after,
            reset_at=now,
            rule_id=rule.rule_id,
        )

    def list_rules(self) -> Tuple[RateLimitRule, ...]:
        """List all registered rate limit rules.

        Returns:
            Tuple[RateLimitRule, ...]: Immutable tuple of rules.
        """
        with self._lock:
            return tuple(self._rules.values())

    def count_rules(self) -> int:
        """Get total count of registered rate limit rules.

        Returns:
            int: Rule count.
        """
        with self._lock:
            return len(self._rules)

    def clear(self) -> None:
        """Clear all registered rules and active quota tracking state."""
        with self._lock:
            self._rules.clear()
            self._window_history.clear()
            self._token_buckets.clear()
            logger.info("RateLimiter cleared.")

    def get_limiter_telemetry(self) -> Dict[str, int]:
        """Get internal rate limiter telemetry counters under lock."""
        with self._lock:
            return {
                "total_evaluations": self._total_evaluations,
                "total_allowed": self._total_allowed,
                "total_rejected": self._total_rejected,
                "registered_rules_count": len(self._rules),
            }
