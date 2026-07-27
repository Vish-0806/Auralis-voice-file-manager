# Workflow Mining & Observation Subsystem

The Workflow Mining & Observation Subsystem is responsible for observing runtime executions, recording action sequence traces, mining repeated user patterns, and validating candidate workflows for promotion into reusable automation routines.

---

## Subsystem Layout

```
backend/memory/workflows/
├── workflow_models.py       # Domain models (WorkflowStepObservation, WorkflowSequence, WorkflowCandidate, etc.)
├── observation_repository.py # SQLAlchemy ORM Repository for persisting observed execution steps
├── workflow_observer.py     # WorkflowObserver: captures real-time step executions and sequences
├── workflow_miner.py        # WorkflowMiner: mines n-gram action sequences and calculates pattern frequencies
├── workflow_validator.py    # WorkflowValidator: verifies cycle-freedom, parameter consistency, and safety
├── sequence_builder.py      # SequenceBuilder: constructs ordered execution graphs from raw observations
└── __init__.py              # Public module exports
```

---

## Core Roles

1. **Runtime Observation:** `WorkflowObserver` records executed steps (`WorkflowStepObservation`) including intent, target, application context, and timestamps without impeding active execution pipelines.
2. **Pattern Mining:** `WorkflowMiner` scans observation logs over configurable time windows, extracting frequent n-gram sequences and computing confidence support scores.
3. **Candidate Validation:** `WorkflowValidator` inspects mined candidate sequences (`WorkflowCandidate`) to ensure that promoted workflows are free of circular dependencies, parameter conflicts, and duplicate definitions before being promoted to `RoutineDefinition` entities.
