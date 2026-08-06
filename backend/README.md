# Auralis Backend API Service

This is the FastAPI backend application for **Auralis**, coordinating local-first natural language intent parsing, operating system adaptations, document intelligence processing, tiered memory context retrieval, provider-independent execution runtimes, application container & dependency injection infrastructure, certified configuration management, API pipeline gateway platforms, and modular voice integration pipelines.

---

## 1. Directory Layout

The backend codebase is divided into independent packages matching specific boundaries:

```
backend/
├── api/               # API Router endpoints (routes.py, voice_routes.py, assistant_routes.py, etc.)
├── application/       # Application Container & Infrastructure (Phases 14 & 15)
│   ├── api/           # API Runtime Architecture Platform (Phase 15)
│   │   ├── routing/   # Request Routing Runtime (Phase 15.2)
│   │   ├── middleware/# Middleware Runtime (Phase 15.3)
│   │   ├── auth/      # Authentication & Authorization Runtime (Phase 15.4)
│   │   ├── validation/# Validation & Serialization Runtime (Phase 15.5)
│   │   ├── versioning/# API Versioning & Documentation Runtime (Phase 15.6)
│   │   ├── websocket/ # WebSocket Runtime (Phase 15.7)
│   │   ├── protection/# API Protection & Rate Limiting Runtime (Phase 15.8)
│   │   └── integration/# API Integration Gateway Runtime (Phase 15.9)
│   ├── config/        # Certified Configuration Runtime Subsystem (Phase 14.3)
│   └── di/            # Dependency Injection Subsystem (Phase 14.2)
├── core/              # Assistant boundary, intent schemas, planner, and dispatcher
├── capabilities/      # Specific OS operations (files, desktop capability, automation, system)
├── automation/        # Workflow Engine sequential orchestration
├── events/            # Centralized event schema interfaces
├── brain/             # AI Brain Orchestration & Execution Architecture
│   ├── assistant/     # Assistant Architecture Platform (Phase 13)
│   ├── ai/            # Provider-Independent AI Architecture & Runtime (Phase 10)
│   ├── execution/     # Provider-Independent Execution Architecture Platform (Phase 12)
│   ├── goal/          # Goal Interpreter
│   ├── reasoning/     # Reasoning Engine
│   └── planning/      # Dynamic Task Planner & ReferenceResolver
├── memory/            # Tiered Memory Subsystem
├── voice/             # Modular Voice Engine subsystems
├── tests/             # Pytest suite verifying core, capabilities, brain, memory, voice, execution, assistant, application, and api (2,905 tests across 162 modules)
├── main.py            # API service initialization endpoint
└── requirements.txt   # Python dependency packages
```

---

## 2. Key Subsystems

### 2.1 Core Assistant & AI Brain
* **AuralisAssistant**: Acts as the system boundary. It wraps requests into `BrainRequest` payloads, routes them through `BrainController`, and dispatches plans.
* **Brain Controller**: Coordinates the end-to-end pipeline: `ContextBuilder` -> `ReferenceResolver` -> `GoalInterpreter` -> `ReasoningEngine` -> `TaskPlanner` -> `CapabilitySelector` -> `ExecutionEngine` -> `RecoveryEngine`.
* **Goal Interpreter**: Classifies commands to canonical goals with confidence scores.
* **Reasoning Engine**: Deduces target objectives, constraints, and required capabilities.
* **Task Planner**: Topological step ordering via Kahn's algorithm and pre-planning step generation.
* **Self-Correction & Recovery Engine**: Intercepts step failures, maps fallback strategies (e.g. Edge when Chrome fails), and resumes execution cleanly.

