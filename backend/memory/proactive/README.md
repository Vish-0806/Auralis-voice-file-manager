# Proactive Assistant Engine

The Proactive Assistant Engine transforms Auralis from a reactive assistant into an intelligent, proactive desktop assistant capable of predicting user needs and suggesting timely automation workflows before explicit commands are issued.

---

## Architectural Principles

- **Zero LLM Overhead:** All suggestions and predictions are generated using deterministic, rule-based scoring and historical activity analysis. No autonomous LLM reasoning is permitted.
- **Traceable Scoring Logic:** Every proactive recommendation is backed by transparent, explainable scoring metrics based on recency, frequency, user feedback, and context affinity.
- **Auditable & Configurable:** Users and system operators can view suggestion histories, inspect decision rationales, and adjust proactive thresholds.

---

## Subsystem Layout

```
backend/memory/proactive/
├── models.py          # Domain models (PredictionContext, ProactiveSuggestion, SuggestionScore, etc.)
├── repository.py      # SQLAlchemy ORM Repository for proactive recommendation persistence
├── predictor.py       # ActivityPredictor: forecasts likely next actions from history and workspace state
├── engine.py          # RecommendationEngine: generates actionable suggestion candidates
├── scorer.py          # RecommendationScoringEngine: applies deterministic multi-factor scoring
├── prioritizer.py     # RecommendationPrioritizer: ranks and filters suggestions by confidence thresholds
├── history.py         # SuggestionHistoryManager: tracks presented suggestions and prevents fatigue/duplicates
├── feedback.py        # UserFeedbackEngine: learns from user acceptance, rejection, and dismissal of suggestions
├── coordinator.py     # ProactiveAssistantCoordinator: orchestrates prediction, scoring, and feedback pipelines
└── __init__.py        # Public module exports
```

---

## Workflow

1. **Context Aggregation:** The `ProactiveAssistantCoordinator` builds a `PredictionContext` containing recent conversation history, workflow executions, active workspace profiles, and time/environment factors.
2. **Activity Prediction:** The `ActivityPredictor` identifies patterns and forecasts potential tasks (e.g., pulling latest Git branch upon opening a workspace, running tests after editing test files).
3. **Candidate Generation & Scoring:** The `RecommendationEngine` generates suggestion candidates which are evaluated by the `RecommendationScoringEngine` using deterministic weights.
4. **Prioritization & Fatigue Control:** The `RecommendationPrioritizer` and `SuggestionHistoryManager` filter out recently rejected or duplicate suggestions, ensuring the user is only presented with high-confidence, non-intrusive recommendations.
5. **Feedback Loop:** The `UserFeedbackEngine` records acceptance and dismissal events, dynamically adjusting future recommendation weights in the database via `ProactiveRecommendationRepository`.
