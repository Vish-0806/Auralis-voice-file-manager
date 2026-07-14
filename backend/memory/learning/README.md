# Routine Learning Engine

The Routine Learning Engine provides a modular, passive, validated, and transaction-safe API for recording user executions, analyzing execution logs to mine recurring action sequences, calculating statistical confidence values, and proposing routine suggestions to users.

## Features

- **Sequential Pattern Mining:** Detects repeating sequences of actions executed close to each other in time (within a 5-minute episode).
- **Statistical Confidence Scores:** Computes a normalized confidence rating derived from pattern support (frequency) and success execution rates.
- **Safety First:** The engine is purely passive. Suggestions require explicit user confirmation (`accept()`) before registering as active routines, preventing automatic background process execution.

## Usage

```python
from memory import RoutineLearningService

# Instantiate service (resolves database connection and repositories automatically)
learning_service = RoutineLearningService()

# 1. Record execution events
learning_service.record(
    user_id=1,
    action="OPEN_APPLICATION",
    input_parameters={"target": "VS Code"},
    status="success",
    duration_ms=450
)
learning_service.record(
    user_id=1,
    action="OPEN_APPLICATION",
    input_parameters={"target": "Terminal"},
    status="success",
    duration_ms=250
)

# 2. Mine execution logs for suggestions
suggestions = learning_service.analyze(user_id=1, min_confidence=0.3)

for sugg in suggestions:
    print(f"Suggested trigger: {sugg.trigger_event}")
    print(f"Sequence: {sugg.action_sequence}")
    print(f"Confidence: {sugg.confidence_score}")

    # 3. Accept/confirm a suggestion
    if sugg.confidence_score > 0.5:
        learning_service.accept(user_id=1, suggestion=sugg)
    else:
        # Or reject/mute it
        learning_service.reject(user_id=1, trigger_event=sugg.trigger_event)

# 4. Start periodic scheduler check
learning_service.start_scheduler(user_id=1, interval_seconds=3600.0)
```