### 2.2 Tiered Memory & Context Retrieval Subsystem
* **PostgresProvider**: Fully active, production-ready PostgreSQL provider supporting session scopes, transactional CRUD, advanced retrieval queries, and vector similarity search.
* **Advanced Memory Retrieval APIs**: Extended ORM repositories (`ConversationRepository`, `ExecutionRepository`, `ContextRepository`, `PreferenceRepository`, `MemoryEventRepository`) with recent, session, user, status, and latest query capabilities.
* **ContextBuilder**: Aggregates recent conversations, executions, latest context state, preferences, and workspace context into a unified `AssistantContext` domain model.
* **MemoryRanker**: Scores retrieved memories using exponential recency decay, session affinity, workspace path matches, entity token overlap, and command verb similarity.
* **ContextWindowConfig**: Restricts database query limits (`short_term_limit`, `long_term_limit`, `session_limit`) and provides high-performance `session_only` context loading.
* **ReferenceResolver**: Resolves conversational pronouns (`it`, `them`, `this`, `that`) and relative spatial pointers (`same folder`, `same app`) before goal interpretation.
* **Workspace Intelligence**: Performs dynamic directory crawling, metadata-indexing, dominant language and build tool detections, Git status parses, and exposes thread-safe cache coordinators.

### 2.3 Desktop Automation & Workflow Subsystem
* **Desktop Capability**: Single capability wrapping Application Management (launch/close), Window Management (minimize/maximize/focus/close), System Controls (volume/brightness/power/network), Clipboard automation (read/write/clear), and Screenshot/Screen recording services.
* **Workflow Engine**: Orchestrates sequential steps of pre-registered workflows (Start Coding, Study Mode, Meeting Mode, Movie Mode, Clean Workspace), performs dependency validations, and logs execution histories for rollbacks.
* **Input Automation**: Low-level mouse (movement, click, double click, scroll, drag) and keyboard (typing, hotkeys, custom macros) automation wrappers.

### 2.4 Voice Subsystem
* **Speech Recognition**: Capture mono PCM streams normalization, silences padding, and translates using offline `faster-whisper` or online Google STT API fallback.
* **Conversation Manager**: Handles session thread starts, sign-off hooks, and inactivity timer callbacks.
* **Text-to-Speech**: Runs online Microsoft Edge-TTS or offline `pyttsx3` locally with non-blocking Windows MCI play workers.
* **Voice UX**: Standardizes states (`SLEEPING`, `LISTENING`, `PROCESSING`, `SPEAKING`, `WAITING`, `ERROR`) and triggers platform chimes.
* **Voice Integration Pipeline**: Continuously listens for wake phrases, loops follow-up speech-to-intent pipelines, and handles system failures (mic disconnection, recognition timeouts, planner/capability exceptions, speech interruption).

### 2.5 Autonomous Routines & Proactive Assistant
* **Autonomous Routine Engine**: Automatically discovers repeated user behavior, converts repeated execution patterns into reusable routines, safely recommends routine creation, executes approved routines, monitors their performance, optimizes them over time, and persists them as long-term knowledge.
* **Proactive Assistant Engine**: Transforms Auralis into a proactive desktop assistant capable of predicting user needs before commands are issued using deterministic activity prediction, recommendation scoring, prioritization, history tracking, and user feedback learning.
* **Adaptive Recommendation Engine**: Evaluates runtime context and environmental triggers (`WorkspaceOpened`, `ApplicationOpened`, etc.) against confidence thresholds and cooldown policies to suggest workflows without interrupting execution.

### 2.6 Conversational Intelligence Subsystem
* **Conversational Intelligence Engine**: Manages multi-turn conversation state, links entities across turns (e.g., resolving `"it"`, `"them"`, `"the second folder"` to previous actions), resolves command ambiguity, formulates interactive clarification requests, and handles conversational error recovery.

### 2.7 Long-Running Task & Background Job Scheduler Subsystems
* **Long-Running Task Subsystem**: Manages observable, asynchronous operations (`LongRunningTaskManager`) with progress tracking, event listener dispatching (`TaskEventDispatcher`), recovery hooks (`TaskPersistenceHook`), timeout cleanup policies, and execution monitor observation without external message queues.
* **Background Job Scheduler Subsystem**: Manages scheduled and recurring jobs (`ONCE`, `INTERVAL`, `DAILY`, `WEEKLY`, `MONTHLY`, `MANUAL`) via `BackgroundJobScheduler`, deterministic schedule calculations (`RecurringScheduleCalculator`), parameter validations (`RecurringTriggerValidator`), persistence hooks (`BackgroundJobPersistenceHook`), expiration rules, retention cleanup, and seamless `ExecutionEngine` integration without cron or APScheduler dependencies.

