# Auralis Codebase Refactor Analysis Report

This document provides a comprehensive architectural analysis of the Auralis Voice File Manager repository. It outlines duplicate modules, redundant responsibilities, dead code, overlapping functionalities, import dependencies, circular dependencies, and a detailed plan for safe structural refactoring.

---

## 1. Executive Summary

Auralis is transitioning from a legacy, coupled, engine-based design to a clean, modular architecture based on abstract interfaces, dependency injection, and domain boundary separation (OSAL and Capabilities model). During this migration, a split has emerged where legacy active logic runs in parallel with dormant or stubbed new-architecture placeholders. 

This analysis details the exact duplication, obsolete stubs, dependency cycles, and refactoring risks to guide the next phase of modernization.

---

## 2. Duplicate Modules & Responsibilities

The codebase currently contains parallel structures representing both the "Legacy Active" engines and the "New Modular" stubs:

1. **AI & Cognitive Processing layer**:
   * **Legacy Active**: [ai_engine](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/ai_engine) houses the command parsing, entity extraction, and intent classification engines used by API gateways.
   * **New/Dormant**: [ai](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/ai) houses agentic and cognitive loops designed to replace static parser rules.
2. **File Systems & Operations**:
   * **Legacy Active**: [file_engine](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/file_engine) implements file operations, indexing, and transfers.
   * **New/Dormant**: [capabilities/files](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/capabilities/files) represents the new clean ports structure, but contains stubs with `pass` parameters.
3. **Task & Workflow Automation**:
   * **Legacy Active**: [automation](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/automation) runs command line scripts and manages workflow definitions.
   * **New/Dormant**: [capabilities/automation](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/capabilities/automation) is defined as a stub capability structure.
4. **Storage & Database Memory**:
   * **Legacy Active**: [memory](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/memory) manages standard session storage, activity log cache, and preferences.
   * **New/Dormant**: [storage](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/storage) contains stub folders for `sqlite`, `vector`, and `index`.
5. **State Management Collision**:
   * Both [backend/app/state_manager.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/app/state_manager.py) and [backend/core/state.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/core/state.py) export a `StateManager` class.
     * `app/state_manager.py` tracks voice action confirmations.
     * `core/state.py` manages central system status transitions.
     * *Risk*: High cognitive load and class naming collisions during imports.

---

## 3. Dead Code & Obsolete Files

### 3.1 Empty Stubs (0-Byte Files)
The following files are completely blank and serve no functional purpose in the current build:
* **Backend**:
  * [controller.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/app/controller.py)
  * [test_ai.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/tests/test_ai.py)
* **Frontend**:
  * [Home.jsx](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/frontend/src/pages/Home.jsx)
  * [CommandOutput.jsx](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/frontend/src/components/CommandOutput.jsx)
  * [FileExplorer.jsx](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/frontend/src/components/FileExplorer.jsx)
  * [useVoice.js](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/frontend/src/hooks/useVoice.js)
  * [helper.js](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/frontend/src/utils/helper.js)

### 3.2 Obsolete / Redundant Files
* **Module Structure**: [MODULE_STRUCTURE.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/MODULE_STRUCTURE.py) is a workspace map script that is not imported or needed for production runs.

---

## 4. Overlapping Functionality & Merge Recommendations

### 4.1 State Manager Consolidation
* **Action**: Rename the class in [backend/app/state_manager.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/app/state_manager.py) to `ConfirmationManager` or `PendingActionManager`, and rename the class in [backend/core/state.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/core/state.py) to `SystemStateManager`. 
* **Rationale**: Resolves the class name collision and differentiates voice-action confirmation state from system lifecycle state.

### 4.2 AI Engine Migration
* **Action**: Merge the rule-based intent parsing from [backend/ai_engine/command_parser.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/ai_engine/command_parser.py) into [backend/ai/prompt_builder.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/ai/prompt_builder.py). Move `entity_extractor.py` and `intent_classifier.py` rules as schema constraints into `ai/models.py`.
* **Rationale**: Unifies rule-based parsing with LLM-based agent reasoning under a single module wrapper, allowing a clean deprecation of `ai_engine/`.

