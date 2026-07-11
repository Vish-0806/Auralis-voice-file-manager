# Goal Interpreter Subsystem

This package implements the **Goal Interpreter** subsystem for Auralis. It converts natural language user requests into high-level structured goals before core planning and dispatching take place.

## Responsibilities

1. **Receive Natural Language**: Accept unstructured text commands from the user/agent.
2. **Normalize Input**: Clean up whitespace, punctuation, and format uniformly.
3. **Identify Goal**: Matches normalized text against registered goals using regex rules and keyword proximity.
4. **Determine Goal Category**: Classifies the identified goal or text request into canonical categories.
5. **Compute Confidence**: Calculates a confidence score justifying why the goal was matched.
6. **Extract Parameters**: Extracts basic goal parameters (e.g. the specific application name for `OPEN_APPLICATION`).

> [!IMPORTANT]
> The Goal Interpreter is strictly a parser and classifier. It **must not** perform reasoning, capability selection, or construct execution plans.

## Directory Structure

- [models.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/brain/goal/models.py): Defines data structures (`Goal`, `GoalCategory`, `GoalConfidence`, `GoalResult`).
- [goal_classifier.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/brain/goal/goal_classifier.py): Categorizes goals and raw text queries.
- [goal_registry.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/brain/goal/goal_registry.py): Stores pre-configured system goals.
- [goal_interpreter.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/brain/goal/goal_interpreter.py): Orchestrates input normalisation, matching, and confidence evaluation.

## Configuration & Fallback

Integration with the Auralis core planner uses a confidence threshold (defaulting to `0.7`):
- If the interpreter's confidence score is **greater than or equal to** the threshold, the planner returns a mapped core execution plan.
- If the confidence score is **below** the threshold, it is treated as `UNKNOWN` and falls back to standard regex/intent parsing inside the existing planner.
