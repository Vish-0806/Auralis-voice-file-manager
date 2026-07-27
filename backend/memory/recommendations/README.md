# Adaptive Recommendation Engine

The Adaptive Recommendation Engine evaluates runtime context and environmental triggers to identify automation opportunities and suggest timely workflows without interrupting normal user execution.

---

## Subsystem Architecture

```
backend/memory/recommendations/
├── models.py          # Domain models (TriggerEvent, TriggerCondition, RecommendationDecision, etc.)
├── trigger_detector.py # TriggerDetector: identifies automation triggers from runtime state
├── policy_engine.py   # RecommendationPolicyEngine: evaluates confidence thresholds and cooldown periods
└── __init__.py        # Public module exports
```

---

## Supported Triggers

The `TriggerDetector` deterministically identifies automation opportunities across several core environmental events:
- **WorkspaceOpened:** Triggered when a project workspace or directory is opened.
- **ApplicationOpened:** Triggered when specific GUI applications or developer tools are launched.
- **TimeOfDay / DayOfWeek:** Time-based triggers for routine scheduled tasks.
- **PreviousWorkflowCompleted:** Sequential triggers chained after successful workflow completions.
- **UserRequestPattern:** Frequent command repetitions detected in short time windows.

---

## Policy Evaluation & Cooldowns

The `RecommendationPolicyEngine` ensures recommendations remain helpful and non-intrusive by enforcing:
- **Confidence Thresholds:** Minimum scoring requirements before a recommendation is surfaced.
- **Cooldown Periods:** Minimum time intervals between identical or similar suggestions to prevent notification spam.
- **Duplicate Suppression:** Automatic filtering of active or recently dismissed recommendations.
- **Rejection History:** Suppression of suggestions that the user has repeatedly rejected.
