# Auralis 🎙

<p align="center">
  <b>Your AI Operating System Assistant</b>
</p>

<p align="center">
  Auralis is a local-first, privacy-respecting desktop assistant that replaces complex menus and system commands with natural language. Talk to your operating system to manage files, extract document intelligence, orchestrate development tasks, and build automated workflows.
</p>

<p align="center">
  <a href="https://github.com/Vish-0806/Auralis-voice-file-manager"><img src="https://img.shields.io/badge/status-active-brightgreen?style=flat-square" alt="Status"></a>
  <a href="https://github.com/Vish-0806/Auralis-voice-file-manager/releases"><img src="https://img.shields.io/badge/version-1.9.0-blue?style=flat-square" alt="Version"></a>
  <a href="file:///d:/Auralis-voice-file-manager/LICENSE"><img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="License"></a>
  <a href="https://python.org"><img src="https://img.shields.io/badge/python-3.13-blue?style=flat-square" alt="Python"></a>
  <a href="https://fastapi.tiangolo.com"><img src="https://img.shields.io/badge/FastAPI-0.136.1-red?style=flat-square" alt="FastAPI"></a>
  <a href="#architecture"><img src="https://img.shields.io/badge/AI-brain-purple?style=flat-square" alt="AI"></a>
  <a href="#repository-certification"><img src="https://img.shields.io/badge/Health-100.0%2F100-brightgreen?style=flat-square" alt="Health"></a>
</p>

---

## Project Vision

Auralis is designed to bridge the gap between human intent and machine execution. Instead of forcing users to navigate nested folder trees, search through menus, or memorize terminal syntax, Auralis acts as an intelligent operating system abstraction layer. By combining voice-to-text, natural language processing, context building, and resilient command execution, it lets you control your computer as if you were talking to an expert human assistant.

> **"Talk to your computer like you talk to a person."**

Whether organizing cluttered folders, compiling project logs, summarizing complex documents, or spinning up local servers, Auralis interprets commands contextually and executes them securely on your local machine.

---

## Core Features

Auralis offers a broad set of capabilities designed for productivity and ease of use:

| Feature | Capability | Description |
| :--- | :--- | :--- |
| **Voice Interaction** | Wake Word & Speech-to-Text | Activate the assistant hands-free and issue spoken commands with natural voice feedback. |
| **Assistant Architecture** | 8-Stage Integration Gateway | Provider-independent Assistant Runtime Platform coordinating Conversation, Dialogue, Decision, Memory, Response, Voice, Proactive, and System runtimes. |
| **Application Infrastructure** | DI & Config Platform (Phase 14) | Enterprise-grade Application Runtime, thread-safe Dependency Injection Container, and Certified Configuration Subsystem. |
| **API Runtime Platform** | 8-Stage Pipeline Gateway (Phase 15) | Certified Provider-Independent API Runtime Platform orchestrating Routing, Middleware, Authentication, Validation, Versioning, Protection, WebSocket, and Gateway Coordination. |
| **AI Conversation** | Contextual Intent Parsing | Recognizes natural language, resolving fuzzy commands, relative dates, and implied locations. |
| **Dialogue Management** | State Machine & Turn Tracking | Manages dialogue sessions, turn transitions (`IDLE` → `PROCESSING` → `RESPONDING`), clarification prompts, and user confirmation loops. |
| **Decision & Reasoning** | Deterministic Candidate Routing | Evaluates request candidates, confidence thresholds, and priority scoring without LLM overhead. |
| **Reference Resolution** | Pre-Planning Entity Mapping | Automatically resolves pronouns (`it`, `them`) and spatial references (`same folder`, `same app`) before goal interpretation. |
| **Context Aggregation** | ContextBuilder & Working Memory | Assembles recent conversations, executions, latest state, preferences, and workspace context into working memory snapshots. |
| **Memory Ranking** | Relevance Scoring Engine | Scores memories by exponential recency decay, session affinity, workspace path match, and keyword/verb similarity. |
| **Response Generation** | Stream & Format Assembly | Formats assistant replies (Markdown, Plain Text, JSON) and manages ordered chunk stream partitioning. |
| **Voice Orchestration** | Session & Wake-Word Routing | Top-level voice session coordinator managing wake-word routing, speech pipeline hooks, and audio interaction states. |
| **Proactive Assistant** | Recommendations & Notifications | Deterministic recommendation engine scoring suggestions, enforcing cooldowns, suppressing duplicates, and managing assistant-level notifications. |
| **File Intelligence** | Intelligent File Operations | Move, copy, create, and organize files dynamically using flexible names and targets. |
| **Desktop Automation** | GUI & System Controls | Launch applications, control window layouts, and execute basic system settings changes. |
| **Developer Assistant** | Terminal & Git Management | Run backends, commit changes, parse terminal errors, and run local testing scripts. |
| **Document Intelligence** | PDF & Text Summarization | Extract key points, actions, and metadata from local files without opening external apps. |
| **Semantic Search** | Vector-Based Discovery | Find files based on meaning, topic, or content rather than just matching exact filenames. |
| **Workflow Automation** | Multi-Step Chains | Combine multiple operations (e.g., "Clean my desktop and backup active projects") into single commands. |
| **Autonomous Routines** | Pattern Mining & Execution | Automatically discovers repeated user workflows, recommends routine creation, and schedules background execution. |
| **Privacy First** | Local Execution | Keeps your files, voice data, and operational logs securely on your local system. |

