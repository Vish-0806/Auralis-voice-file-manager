# Migration Plan

This document details the migration path for every existing file in the Auralis repository from the current command-driven structure to the redesigned modular, agentic AI architecture.

---

## File-by-File Migration Path

### 1. `backend/main.py`
* **Future Location:** `backend/main.py` (remains main API entry)
* **Reason:** Main startup configuration wrapper. It must be refactored to initialize the `AuralisAssistant` orchestrator and include the new API routers.
* **Migration Priority:** High (Phase 2)
* **Risk Level:** Medium
* **Dependencies:** `backend/core/assistant.py`, `backend/services/`

### 2. `backend/config.yaml`
* **Future Location:** `config/app.yaml`
* **Reason:** Decoupled from the backend package directory. Configuration must reside in the root directory context.
* **Migration Priority:** High (Phase 1)
* **Risk Level:** Low
* **Dependencies:** `backend/config/`

### 3. `backend/ai_engine/command_normalizer.py`
* **Future Location:** `backend/ai/context_builder.py` (integrated)
* **Reason:** Prompt context cleaning should be handled by the AI Context Builder.
* **Migration Priority:** Medium (Phase 3)
* **Risk Level:** Low
* **Dependencies:** None

### 4. `backend/ai_engine/command_parser.py`
* **Future Location:** `backend/ai/prompt_builder.py` (deconstructed)
* **Reason:** Legacy parsing matches text commands using static rules. The new design delegates extraction to the AI Agent reasoning loop.
* **Migration Priority:** Low (Phase 3)
* **Risk Level:** High (core NLP logic change)
* **Dependencies:** `backend/ai/interfaces.py`

### 5. `backend/ai_engine/intent_classifier.py` & `entity_extractor.py`
* **Future Location:** `backend/ai/prompt_builder.py` (re-engineered as tool schemas)
* **Reason:** Instead of parsing queries with rules, intents and entities are defined as tool action parameters and resolved by the LLM.
* **Migration Priority:** Low (Phase 3)
* **Risk Level:** High
* **Dependencies:** `backend/ai/models.py`

### 6. `backend/ai_engine/response_generator.py`
* **Future Location:** `backend/ai/response_generator.py` (adapted)
* **Reason:** Directly maps to formatting conversational summaries.
* **Migration Priority:** Medium (Phase 3)
* **Risk Level:** Low
* **Dependencies:** None

### 7. `backend/api/routes.py` & `voice_routes.py`
* **Future Location:** `backend/services/routes_chat.py` (rewritten)
* **Reason:** Business logic must be separated from routing definitions. The endpoints will call the `AuralisAssistant` instead of running command execution blocks directly.
* **Migration Priority:** High (Phase 2)
* **Risk Level:** Medium
* **Dependencies:** `backend/core/assistant.py`

### 8. `backend/api/listener_routes.py`
* **Future Location:** `backend/services/routes_system.py`
* **Reason:** Re-maps listener statuses and configurations to the system endpoint manager.
* **Migration Priority:** Medium (Phase 2)
* **Risk Level:** Low
* **Dependencies:** `backend/voice/`

### 9. `backend/api/file_routes.py`
* **Future Location:** `backend/services/routes_chat.py` (integrated)
* **Reason:** Replaced by Capability tool requests or directory explorer queries.
* **Migration Priority:** Medium (Phase 2)
* **Risk Level:** Low
* **Dependencies:** `backend/capabilities/files/`

### 10. `backend/app/controller.py`
* **Future Location:** `backend/core/assistant.py` (deconstructed and rewritten)
* **Reason:** The old controller ran static command pipelines. It is replaced by the `AuralisAssistant` orchestrator.
* **Migration Priority:** High (Phase 2)
* **Risk Level:** High
* **Dependencies:** `backend/core/`

