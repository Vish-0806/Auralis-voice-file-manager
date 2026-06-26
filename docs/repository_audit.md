# Auralis Repository Audit - Sprint 1

This document provides a detailed breakdown of the directory structures, detected duplications, placeholder files, unused modules, and import/documentation inconsistencies across the Auralis codebase as of Sprint 1.

---

## 1. Verified Directory Structures

### 1.1 Backend Structure (`backend/`)
The backend is a FastAPI application running on Python 3.13. It is divided into core orchestration, domain engines, capability definitions, and API routes.

```
backend/
├── api/                    # API Endpoints (routes.py, voice_routes.py, listener_routes.py, file_routes.py)
├── app/                    # Application state containers (controller.py, state_manager.py)
├── core/                   # Core orchestrator (assistant.py, planner.py, dispatcher.py, state.py, session.py)
├── events/                 # Pub/Sub Event System (event_bus.py, dispatcher.py, event_types.py)
├── os/                     # OS Adapters (adapters/windows, macos, linux adapters & registries)
├── ai/                     # Cognitive/Agent Reasoning layer (agent.py, reasoning.py, prompt_builder.py)
├── ai_engine/              # Command parsing engine (command_parser.py, entity_extractor.py)
├── file_engine/            # File system operational logic (file_operations.py, search_engine.py)
├── voice/                  # Audio recording and speech recognition (speech_to_text.py, wake_word.py)
├── capabilities/           # Capability registrations & managers (subfolders for desktop, files, system, etc.)
├── utils/                  # Shared utilities (logger.py, helpers.py, constants.py)
├── tests/                  # Backend pytest suite (test_command_parser.py, test_confirmation.py, etc.)
├── main.py                 # Application entry point
└── requirements.txt        # Backend dependencies
```

### 1.2 Frontend Structure (`frontend/`)
The frontend is a React single-page application built with Vite and Tailwind/Vanilla CSS.

```
frontend/
├── src/
│   ├── components/         # UI Elements (CommandCard, StatusIndicator, VoiceButton, SearchResults)
│   ├── hooks/              # Custom hooks (useVoiceCommands, useVoice)
│   ├── pages/              # View pages (Dashboard, Home)
│   ├── services/           # API integration (api.js)
│   ├── styles/             # Application stylesheets (global.css)
│   ├── utils/              # Utility helpers (helper.js)
│   ├── App.jsx             # React root component
│   └── main.jsx            # Vite mounting script
├── index.html              # HTML template
├── package.json            # Node.js dependencies
└── vite.config.js          # Vite configurations
```

---

## 2. Detected Duplications

### 2.1 Duplicate Folders
Several directory hierarchies exist in both a "legacy/active" form and a "new/placeholder" capability or architecture form:

1. **AI Cognitive Processing**:
   * `backend/ai_engine/`: **Active**. Contains parser, entity extractor, intent classifier, and normalizer. Used by `core/assistant.py` and `voice/continuous_listener.py`.
   * `backend/ai/`: **Unused**. Contains newer agentic layouts (`agent.py`, `reasoning.py`, `prompt_builder.py`, `tool_selector.py`).
2. **Task & Workflow Automation**:
   * `backend/automation/`: **Active**. Contains `task_runner.py` and `workflow_manager.py`.
   * `backend/capabilities/automation/`: **Unused**. Contains placeholder triggers, conditions, actions, and workflows.
3. **Storage & Memory Layer**:
   * `backend/memory/`: **Active**. Contains cache, preference, workflow, and long term memories.
   * `backend/storage/`: **Unused**. Contains empty subdirectories (`sqlite/`, `vector/`, `index/`).
4. **File Systems & Operations**:
   * `backend/file_engine/`: **Active**. Houses `file_operations.py`, `source_resolver.py`, and `search_engine.py`.
   * `backend/capabilities/files/`: **Unused**. Contains empty capability templates (`indexing.py`, `operations.py`, `search.py`).

### 2.2 Conflicting Classes / Modules
* **State Management split**:
  * `backend/core/state.py` defines `StateManager` for system state transitions (Idle, Listening, Processing, Confirming, Executing) but the implementation is placeholder (`pass`).
  * `backend/app/state_manager.py` defines `StateManager` for confirmation workflows (tracking pending actions).
  * *Impact*: Two classes share the name `StateManager`, leading to class/module name collisions and high cognitive load.

---

## 3. Detected Placeholder Modules & Stubs

### 3.1 Empty Files (0 Bytes)
* **Backend**:
  * `backend/app/controller.py`
  * `backend/tests/test_ai.py`
* **Frontend**:
  * `frontend/src/pages/Home.jsx`
  * `frontend/src/components/CommandOutput.jsx`
  * `frontend/src/components/FileExplorer.jsx`
  * `frontend/src/hooks/useVoice.js`
  * `frontend/src/utils/helper.js`

### 3.2 Placeholder Directories / Packages
* `backend/services/`: Empty directory containing only a `README.md` and `__init__.py`.
* `backend/config/`: Empty directory containing only a `README.md` and `__init__.py`.
* `backend/storage/`: Empty directories `index/`, `sqlite/`, and `vector/`.
* `backend/capabilities/`: Entirely stubbed. Subfolders `desktop`, `developer`, `documents`, `files`, `system`, and `automation` contain only basic model and interface definitions with `pass` logic.

---

## 4. Detected Unused Files
All files listed in section **3.1** are empty and unused by the current production build and imports:
* `Home.jsx` is never rendered by `App.jsx` (which directly mounts `Dashboard.jsx`).
* `CommandOutput.jsx` and `FileExplorer.jsx` are never imported or rendered by `Dashboard.jsx`.
* `useVoice.js` is never imported (the dashboard uses `useVoiceCommands.js`).
* `helper.js` is never imported.
* `controller.py` and `test_ai.py` are empty and never loaded.

---

## 5. Broken / Inconsistent Imports & Documentation

### 5.1 Documentation-to-Code Divergence
* **Module name mismatch**: `backend/BACKEND_MODULES.md` refers to the speech packages as `voice_engine/` (e.g. `from voice_engine.speech_to_text import listen`). However, the actual module folder is named `voice/` (causing `from voice.speech_to_text import listen` to be the actual working code import).
* **Reference links**: Multiple markdown documents in `docs/` point to non-existent config paths or use outdated naming references.

### 5.2 Executable Imports Status
* All executable Python imports in `backend/main.py` and the `tests/` directory are fully functional and pass validation checks (verified via test executions).

---

## 6. Missing Documentation
* **Architectural Transition Guide**: There is no documentation explaining the transition strategy from the legacy engines (`ai_engine`, `file_engine`, `voice`) to the new core structures (`planner.py`, `dispatcher.py`, `assistant.py`).
* **Capability Registry Guidelines**: The registry mechanism for third-party extensions (under `capabilities/registry.py`) is completely undocumented, making it unclear how future developers should register new tools.