### 4.3 OS Abstraction Layer Migration
* **Action**: Relocate platform-specific path and permission resolution from [backend/file_engine/path_resolver.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/file_engine/path_resolver.py) and [backend/file_engine/permissions.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/file_engine/permissions.py) into the OS adapter package: [backend/os/adapters/windows/files.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/os/adapters/windows/files.py).
* **Rationale**: Decouples the general file engine from platform-specific APIs (e.g. Windows win32 API or path separators).

### 4.4 File Operations Capability Migration
* **Action**: Consolidate file system operations from [backend/file_engine/file_operations.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/file_engine/file_operations.py), [backend/file_engine/source_resolver.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/file_engine/source_resolver.py), and [backend/file_engine/transfer.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/file_engine/transfer.py) into [backend/capabilities/files/operations.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/capabilities/files/operations.py).
* **Rationale**: Moves direct operations to the pluggable Capability framework, freeing core handlers from direct disk IO.

---

## 5. Folders to Remove vs. Folders to Keep

### 5.1 Folders that can be Removed
* `backend/storage/`: **Remove**. Entirely empty placeholders for DB vectors. The operational session manager and caches reside in `backend/memory/`.
* `backend/services/`: **Remove**. Contains only an empty `__init__.py` and `README.md`.
* `backend/config/`: **Remove**. Contains only an empty `__init__.py` and `README.md`. (System configurations reside in `backend/config.yaml` or are handled in `core/`).
* *Post-Migration Deprecations* (Once files are merged):
  * `backend/ai_engine/`
  * `backend/file_engine/`
  * `backend/automation/`

### 5.2 Folders that Should Stay
* `backend/core/`: **Stay**. The main system orchestrator (assistant, planners, and dispatchers).
* `backend/ai/`: **Stay**. Target location for unified cognitive agent workflows.
* `backend/api/`: **Stay**. Contains REST API route descriptors.
* `backend/capabilities/`: **Stay**. The plugin Capability folders (`desktop`, `developer`, `documents`, `files`, `system`, `automation`).
* `backend/events/`: **Stay**. Asynchronous Pub/Sub event infrastructure.
* `backend/memory/`: **Stay**. Active session context and activity cache.
* `backend/os/`: **Stay**. Cross-platform OS adapters (Windows, macOS, Linux adapters).
* `backend/voice/`: **Stay**. Speech recording, STT, and TTS engines.
* `backend/utils/`: **Stay**. Generic helpers and logging libraries.
* `backend/tests/`: **Stay**. Pytest suites.
* `frontend/src/components/`, `hooks/`, `pages/`, `services/`, `styles/`, `utils/`: **Stay** (after removing the dead stubs detailed in section 3.1).

---

## 6. Import Dependency Analysis & Topology

### 6.1 Dependency Coupling
* Gateway routes (`api/routes.py` and `api/voice_routes.py`) bypass core boundaries to import concrete engines directly (e.g., `from file_engine.file_operations import execute_action`).
* **Target Design**: Gateways should import only `AuralisAssistant` (core orchestrator), which utilizes dispatcher ports to execute decoupled Capabilities.

### 6.2 Circular Imports
The analysis detected **1 circular import cycle**:
* `backend/voice/continuous_listener.py` $\leftrightarrow$ `backend/voice/listener.py`
  * *Mechanism*: `continuous_listener.py` imports `ContinuousListener` from `listener.py`. At the same time, `listener.py` imports `voice.continuous_listener` inside its runtime `listen_loop` method to invoke patched methods during tests.
  * *Resolution*: Decouple testing overrides by providing a mock listener implementation in test suites rather than patching wrapping modules.

---

## 7. Complete Active (Imported) Files Catalog

