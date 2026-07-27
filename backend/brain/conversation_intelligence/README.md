# Conversational Intelligence Engine

The Conversational Intelligence Engine equips Auralis with human-like dialog awareness, enabling multi-turn conversation tracking, cross-turn entity linking, automatic ambiguity resolution, follow-up clarification requests, and conversational error recovery.

---

## Architecture & Components

```
backend/brain/conversation_intelligence/
├── models.py              # Domain models (ConversationTurn, EntitySpan, AmbiguityResolution, etc.)
├── state_manager.py       # ConversationStateManager: manages multi-turn dialog state and turn history
├── entity_linking.py      # EntityLinkingEngine: links pronouns and entity references across dialog turns
├── ambiguity_resolver.py  # AmbiguityResolver: detects ambiguous intent parameters and resolves options
├── clarification_manager.py # ClarificationManager: formulates interactive clarification questions for users
├── followup_resolver.py   # FollowupResolver: interprets follow-up commands relative to previous actions
├── history_manager.py     # ConversationHistoryManager: prunes, summarizes, and persists session turns
├── recovery_engine.py     # ConversationalRecoveryEngine: recovers gracefully from dialog misunderstandings
├── runtime.py             # ConversationalIntelligenceRuntime: unified coordinator and execution boundary
├── persistence.py         # SQLAlchemy persistence adapters for conversational turns and state
└── __init__.py            # Public module exports
```

---

## Key Features

1. **Multi-Turn State Tracking:** Maintains structured conversation turns, recording user intents, executed plans, extracted entities, and assistant responses across ongoing sessions.
2. **Cross-Turn Entity Linking:** Resolves complex conversational pronouns (e.g., `"move it there"`, `"delete the second one"`, `"open that folder again"`) by binding mentions to previously referenced file paths, windows, or applications.
3. **Deterministic Ambiguity Resolution:** Detects underspecified commands (e.g., multiple files matching `"report.pdf"` or ambiguous window titles) and evaluates confidence scores to decide whether to auto-resolve or ask for clarification.
4. **Interactive Clarification Management:** Automatically generates concise, human-friendly clarification prompts when ambiguity exceeds safe execution thresholds.
5. **Conversational Recovery:** Monitors failed turn executions and dialog dead-ends, offering graceful recovery suggestions and reset strategies without losing broader session context.
