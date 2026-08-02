# Auralis Backend API Service

This is the FastAPI backend application for **Auralis**, coordinating local-first natural language intent parsing, operating system adaptations, document intelligence processing, tiered memory context retrieval, and modular voice integration pipelines.

---

## 1. Directory Layout

The backend codebase is divided into independent packages matching specific boundaries:

```
backend/
├── api/               # API Router endpoints (routes.py, voice_routes.py, assistant_routes.py, etc.)
├── core/              # Assistant boundary, intent schemas, planner, and dispatcher
├── capabilities/      # Specific OS operations (files, desktop capability, automation, system)
├── automation/        # Workflow Engine sequential orchestration
├── events/            # Centralized event schema interfaces
├── brain/             # AI Brain Orchestration & Execution Architecture
│   ├── ai/            # Provider-Independent AI Architecture & Runtime (Phase 10)
│   ├── execution/     # Provider-Independent Execution Architecture Platform (Phase 12)
│   │   ├── intent/       # Intent Resolution Engine (Phase 12.2)
│   │   ├── orchestrator/ # Command Execution Orchestrator (Phase 12.3)
│   │   ├── workflow/     # Workflow Execution Engine (Phase 12.4)
│   │   ├── task/         # Task Management Runtime (Phase 12.5)
│   │   ├── automation/   # Automation & Scheduling Runtime (Phase 12.6)
│   │   ├── analytics/    # Execution Analytics & Observability (Phase 12.7)
│   │   ├── recovery/     # Execution Recovery & State Management (Phase 12.8)
│   │   └── integration/  # Execution Runtime Integration (Phase 12.9)
│   ├── goal/          # Goal Interpreter
│   ├── reasoning/     # Reasoning Engine
│   ├── planning/      # Dynamic Task Planner & ReferenceResolver
│   └── conversation_intelligence/ # Multi-Turn Dialog, Entity Linking, & Ambiguity Resolver
├── memory/            # Tiered Memory Subsystem
│   ├── config.py      # Memory settings and provider resolution
│   ├── models/        # Domain models (MemoryEntry, AssistantContext, etc.)
│   ├── manager/       # MemoryService, ContextBuilder, MemoryRanker, ContextWindowConfig
│   ├── repository/    # ORM Repositories (Conversation, Execution, Context, Preference, etc.)
│   ├── providers/     # InMemoryProvider and PostgresProvider
│   ├── preferences/   # Preference Engine
│   ├── context/       # Short-term Context Memory
│   ├── workspace/     # Workspace Profiles & Intelligence Subsystem
│   ├── learning/      # Routine Learning Engine
│   ├── personalization/ # Personalization Engine
│   ├── coordinator/   # Memory Coordinator
│   ├── routines/      # Autonomous Routine Engine (detection, library, matching, scheduling)
│   ├── proactive/     # Proactive Assistant Engine (prediction, suggestions, scoring, feedback)
│   ├── recommendations/ # Adaptive Recommendation triggers and policy evaluation
│   └── workflows/     # Workflow mining and runtime observation
├── voice/             # Modular Voice Engine subsystems
│   ├── speech/        # PyAudio device interactions and Speech-to-Text transcription
│   ├── conversation/  # Voice session state machine and inactivity tracking
│   ├── tts/           # Edge-TTS synthesis and asynchronous play queues
│   ├── ux/            # Chimes/sound triggers and notification observers
│   ├── context/       # Pronoun/ordinal resolution and temporary session memory
│   └── integration/   # Pipeline loops, EventRouter, and Error Recovery controller
├── tests/             # Pytest suite verifying core, capabilities, brain, memory, and voice
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

### 2.9 Provider-Independent Execution Architecture & Runtime Subsystem (Phase 12)
* **Brain Execution Engine (Phase 12.1)**: Core request analyzer, execution pipeline, decision engine router, and `ExecutionRuntime` singleton lifecycle manager.
* **Intent Resolution Engine (Phase 12.2)**: Provider-independent intent recognizer (`backend/brain/execution/intent/`), filler word remover, entity extractor (paths, apps, dates, devices), scoring engine, and ambiguity resolver.
* **Command Execution Orchestrator (Phase 12.3)**: Coordinates execution between Intent Resolution, Brain Engine, Planning Runtime, AI Engine, Security Runtime, and OS Integration Runtime (`backend/brain/execution/orchestrator/`).
* **Workflow Execution Engine (Phase 12.4)**: Multi-step DAG workflow builder (`backend/brain/execution/workflow/`), cycle detection, topological step scheduler, and step execution.
* **Task Management Runtime (Phase 12.5)**: Observable long-running task manager (`backend/brain/execution/task/`), priority queuing, state persistence, progress monitoring, and pause/resume/cancel controls.
* **Automation & Scheduling Runtime (Phase 12.6)**: Provider-independent automation engine (`backend/brain/execution/automation/`), time/event/manual triggers, cron-style scheduling, and run history store.
* **Execution Analytics & Observability Runtime (Phase 12.7)**: Metrics collection (`backend/brain/execution/analytics/`), distributed tracing with correlation IDs and nested span trees, and immutable audit logger.
* **Execution Recovery & State Management Runtime (Phase 12.8)**: Execution checkpoint manager (`backend/brain/execution/recovery/`), state snapshot store, recovery strategy planner (`RETRY_STEP`, `RESUME_CHECKPOINT`, `ROLLBACK_STAGE`, `FAILOVER`), and step rollback manager.
* **Execution Runtime Integration (Phase 12.9)**: Top-level integration provider (`backend/brain/execution/integration/`), capability registry, execution router, and multi-stage pipeline orchestrator.
* **End-to-End Production Certification (Phase 12.10)**: Complete architectural dependency audit, end-to-end pipeline test suite (`test_execution_pipeline.py`), 100% test pass rate across **2,121 backend unit tests**, and Production Ready certification.

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
4. For Windows users, run the automated audio configuration:
   ```powershell
   powershell -ExecutionPolicy Bypass -File ..\scripts\setup_audio_windows.ps1
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
pytest
```
Currently, the backend contains **2,121 unit and integration tests across 120+ test modules** with a **100% pass rate**, verifying core flows, file operations, state transitions, speech, memory retrieval, brain orchestration, memory ranking, context windows, reference resolution, workspace intelligence, autonomous routines, proactive assistant, conversational intelligence, long-running tasks, background job scheduler, recurring triggers, persistence hooks, provider-independent AI architecture, prompt intelligence, tool execution, memory-aware AI, multi-step planning, runtime resilience, intent resolution, command orchestration, workflow engines, task management, automation scheduling, execution analytics, recovery state management, execution integration, and end-to-end pipeline steps.



