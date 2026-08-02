"""Intent Provider for the Auralis Intent Resolution Subsystem (Phase 12.2).

Aggregates Recognizer, Extractor, Resolver, and Validator into a unified, thread-safe provider.
Supports end-to-end resolution, health checks, statistics collection, and diagnostics.
"""

from datetime import datetime, timezone
import logging
import threading
import time
from typing import Any, Dict, List, Optional

from brain.execution.intent.entity_extractor import EntityExtractor
from brain.execution.intent.exceptions import IntentResolutionError
from brain.execution.intent.intent_models import (
    AmbiguityLevel,
    IntentContext,
    IntentHealth,
    IntentResolution,
    ResolutionStatistics,
    ResolutionStatus,
)
from brain.execution.intent.intent_recognizer import IntentRecognizer
from brain.execution.intent.intent_resolver import IntentResolver
from brain.execution.intent.intent_validator import IntentValidator
from brain.execution.intent.interfaces import (
    IEntityExtractor,
    IIntentProvider,
    IIntentRecognizer,
    IIntentResolver,
    IIntentValidator,
)

logger = logging.getLogger(__name__)


class IntentProvider(IIntentProvider):
    """Thread-safe provider aggregating intent recognition, extraction, resolution, and validation."""

    def __init__(
        self,
        recognizer: Optional[IIntentRecognizer] = None,
        extractor: Optional[IEntityExtractor] = None,
        resolver: Optional[IIntentResolver] = None,
        validator: Optional[IIntentValidator] = None,
    ) -> None:
        """Initializes IntentProvider with injected or default components."""
        self._lock = threading.RLock()
        self._recognizer = recognizer or IntentRecognizer()
        self._extractor = extractor or EntityExtractor()
        self._resolver = resolver or IntentResolver()
        self._validator = validator or IntentValidator()

        self._total_resolutions = 0
        self._resolved_count = 0
        self._ambiguous_count = 0
        self._failed_count = 0
        self._total_resolution_time_ms = 0.0
        self._resolutions_by_category: Dict[str, int] = {}

    def resolve_intent(
        self,
        text: str,
        context: Optional[IntentContext] = None,
    ) -> IntentResolution:
        """Process input text through recognition, extraction, resolution, and validation.

        Args:
            text: User prompt text.
            context: Optional IntentContext.

        Returns:
            Fully validated IntentResolution model.
        """
        start_time = time.perf_counter()
        with self._lock:
            self._total_resolutions += 1

        try:
            user_intent = self._recognizer.recognize(text)
            entities = self._extractor.extract_entities(text)
            resolution = self._resolver.resolve(
                text=text,
                intent=user_intent,
                entities=entities,
                context=context,
            )

            # Validate resolution
            validation_diagnostics = self._validator.validate(resolution, context=context)

            # If validation diagnostics contain critical security alerts or errors, update status
            eff_status = resolution.status
            eff_ambiguity = resolution.ambiguity_level
            combined_diagnostics = list(resolution.diagnostics) + validation_diagnostics

            if any("SECURITY_ALERT" in d for d in validation_diagnostics):
                eff_status = ResolutionStatus.INVALID
            elif any("Missing required" in d for d in validation_diagnostics):
                if eff_status == ResolutionStatus.RESOLVED:
                    eff_status = ResolutionStatus.AMBIGUOUS
                    eff_ambiguity = AmbiguityLevel.MEDIUM

            elapsed_ms = (time.perf_counter() - start_time) * 1000.0

            final_resolution = IntentResolution(
                resolution_id=resolution.resolution_id,
                status=eff_status,
                primary_intent=resolution.primary_intent,
                entities=resolution.entities,
                candidates=resolution.candidates,
                ambiguity_level=eff_ambiguity,
                diagnostics=combined_diagnostics,
                execution_time_ms=elapsed_ms,
                created_at=resolution.created_at,
                metadata=resolution.metadata,
            )

            with self._lock:
                if final_resolution.status == ResolutionStatus.RESOLVED:
                    self._resolved_count += 1
                elif final_resolution.status == ResolutionStatus.AMBIGUOUS:
                    self._ambiguous_count += 1
                else:
                    self._failed_count += 1

                self._total_resolution_time_ms += elapsed_ms

                cat_key = user_intent.category.value
                self._resolutions_by_category[cat_key] = self._resolutions_by_category.get(cat_key, 0) + 1

            return final_resolution

        except Exception as exc:
            logger.error("Intent resolution failed: %s", exc)
            with self._lock:
                self._failed_count += 1

            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return IntentResolution(
                status=ResolutionStatus.FAILED,
                diagnostics=[f"Resolution Exception: {str(exc)}"],
                execution_time_ms=elapsed_ms,
                created_at=datetime.now(timezone.utc),
            )

    def health_check(self) -> IntentHealth:
        """Report component health statuses."""
        with self._lock:
            registered = {
                "IntentRecognizer": self._recognizer is not None,
                "EntityExtractor": self._extractor is not None,
                "IntentResolver": self._resolver is not None,
                "IntentValidator": self._validator is not None,
            }
            all_ok = all(registered.values())

            return IntentHealth(
                status="READY" if all_ok else "ERROR",
                healthy=all_ok,
                components=registered,
                statistics=self.get_statistics().model_dump(),
                detected_issues=[] if all_ok else ["One or more sub-components are unavailable"],
                metadata={"thread_safety": "PROTECTED"},
            )

    def get_statistics(self) -> ResolutionStatistics:
        """Return aggregated diagnostic resolution statistics snapshot."""
        with self._lock:
            avg_time = (self._total_resolution_time_ms / self._total_resolutions) if self._total_resolutions > 0 else 0.0
            return ResolutionStatistics(
                total_resolutions=self._total_resolutions,
                resolved_count=self._resolved_count,
                ambiguous_count=self._ambiguous_count,
                failed_count=self._failed_count,
                average_resolution_time_ms=avg_time,
                resolutions_by_category=dict(self._resolutions_by_category),
                active_resolutions=0,
                metadata={"thread_safety": "PROTECTED"},
            )

    def clear(self) -> None:
        """Reset resolution statistics counters."""
        with self._lock:
            self._total_resolutions = 0
            self._resolved_count = 0
            self._ambiguous_count = 0
            self._failed_count = 0
            self._total_resolution_time_ms = 0.0
            self._resolutions_by_category.clear()
