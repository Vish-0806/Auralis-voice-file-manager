"""Intent Resolver for the Auralis Intent Resolution Subsystem (Phase 12.2).

Combines recognized UserIntent, extracted IntentEntity parameters, and IntentContext
into a fully synthesized IntentResolution containing scored IntentCandidates and ambiguity assessments.
"""

from datetime import datetime, timezone
import time
from typing import List, Optional

from brain.execution.intent.exceptions import IntentResolutionError
from brain.execution.intent.intent_models import (
    AmbiguityLevel,
    EntityType,
    IntentCandidate,
    IntentCategory,
    IntentConfidence,
    IntentContext,
    IntentEntity,
    IntentResolution,
    ResolutionStatus,
    UserIntent,
)
from brain.execution.intent.interfaces import IIntentResolver


class IntentResolver(IIntentResolver):
    """Deterministic intent resolver synthesizing primary intent, entities, and context."""

    def resolve(
        self,
        text: str,
        intent: Optional[UserIntent] = None,
        entities: Optional[List[IntentEntity]] = None,
        context: Optional[IntentContext] = None,
    ) -> IntentResolution:
        """Synthesize primary intent, candidates, and context into an IntentResolution.

        Args:
            text: Raw input text.
            intent: Recognized UserIntent object.
            entities: Extracted list of IntentEntity objects.
            context: IntentContext object containing active state.

        Returns:
            IntentResolution object.

        Raises:
            IntentResolutionError: If unexpected internal error occurs during resolution.
        """
        start_time = time.perf_counter()
        diagnostics: List[str] = []

        eff_intent = intent or UserIntent(raw_prompt=text)
        eff_entities = list(entities or [])
        eff_context = context or IntentContext()

        # Merge entities from workspace or execution context if missing
        if not eff_entities and eff_context.workspace_context.get("active_file"):
            eff_entities.append(
                IntentEntity(
                    entity_type=EntityType.FILE,
                    name="active_file",
                    value=eff_context.workspace_context["active_file"],
                    confidence=0.80,
                    metadata={"source": "workspace_context"},
                )
            )

        # Build primary candidate
        primary_score = 1.0 if eff_intent.confidence == IntentConfidence.HIGH else (
            0.75 if eff_intent.confidence == IntentConfidence.MEDIUM else (
                0.50 if eff_intent.confidence == IntentConfidence.LOW else 0.0
            )
        )

        # Entity presence bonus/penalty
        if eff_intent.category in (IntentCategory.FILE_MANAGEMENT, IntentCategory.FILE_SEARCH) and not eff_entities:
            primary_score = max(0.2, primary_score - 0.3)
            diagnostics.append("File operation request missing target file or folder entity")

        primary_candidate = IntentCandidate(
            intent=eff_intent,
            entities=eff_entities,
            score=primary_score,
            reason=f"Primary category {eff_intent.category.value} with confidence {eff_intent.confidence.value}",
        )

        candidates: List[IntentCandidate] = [primary_candidate]

        # Check for multiple conflicting entities of the same type
        files_found = [e for e in eff_entities if e.entity_type == EntityType.FILE]
        folders_found = [e for e in eff_entities if e.entity_type == EntityType.FOLDER]
        apps_found = [e for e in eff_entities if e.entity_type == EntityType.APPLICATION]

        has_conflicting_targets = len(files_found) > 2 or len(folders_found) > 2 or len(apps_found) > 2

        # Assess ambiguity level and status
        if eff_intent.category == IntentCategory.UNKNOWN or primary_score == 0.0:
            ambiguity_level = AmbiguityLevel.HIGH
            status = ResolutionStatus.UNRESOLVED
            diagnostics.append("Intent category unknown or prompt empty")
        elif has_conflicting_targets:
            ambiguity_level = AmbiguityLevel.HIGH
            status = ResolutionStatus.AMBIGUOUS
            diagnostics.append("Multiple conflicting target entities detected")
        elif primary_score < 0.5:
            ambiguity_level = AmbiguityLevel.MEDIUM
            status = ResolutionStatus.AMBIGUOUS
            diagnostics.append("Low confidence intent classification")
        elif primary_score < 0.8:
            ambiguity_level = AmbiguityLevel.LOW
            status = ResolutionStatus.RESOLVED
        else:
            ambiguity_level = AmbiguityLevel.NONE
            status = ResolutionStatus.RESOLVED

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return IntentResolution(
            status=status,
            primary_intent=eff_intent,
            entities=eff_entities,
            candidates=candidates,
            ambiguity_level=ambiguity_level,
            diagnostics=diagnostics,
            execution_time_ms=elapsed_ms,
            created_at=datetime.now(timezone.utc),
            metadata={
                "candidate_count": len(candidates),
                "entity_count": len(eff_entities),
            },
        )
