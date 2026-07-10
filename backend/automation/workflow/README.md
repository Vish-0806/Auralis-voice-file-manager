# Intelligent Desktop Workflow Engine Subsystem

## Purpose
Manages multi-step desktop workflows (such as Start Coding, Study Mode, Meeting Mode, Movie Mode, Clean Workspace) by orchestrating existing desktop, system, clipboard, screenshot, and input capabilities through the execution pipeline.

## Architecture

- **`workflow_engine.py`**: Coordinates registry mappings, validators, and executors as an integrated capability service.
- **`workflow_executor.py`**: Executes steps sequentially, intercepts action results, and records histories.
- **`workflow_registry.py`**: Declares default built-in workflows.
- **`workflow_validator.py`**: Validates application and path dependencies prior to execution.
- **`workflow_parser.py`**: Normalizes workflow command names.
- **`models.py`**: Declares structured step and definition models.