### Backend Active Files:
- [interfaces.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/ai/interfaces.py) *(Imported by: backend/ai/agent.py, backend/ai/context_builder.py, backend/ai/prompt_builder.py, backend/ai/reasoning.py, backend/ai/safety.py, backend/ai/tool_selector.py)*
- [models.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/ai/models.py) *(Imported by: backend/ai/agent.py, backend/ai/conversation.py, backend/ai/interfaces.py, backend/ai/prompt_builder.py, backend/ai/reasoning.py, backend/ai/safety.py, backend/ai/tool_selector.py)*
- [command_normalizer.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/ai_engine/command_normalizer.py) *(Imported by: backend/ai_engine/command_parser.py, backend/ai_engine/entity_extractor.py, backend/ai_engine/__init__.py, backend/tests/test_command_parser.py)*
- [command_parser.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/ai_engine/command_parser.py) *(Imported by: backend/ai_engine/__init__.py, backend/scripts/run_parser_smoke.py, backend/tests/test_command_parser.py, backend/voice/continuous_listener.py)*
- [entity_extractor.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/ai_engine/entity_extractor.py) *(Imported by: backend/ai_engine/command_parser.py, backend/ai_engine/__init__.py, backend/tests/test_command_parser.py)*
- [intent_classifier.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/ai_engine/intent_classifier.py) *(Imported by: backend/ai_engine/command_parser.py, backend/ai_engine/__init__.py, backend/tests/test_command_parser.py, backend/tests/test_confirmation.py, backend/voice/listener.py)*
- [assistant_routes.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/api/assistant_routes.py) *(Imported by: backend/main.py)*
- [file_routes.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/api/file_routes.py) *(Imported by: backend/main.py)*
- [listener_routes.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/api/listener_routes.py) *(Imported by: backend/main.py)*
- [routes.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/api/routes.py) *(Imported by: backend/main.py)*
- [voice_routes.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/api/voice_routes.py) *(Imported by: backend/main.py)*
- [state_manager.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/app/state_manager.py) *(Imported by: backend/app/__init__.py, backend/tests/test_state_manager.py, backend/voice/voice_session.py)*
- [__init__.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/capabilities/files/__init__.py) *(Imported by: backend/api/assistant_routes.py)*
- [file_capability.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/capabilities/files/file_capability.py) *(Imported by: backend/capabilities/files/__init__.py, backend/tests/test_folder_ops.py, backend/tests/test_integration.py, backend/tests/test_organizer_ops.py)*
- [file_operation_service.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/capabilities/files/file_operation_service.py) *(Imported by: backend/capabilities/files/file_capability.py, backend/capabilities/files/__init__.py)*
- [folder_service.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/capabilities/files/folder_service.py) *(Imported by: backend/capabilities/files/file_capability.py, backend/capabilities/files/__init__.py, backend/tests/test_folder_ops.py)*
- [download_organizer.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/capabilities/files/organizer/download_organizer.py) *(Imported by: backend/capabilities/files/file_capability.py, backend/capabilities/files/__init__.py, backend/tests/test_organizer_ops.py)*
- [file_classifier.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/capabilities/files/organizer/file_classifier.py) *(Imported by: backend/capabilities/files/organizer/download_organizer.py, backend/tests/test_organizer_ops.py)*
- [organization_rules.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/capabilities/files/organizer/organization_rules.py) *(Imported by: backend/capabilities/files/organizer/download_organizer.py, backend/capabilities/files/organizer/file_classifier.py, backend/tests/test_organizer_ops.py)*
- [report_generator.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/capabilities/files/organizer/report_generator.py) *(Imported by: backend/capabilities/files/organizer/download_organizer.py, backend/tests/test_organizer_ops.py)*
- [path_resolver.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/capabilities/files/path_resolver.py) *(Imported by: backend/capabilities/files/file_capability.py, backend/capabilities/files/search_engine.py, backend/capabilities/files/__init__.py)*
- [search_engine.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/capabilities/files/search_engine.py) *(Imported by: backend/capabilities/files/file_capability.py, backend/capabilities/files/__init__.py)*
- [transfer_service.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/capabilities/files/transfer_service.py) *(Imported by: backend/capabilities/files/file_capability.py, backend/capabilities/files/__init__.py)*
- [interfaces.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/capabilities/interfaces.py) *(Imported by: backend/capabilities/manager.py, backend/capabilities/registry.py, backend/capabilities/automation/manager.py, backend/capabilities/desktop/manager.py, backend/capabilities/developer/manager.py, backend/capabilities/documents/manager.py, backend/capabilities/files/manager.py, backend/capabilities/system/manager.py)*
- [mock_file.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/capabilities/mock/mock_file.py) *(Imported by: backend/core/dispatcher.py)*
- [models.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/capabilities/models.py) *(Imported by: backend/capabilities/interfaces.py)*
- [conftest.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/conftest.py) *(Imported by: System EntryPoint)*
- [assistant.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/core/assistant.py) *(Imported by: backend/api/assistant_routes.py, backend/api/file_routes.py, backend/api/listener_routes.py, backend/api/routes.py, backend/api/voice_routes.py, backend/tests/test_integration.py)*
- [dispatcher.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/core/dispatcher.py) *(Imported by: backend/api/assistant_routes.py, backend/tests/test_integration.py)*
- [exceptions.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/core/exceptions.py) *(Imported by: backend/capabilities/exceptions.py, backend/core/assistant.py, backend/core/dispatcher.py, backend/core/planner.py, backend/core/__init__.py, backend/os/exceptions.py)*
- [intents.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/core/intents.py) *(Imported by: backend/capabilities/files/file_capability.py, backend/core/assistant.py, backend/core/dispatcher.py, backend/core/models.py, backend/core/planner.py, backend/core/__init__.py, backend/tests/test_folder_ops.py, backend/tests/test_integration.py, backend/tests/test_organizer_ops.py)*
- [interfaces.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/core/interfaces.py) *(Imported by: backend/capabilities/files/file_capability.py, backend/capabilities/mock/mock_file.py, backend/core/assistant.py, backend/core/context.py, backend/core/dispatcher.py, backend/core/planner.py, backend/core/__init__.py)*
- [models.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/core/models.py) *(Imported by: backend/api/assistant_routes.py, backend/capabilities/files/file_capability.py, backend/core/assistant.py, backend/core/dispatcher.py, backend/core/interfaces.py, backend/core/planner.py, backend/core/__init__.py, backend/tests/test_folder_ops.py, backend/tests/test_integration.py, backend/tests/test_organizer_ops.py)*
- [planner.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/core/planner.py) *(Imported by: backend/api/assistant_routes.py, backend/tests/test_folder_ops.py, backend/tests/test_integration.py, backend/tests/test_organizer_ops.py)*
- [dispatcher.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/events/dispatcher.py) *(Imported by: backend/events/event_bus.py)*
- [interfaces.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/events/interfaces.py) *(Imported by: backend/events/dispatcher.py, backend/events/event_bus.py, backend/events/publisher.py, backend/events/registry.py, backend/events/subscriber.py)*
- [models.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/events/models.py) *(Imported by: backend/events/dispatcher.py, backend/events/event.py, backend/events/event_bus.py, backend/events/interfaces.py, backend/events/registry.py, backend/events/subscriber.py)*
- [registry.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/events/registry.py) *(Imported by: backend/events/event_bus.py)*
- [file_operations.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/file_engine/file_operations.py) *(Imported by: backend/tests/test_confirmation.py, backend/tests/test_file_ops.py, backend/tests/test_organizer.py, backend/tests/test_source_resolution.py, backend/voice/continuous_listener.py, backend/voice/listener.py, backend/voice/voice_session.py)*
- [organizer.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/file_engine/organizer.py) *(Imported by: backend/file_engine/file_operations.py, backend/file_engine/__init__.py, backend/tests/test_organizer.py)*
- [search_engine.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/file_engine/search_engine.py) *(Imported by: backend/file_engine/file_operations.py, backend/file_engine/source_resolver.py, backend/file_engine/__init__.py, backend/tests/test_file_ops.py)*
- [source_resolver.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/file_engine/source_resolver.py) *(Imported by: backend/file_engine/file_operations.py, backend/file_engine/__init__.py, backend/tests/test_source_resolution.py)*
- [transfer.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/file_engine/transfer.py) *(Imported by: backend/file_engine/file_operations.py, backend/file_engine/__init__.py, backend/tests/test_transfer.py)*
- [main.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/main.py) *(Imported by: backend/tests/test_confirmation.py, backend/tests/test_listener_routes.py)*
- [interfaces.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/memory/interfaces.py) *(Imported by: backend/memory/cache.py, backend/memory/long_term_memory.py, backend/memory/manager.py, backend/memory/preference_memory.py, backend/memory/storage.py)*
- [models.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/memory/models.py) *(Imported by: backend/memory/interfaces.py, backend/memory/long_term_memory.py, backend/memory/preference_memory.py, backend/memory/storage.py)*
- [__init__.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/os/__init__.py) *(Imported by: backend/conftest.py, backend/main.py, backend/capabilities/files/file_capability.py, backend/capabilities/files/file_operation_service.py, backend/capabilities/files/folder_service.py, backend/capabilities/files/path_resolver.py, backend/file_engine/file_operations.py, backend/file_engine/organizer.py, backend/file_engine/search_engine.py, backend/file_engine/source_resolver.py, backend/file_engine/transfer.py, backend/tests/test_confirmation.py, backend/tests/test_file_ops.py, backend/tests/test_folder_ops.py, backend/tests/test_integration.py, backend/tests/test_organizer.py, backend/tests/test_organizer_ops.py, backend/tests/test_source_resolution.py, backend/tests/test_transfer.py, backend/utils/helpers.py, backend/utils/logger.py)*
- [interfaces.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/os/interfaces.py) *(Imported by: backend/os/manager.py, backend/os/registry.py, backend/os/adapters/linux/adapter.py, backend/os/adapters/macos/adapter.py, backend/os/adapters/windows/adapter.py)*
- [desktop_port.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/os/ports/desktop_port.py) *(Imported by: backend/os/adapters/linux/desktop.py, backend/os/adapters/macos/desktop.py, backend/os/adapters/windows/desktop.py)*
- [file_port.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/os/ports/file_port.py) *(Imported by: backend/os/adapters/linux/files.py, backend/os/adapters/macos/files.py, backend/os/adapters/windows/files.py)*
- [notification_port.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/os/ports/notification_port.py) *(Imported by: backend/os/adapters/linux/notifications.py, backend/os/adapters/macos/notifications.py, backend/os/adapters/windows/notifications.py)*
- [process_port.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/os/ports/process_port.py) *(Imported by: backend/os/adapters/linux/processes.py, backend/os/adapters/macos/processes.py, backend/os/adapters/windows/processes.py)*
- [system_port.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/os/ports/system_port.py) *(Imported by: backend/os/adapters/linux/system.py, backend/os/adapters/macos/system.py, backend/os/adapters/windows/system.py)*
- [registry.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/os/registry.py) *(Imported by: backend/os/manager.py)*
- [constants.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/utils/constants.py) *(Imported by: backend/file_engine/organizer.py)*
- [helpers.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/utils/helpers.py) *(Imported by: backend/tests/test_confirmation.py, backend/tests/test_file_ops.py, backend/tests/test_organizer.py, backend/tests/test_source_resolution.py, backend/voice/listener.py)*
- [logger.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/utils/logger.py) *(Imported by: backend/ai_engine/command_normalizer.py, backend/ai_engine/command_parser.py, backend/ai_engine/entity_extractor.py, backend/ai_engine/intent_classifier.py, backend/api/assistant_routes.py, backend/api/file_routes.py, backend/api/listener_routes.py, backend/api/voice_routes.py, backend/file_engine/organizer.py, backend/file_engine/search_engine.py, backend/file_engine/source_resolver.py, backend/file_engine/transfer.py, backend/voice/listener.py, backend/voice/providers/google_recognizer.py, backend/voice/providers/pyttsx3_synthesizer.py, backend/voice/providers/rule_wake_word.py)*
- [audio_stream.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/voice/audio_stream.py) *(Imported by: backend/voice/providers/google_recognizer.py)*
- [continuous_listener.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/voice/continuous_listener.py) *(Imported by: backend/tests/test_voice.py, backend/voice/listener.py)*
- [interfaces.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/voice/interfaces.py) *(Imported by: backend/voice/audio_stream.py, backend/voice/listener.py, backend/voice/manager.py, backend/voice/recognizer.py, backend/voice/synthesizer.py, backend/voice/voice_session.py, backend/voice/providers/google_recognizer.py, backend/voice/providers/pyttsx3_synthesizer.py, backend/voice/providers/rule_wake_word.py)*
- [listener.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/voice/listener.py) *(Imported by: backend/voice/continuous_listener.py, backend/voice/__init__.py)*
- [manager.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/voice/manager.py) *(Imported by: backend/voice/listener.py, backend/voice/speech_to_text.py, backend/voice/text_to_speech.py, backend/voice/wake_word.py, backend/voice/__init__.py)*
- [models.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/voice/models.py) *(Imported by: backend/voice/voice_session.py)*
- [google_recognizer.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/voice/providers/google_recognizer.py) *(Imported by: backend/voice/recognizer.py)*
- [pyttsx3_synthesizer.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/voice/providers/pyttsx3_synthesizer.py) *(Imported by: backend/voice/synthesizer.py)*
- [rule_wake_word.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/voice/providers/rule_wake_word.py) *(Imported by: backend/voice/manager.py, backend/voice/wake_word.py)*
- [recognizer.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/voice/recognizer.py) *(Imported by: backend/voice/manager.py)*
- [speech_to_text.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/voice/speech_to_text.py) *(Imported by: backend/voice/continuous_listener.py, backend/voice/__init__.py)*
- [synthesizer.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/voice/synthesizer.py) *(Imported by: backend/voice/manager.py)*
- [text_to_speech.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/voice/text_to_speech.py) *(Imported by: backend/voice/continuous_listener.py, backend/voice/__init__.py)*
- [voice_session.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/voice/voice_session.py) *(Imported by: backend/voice/manager.py)*
- [wake_word.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/voice/wake_word.py) *(Imported by: backend/tests/test_wake_word.py, backend/voice/continuous_listener.py, backend/voice/__init__.py)*

