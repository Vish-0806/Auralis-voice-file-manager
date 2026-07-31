# Reusability Report

This document evaluates the reusability of every existing file in Auralis, classifying them by action (Move, Split, Rewrite, Delete, or Archive) to guide the migration.

---

## Reusability Classifications

### 1. Reuse Directly (Move)
These modules are functional and stable; they only need to be relocated to their new paths:

* **Voice Engine Modules:**
  * `backend/voice_engine/speech_to_text.py` ➔ Move to `backend/voice/speech_to_text.py`
  * `backend/voice_engine/text_to_speech.py` ➔ Move to `backend/voice/text_to_speech.py`
  * `backend/voice_engine/continuous_listener.py` ➔ Move to `backend/voice/continuous_listener.py`
  * `backend/voice_engine/wake_word.py` ➔ Move to `backend/voice/wake_word.py`
  * *Reason:* These modules contain stable Pyaudio and SpeechRecognition drivers.
* **Shared Utilities:**
  * `backend/utils/logger.py` ➔ Keep in `backend/utils/logger.py`
  * `backend/utils/helpers.py` ➔ Keep in `backend/utils/helpers.py`
  * *Reason:* Central logging and helper configurations are already decoupled.
* **Task Automation Managers:**
  * `backend/automation/workflow_manager.py` ➔ Move to `backend/capabilities/automation/workflows.py`
  * *Reason:* Encapsulates sequence chains and is ready to be loaded as a capability.

---

### 2. Split
These files combine multiple responsibilities (e.g. system calls and business rules) and must be split:

* **File Operations (`backend/file_engine/file_operations.py`):**
  * *Destination:* Split into `backend/capabilities/files/operations.py` (capability schemas) and `backend/os/ports/file_port.py` (system calls interface).
  * *Reason:* Standardizes filesystem commands while decoupling direct disk calls.
* **Command Normalizer (`backend/ai_engine/command_normalizer.py`):**
  * *Destination:* Split into `backend/ai/context_builder.py` (context assembly) and `backend/ai/prompt_builder.py` (string syntax normalization).
  * *Reason:* Separates context assembly from prompt templating.

---

### 3. Rewrite
These files implement outdated command-driven paradigms and must be rewritten:

* **Command Parser & Classifiers (`backend/ai_engine/command_parser.py`, `intent_classifier.py`, `entity_extractor.py`):**
  * *Destination:* Rewrite as JSON tool action definitions inside capability packages.
  * *Reason:* Replaces static regex-based intent matching with dynamic, LLM-driven tool calling.
* **Application Controller (`backend/app/controller.py`):**
  * *Destination:* Rewrite as `backend/core/assistant.py` (orchestration flow).
  * *Reason:* Replaces the legacy command loop with an agentic reasoning loop.
* **API Endpoints (`backend/api/routes.py`, `voice_routes.py`):**
  * *Destination:* Rewrite as `backend/services/routes_chat.py`.
  * *Reason:* Decouples API routes from business execution; endpoints will now interact only with the `AuralisAssistant` orchestrator.

---

### 4. Archive (Retain for reference)
* **Legacy importing guidelines:**
  * `backend/BACKEND_MODULES.md`
  * `backend/IMPORT_TROUBLESHOOTING.md`
  * `backend/MODULE_STRUCTURE.py`
  * *Reason:* These files remain in the repository for reference but are not imported by the new architecture.