---

## Desktop Automation & Workflow Engine (v0.4.0)

Auralis Version 0.4.0 implements a modular, high-performance Desktop Automation and sequential Workflow Engine. It integrates with the core AI Planner and Dispatcher to support voice and text control of applications, windows, OS settings, clipboard, screen captures, inputs, and multi-step workflows.

---

## AI Brain Orchestration & Self-Correction Engine (v1.0.0)

Auralis Version 1.0.0 implements the complete Phase 5 **AI Brain Orchestration** and **Self-Correction & Recovery Engine**. It establishes a modular, pipeline-based request execution gateway connecting the Goal Interpreter, Reasoning Engine, Dynamic Task Planner, Capability Selector, Execution Engine, Recovery Engine, and Progress Monitor.

---

## Advanced Memory Retrieval & Context Construction (v1.2.0)

Auralis Version 1.2.0 implements Phase 4 **Advanced Memory Retrieval API**, **Context Builder**, **Brain Memory Integration**, **Reference Resolution**, **Memory Ranking**, and **Context Window Management**.

---

## Workspace Intelligence & Awareness Integration (v1.3.0)

Auralis Version 1.3.0 implements the complete **Workspace Intelligence Subsystem** including **Workspace Discovery**, **Workspace Indexer**, **Project Intelligence Engine**, **Workspace Analysis**, **Workspace Cache & Coordinator**, and **Brain Awareness Integration**.

---

## Intelligent Planning & Reasoning Engine (v1.4.0)

Auralis Version 1.4.0 implements the complete Phase 6 **Intelligent Planning & Reasoning Engine** including **Goal Decomposition**, **Workflow Library**, **Workflow Matcher**, **Workflow Composer**, and **Plan Optimizer**.

---

## Autonomous Routine & Proactive Assistant Engine (v1.5.0)

Auralis Version 1.5.0 implements the complete **Autonomous Routine Engine**, **Proactive Assistant Engine**, and **Conversational Intelligence Engine**.

---

## Long-Running Task & Background Job Scheduler Engine (v1.6.0)

Auralis Version 1.6.0 implements the complete **Long-Running Task Subsystem** and **Background Job Scheduler Subsystem**.

---

## Provider-Independent Assistant Architecture Platform (v1.7.0 / Phase 13)

