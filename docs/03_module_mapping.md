# Module Mapping

This document maps all existing legacy packages and files in Auralis to their respective destination directories in the new modular architecture.

---

## Architecture Package Mapping

| Legacy Sub-system / File | New Architecture Module | Target Path in Repository |
| :--- | :--- | :--- |
| **Core Assistant State** | Core | `backend/core/` |
| `backend/app/state_manager.py` | Core | `backend/core/state.py` |
| `backend/app/controller.py` | Core (Orchestrator) | `backend/core/assistant.py` |
| **AI Parsing & Prompt Models** | AI | `backend/ai/` |
| `backend/ai_engine/command_normalizer.py` | AI (Context Builder) | `backend/ai/context_builder.py` |
| `backend/ai_engine/command_parser.py` | AI (Prompt Builder) | `backend/ai/prompt_builder.py` |
| `backend/ai_engine/entity_extractor.py` | AI (Prompt Builder) | `backend/ai/prompt_builder.py` |
| `backend/ai_engine/intent_classifier.py` | AI (Prompt Builder) | `backend/ai/prompt_builder.py` |
| `backend/ai_engine/response_generator.py` | AI (Response Generator)| `backend/ai/response_generator.py` |
| **Voice Processing** | Voice | `backend/voice/` |
| `backend/voice_engine/speech_to_text.py` | Voice (STT) | `backend/voice/speech_to_text.py` |
| `backend/voice_engine/text_to_speech.py` | Voice (TTS) | `backend/voice/text_to_speech.py` |
| `backend/voice_engine/continuous_listener.py`| Voice (Listener) | `backend/voice/continuous_listener.py`|
| `backend/voice_engine/wake_word.py` | Voice (Wake Word) | `backend/voice/wake_word.py` |
| **File Systems Operations** | Capabilities (Files) | `backend/capabilities/files/` |
| `backend/file_engine/file_operations.py` | Capabilities (Files) | `backend/capabilities/files/operations.py`|
| `backend/file_engine/organizer.py` | Capabilities (Files) | `backend/capabilities/files/organization.py`|
| `backend/file_engine/search_engine.py` | Capabilities (Files) | `backend/capabilities/files/search.py` |
| `backend/file_engine/source_resolver.py` | Capabilities (Files) | `backend/capabilities/files/operations.py`|
| `backend/file_engine/transfer.py` | Capabilities (Files) | `backend/capabilities/files/operations.py`|
| **Automation Routines** | Capabilities (Automation)| `backend/capabilities/automation/` |
| `backend/automation/workflow_manager.py` | Capabilities (Automation)| `backend/capabilities/automation/workflows.py`|
| **Terminal / Commands** | Capabilities (Developer) | `backend/capabilities/developer/` |
| `backend/automation/task_runner.py` | Capabilities (Developer) | `backend/capabilities/developer/terminal.py` |
| **Path / Permissions Adapters**| OS Abstraction Layer | `backend/os/adapters/windows/` |
| `backend/file_engine/path_resolver.py` | OS Adapters (Windows) | `backend/os/adapters/windows/files.py` |
| `backend/file_engine/permissions.py` | OS Adapters (Windows) | `backend/os/adapters/windows/files.py` |
| **API Routers & Web Servers** | Services | `backend/services/` |
| `backend/main.py` | Services (Main entry) | `backend/main.py` |
| `backend/api/routes.py` | Services (REST Chat) | `backend/services/routes_chat.py` |
| `backend/api/voice_routes.py` | Services (REST Chat) | `backend/services/routes_chat.py` |
| `backend/api/listener_routes.py` | Services (REST System) | `backend/services/routes_system.py` |
| `backend/api/file_routes.py` | Services (REST Chat) | `backend/services/routes_chat.py` |
| **Config & Constants** | Config / Core | `backend/config/` / `backend/core/` |
| `backend/config.yaml` | Config | `config/app.yaml` |
| `backend/utils/constants.py` | Core (Exceptions/Defs) | `backend/core/exceptions.py` |
| `backend/utils/validators.py` | Config (Validators) | `backend/config/` |
| `backend/utils/logger.py` | Utilities | `backend/utils/logger.py` |
| `backend/utils/helpers.py` | Utilities | `backend/utils/helpers.py` |
