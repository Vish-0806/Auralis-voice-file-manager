"""Dependency resolver for analyzing ActionPlan objects and legacy ExecutionSequence objects to produce execution ordering.

This module provides thread-safe dependency resolution without executing actions, modifying ActionPlans,
validating plans, analyzing execution risks, calling LLMs, or accessing memory providers.
"""

from collections import defaultdict
from datetime import datetime, timezone
from enum import Enum
import logging
import threading
from typing import Any, Callable, Dict, List, Optional

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict, Field

from brain.planning.action_planner import ActionPlan, ActionStep, ActionType
from brain.planning.models import ExecutionSequence, ExecutionStep

logger = logging.getLogger(__name__)


class DependencyType(str, Enum):
    """Enumeration of action dependency relationship types."""

    NONE = "NONE"
    HARD = "HARD"
    SOFT = "SOFT"
    OPTIONAL = "OPTIONAL"
    BLOCKING = "BLOCKING"


class DependencyStatus(str, Enum):
    """Enumeration of dependency resolution outcome statuses."""

    RESOLVED = "RESOLVED"
    UNRESOLVED = "UNRESOLVED"
    CONFLICT = "CONFLICT"
    CYCLIC = "CYCLIC"


class ActionDependency(BaseModel):
    """Immutable model representing a dependency link between two ActionSteps."""

    model_config = ConfigDict(frozen=True)

    source_step: int
    target_step: int
    dependency_type: DependencyType = DependencyType.HARD
    description: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DependencyResolutionResult(BaseModel):
    """Immutable model representing the outcome of dependency resolution."""

    model_config = ConfigDict(frozen=True)

    resolved: bool
    status: DependencyStatus
    execution_order: List[int] = Field(default_factory=list)
    dependencies: List[ActionDependency] = Field(default_factory=list)
    conflicts: List[str] = Field(default_factory=list)
    resolved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DependencyResolverConfig(BaseModel):
    """Configuration options for DependencyResolver behavior."""

    detect_cycles: bool = True
    strict_resolution: bool = True
    maximum_dependencies: int = 500