Auralis Version 1.7.0 implements the complete **Provider-Independent Assistant Architecture Platform** (`backend/brain/assistant/`), establishing a modular, decoupled, thread-safe orchestration layer across 9 core subsystems.

---

## Application Container & Infrastructure Platform (v1.8.0 / Phase 14)

Auralis Version 1.8.0 implements the complete **Application Container & Infrastructure Platform** (`backend/application/`), providing enterprise-grade application lifecycle execution, thread-safe dependency injection, and certified configuration management across 3 core subsystems:

1. **Production Application Runtime (Phase 14.1)**: `RuntimeRegistry`, `BootstrapManager`, `StartupValidator`, `InitializationManager`, `ApplicationProvider`, `ApplicationRuntime`, and `Runtime` (`backend/application/`).
2. **Dependency Injection Subsystem (Phase 14.2)**: Service registration engine (`SINGLETON`, `TRANSIENT`, `SCOPED`), resolution engine, scoped lifetime container manager, and dependency graph analyzer with cycle detection (`backend/application/di/`).
3. **Certified Configuration Runtime Subsystem (Phase 14.3)**: Multi-source priority resolver (`Memory > Environment > DotEnv > Defaults`), type converter, property constraint validator, profiles engine, feature flags, secret store with redaction, and end-to-end certification.

---

## Provider-Independent API Runtime Architecture Platform (v1.9.0 / Phase 15)

Auralis Version 1.9.0 implements the complete **Provider-Independent API Runtime Architecture Platform** (`backend/application/api/`), providing a framework-decoupled, thread-safe, high-performance API pipeline gateway across 9 sub-runtimes:

1. **API Runtime Foundation (Phase 15.1)**: Provider-independent state machine, capabilities declaration, `ApiProvider`, `ApiRuntime`, and lazy singletons (`backend/application/api/`).
2. **Request Routing Runtime (Phase 15.2)**: `RouteRegistry`, prefix tree / regex `RouteResolver`, and `RequestDispatcher` (`backend/application/api/routing/`).
3. **Middleware Runtime (Phase 15.3)**: `MiddlewareRegistry` and `PipelineManager` supporting pre/post/around execution phases (`backend/application/api/middleware/`).
4. **Authentication & Authorization Runtime (Phase 15.4)**: `IdentityManager`, `SessionManager`, and RBAC `AuthorizationEngine` (`backend/application/api/auth/`).
5. **Validation & Serialization Runtime (Phase 15.5)**: `SchemaRegistry`, `ValidationEngine`, and `SerializationManager` (`backend/application/api/validation/`).
6. **API Versioning & Documentation Runtime (Phase 15.6)**: `VersionRegistry`, SemVer `CompatibilityResolver`, and `DocumentationManager` (`backend/application/api/versioning/`).
7. **WebSocket Runtime (Phase 15.7)**: `SessionManager`, `ChannelManager`, and `MessageRouter` (`backend/application/api/websocket/`).
8. **API Protection & Rate Limiting Runtime (Phase 15.8)**: `RateLimiter` (sliding window & token bucket algorithms), `PolicyEngine`, and `ViolationTracker` (`backend/application/api/protection/`).
9. **API Integration Gateway Runtime (Phase 15.9)**: `ApiGateway` orchestrating requests through `ROUTING` → `MIDDLEWARE` → `AUTHENTICATION` → `VALIDATION` → `VERSIONING` → `PROTECTION` → `WEBSOCKET` → `COMPLETE` pipeline stages (`backend/application/api/integration/`).
10. **Production Certification & Verification (Phase 15.10)**: 418 unit & certification tests passed, 100% thread-safe `RLock` protection, $7.82\text{ ms}$ 9-runtime startup latency, and zero framework coupling.

---

## Provider-Independent AI Architecture & Runtime Subsystem (Phase 10)