### Frontend Active Files:
- [App.jsx](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/frontend/src/App.jsx) *(Imported by: frontend/src/main.jsx)*
- [CommandCard.jsx](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/frontend/src/components/CommandCard.jsx) *(Imported by: frontend/src/pages/Dashboard.jsx)*
- [SearchResults.jsx](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/frontend/src/components/SearchResults.jsx) *(Imported by: frontend/src/pages/Dashboard.jsx)*
- [StatusIndicator.jsx](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/frontend/src/components/StatusIndicator.jsx) *(Imported by: frontend/src/pages/Dashboard.jsx)*
- [VoiceButton.jsx](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/frontend/src/components/VoiceButton.jsx) *(Imported by: frontend/src/pages/Dashboard.jsx)*
- [useVoiceCommands.js](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/frontend/src/hooks/useVoiceCommands.js) *(Imported by: frontend/src/pages/Dashboard.jsx)*
- [main.jsx](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/frontend/src/main.jsx) *(Imported by: Vite EntryPoint)*
- [Dashboard.jsx](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/frontend/src/pages/Dashboard.jsx) *(Imported by: frontend/src/App.jsx)*
- [api.js](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/frontend/src/services/api.js) *(Imported by: frontend/src/hooks/useVoiceCommands.js)*
- [global.css](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/frontend/src/styles/global.css) *(Imported by: frontend/src/App.jsx)*