class DependencyResolver:
    """Thread-safe engine for resolving ActionPlan dependencies and legacy ExecutionSequences."""

    def __init__(
        self,
        config: Optional[DependencyResolverConfig] = None,
        logger_instance: Optional[logging.Logger] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        """Initializes the DependencyResolver with optional configuration and thread lock."""
        self.config = config or DependencyResolverConfig()
        self._logger = logger or logger_instance or logging.getLogger(__name__)
        self._dependency_rules: List[Dict[str, Any]] = []
        self._lock = threading.RLock()

    def register_dependency_rule(
        self,
        rule_id: str,
        rule_func: Callable[[ActionPlan], List[ActionDependency]],
        priority: int = 10,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Registers a custom dependency extraction rule."""
        with self._lock:
            self._dependency_rules = [r for r in self._dependency_rules if r["rule_id"] != rule_id]
            entry = {
                "rule_id": rule_id,
                "rule_func": rule_func,
                "priority": priority,
                "metadata": metadata or {},
            }
            self._dependency_rules.append(entry)
            self._logger.info("Dependency Rule Registered: rule_id=%s", rule_id)
            return True

    def remove_dependency_rule(self, rule_id: str) -> bool:
        """Removes a registered custom dependency rule by rule_id."""
        with self._lock:
            initial_count = len(self._dependency_rules)
            self._dependency_rules = [r for r in self._dependency_rules if r["rule_id"] != rule_id]
            removed = len(self._dependency_rules) < initial_count

            if removed:
                self._logger.info("Dependency Rule Removed: rule_id=%s", rule_id)
                return True
            return False

    def clear_dependency_rules(self) -> None:
        """Clears all custom dependency rules from the registry."""
        with self._lock:
            self._dependency_rules.clear()
            self._logger.info("Dependency Registry Cleared")

    def resolve_dependencies(self, plan: Optional[ActionPlan] = None) -> DependencyResolutionResult:
        """Analyzes an ActionPlan to determine execution ordering and dependency relationships."""
        with self._lock:
            now = datetime.now(timezone.utc)

            if not isinstance(plan, ActionPlan):
                result = DependencyResolutionResult(
                    resolved=False,
                    status=DependencyStatus.UNRESOLVED,
                    execution_order=[],
                    dependencies=[],
                    conflicts=["Invalid input: plan is not an ActionPlan instance"],
                    resolved_at=now,
                    metadata={},
                )
                self._logger.info("Dependencies Resolved")
                return result

            if not plan.steps:
                result = DependencyResolutionResult(
                    resolved=True,
                    status=DependencyStatus.RESOLVED,
                    execution_order=[],
                    dependencies=[],
                    conflicts=[],
                    resolved_at=now,
                    metadata=dict(plan.metadata),
                )
                self._logger.info("Dependencies Resolved")
                return result

            extracted_deps: List[ActionDependency] = []
            seen_dep_keys = set()

            def add_dep(src: int, tgt: int, dtype: DependencyType, desc: str) -> None:
                key = (src, tgt)
                if key not in seen_dep_keys and len(extracted_deps) < self.config.maximum_dependencies:
                    seen_dep_keys.add(key)
                    extracted_deps.append(
                        ActionDependency(
                            source_step=src,
                            target_step=tgt,
                            dependency_type=dtype,
                            description=desc,
                        )
                    )

            # Built-in dependency inferencing across ActionType steps
            step_by_num = {s.step_number: s for s in plan.steps}
            step_nums = sorted(step_by_num.keys())

            # Infer standard dependencies between steps
            for i in range(len(step_nums)):
                s_i = step_by_num[step_nums[i]]
                for j in range(i + 1, len(step_nums)):
                    s_j = step_by_num[step_nums[j]]

                    # LOCATE_FILES before MOVE/COPY/DELETE/RENAME/OPEN
                    if s_i.action_type == ActionType.LOCATE_FILES and s_j.action_type in (
                        ActionType.MOVE_FILES, ActionType.COPY_FILES, ActionType.DELETE_FILES, ActionType.RENAME_FILES, ActionType.OPEN_FILE
                    ):
                        add_dep(s_i.step_number, s_j.step_number, DependencyType.HARD, "Locate step must precede action")

                    # CREATE_FOLDER before MOVE/COPY
                    if s_i.action_type == ActionType.CREATE_FOLDER and s_j.action_type in (ActionType.MOVE_FILES, ActionType.COPY_FILES):
                        add_dep(s_i.step_number, s_j.step_number, DependencyType.HARD, "Create folder must precede move/copy")

                    # SEARCH before OPEN_FILE
                    if s_i.action_type == ActionType.SEARCH and s_j.action_type == ActionType.OPEN_FILE:
                        add_dep(s_i.step_number, s_j.step_number, DependencyType.HARD, "Search must precede opening file")

                    # MOVE_FILES before DELETE_FILES/DELETE_FOLDER
                    if s_i.action_type == ActionType.MOVE_FILES and s_j.action_type in (ActionType.DELETE_FILES, ActionType.DELETE_FOLDER):
                        add_dep(s_i.step_number, s_j.step_number, DependencyType.HARD, "Move must complete before deletion")

            # Custom registered rules sorted by priority descending
            if self._dependency_rules:
                sorted_rules = sorted(self._dependency_rules, key=lambda r: r.get("priority", 10), reverse=True)
                for r in sorted_rules:
                    try:
                        custom_deps = r["rule_func"](plan)
                        if custom_deps and isinstance(custom_deps, list):
                            for cd in custom_deps:
                                if isinstance(cd, ActionDependency):
                                    add_dep(cd.source_step, cd.target_step, cd.dependency_type, cd.description)
                    except Exception as e:
                        self._logger.warning("Dependency rule '%s' raised exception: %s", r.get("rule_id"), e)

            # Perform Topological Sorting & Cycle Detection
            nodes = set(step_nums)
            adj_list = defaultdict(list)
            in_degree = {n: 0 for n in nodes}

            for dep in extracted_deps:
                if dep.source_step in nodes and dep.target_step in nodes:
                    adj_list[dep.source_step].append(dep.target_step)
                    in_degree[dep.target_step] += 1

            queue = [n for n in nodes if in_degree[n] == 0]
            execution_order: List[int] = []

            while queue:
                queue.sort()
                curr = queue.pop(0)
                execution_order.append(curr)

                for neighbor in adj_list[curr]:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        queue.append(neighbor)

            is_cyclic = len(execution_order) != len(nodes)
            conflicts: List[str] = []

            if is_cyclic:
                cycle_nodes = [n for n in nodes if in_degree[n] > 0]
                conflicts.append(f"Circular dependency detected involving steps: {cycle_nodes}")
                status = DependencyStatus.CYCLIC
                resolved = False
            else:
                status = DependencyStatus.RESOLVED
                resolved = True

            result = DependencyResolutionResult(
                resolved=resolved,
                status=status,
                execution_order=execution_order if resolved else step_nums,
                dependencies=extracted_deps,
                conflicts=conflicts,
                resolved_at=now,
                metadata=dict(plan.metadata),
            )

            self._logger.info("Dependencies Resolved")
            return result

    def list_dependency_rules(self) -> List[Dict[str, Any]]:
        """Lists registered custom dependency rules."""
        with self._lock:
            return [
                {
                    "rule_id": r["rule_id"],
                    "priority": r["priority"],
                    "metadata": dict(r.get("metadata", {})),
                }
                for r in self._dependency_rules
            ]

    def resolve_order(self, sequence: ExecutionSequence) -> List[ExecutionStep]:
        """Legacy method resolving task order using topological sort for ExecutionSequence."""
        steps_map = {step.step_id: step for step in sequence.steps}
        adj_list = defaultdict(list)
        in_degree = defaultdict(int)

        for step_id in steps_map:
            in_degree[step_id] = 0

        for dep in sequence.dependencies:
            step_id = dep.step_id
            if step_id not in steps_map:
                continue

            for parent_id in dep.depends_on:
                if parent_id not in steps_map:
                    continue
                adj_list[parent_id].append(step_id)
                in_degree[step_id] += 1

        queue = [step_id for step_id, deg in in_degree.items() if deg == 0]
        ordered_step_ids: list[str] = []

        while queue:
            queue.sort()
            curr = queue.pop(0)
            ordered_step_ids.append(curr)

            for neighbor in adj_list[curr]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(ordered_step_ids) != len(steps_map):
            cycle_nodes = [step_id for step_id, deg in in_degree.items() if deg > 0]
            self._logger.error("Circular dependency detected", extra={"cycle_nodes": cycle_nodes})
            raise ValueError(f"Circular dependency detected between steps: {cycle_nodes}")

        ordered_steps = [steps_map[step_id] for step_id in ordered_step_ids]
        self._logger.info(
            "Resolved dependency order successfully",
            extra={"ordered_steps": [s.step_id for s in ordered_steps]},
        )
        return ordered_steps
