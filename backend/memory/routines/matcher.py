"""Routine Matcher identifying routines matching context goals or tag structures."""

import logging
from typing import Any, List, Tuple
from memory.routines.models import RoutineDefinitionDomain

logger = logging.getLogger(__name__)


class RoutineMatcher:
    """Matches user query strings and context parameters against persistent routine catalogues."""

    def match_routines(self, query: str, routines: List[RoutineDefinitionDomain]) -> List[RoutineDefinitionDomain]:
        """Calculates match similarity scores based on triggers, names, descriptions, and tags."""
        scored: List[Tuple[RoutineDefinitionDomain, float]] = []
        q_low = query.lower()

        for r in routines:
            score = 0.0

            # 1. Goal / trigger condition matching
            trigger = r.trigger_condition.get("trigger_event", "").lower().replace("_", " ")
            q_norm = q_low.replace("_", " ")
            if trigger and (trigger in q_norm or q_norm in trigger):
                score += 0.5

            # 2. Text name matching
            name = r.name.lower().replace("_", " ")
            if name and (name in q_norm or q_norm in name):
                score += 0.3

            # 3. Description search mapping
            desc = (r.description or "").lower().replace("_", " ")
            if desc and desc in q_norm:
                score += 0.1

            # 4. Tag similarity match
            tags = r.metadata_info.get("tags", [])
            for tag in tags:
                tag_norm = tag.lower().replace("_", " ")
                if tag_norm in q_norm:
                    score += 0.2

            if score > 0.0:
                # Add base confidence score boost
                score += r.metadata_info.get("avg_success_rate", 1.0) * 0.1
                scored.append((r, score))

        # Rank by score descending
        scored.sort(key=lambda x: x[1], reverse=True)
        return [item[0] for item in scored]