---

## 8. Complete Inactive (Never Imported) Files Catalog

*Note: Test files and helper scripts are categorized as inactive below because they are executed externally (e.g. via pytest) rather than imported directly by production code paths.*

### Backend Inactive Files:
- [MODULE_STRUCTURE.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/MODULE_STRUCTURE.py)
- [__init__.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/ai/__init__.py)
- [agent.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/ai/agent.py)
- [context_builder.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/ai/context_builder.py)
- [conversation.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/ai/conversation.py)
- [prompt_builder.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/ai/prompt_builder.py)
- [reasoning.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/ai/reasoning.py)
- [response_generator.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/ai/response_generator.py)
- [safety.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/ai/safety.py)
- [tool_selector.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/ai/tool_selector.py)
- [__init__.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/ai_engine/__init__.py)
- [response_generator.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/ai_engine/response_generator.py)
- [__init__.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/api/__init__.py)
- [__init__.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/app/__init__.py)
- [controller.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/app/controller.py)
- [__init__.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/automation/__init__.py)
- [task_runner.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/automation/task_runner.py)
- [workflow_manager.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/automation/workflow_manager.py)
- [__init__.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/capabilities/__init__.py)
- [__init__.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/capabilities/automation/__init__.py)
- [actions.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/capabilities/automation/actions.py)
- [conditions.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/capabilities/automation/conditions.py)
- [interfaces.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/capabilities/automation/interfaces.py)
- [manager.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/capabilities/automation/manager.py)
- [models.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/capabilities/automation/models.py)
- [scheduler.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/capabilities/automation/scheduler.py)
- [triggers.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/capabilities/automation/triggers.py)
- [workflows.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/capabilities/automation/workflows.py)
- [__init__.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/capabilities/desktop/__init__.py)
- [applications.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/capabilities/desktop/applications.py)
- [clipboard.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/capabilities/desktop/clipboard.py)
- [interfaces.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/capabilities/desktop/interfaces.py)
- [manager.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/capabilities/desktop/manager.py)
- [models.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/capabilities/desktop/models.py)
- [notifications.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/capabilities/desktop/notifications.py)
- [screenshots.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/capabilities/desktop/screenshots.py)
- [windows.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/capabilities/desktop/windows.py)
- [__init__.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/capabilities/developer/__init__.py)
- [docker.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/capabilities/developer/docker.py)
- [git.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/capabilities/developer/git.py)
- [interfaces.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/capabilities/developer/interfaces.py)
- [java.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/capabilities/developer/java.py)
- [manager.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/capabilities/developer/manager.py)
- [models.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/capabilities/developer/models.py)
- [node.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/capabilities/developer/node.py)
- [python.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/capabilities/developer/python.py)
- [terminal.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/capabilities/developer/terminal.py)
- [vscode.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/capabilities/developer/vscode.py)
- [__init__.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/capabilities/documents/__init__.py)
- [interfaces.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/capabilities/documents/interfaces.py)
- [manager.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/capabilities/documents/manager.py)
- [models.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/capabilities/documents/models.py)
- [office.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/capabilities/documents/office.py)
- [pdf.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/capabilities/documents/pdf.py)
- [reader.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/capabilities/documents/reader.py)
- [summarize.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/capabilities/documents/summarize.py)
- [translate.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/capabilities/documents/translate.py)
- [exceptions.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/capabilities/exceptions.py)
- [indexing.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/capabilities/files/indexing.py)
- [interfaces.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/capabilities/files/interfaces.py)
- [manager.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/capabilities/files/manager.py)
- [models.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/capabilities/files/models.py)
- [operations.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/capabilities/files/operations.py)
- [organization.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/capabilities/files/organization.py)
- [search.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/capabilities/files/search.py)
- [manager.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/capabilities/manager.py)
- [registry.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/capabilities/registry.py)
- [__init__.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/capabilities/system/__init__.py)
- [battery.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/capabilities/system/battery.py)
- [cpu.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/capabilities/system/cpu.py)
- [interfaces.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/capabilities/system/interfaces.py)
- [manager.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/capabilities/system/manager.py)
- [memory.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/capabilities/system/memory.py)
- [models.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/capabilities/system/models.py)
- [network.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/capabilities/system/network.py)
- [processes.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/capabilities/system/processes.py)
- [storage.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/capabilities/system/storage.py)
- [__init__.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/config/__init__.py)
- [__init__.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/core/__init__.py)
- [context.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/core/context.py)
- [session.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/core/session.py)
- [state.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/core/state.py)
- [__init__.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/events/__init__.py)
- [event.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/events/event.py)
- [event_bus.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/events/event_bus.py)
- [event_types.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/events/event_types.py)
- [publisher.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/events/publisher.py)
- [subscriber.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/events/subscriber.py)
- [__init__.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/file_engine/__init__.py)
- [path_resolver.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/file_engine/path_resolver.py)
- [permissions.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/file_engine/permissions.py)
- [__init__.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/memory/__init__.py)
- [activity_memory.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/memory/activity_memory.py)
- [cache.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/memory/cache.py)
- [conversation_memory.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/memory/conversation_memory.py)
- [file_memory.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/memory/file_memory.py)
- [long_term_memory.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/memory/long_term_memory.py)
- [manager.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/memory/manager.py)
- [preference_memory.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/memory/preference_memory.py)
- [project_memory.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/memory/project_memory.py)
- [session_memory.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/memory/session_memory.py)
- [storage.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/memory/storage.py)
- [workflow_memory.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/memory/workflow_memory.py)
- [__init__.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/os/adapters/__init__.py)
- [__init__.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/os/adapters/linux/__init__.py)
- [adapter.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/os/adapters/linux/adapter.py)
- [desktop.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/os/adapters/linux/desktop.py)
- [files.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/os/adapters/linux/files.py)
- [notifications.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/os/adapters/linux/notifications.py)
- [processes.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/os/adapters/linux/processes.py)
- [system.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/os/adapters/linux/system.py)
- [__init__.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/os/adapters/macos/__init__.py)
- [adapter.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/os/adapters/macos/adapter.py)
- [desktop.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/os/adapters/macos/desktop.py)
- [files.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/os/adapters/macos/files.py)
- [notifications.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/os/adapters/macos/notifications.py)
- [processes.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/os/adapters/macos/processes.py)
- [system.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/os/adapters/macos/system.py)
- [__init__.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/os/adapters/windows/__init__.py)
- [adapter.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/os/adapters/windows/adapter.py)
- [desktop.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/os/adapters/windows/desktop.py)
- [files.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/os/adapters/windows/files.py)
- [notifications.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/os/adapters/windows/notifications.py)
- [processes.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/os/adapters/windows/processes.py)
- [system.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/os/adapters/windows/system.py)
- [exceptions.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/os/exceptions.py)
- [manager.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/os/manager.py)
- [models.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/os/models.py)
- [__init__.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/os/ports/__init__.py)
- [run_parser_smoke.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/scripts/run_parser_smoke.py)
- [__init__.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/services/__init__.py)
- [__init__.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/storage/__init__.py)
- [__init__.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/storage/index/__init__.py)
- [__init__.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/storage/sqlite/__init__.py)
- [__init__.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/storage/vector/__init__.py)
- [__init__.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/tests/__init__.py)
- [test_ai.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/tests/test_ai.py)
- [test_command_parser.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/tests/test_command_parser.py)
- [test_confirmation.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/tests/test_confirmation.py)
- [test_file_ops.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/tests/test_file_ops.py)
- [test_folder_ops.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/tests/test_folder_ops.py)
- [test_integration.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/tests/test_integration.py)
- [test_listener_routes.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/tests/test_listener_routes.py)
- [test_organizer.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/tests/test_organizer.py)
- [test_organizer_ops.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/tests/test_organizer_ops.py)
- [test_source_resolution.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/tests/test_source_resolution.py)
- [test_state_manager.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/tests/test_state_manager.py)
- [test_transfer.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/tests/test_transfer.py)
- [test_voice.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/tests/test_voice.py)
- [test_wake_word.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/tests/test_wake_word.py)
- [__init__.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/utils/__init__.py)
- [validators.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/utils/validators.py)
- [__init__.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/voice/__init__.py)
- [__init__.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/voice/providers/__init__.py)