### 2.8 Provider-Independent AI Architecture & Runtime Subsystem
* **Provider Framework (Phase 10.2)**: Abstract `BaseAIProvider`, `GroqProvider`, and `ProviderManager` handling priority provider registration, default selection, and failover routing.
* **Prompt Intelligence Pipeline (Phase 10.3)**: `PromptTemplates`, `TokenEstimator`, `ConversationBuilder`, `MemoryInjector`, `WorkspaceContextInjector`, and `PromptOptimizer` enforcing priority order (`System` > `Developer` > `Memory` > `Workspace` > `Conversation` > `User`).
* **Tool Calling Runtime (Phase 10.4)**: `DefaultToolRegistry`, `DefaultToolParser`, `DefaultToolExecutor`, permission model (`READ`, `WRITE`, `EXECUTE`, `ADMIN`), metadata models, tool schema generation, and routing.
* **Memory-aware AI Integration (Phase 10.5)**: `AIMemoryProvider`, `DefaultMemoryRetriever`, `DefaultMemoryRanker`, and `DefaultMemoryFilter` enforcing relevance scoring, token budgets, and deduplication.
* **Multi-Step Planning Engine (Phase 10.6)**: `AIPlanner`, `DefaultGoalAnalyzer`, `DefaultPlanGenerator`, `DefaultPlanValidator`, `DefaultExecutionPlanner` (topological graph cycle detection), and `DefaultExecutionMonitor`.
* **Runtime Validation & Resilience (Phase 10.7)**: `AIResilienceRuntime`, `DefaultRetryManager` (exponential backoff), `DefaultTimeoutManager`, `DefaultCancellationManager`, `DefaultFailureClassifier`, `DefaultRecoveryManager`, `DefaultCircuitBreaker` (CLOSED/OPEN/HALF_OPEN), and `DefaultEventDispatcher`.

### 2.9 Provider-Independent Execution Architecture & Runtime Platform (Phase 12)
* **Brain Execution Engine (Phase 12.1)**: Core request analyzer, execution pipeline, decision engine router, and `ExecutionRuntime` singleton lifecycle manager.
* **Intent Resolution Engine (Phase 12.2)**: Provider-independent intent recognizer, filler word remover, entity extractor (paths, apps, dates, devices), scoring engine, and ambiguity resolver.
* **Command Execution Orchestrator (Phase 12.3)**: Coordinates execution between Intent Resolution, Brain Engine, Planning Runtime, AI Engine, Security Runtime, and OS Integration Runtime.
* **Workflow Execution Engine (Phase 12.4)**: Multi-step DAG workflow builder, cycle detection, topological step scheduler, and step execution.
* **Task Management Runtime (Phase 12.5)**: Observable long-running task manager, priority queuing, state persistence, progress monitoring, and pause/resume/cancel controls.
* **Automation & Scheduling Runtime (Phase 12.6)**: Provider-independent automation engine, time/event/manual triggers, cron-style scheduling, and run history store.
* **Execution Analytics & Observability Runtime (Phase 12.7)**: Metrics collection, distributed tracing with correlation IDs and nested span trees, and immutable audit logger.
* **Execution Recovery & State Management Runtime (Phase 12.8)**: Execution checkpoint manager, state snapshot store, recovery strategy planner, and step rollback manager.
* **Execution Runtime Integration (Phase 12.9)**: Top-level integration provider, capability registry, execution router, and multi-stage pipeline orchestrator.

