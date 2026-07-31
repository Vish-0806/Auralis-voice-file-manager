# Provider-Independent AI Architecture & Runtime Subsystem (`backend/brain/ai/`)

The `backend/brain/ai` package implements a provider-independent, modular, agentic AI execution framework connecting LLM providers, prompt intelligence pipelines, tool execution runtimes, memory retrieval engines, multi-step planning engines, and runtime resilience managers.

---

## Subsystem Architecture & Components

```
backend/brain/ai/
├── exceptions.py             # Hierarchy of base AI exceptions
├── ai_models.py              # Core Pydantic domain models (AIContext, Prompt, ToolCall, ToolResult, etc.)
├── interfaces.py             # Abstract base interfaces (AIProvider, PromptBuilder, ContextBuilder, ToolRouter)
├── provider_config.py        # ProviderConfig schema & environment configuration loaders
├── provider_manager.py       # Priority provider registration, default selection, and failover router
├── context_builder.py        # DefaultContextBuilder assembling system, memory, and workspace context
├── prompt_engine.py          # DefaultPromptBuilder coordinating prompt templates & layers
├── tool_router.py            # DefaultToolRouter delegating tool call execution & parsing
├── orchestrator.py           # AIOrchestrator coordinating top-level execution requests
│
├── providers/                # Provider Framework (Phase 10.2)
│   ├── base_provider.py      # Abstract BaseAIProvider HTTP session handler
│   ├── groq_provider.py      # Groq Cloud API provider implementation
│   └── __init__.py           # Package exports
│
├── prompt_templates.py       # Prompt Templates (Phase 10.3)
├── token_estimator.py        # TokenEstimator (~4 chars per token + overhead calculation)
├── conversation_builder.py   # ConversationBuilder history manager & trimming engine
├── memory_injector.py        # MemoryInjector prompt layer injector
├── workspace_context.py      # WorkspaceContextInjector project intelligence layer injector
├── prompt_optimizer.py       # PromptOptimizer priority sorting (System > Developer > Memory > Workspace > Conversation > User)
│
├── tools/                    # Tool Calling Runtime (Phase 10.4)
│   ├── exceptions.py         # Tool runtime exception hierarchy
│   ├── permissions.py        # PermissionLevel enum (READ, WRITE, EXECUTE, ADMIN)
│   ├── metadata.py           # ToolMetadata domain models & OpenAPI schema generator
│   ├── interfaces.py         # AITool, ToolRegistryInterface, ToolParserInterface, ToolExecutorInterface
│   ├── registry.py           # DefaultToolRegistry manager
│   ├── parser.py             # DefaultToolParser dictionary & OpenAI/Groq call parser
│   ├── executor.py           # DefaultToolExecutor sequential tool runner
│   └── __init__.py           # Package exports
│
├── memory/                   # Memory-aware AI Integration (Phase 10.5)
│   ├── exceptions.py         # Memory subsystem exception hierarchy
│   ├── memory_models.py      # MemoryScope, AIMemoryItem, MemoryQueryResult models
│   ├── interfaces.py         # MemoryRetrieverInterface, MemoryRankerInterface, MemoryFilterInterface
│   ├── memory_retriever.py   # DefaultMemoryRetriever multi-scope query engine
│   ├── memory_ranker.py      # DefaultMemoryRanker relevance scoring engine
│   ├── memory_filter.py     # DefaultMemoryFilter deduplication & token budget engine
│   ├── memory_provider.py    # AIMemoryProvider pipeline integration wrapper
│   └── __init__.py           # Package exports
│
├── planning/                 # Multi-Step Planning Engine (Phase 10.6)
│   ├── exceptions.py         # Planning subsystem exception hierarchy
│   ├── planning_models.py    # PlanningGoal, PlanStep, StepDependency, Plan, ExecutionResult models
│   ├── interfaces.py         # GoalAnalyzerInterface, PlanGeneratorInterface, PlanValidatorInterface, ExecutionPlannerInterface, ExecutionMonitorInterface
│   ├── goal_analyzer.py      # DefaultGoalAnalyzer request normalization engine
│   ├── plan_generator.py     # DefaultPlanGenerator template plan generator
│   ├── plan_validator.py     # DefaultPlanValidator structure & cycle detector (Kahn's graph algorithm)
│   ├── execution_planner.py  # DefaultExecutionPlanner topological step sorter
│   ├── execution_monitor.py  # DefaultExecutionMonitor lifecycle metric tracker
│   ├── planner.py            # AIPlanner coordinator
│   └── __init__.py           # Package exports
│
└── resilience/               # Runtime Validation & Resilience Framework (Phase 10.7)
    ├── exceptions.py         # Resilience exception hierarchy
    ├── resilience_models.py  # RetryPolicy, TimeoutPolicy, CancellationRequest, FailureInfo, RecoveryDecision, CircuitBreakerState, RuntimeEvent
    ├── interfaces.py         # RetryManagerInterface, TimeoutManagerInterface, CancellationManagerInterface, FailureClassifierInterface, RecoveryManagerInterface, CircuitBreakerInterface, EventDispatcherInterface
    ├── retry_manager.py      # DefaultRetryManager exponential backoff with jitter
    ├── timeout_manager.py    # DefaultTimeoutManager timer tracker
    ├── cancellation_manager.py # DefaultCancellationManager cancellation tracker
    ├── failure_classifier.py  # DefaultFailureClassifier exception categorizer
    ├── recovery_manager.py   # DefaultRecoveryManager decision engine
    ├── circuit_breaker.py    # DefaultCircuitBreaker state machine (CLOSED/OPEN/HALF_OPEN)
    ├── event_dispatcher.py   # DefaultEventDispatcher observer dispatcher
    ├── resilience_runtime.py # AIResilienceRuntime high-level coordinator
    └── __init__.py           # Package exports
```

---

## Key Technical Features

1. **Provider Independence**: Completely decoupled from specific LLMs or cloud endpoints. Easily swap between local models or Groq/OpenAI APIs.
2. **Priority Provider Failover**: `ProviderManager` automatically routes requests to registered fallback providers if the primary provider encounters timeouts or connection failures.
3. **Structured Prompt Priority**: `PromptOptimizer` enforces strict layer order (`System` > `Developer` > `Memory` > `Workspace` > `Conversation` > `User`) and trims lower-priority turns under token constraints.
4. **Fine-Grained Permissions**: `DefaultToolRegistry` enforces `READ`, `WRITE`, `EXECUTE`, and `ADMIN` permission models before tool execution.
5. **Memory Relevance Ranking**: `DefaultMemoryRanker` scores memories dynamically using recency decay, session affinity, workspace path overlap, and keyword matching.
6. **Cycle-Safe Planning**: `DefaultPlanValidator` & `DefaultExecutionPlanner` execute topological graph sorting and detect dependency cycles before plan execution.
7. **Runtime Fault Tolerance**: `AIResilienceRuntime` provides circuit breakers (CLOSED/OPEN/HALF_OPEN), exponential retry backoff, execution timeouts, and cancellation hooks.
