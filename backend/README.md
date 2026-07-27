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
├── brain/             # AI Brain Orchestration & Self-Correction Pipeline
│   ├── goal/          # Goal Interpreter
│   ├── reasoning/     # Reasoning Engine
│   ├── planning/      # Dynamic Task Planner & ReferenceResolver
│   ├── capability/    # Capability Selector
│   ├── execution/     # Multi-Step Execution Engine
│   ├── recovery/      # Self-Correction & Recovery Engine
│   ├── monitoring/    # Progress Monitoring
│   ├── controller/    # Brain Controller orchestrator
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
Currently, the backend contains **644 unit and integration tests** verifying core flows, file operations, state transitions, speech, memory retrieval, brain orchestration, memory ranking, context windows, reference resolution, workspace intelligence, autonomous routines, proactive assistant, conversational intelligence, and integration pipeline steps.