### 2.10 Provider-Independent Assistant Architecture Platform (Phase 13)
* **Assistant Runtime Foundation (Phase 13.1)**: Base assistant controller, provider abstraction, capabilities specification, diagnostic health models, and `AssistantRuntime` singleton.
* **Conversation Runtime (Phase 13.2)**: Immutable conversation session models, message history tracking, context variable store, pagination, and `ConversationRuntime`.
* **Dialogue Management Runtime (Phase 13.3)**: State machine turn manager (`IDLE` → `PROCESSING` → `RESPONDING`), clarification/confirmation triggers, policy evaluator, and `DialogueRuntime`.
* **Decision & Reasoning Coordinator (Phase 13.4)**: Provider-independent decision engine routing request candidates, policy score calculations, and `DecisionRuntime`.
* **Assistant Memory & Context Integration Runtime (Phase 13.5)**: Context merging engine across AI memory, conversation history, dialogue state, and execution history with priority sorting and token budget enforcement.
* **Assistant Response Generation & Streaming Runtime (Phase 13.6)**: Response assembly engine, Markdown/Plain Text/JSON formatters, chunk stream partitioner, and `ResponseRuntime`.
* **Voice Orchestration Runtime (Phase 13.7)**: Top-level voice session manager, wake-word routing, speech pipeline coordinator, and `VoiceRuntime`.
* **Proactive Assistant & Notification Runtime (Phase 13.8)**: Proactive suggestion engine, recommendation ranking, duplicate suppression, cooldown period enforcement, and assistant-level notification manager.
* **Assistant Runtime Integration Layer (Phase 13.9)**: Single integration gateway, runtime registry, 8-stage pipeline coordinator, and 12-subsystem health aggregator.

### 2.11 Application Container & Infrastructure Subsystems (Phase 14)
* **Production Application Runtime (Phase 14.1)**: `RuntimeRegistry`, `BootstrapManager`, `StartupValidator`, `InitializationManager`, `ApplicationProvider`, `ApplicationRuntime`, and `Runtime`.
* **Dependency Injection Subsystem (Phase 14.2)**: `ServiceCollection`, `ServiceDescriptor`, `ServiceLifetime` (`SINGLETON`, `TRANSIENT`, `SCOPED`), `ServiceRegistry`, `DependencyContainer`, `ContainerScope`, and `DependencyGraphAnalyzer` with cycle detection.
* **Certified Configuration Runtime Subsystem (Phase 14.3)**: Multi-source priority resolver (`Memory > Environment > DotEnv > Defaults`), automatic type converter, constraint validator, profiles engine, feature flags, secret store with redaction, and end-to-end certification.

### 2.12 Provider-Independent API Runtime Architecture Platform (Phase 15)
* **API Runtime Foundation (Phase 15.1)**: Provider-independent state machine, capabilities declaration, `ApiProvider`, `ApiRuntime`, and lazy singletons.
* **Request Routing Runtime (Phase 15.2)**: `RouteRegistry`, prefix tree / regex `RouteResolver`, and `RequestDispatcher`.
* **Middleware Runtime (Phase 15.3)**: `MiddlewareRegistry` and `PipelineManager` supporting pre/post/around execution phases.
* **Authentication & Authorization Runtime (Phase 15.4)**: `IdentityManager`, `SessionManager`, and RBAC `AuthorizationEngine`.
* **Validation & Serialization Runtime (Phase 15.5)**: `SchemaRegistry`, `ValidationEngine`, and `SerializationManager`.
* **API Versioning & Documentation Runtime (Phase 15.6)**: `VersionRegistry`, SemVer `CompatibilityResolver`, and `DocumentationManager`.
* **WebSocket Runtime (Phase 15.7)**: `SessionManager`, `ChannelManager`, and `MessageRouter`.
* **API Protection & Rate Limiting Runtime (Phase 15.8)**: `RateLimiter` (sliding window & token bucket algorithms), `PolicyEngine`, and `ViolationTracker`.
* **API Integration Gateway Runtime (Phase 15.9)**: `ApiGateway` orchestrating requests through `ROUTING` → `MIDDLEWARE` → `AUTHENTICATION` → `VALIDATION` → `VERSIONING` → `PROTECTION` → `WEBSOCKET` → `COMPLETE` pipeline stages.

---

## 3. Getting Started

### Installation
1. Ensure Python 3.13 is installed.
2. Initialize virtual environment:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate  # Windows
   source venv/bin/activate # macOS/Linux
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running Server
Start the development ASGI server:
```bash
uvicorn main:app --reload
```
The backend API documentation is available at `http://127.0.0.1:8000/docs`.

### Running Tests
Execute the entire Pytest suite:
```bash
pytest backend/tests
```
Currently, the backend contains **2,905 unit and integration tests across 162 test modules** with a **100% pass rate**, verifying all core, execution, assistant, application, and API subsystems.
