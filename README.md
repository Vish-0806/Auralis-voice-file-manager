# Auralis 🎙

<p align="center">
  <b>Your AI Operating System Assistant</b>
</p>

<p align="center">
  Auralis is a local-first, privacy-respecting desktop assistant that replaces complex menus and system commands with natural language. Talk to your operating system to manage files, extract document intelligence, orchestrate development tasks, and build automated workflows.
</p>

<p align="center">
  <a href="https://github.com/Vish-0806/Auralis-voice-file-manager"><img src="https://img.shields.io/badge/status-active-brightgreen?style=flat-square" alt="Status"></a>
  <a href="https://github.com/Vish-0806/Auralis-voice-file-manager/releases"><img src="https://img.shields.io/badge/version-2.0.0-blue?style=flat-square" alt="Version"></a>
  <a href="file:///d:/Auralis-voice-file-manager/LICENSE"><img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="License"></a>
  <a href="https://python.org"><img src="https://img.shields.io/badge/python-3.13-blue?style=flat-square" alt="Python"></a>
  <a href="https://fastapi.tiangolo.com"><img src="https://img.shields.io/badge/FastAPI-0.136.1-red?style=flat-square" alt="FastAPI"></a>
  <a href="https://typescriptlang.org"><img src="https://img.shields.io/badge/TypeScript-5.5-blue?style=flat-square" alt="TypeScript"></a>
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
| **Frontend Runtime Platform** | 5 Subsystem Architecture (Phase 16) | Provider-Independent Frontend Runtime orchestrating Dependency Injection, Application Lifecycle & Plugins, Certified Configuration, Event Runtime, and State Management. |
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

Auralis Version 1.8.0 implements the complete **Application Container & Infrastructure Platform** (`backend/application/`), providing enterprise-grade application lifecycle execution, thread-safe dependency injection, and certified configuration management across 3 core subsystems.

---

## Provider-Independent API Runtime Architecture Platform (v1.9.0 / Phase 15)

Auralis Version 1.9.0 implements the complete **Provider-Independent API Runtime Architecture Platform** (`backend/application/api/`), providing a framework-decoupled, thread-safe, high-performance API pipeline gateway across 9 sub-runtimes.

---

## Rebuilt Lightweight Frontend Architecture & Runtime Platform (v2.0.0 / Phase 16)

Auralis Version 2.0.0 implements a complete, clean-slate **Frontend V2 Subsystem** (`frontend/src/`), establishing a modern, responsive, and type-safe architecture:

1. **Frontend Runtime Foundation (Phase 16.1)**: Clean folder infrastructure and package environment mappings.
2. **Frontend Component Runtime (Phase 16.2)**: Accessible, semantic, presentational components (`src/components/common/`, `src/components/layout/`) with 100% keyboard accessibility and WAI-ARIA validation.
3. **Layout & Navigation Runtime (Phase 16.3)**: Breadcrumbs, dynamic page headers, mobile off-canvas menus, and collapsible sidebars mapping nested react-router routes (`src/layouts/AppLayout.tsx`).
4. **Theme & Design System Runtime (Phase 16.4)**: Dynamic styling tokens system, light/dark/system mode configurations (`src/theme/ThemeToggle.tsx`), local cache persistence, and prefers-reduced-motion animation mitigations.
5. **State Management Runtime (Phase 16.5)**: Decoupled Zustand state store boundaries (UI, Assistant, Files, Workspace, Settings) and narrow, typed selectors mapping selective local persistence.
6. **API Client & Synchronization Runtime (Phase 16.6)**: Axios client intercepting bearer headers, error normalizers resolving FastAPI details exceptions, in-memory AuthService, WebSocket client with backoff reconnects, and synchronization bridges dispatching socket updates directly to stores.
7. **Voice UI Runtime (Phase 16.7)**: Real-time audio waveform visualizers, speech-state coordinators, and push-to-talk button interface widgets.
8. **Dashboard & Workspace Runtime (Phase 16.8)**: Collapsible sidebar directory explorer, workspace tab management panels, details visualizers, and quick action shortcuts.
9. **Frontend Integration Runtime (Phase 16.9)**: Localized error boundaries, global rendering crash safe guards, and centralized mock auth bootstrap gateways.
10. **Frontend Production Certification & Hardening (Phase 16.10)**: Global deterministic mock isolation, warning-free bundle compiles, and 7 comprehensive integration workflows verifying all core UI transitions. Certified with 132 passed Vitest tests.

