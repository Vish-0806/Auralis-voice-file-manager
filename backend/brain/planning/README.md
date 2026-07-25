# Intelligent Task Planning Subsystem

This package implements the Phase 6 **Intelligent Task Planning & Reasoning Engine** for Auralis. It decomposes natural language intents into structured objective graphs, matches templates, merges workflow sequences with conflict resolution, and optimizes step execution using parallel concurrency paths.

## Architecture

The task planner is composed of 11 modular components:

```
ReasoningResult
        ↓
GoalDecomposer (DecompositionRules, DecompositionValidator)
        ↓
ObjectiveGraph
        ↓
ObjectiveAnalyzer (Objective, ObjectiveNode)
        ↓
WorkflowMatcher
        ↓
WorkflowComposer (WorkflowComposition, WorkflowMergeConflict)
        ↓
SubtaskGenerator
        ↓
DependencyBuilder
        ↓
DependencyResolver (Kahn's Topological Sort)
        ↓
PlanOptimizer (OptimizationReport, OptimizationResult)
        ↓
WorkflowCompiler
        ↓
ExecutionPlan
```

## Component Directory & Roles

### 1. Goal Decomposition
* **`goal_decomposer.py`**: Entrance gateway mapping `ReasoningResult` into an `ObjectiveGraph`.
* **`decomposition_rules.py`**: Rules-driven catalog specifying decomposition conditions for different user intents.
* **`decomposition_validator.py`**: Validates the objective graph, executing cycle-detection using color-based DFS traversal.

### 2. Intent Analysis & Subtask Generation
* **`objective_analyzer.py`**: Resolves the primary executing node from the objective graph.
* **`subtask_generator.py`**: Translates graph objectives into structured `ExecutionStep` sequences.
* **`dependency_builder.py`**: Builds dependency edges (`ExecutionDependency`) between step nodes based on objective graphs.
* **`dependency_resolver.py`**: Runs Kahn's topological sorting algorithm on the step dependency network.

### 3. Workflow Matcher & Composer
* **`workflow_library.py`**: Serves as a library index of default built-in and dynamically generated workflows.
* **`workflow_matcher.py`**: Computes ranked templates matching by matching goals, intents, and signatures.
* **`workflow_composer.py`**: Merges matched templates with dynamic steps, checking parameter collisions, exclusive actions (like pc locks during layout updates), and ordering loop cycles.

### 4. Plan Optimization & Compilation
* **`plan_optimizer.py`**: Prunes duplicate intents, drops redundant prep steps, groups independent steps into parallel concurrency levels, and metrics estimated execution reductions.
* **`workflow_compiler.py`**: Compiles finalized execution plans and registers the compiled workflow back to the library.

## Usage in Pipeline

TaskPlanner orchestrates the sequence during request processing:
```python
from brain.planning import TaskPlanner

# TaskPlanner is instantiated using dependency injection
planner = TaskPlanner(...)
execution_plan = planner.plan(reasoning_result)
```
