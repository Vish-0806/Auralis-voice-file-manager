# Auralis Technical Debt Register - Sprint 1

This document registers the architectural layout of Auralis, highlights operational risks introduced by code fragmentation, and outlines specific tasks to be performed in the next sprint to refactor and stabilize the repository.

---

## 1. Explanation of Current Architecture

Auralis is transitioning from a legacy engine-based structure to a modern clean architecture built on dependency injection and domain boundary isolation.

### 1.1 Request and Command Flow
1. **Gateways**: API routes (in `backend/api/`) and the continuous microphone listener (in `backend/voice/continuous_listener.py`) receive commands from the frontend.
2. **Orchestrator**: Gateway requests are forwarded to the central coordinator: `AuralisAssistant` (defined in `backend/core/assistant.py`).
3. **Adapters & Interfaces**: `AuralisAssistant` uses abstract interfaces (such as `IAgentBrain`, `IMemoryManager`, `IEventBus`, `IOSAdapter`) and instantiates lightweight, legacy adapters to bridge the core pipeline to the original engines:
   * `LegacyAgentBrain` → delegates to `ai_engine.command_parser.parse_command`
   * `LegacyOSAdapter` → delegates to `file_engine.source_resolver.resolve_source`
4. **Engines**: The actual work is executed inside domain engines like `ai_engine/` (for command parsing) and `file_engine/` (for writing and searching folders/files).

---

## 2. Current Risks & Impact Assessment

### 2.1 Codebase Split & Redundancy
* **AI Split (`ai_engine/` vs. `ai/`)**:
  * *Risk*: The agentic cognitive layers inside `backend/ai/` are currently dormant/placeholder, while the legacy parser in `backend/ai_engine/` remains active. Developers editing the parsing logic may mistakenly modify files under `ai/` expecting behavior changes.
* **Capabilities Split (`capabilities/files/` vs. `file_engine/` & `capabilities/automation/` vs. `automation/`)**:
  * *Risk*: File operations and automated workflows are implemented in the root engines, but empty stubs also exist under `capabilities/`. This duplicate structure makes finding the true operational code paths difficult.
* **Storage Split (`storage/` vs. `memory/`)**:
  * *Risk*: There is a `backend/storage/` package which is entirely unused and consists of empty placeholders. The active data cache and session handlers are located inside `backend/memory/`.

### 2.2 Class Name Collision
* **The `StateManager` Conflict**:
  * *Risk*: Both `backend/core/state.py` and `backend/app/state_manager.py` export a class named `StateManager`.
  * *Impact*: This increases search noise, leads to developer errors during imports, and can confuse automated IDE refactoring or static analysis tools.

### 2.3 Noise & Bundle bloat (Frontend & Backend)
* **Empty React modules**: 5 empty files (`Home.jsx`, `CommandOutput.jsx`, `FileExplorer.jsx`, `useVoice.js`, `helper.js`) exist in the frontend. This adds cognitive drag and creates dead code routes.
* **Empty python stubs**: `backend/app/controller.py` and `backend/tests/test_ai.py` are empty, artificially lowering code density and giving false impressions of testing coverage.

---

## 3. Future Cleanup Tasks (Sprint 2 Roadmap)

The following cleanup and deprecation tasks should be completed during Sprint 2:

### 3.1 Reconcile State Managers
* Rename or consolidate the two `StateManager` classes.
* We recommend renaming `app/state_manager.py`'s class to `ConfirmationManager` or `PendingActionManager`, while leaving `core/state.py`'s class as `SystemStateManager` to reflect its system-wide status transition role.

### 3.2 Consolidate AI and Engine Folders
* **Migrate AI Engines**: Integrate the command normalizer and parser from `ai_engine/` into the new agentic framework in `ai/`. Once all entry points import from `ai.agent` or `ai.parser`, completely deprecate the `ai_engine/` directory.
* **Integrate Capabilities**: Implement `load_capabilities` inside `backend/capabilities/manager.py` to automatically register actions from the capabilities packages, and gradually move logic from `file_engine/` into the `capabilities/files/` package.

### 3.3 Purge Unused Files
Delete the following files and directories which have been audited and confirmed as empty placeholders or dead code:

#### Frontend:
* `frontend/src/pages/Home.jsx`
* `frontend/src/components/CommandOutput.jsx`
* `frontend/src/components/FileExplorer.jsx`
* `frontend/src/hooks/useVoice.js`
* `frontend/src/utils/helper.js`

#### Backend:
* `backend/app/controller.py`
* `backend/tests/test_ai.py`
* `backend/storage/` (directory)
* `backend/services/` (directory)
* `backend/config/` (directory)

### 3.4 Update Reference Documentation
* Rename all occurrences of `voice_engine` in `backend/BACKEND_MODULES.md` and other documentation to `voice` to match the actual folder namespace and eliminate setup import errors.
