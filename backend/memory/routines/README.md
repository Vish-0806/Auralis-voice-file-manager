# Autonomous Routine Engine

The Autonomous Routine Engine is responsible for automatically discovering repeated user behavior, converting repeated execution patterns into reusable routines, safely recommending routine creation, executing approved routines, monitoring their performance, optimizing them over time, and persisting them as long-term knowledge in PostgreSQL.

---

## Architecture & Components

The engine follows a layered architecture with dependency injection, Pydantic domain models, SQLAlchemy persistence, and async execution:

```
backend/memory/routines/
├── models.py          # Domain models (RoutineDefinition, RoutinePattern, RoutineExecution, RoutineStatus)
├── repository.py      # SQLAlchemy ORM Repository for routine persistence
├── detector.py        # PatternDetector: discovers repeated sequences in execution history
├── validator.py       # RoutineValidator: validates safety, cycle-freedom, and feasibility of routines
├── optimizer.py       # RoutineOptimizer: deduplicates steps and optimizes routine execution parameters
├── library.py         # RoutineLibrary: manages registered routines and metadata
├── matcher.py         # RoutineMatcher: matches current runtime context against routine triggers
├── scheduler.py       # RoutineScheduler: schedules and manages background execution of routines
├── monitor.py         # RoutineMonitor: observes routine execution outcomes and records metrics
├── coordinator.py     # AutonomousRoutineCoordinator: central facade integrating all routine subsystems
└── __init__.py        # Public module exports
```

---

## Key Capabilities

1. **Pattern Detection:** Analyzes execution history to mine n-gram sequences and repeated workflow behaviors that occur across similar timeframes, applications, or workspaces.
2. **Safety & Validation:** Ensures candidate routines are free from dangerous system commands, infinite loops, or conflicting parameters before promotion.
3. **Contextual Matching:** Evaluates runtime state (time of day, active workspace, running applications) to match and trigger relevant routines deterministically without LLM reasoning.
4. **Execution Monitoring & Optimization:** Continuously tracks success rates, average execution durations, and failure points to refine and prune routine definitions over time.
5. **Database Persistence:** Persists routine definitions, triggers, and execution statistics in PostgreSQL via `RoutineDefinitionRepository`.