---

## Plugin & Extension Runtime Platform (Phase 17)

Auralis implements a comprehensive, enterprise-ready **Plugin & Extension Runtime Platform** (`frontend/src/plugins/`) providing dynamic extendability with complete safety guarantees:

1. **Plugin Runtime Foundation (Phase 17.1)**: Extensible folder structure, type-safe manifest interfaces, registration events, and baseline mock registries.
2. **Plugin Discovery & Manifest Runtime (Phase 17.2)**: Scans directories, validates manifest JSON schemas (name, version, entryPoint, permissions, dependencies), and handles validation recovery.
3. **Plugin Dependency Resolution Runtime (Phase 17.3)**: Directed Acyclic Graph (DAG) sorting, cycles detection, missing dependencies reporting, and version-compatibility checking.
4. **Plugin Loading Runtime (Phase 17.4)**: Dynamic ES module loading, script tag injections, sandbox isolation bindings, and load timeouts.
5. **Plugin Lifecycle Runtime (Phase 17.5)**: Lifecycle state transitions (`LOADED` → `INITIALIZED` → `ACTIVATED` → `DEACTIVATED` → `UNLOADED`) with cascading state hooks.
6. **Plugin Capability & Extension Runtime (Phase 17.6)**: Registers capability handlers (UI elements, theme skins, custom voice commands, file parsers) under a global extension point registry.
7. **Plugin Security Sandbox Runtime (Phase 17.7)**: Restricts API access using safe proxies, freezing global structures, and sandboxing storage/network modules.
8. **Plugin Configuration Runtime (Phase 17.8)**: Merges default parameters, validates configurations using schema rules, and supports runtime settings updates.
9. **Plugin Runtime Integration (Phase 17.9)**: Incorporates plugin actions into main UI views and assistant planners.
10. **Plugin Runtime Certification (Phase 17.10)**: E2E scenarios verification, mock isolation, certified with 144 passing Vitest tests.

---

## Observability & Operations Runtime Platform (Phase 18)

Auralis implements a clean, provider-independent, strongly-typed **Observability & Operations Runtime Platform** (`frontend/src/observability/`):

1. **Monitoring Foundation (Phase 18.1)**: Unified core registry, custom errors, lifecycle states, diagnostic structures, and deep-freezing immutability rules.
2. **Logging Runtime (Phase 18.2)**: Structured logging engine with severity levels (`DEBUG`, `INFO`, `WARN`, `ERROR`, `FATAL`), message formats, custom destination sinks, and credential redactions.
3. **Metrics Runtime (Phase 18.3)**: Bounded instruments (Counters, Gauges, Histograms) supporting labels, delta aggregations, and statistics.
4. **Distributed Tracing Runtime (Phase 18.4)**: Cryptographic trace/span generation, hierarchical parent-child linking, diagnostics, and capacity-based trace eviction.
5. **Telemetry Runtime (Phase 18.5)**: Collection, normalization, batching, buffering (FIFO bounded queues), deterministic sampling, and multi-exporter isolation pipelines.

---

## Architecture Overview

