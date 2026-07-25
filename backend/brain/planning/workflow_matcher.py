"""Workflow Matcher subsystem executing deterministic matching on WorkflowLibrary in Auralis."""

from __future__ import annotations

import logging
from typing import Any, List, Dict, Optional, Set
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field

from core.intents import Intent
from brain.reasoning.models import ReasoningResult
from automation.workflow.models import WorkflowDefinition
from .objective_graph import ObjectiveGraph
from .workflow_library import WorkflowLibrary, WorkflowSignature


class WorkflowMatchScore(BaseModel):
    """Represents a detailed breakdown of a workflow matching score."""

    goal_name_score: float = Field(0.0, description="Score contribution of exact goal name matching")
    name_score: float = Field(0.0, description="Score contribution of workflow name matching")
    intent_score: float = Field(0.0, description="Score contribution of intent overlap matching")
    tag_score: float = Field(0.0, description="Score contribution of tag overlap matching")
    signature_score: float = Field(0.0, description="Score contribution of signature compatibility")
    total_score: float = Field(0.0, description="Sum total matching score")


class WorkflowMatch(BaseModel):
    """Represents a matched workflow with scoring and confidence."""

    workflow: WorkflowDefinition = Field(description="The matched WorkflowDefinition model")
    confidence: float = Field(description="Normalized matching confidence between 0.0 and 1.0")
    matched_fields: List[str] = Field(default_factory=list, description="Fields that matched successfully")
    score_breakdown: Dict[str, float] = Field(default_factory=dict, description="Numerical details for each score field")


class WorkflowMatchQuery(BaseModel):
    """Represents the search criteria query for finding workflows."""

    goal_name: Optional[str] = Field(None, description="Optional target goal name")
    workflow_name: Optional[str] = Field(None, description="Optional target workflow name")
    intents: List[Intent] = Field(default_factory=list, description="List of target system Intents")
    tags: List[str] = Field(default_factory=list, description="List of target category tags")
    signature: Optional[WorkflowSignature] = Field(None, description="Expected inputs/outputs signature contract")


class WorkflowMatcher:
    """Evaluates search parameters against WorkflowLibrary contents using deterministic rules."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        """Initializes the WorkflowMatcher.

        Args:
            logger: Optional custom logger.
        """
        self._logger = logger or logging.getLogger(__name__)

    def match(
        self,
        library: WorkflowLibrary,
        query: WorkflowMatchQuery | ReasoningResult | ObjectiveGraph,
    ) -> List[WorkflowMatch]:
        """Finds matching workflows in the library and ranks them by descending confidence.

        Args:
            library: The WorkflowLibrary to search.
            query: Search parameters or source models.

        Returns:
            A list of ranked WorkflowMatch models.
        """
        norm_query = self._normalize_query(query)
        self._logger.info(
            "Executing deterministic workflow matching",
            extra={
                "query_goal": norm_query.goal_name,
                "query_name": norm_query.workflow_name,
                "query_tags_count": len(norm_query.tags),
            },
        )

        matches: List[WorkflowMatch] = []
        workflows = library.list_workflows()

        # Deterministic Weights
        WEIGHT_GOAL = 1.0
        WEIGHT_NAME = 0.8
        WEIGHT_INTENT = 0.5
        WEIGHT_TAGS = 0.3
        WEIGHT_SIG = 0.2

        # Sum total query weight for normalization
        query_weight = 0.0
        if norm_query.goal_name:
            query_weight += WEIGHT_GOAL
        if norm_query.workflow_name:
            query_weight += WEIGHT_NAME
        if norm_query.intents:
            query_weight += WEIGHT_INTENT
        if norm_query.tags:
            query_weight += WEIGHT_TAGS
        if norm_query.signature:
            query_weight += WEIGHT_SIG

        if query_weight == 0.0:
            return []

        for wf in workflows:
            meta = library.get_metadata(wf.name)
            matched_fields: List[str] = []
            
            # 1. Goal Match (Priority 1)
            goal_score = 0.0
            if norm_query.goal_name and meta and meta.goal_name:
                if norm_query.goal_name.upper() == meta.goal_name.upper():
                    goal_score = WEIGHT_GOAL
                    matched_fields.append("goal_name")

            # 2. Name Match (Priority 2)
            name_score = 0.0
            if norm_query.workflow_name:
                if norm_query.workflow_name.lower() == wf.name.lower():
                    name_score = WEIGHT_NAME
                    matched_fields.append("name")

            # 3. Intent Match (Priority 3)
            intent_score = 0.0
            if norm_query.intents and wf.steps:
                wf_intents = {step.intent for step in wf.steps}
                matched_intents = set(norm_query.intents) & wf_intents
                if matched_intents:
                    intent_score = (len(matched_intents) / len(norm_query.intents)) * WEIGHT_INTENT
                    matched_fields.append("intents")

            # 4. Tag Overlap (Priority 4)
            tag_score = 0.0
            if norm_query.tags and meta and meta.tags:
                meta_tags_lower = {t.lower() for t in meta.tags}
                query_tags_lower = {t.lower() for t in norm_query.tags}
                matched_tags = query_tags_lower & meta_tags_lower
                if matched_tags:
                    tag_score = (len(matched_tags) / len(norm_query.tags)) * WEIGHT_TAGS
                    matched_fields.append("tags")

            # 5. Signature Compatibility (Priority 5)
            sig_score = 0.0
            if norm_query.signature and meta and meta.signature:
                query_inputs = set(norm_query.signature.inputs)
                meta_inputs = set(meta.signature.inputs)
                if query_inputs.issubset(meta_inputs):
                    sig_score = WEIGHT_SIG
                    matched_fields.append("signature")

            total_score = goal_score + name_score + intent_score + tag_score + sig_score
            if total_score > 0.0:
                confidence = round(total_score / query_weight, 4)
                confidence = min(confidence, 1.0)
                
                breakdown = {
                    "goal_name_score": goal_score,
                    "name_score": name_score,
                    "intent_score": intent_score,
                    "tag_score": tag_score,
                    "signature_score": sig_score,
                    "total_score": total_score,
                }

                matches.append(
                    WorkflowMatch(
                        workflow=wf,
                        confidence=confidence,
                        matched_fields=matched_fields,
                        score_breakdown=breakdown,
                    )
                )

        # Sort matches by confidence descending, then by name for determinism
        matches.sort(key=lambda m: (-m.confidence, m.workflow.name))
        return matches

    def _normalize_query(
        self, query: WorkflowMatchQuery | ReasoningResult | ObjectiveGraph
    ) -> WorkflowMatchQuery:
        """Helper to normalize inputs into a unified WorkflowMatchQuery struct."""
        if isinstance(query, WorkflowMatchQuery):
            return query

        if isinstance(query, ReasoningResult):
            intents = []
            for c in query.constraints:
                if not c.satisfied:
                    if c.type == "internet":
                        intents.append(Intent.ENABLE_WIFI)
            return WorkflowMatchQuery(
                goal_name=query.goal_name,
                workflow_name=query.objective.title,
                intents=intents,
            )

        if isinstance(query, ObjectiveGraph):
            root_node = query.nodes[query.root_id]
            intents = []
            for node in query.nodes.values():
                if node.goal_name == "PREP_WIFI":
                    intents.append(Intent.ENABLE_WIFI)
                elif node.goal_name == "LAUNCH_VSCODE":
                    intents.append(Intent.OPEN_APPLICATION)
            return WorkflowMatchQuery(
                goal_name=root_node.goal_name,
                workflow_name=root_node.objective.title,
                intents=intents,
            )

        raise TypeError(f"Unsupported query type: {type(query)}")
