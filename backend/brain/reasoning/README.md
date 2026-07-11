# Reasoning Engine Subsystem

This package implements the **Reasoning Engine** subsystem for Auralis. It converts structured `Goal` objects into detailed `ReasoningResult` representations.

## Responsibilities

1. **Receive Goal**: Accept Goal definitions identified by the Goal Interpreter.
2. **Translate Objective**: Formulate a high-level user objective (including target parameters).
3. **Determine Capabilities**: Resolve what capability modules (e.g. `mock_file`, `desktop`, `workflow`) are required to accomplish the goal.
4. **Analyze Constraints**: Scan the host system and environment for constraints:
   - Internet connection dependencies.
   - Installed desktop application requirements.
   - Session or OS permission constraints.
   - Local directory/file structure preconditions (e.g. existence of the Downloads folder).
5. **Evaluate Priority**: Assign a task priority level (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).
6. **Estimate Complexity**: Provide a complexity rating (`LOW`, `MEDIUM`, `HIGH`).

> [!IMPORTANT]
> The Reasoning Engine operates purely as an analytical boundaries engine. It **must not** generate concrete execution steps, select specific tool capability handlers, or execute tasks.

## Directory Structure

- [models.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/brain/reasoning/models.py): Defines structured output models (`Objective`, `Constraint`, `Priority`, `ReasoningResult`).
- [objective_builder.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/brain/reasoning/objective_builder.py): Formulates structured user objectives.
- [constraint_analyzer.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/brain/reasoning/constraint_analyzer.py): Checks OS/network constraints and dependencies.
- [priority_manager.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/brain/reasoning/priority_manager.py): Calculates scheduling priorities.
- [reasoning_engine.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/brain/reasoning/reasoning_engine.py): Coordinates the overall reasoning pipeline.