```mermaid
graph TD
    User([User]) -->|Spoken / Typed Command| FrontendRuntime[Frontend Runtime Platform]
    
    subgraph Frontend Runtime Architecture Platform (Phase 16)
        FrontendRuntime --> FrontDI[1. Dependency Injection Container]
        FrontendRuntime --> FrontApp[2. Application & Plugin Runtime]
        FrontendRuntime --> FrontConfig[3. Configuration Runtime Subsystem]
        FrontendRuntime --> FrontEvents[4. Event Runtime Platform]
        FrontendRuntime --> FrontState[5. State Management Runtime Platform]
    end

    FrontEvents -->|API Request| Gateway[API Integration Gateway (Phase 15)]

    subgraph API & Backend Infrastructure Platform (Phases 14 & 15)
        Gateway --> ApiRouting[Request Routing & Auth Runtime]
        Gateway --> AppRuntime[Application Runtime & DI Container]
        Gateway --> AppConfig[Configuration Subsystem]
    end

    subgraph Assistant Architecture Platform (Phase 13)
        ApiRouting --> ConvRuntime[Conversation & Dialogue Runtime]
        ApiRouting --> DecRuntime[Decision & Reasoning Coordinator]
        ApiRouting --> MemRuntime[Assistant Memory Runtime]
        ApiRouting --> ExecRuntimeRef[Execution Runtime]
        ApiRouting --> VoiceRuntime[Voice Orchestration Runtime]
    end

    subgraph Capabilities & OS Abstraction
        ExecRuntimeRef --> FileIntel[File Intelligence]
        ExecRuntimeRef --> DesktopControl[Desktop Control]
        ExecRuntimeRef --> DevAssistant[Developer Assistant]
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
| **Vite** | 5.4.21 | Next-generation build tool and dev server. |
| **React** | 18.x | Component-based UI library. |
| **TypeScript** | 5.5 | Strongly-typed JavaScript superset for pure runtime architecture. |
| **Vitest** | 4.1.10 | High-performance unit testing framework for runtime certification. |
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
│   │   ├── config/            # Certified Configuration Runtime Subsystem (Phase 14.3)
│   │   └── di/                # Dependency Injection Subsystem (Phase 14.2)
│   ├── brain/                 # AI Brain Orchestration
│   │   ├── assistant/         # Assistant Architecture Platform (Phase 13)
│   │   ├── ai/                # AI Architecture & Runtime Platform (Phase 10)
│   │   ├── execution/         # Execution Architecture Platform (Phase 12)
│   │   ├── goal/              # Goal Interpreter
│   │   ├── reasoning/         # Reasoning Engine
│   │   └── planning/          # Dynamic Task Planner & ReferenceResolver
│   ├── capabilities/          # OS capabilities (files, desktop, automation, developer)
│   ├── core/                  # Assistant boundary, intent schemas, planner, and dispatcher
│   ├── memory/                # Tiered Memory System
│   ├── voice/                 # Modular Voice Engine subsystems
│   └── tests/                 # 2,905 unit & integration tests across 162 test modules
├── frontend/                  # Vite + React + TypeScript Frontend V2 App
│   ├── src/
│   │   ├── app/               # Application registry, routes, and providers
│   │   ├── components/        # Reusable presentation widgets (common, layout, navigation)
│   │   ├── layouts/           # Shell templates (AppLayout, DashboardLayout, WorkspaceLayout)
│   │   ├── pages/             # Route views (Dashboard, Files, Workspace, Assistant, Settings)
│   │   ├── services/          # Client layers (apiClient, authService, websocket, sync)
│   │   ├── state/             # Global Zustand stores, selectors, and models
│   │   └── theme/             # Styling theme provider templates
│   └── tests/                 # 132 Vitest tests covering state, views, themes, and integration workflows
└── docs/                      # Technical documentation and architecture specifications
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
* [x] **Lightweight Rebuilt Frontend Architecture (Phases 16.1 to 16.10):** Component Runtime, Layout & Navigation structures, Theme systems, global Zustand state store boundaries, API Client interfaces, WebSocket synchronization, voice and workspace controls, localized error boundaries, production builds, and 132 passed Vitest tests.
* [x] **Plugin & Extension Runtime Platform (Phases 17.1 to 17.10):** Plugin Runtime Foundation, discovery and manifest parsing, dependency resolution, ES module loaders, dynamic lifecycle hook pipelines, capability extension registries, security sandboxing proxies, and integration. Certified with 144 passed Vitest tests.
* [x] **Observability & Operations Runtime Platform (Phases 18.1 to 18.5):** Monitoring Foundation, structured Logging Runtime with credentials redaction, metrics aggregation instrument systems, hierarchical Trace/Span indexing, and Telemetry buffer pipelines. Certified with 97 passed Vitest tests.
* [ ] **Future Objectives:**
  * [ ] Operating System Desktop Packaging (Phase 11 / Electron & Tauri integration).
  * [ ] Document intelligence parser using local PyMuPDF extraction.
  * [ ] Plugin Marketplace for community extensions.
  * [ ] Drag-and-drop workflow visual builder.

---

## Installation & Testing

```bash
# Backend Setup & Test Suite (2,905 Pytest tests)
python -m venv venv
.\venv\Scripts\activate
pip install -r backend/requirements.txt
pytest backend/tests

# Frontend Setup, Test Suite & Build (520 Vitest tests)
cd frontend
npm install
npm test
npm run build
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