### Frontend Inactive Files:
- [CommandOutput.jsx](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/frontend/src/components/CommandOutput.jsx)
- [FileExplorer.jsx](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/frontend/src/components/FileExplorer.jsx)
- [useVoice.js](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/frontend/src/hooks/useVoice.js)
- [Home.jsx](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/frontend/src/pages/Home.jsx)
- [helper.js](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/frontend/src/utils/helper.js)

---

## 9. Potential Risks of Refactoring & Mitigation Strategies

### 9.1 Test Patching Breakages
* **Risk**: The circular import between `continuous_listener.py` and `listener.py` exists because the test suite targets mock-patched references in `continuous_listener.py`. Breaking this cycle by moving imports out of methods will break active voice unit tests.
* **Mitigation**: Before refactoring the listener import, verify that the pytest suite is updated to mock the raw speech-to-text (`voice.speech_to_text.listen`) and wake-word functions directly at their source.

### 9.2 State Manager Import Collision
* **Risk**: Renaming `app/state_manager.py`'s `StateManager` to `ConfirmationManager` will break files that currently import it (such as `app/__init__.py` and `voice/voice_session.py`).
* **Mitigation**: Perform a global string search for `state_manager` and `StateManager` imports prior to making changes and update imports in a single commit.

### 9.3 Dormant Stubs Activation
* **Risk**: Activating stubs under `capabilities/` or `ai/` by importing them into `core/` before they are fully implemented will lead to empty logic execution (`pass` statements) and test failures.
* **Mitigation**: Perform capability migrations incrementally (file-by-file). Run `pytest` after each module is migrated to ensure functional parity between legacy engines and capabilities.
