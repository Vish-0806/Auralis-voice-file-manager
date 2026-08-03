"""Rule Evaluator implementation for Auralis (Phase 13.8).

Evaluates proactive rules, condition checks, cooldown periods, duplicate suppression, and confidence rules.
Does NOT execute automation workflows or OS commands. Thread-safe using threading.RLock().
"""

from datetime import datetime, timezone
import logging
import threading
import time
from typing import Dict, Optional

from brain.assistant.proactive.exceptions import RuleValidationException
from brain.assistant.proactive.interfaces import IRuleEvaluator
from brain.assistant.proactive.models import (
    EvaluationResult,
    ProactiveContext,
    ProactiveEvent,
    ProactiveRule,
)

logger = logging.getLogger(__name__)


class RuleEvaluator(IRuleEvaluator):
    """Thread-safe rule evaluator evaluating triggers, cooldowns, and suppression rules."""

    def __init__(self, lock: Optional[threading.RLock] = None) -> None:
        self._lock = lock or threading.RLock()
        self._rules: Dict[str, ProactiveRule] = {}
        self._last_trigger_times: Dict[str, float] = {}

        # Cooldown & Suppression metrics
        self._cooldowns_enforced = 0
        self._suppressed_count = 0

    @property
    def cooldowns_enforced_count(self) -> int:
        with self._lock:
            return self._cooldowns_enforced

    @property
    def suppressed_count(self) -> int:
        with self._lock:
            return self._suppressed_count

    def register_rule(self, rule: ProactiveRule) -> None:
        """Register a ProactiveRule model instance."""
        if not isinstance(rule, ProactiveRule) or not rule.rule_id:
            raise RuleValidationException("rule must be a valid ProactiveRule with non-empty rule_id")

        with self._lock:
            self._rules[rule.rule_id] = rule
            logger.debug("Registered proactive rule id=%s name='%s'", rule.rule_id, rule.name)

    def evaluate_rule(
        self,
        rule: ProactiveRule,
        context: ProactiveContext,
        event: Optional[ProactiveEvent] = None,
    ) -> EvaluationResult:
        """Evaluate whether a proactive rule should trigger."""
        if not isinstance(rule, ProactiveRule):
            raise RuleValidationException("rule must be an instance of ProactiveRule")

        with self._lock:
            # 1. Enabled check
            if not rule.enabled:
                return EvaluationResult.REJECTED

            # 2. Cooldown check
            now = time.time()
            last = self._last_trigger_times.get(rule.rule_id, 0.0)
            if last > 0.0 and (now - last) < rule.cooldown_seconds:
                self._cooldowns_enforced += 1
                logger.debug("Rule id=%s cooldown active (%.1fs remaining)", rule.rule_id, rule.cooldown_seconds - (now - last))
                return EvaluationResult.COOLDOWN_ACTIVE

            # 3. Event Type matching
            if event is not None and rule.event_type != "*":
                if event.event_type != rule.event_type:
                    return EvaluationResult.NO_ACTION

            # 4. Min confidence check
            conf = float(context.context_variables.get("confidence", 1.0))
            if conf < rule.min_confidence:
                self._suppressed_count += 1
                logger.debug("Rule id=%s suppressed due to low confidence %.2f < %.2f", rule.rule_id, conf, rule.min_confidence)
                return EvaluationResult.SUPPRESSED

            # 5. Conditions evaluation
            for cond_key, expected_val in rule.conditions.items():
                actual_val = context.context_variables.get(cond_key)
                if actual_val != expected_val:
                    return EvaluationResult.NO_ACTION

            # Rule triggered successfully
            self._last_trigger_times[rule.rule_id] = now
            logger.info("Rule id=%s name='%s' TRIGGERED successfully", rule.rule_id, rule.name)
            return EvaluationResult.TRIGGERED

    def clear(self) -> None:
        """Reset rule evaluator state."""
        with self._lock:
            self._rules.clear()
            self._last_trigger_times.clear()
            self._cooldowns_enforced = 0
            self._suppressed_count = 0