### 11. `backend/app/state_manager.py`
* **Future Location:** `backend/core/state.py` (extended)
* **Reason:** Ported to the core thread-safe state container.
* **Migration Priority:** High (Phase 1)
* **Risk Level:** Low
* **Dependencies:** None

### 12. `backend/automation/task_runner.py`
* **Future Location:** `backend/capabilities/developer/terminal.py`
* **Reason:** Command line actions are now managed by the Developer Capability subsystem.
* **Migration Priority:** Low (Phase 5)
* **Risk Level:** Medium
* **Dependencies:** `backend/os/ports/process_port.py`

### 13. `backend/automation/workflow_manager.py`
* **Future Location:** `backend/capabilities/automation/workflows.py`
* **Reason:** Part of the new Automation capability package.
* **Migration Priority:** Low (Phase 5)
* **Risk Level:** Medium
* **Dependencies:** `backend/capabilities/automation/`

### 14. `backend/file_engine/file_operations.py`
* **Future Location:** `backend/capabilities/files/operations.py`
* **Reason:** Part of the Files capability package. The actual system operations will be routed through the OSAL FilePort adapter.
* **Migration Priority:** High (Phase 1)
* **Risk Level:** Low
* **Dependencies:** `backend/os/ports/file_port.py`

### 15. `backend/file_engine/organizer.py`
* **Future Location:** `backend/capabilities/files/organization.py`
* **Reason:** Maps to the Files capability package.
* **Migration Priority:** Low (Phase 5)
* **Risk Level:** Low
* **Dependencies:** `backend/os/ports/file_port.py`

### 16. `backend/file_engine/path_resolver.py`
* **Future Location:** `backend/os/adapters/windows/files.py` (integrated)
* **Reason:** Path resolution is platform-specific (Windows vs macOS paths) and must reside in the OS adapters.
* **Migration Priority:** High (Phase 1)
* **Risk Level:** Medium
* **Dependencies:** `backend/os/ports/file_port.py`

### 17. `backend/file_engine/permissions.py`
* **Future Location:** `backend/os/adapters/windows/files.py` (integrated)
* **Reason:** Directory permission checks are platform-specific.
* **Migration Priority:** High (Phase 1)
* **Risk Level:** Low
* **Dependencies:** `backend/os/ports/file_port.py`

### 18. `backend/file_engine/search_engine.py`
* **Future Location:** `backend/capabilities/files/search.py`
* **Reason:** Maps to Files capability searches.
* **Migration Priority:** Medium (Phase 5)
* **Risk Level:** Low
* **Dependencies:** `backend/os/ports/file_port.py`

### 19. `backend/file_engine/source_resolver.py` & `transfer.py`
* **Future Location:** `backend/capabilities/files/operations.py` (integrated)
* **Reason:** Deconstructed and integrated into Files operations for path verification.
* **Migration Priority:** High (Phase 1)
* **Risk Level:** Low
* **Dependencies:** `backend/os/ports/file_port.py`

### 20. `backend/voice_engine/speech_to_text.py` & `text_to_speech.py`
* **Future Location:** `backend/voice/speech_to_text.py` & `text_to_speech.py`
* **Reason:** Direct migration to the new Voice sub-system.
* **Migration Priority:** Medium (Phase 4)
* **Risk Level:** Low
* **Dependencies:** None

### 21. `backend/voice_engine/continuous_listener.py` & `wake_word.py`
* **Future Location:** `backend/voice/continuous_listener.py` & `wake_word.py`
* **Reason:** Direct migration to the new Voice sub-system.
* **Migration Priority:** Medium (Phase 4)
* **Risk Level:** Low
* **Dependencies:** None

### 22. `backend/utils/`
* **Future Location:** `backend/config/` & `backend/utils/` (legacy imports preserved)
* **Reason:** Helpers remain in utilities, while validation and constant values map to `backend/config/` and `backend/core/exceptions.py`.
* **Migration Priority:** Medium (Phase 1)
* **Risk Level:** Low
* **Dependencies:** None