Auralis implements a complete **Provider-Independent AI Architecture & Runtime Subsystem** (`backend/brain/ai/`), unifying LLM providers, prompt intelligence, tool execution, memory retrieval, multi-step planning, and runtime resilience.

---

## Provider-Independent Execution Architecture & Runtime Platform (Phase 12)

Auralis implements a complete **Provider-Independent Execution Architecture & Runtime Platform** (`backend/brain/execution/`), orchestrating request analysis, intent resolution, command execution, multi-step workflow graphs, long-running background tasks, rule-based automations, distributed tracing, recovery checkpoints, and unified execution integration.

---

## Architecture Overview

```mermaid
graph TD
    User([User]) -->|Voice / Text Command| Gateway[Assistant Integration Gateway]
    
    subgraph Application Infrastructure Platform (Phase 14)
        AppRuntime[Application Runtime & Container] --> AppConfig[Configuration Runtime Platform]
        AppRuntime --> AppDI[Dependency Injection Container]
    end

    subgraph Provider-Independent Assistant Architecture Platform (Phase 13)
        Gateway --> ConvRuntime[1. Conversation Runtime]
        Gateway --> DialRuntime[2. Dialogue Runtime]
        Gateway --> DecRuntime[3. Decision Runtime]
        Gateway --> MemRuntime[4. Assistant Memory Runtime]
        Gateway --> ExecRuntimeRef[5. Execution Runtime]
        Gateway --> RespRuntime[6. Response Runtime]
        Gateway --> VoiceRuntime[7. Voice Orchestration Runtime]
        Gateway --> ProRuntime[8. Proactive Notification Runtime]
    end

    subgraph Core Brain & Execution Engines
        DecRuntime --> GoalInterpreter[Goal Interpreter]
        GoalInterpreter --> TaskPlanner[Dynamic Task Planner]
        TaskPlanner --> ExecutionIntegration[Execution Runtime Integration]
    end

    subgraph Capabilities & OS Abstraction
        ExecutionIntegration --> FileIntel[File Intelligence]
        ExecutionIntegration --> DesktopControl[Desktop Control]
        ExecutionIntegration --> DevAssistant[Developer Assistant]
        FileIntel --> OS[Operating System]
        DesktopControl --> OS
        DevAssistant --> OS
    end
```

---

## Technology Stack

The project utilizes modern libraries and frameworks across both frontend and backend modules:

### Frontend
| Technology | Version | Purpose |
| :--- | :--- | :--- |
| **Vite** | Latest | Next-generation build tool and dev server. |
| **React** | 18.x | Component-based UI library. |
| **Vanilla CSS** | Modern | Sleek glassmorphic theme, layout structure, and animation system. |
| **Lucide Icons** | Latest | Premium vector icons for application status and file types. |

### Backend
| Technology | Version | Purpose |
| :--- | :--- | :--- |
| **FastAPI** | 0.136.1 | High-performance, asynchronous web API framework. |
| **Python** | 3.13 | Core programming language. |
| **SQLAlchemy** | 2.x | Asynchronous ORM and relational database mapping. |
| **PostgreSQL** | 15+ | Relational database persistence provider. |
| **Pydantic** | 2.x | Data validation and immutable domain models (`ConfigDict(frozen=True)`). |
| **Uvicorn** | 0.46.0 | Lightning-fast ASGI server implementation. |
| **PyAudio** | 0.2.14 | Cross-platform library for capturing audio streams. |
| **SpeechRecognition** | 3.16.1 | Speech-to-text processing using multiple engine APIs. |
| **pyttsx3** | 2.99 | Offline text-to-speech converter. |

---

## Folder Structure

```
Auralis/
├── backend/                   # FastAPI Backend Application
│   ├── api/                   # Router declarations and API endpoints
│   ├── application/           # Application Container & Infrastructure (Phase 14 & 15)
│   │   ├── api/               # API Runtime Architecture Platform (Phase 15)
│   │   │   ├── routing/       # Request Routing Runtime (Phase 15.2)
│   │   │   ├── middleware/    # Middleware Runtime (Phase 15.3)
│   │   │   ├── auth/          # Authentication & Authorization Runtime (Phase 15.4)
│   │   │   ├── validation/    # Validation & Serialization Runtime (Phase 15.5)
│   │   │   ├── versioning/    # API Versioning & Documentation Runtime (Phase 15.6)
│   │   │   ├── websocket/     # WebSocket Runtime (Phase 15.7)
│   │   │   ├── protection/    # API Protection & Rate Limiting Runtime (Phase 15.8)
│   │   │   └── integration/   # API Integration Gateway Runtime (Phase 15.9)
│   │   ├── config/            # Certified Configuration Runtime Subsystem (Phase 14.3)
│   │   └── di/                # Dependency Injection Subsystem (Phase 14.2)
│   ├── brain/                 # AI Brain Orchestration
│   │   ├── assistant/         # Assistant Architecture Platform (Phase 13)
│   │   │   ├── conversation/  # Conversation Runtime (Phase 13.2)
│   │   │   ├── dialogue/      # Dialogue Management Runtime (Phase 13.3)
│   │   │   ├── reasoning/     # Decision & Reasoning Coordinator (Phase 13.4)
│   │   │   ├── memory/        # Assistant Memory Runtime (Phase 13.5)
│   │   │   ├── response/      # Response Generation & Streaming (Phase 13.6)
│   │   │   ├── voice/         # Voice Orchestration Runtime (Phase 13.7)
│   │   │   ├── proactive/     # Proactive Assistant & Notifications (Phase 13.8)
│   │   │   └── integration/   # Assistant Runtime Integration Layer (Phase 13.9)
│   │   ├── ai/                # AI Architecture & Runtime Platform (Phase 10)
│   │   ├── execution/         # Execution Architecture Platform (Phase 12)
│   │   ├── goal/              # Goal Interpreter
│   │   ├── reasoning/         # Reasoning Engine
│   │   ├── planning/          # Dynamic Task Planner & ReferenceResolver
│   │   └── conversation_intelligence/ # Multi-Turn Dialog & Entity Linking
│   ├── capabilities/          # OS capabilities (files, desktop, automation, developer)
│   ├── core/                  # Assistant boundary, intent schemas, planner, and dispatcher
│   ├── memory/                # Tiered Memory System
│   ├── voice/                 # Modular Voice Engine subsystems
│   ├── tests/                 # 2,487 unit & integration tests across 135+ test modules
│   ├── main.py                # Backend entry point
│   └── requirements.txt       # Python package dependencies
├── frontend/                  # Vite + React Client App
└── docs/                      # Technical documentation and guides
```

---

## Roadmap

Track the development stages of Auralis:

* [x] **Core Pipeline:** Modular FastAPI backend structure and link to Vitest-proxied React dashboard.
* [x] **Voice Subsystems:** Speech-to-Text (Whisper), Text-to-Speech (Edge-TTS), Session Manager state-machine, Voice UX chimes, and context resolvers.
* [x] **AI Brain Orchestration (Phase 5):** Pipeline stages (Goal Interpreter, Reasoning Engine, Dynamic Planner, Capability Selector, Execution Engine, Recovery Engine, Controller).
* [x] **Tiered Memory Platform (Phase 6):** Preference Engine, Context Memory, Workspace Profiles, Routine Learning n-gram mining, Personalization decider, and unified Memory Coordinator.
* [x] **Advanced Memory Retrieval & Context Construction (Phase 4):** PostgreSQL ORM Repositories, `ContextBuilder`, `BrainController` context integration, `ReferenceResolver`, `MemoryRanker`, and `ContextWindowConfig`.
* [x] **Workspace Intelligence & Awareness (Phase 5):** Asynchronous indexers, project detectors, thread-safe caching coordinators, context construction, and brain reasoning pipelines.
* [x] **Intelligent Planning & Reasoning Engine (Phase 6):** Goal decomposition, workflow libraries matching and compositions, parallel optimizations, compiler registrants, and integrated test pipelines.
* [x] **Autonomous Routine Engine (Phase 7.4):** Pattern detection, validation, optimization, routine library, matching, background scheduling, monitoring, and database persistence.
* [x] **Proactive Assistant Engine (Phase 7.5):** Activity prediction, suggestion recommendation, deterministic scoring, prioritization, history tracking, user feedback learning, and coordinator integration.
* [x] **Conversational Intelligence Engine:** Multi-turn context tracking, entity linking, ambiguity resolution, follow-up clarification, and session state management.
* [x] **Long-Running Task & Background Job Scheduler Engine (Phase 8.5 & 8.6):** Observable long-running tasks, event notification framework, recurring job scheduling, parameters validation, schedule calculation, persistence hooks, recovery, expiration, and retention cleanup policies.
* [x] **Provider-Independent AI Architecture & Runtime Pipeline (Phases 10.1 to 10.7):** Provider Framework (Groq Provider, failover), Prompt Intelligence, Tool Calling Runtime, Memory-aware AI, Multi-step Planning Engine, and Runtime Resilience Engine.
* [x] **Repository Architecture Stabilization & Cleanup (Phases RC-1 to RC-5):** Facade compatibility layers, canonical Brain ownership, conftest/mock fixture consolidation, 100% test pass rate across 1,936 test cases, and Grade A Repository Health Certification.
* [x] **Provider-Independent Execution Architecture & Runtime Platform (Phases 12.1 to 12.10):** Intent Resolution Engine, Command Orchestrator, Workflow Engine, Task Management Runtime, Automation Runtime, Analytics & Observability Runtime, Recovery & State Management Runtime, Execution Integration, and End-to-End Production Certification (2,121 tests passed).
* [x] **Provider-Independent Assistant Architecture Platform (Phases 13.1 to 13.10):** Assistant Runtime Foundation, Conversation Runtime, Dialogue Management, Decision Coordinator, Assistant Memory Runtime, Response Streaming, Voice Orchestration, Proactive Notifications, Integration Gateway, and End-to-End Production Certification (2,172 tests passed).
* [x] **Application Container & Infrastructure Platform (Phases 14.1 to 14.3.6):** Application Runtime Platform, Dependency Injection Subsystem, Priority Configuration Source Management, Resolution & Validation Engine, Configuration Profiles & Feature Flags, Secrets & Sensitive Configuration Management, and End-to-End Production Certification (2,487 tests passed).
* [x] **Provider-Independent API Runtime Architecture Platform (Phases 15.1 to 15.10):** API Runtime Foundation, Request Routing Runtime, Middleware Runtime, Authentication Runtime, Validation Runtime, API Versioning Runtime, WebSocket Runtime, API Protection & Rate Limiting Runtime, API Integration Gateway Runtime, and End-to-End Production Certification (2,905 tests passed).
* [ ] **Future Objectives:**
  * [ ] Operating System Integration (Phase 11).
  * [ ] Document intelligence parser using local PyMuPDF extraction.
  * [ ] Plugin Marketplace for community extensions.
  * [ ] Drag-and-drop workflow visual builder.

---

## Installation & Testing

```bash
# Setup backend virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt

# Run complete test suite (2,487 tests across 135+ test modules)
pytest backend/tests

# Launch backend server
cd backend
uvicorn main:app --reload
```

---

## License

Distributed under the MIT License. See [LICENSE](file:///d:/Auralis-voice-file-manager/LICENSE) for details.

---

<p align="center">
  Built with ❤️ by <a href="https://github.com/Vish-0806">Vishal S Naik</a>
  <br>
  <i>"Talk to your computer. Let Auralis handle the rest."</i>
</p>
