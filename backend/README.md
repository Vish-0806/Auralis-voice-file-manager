# Auralis Backend API Service

This is the FastAPI backend application for **Auralis**, coordinating local-first natural language intent parsing, operating system adaptations, document intelligence processing, and modular voice integration pipelines.

---

## 1. Directory Layout

The backend codebase is divided into independent packages matching specific boundaries:

```
backend/
├── api/               # API Router endpoints (routes.py, voice_routes.py, etc.)
├── core/              # Assistant boundary, intent schemas, planner, and dispatcher
├── capabilities/      # Specific OS operations (files, desktop capability, etc.)
├── automation/        # Workflow Engine sequential orchestration
├── events/            # Centralized event schema interfaces
├── voice/             # Modular Voice Engine subsystems
│   ├── speech/        # PyAudio device interactions and Speech-to-Text transcription
│   ├── conversation/  # Voice session state machine and inactivity tracking
│   ├── tts/           # Edge-TTS synthesis and asynchronous play queues
│   ├── ux/            # Chimes/sound triggers and notification observers
│   ├── context/       # Pronoun/ordinal resolution and temporary session memory
│   └── integration/   # Pipeline loops, EventRouter, and Error Recovery controller
├── tests/             # Pytest suite verifying core, capabilities, and voice
├── main.py            # API service initialization endpoint
└── requirements.txt   # Python dependency packages
```

---

## 2. Key Subsystems

### 2.1 Core Assistant & Planner
* **AuralisAssistant**: Acts as the system boundary. It receives an `AssistantRequest`, queries the `Planner` for an sequence of actions (`ExecutionPlan`), dispatches it, and returns the response.
* **Planner**: Rules-based parser checking for parameters, relative paths, and folders.
* **ActionDispatcher**: Dynamically routes plans to capabilities matching their loaded namespaces.

### 2.2 Voice Subsystem (Phase 3)
* **Speech Recognition**: Capture mono PCM streams normalization, silences padding, and translates using offline `faster-whisper` or online Google STT API fallback.
* **Conversation Manager**: Handles session thread starts, sign-off hooks, and inactivity timer callbacks.
* **Text-to-Speech**: Runs online Microsoft Edge-TTS or offline `pyttsx3` locally with non-blocking Windows MCI play workers.
* **Voice UX**: Standardizes states (`SLEEPING`, `LISTENING`, `PROCESSING`, `SPEAKING`, `WAITING`, `ERROR`) and triggers platform chimes.
* **Context Awareness**: Resolves fuzzy pronoun/ordinal references (like "delete it" or "the second one") using `ReferenceResolver`.
* **Voice Integration Pipeline**: Continuously listens for wake phrases, loops follow-up speech-to-intent pipelines, and handles system failures (mic disconnection, recognition timeouts, planner/capability exceptions, speech interruption).

### 2.3 Desktop Automation & Workflow Subsystem (v0.4.0)
* **Desktop Capability**: Single capability wrapping Application Management (launch/close), Window Management (minimize/maximize/focus/close), System Controls (volume/brightness/power/network), Clipboard automation (read/write/clear), and Screenshot/Screen recording services.
* **Workflow Engine**: Orchestrates sequential steps of pre-registered workflows (Start Coding, Study Mode, Meeting Mode, Movie Mode, Clean Workspace), performs dependency validations, and logs execution histories for rollbacks.
* **Input Automation**: Low-level mouse (movement, click, double click, scroll, drag) and keyboard (typing, hotkeys, custom macros) automation wrappers.

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
Currently, the backend contains **326 unit and integration tests** verifying core flows, file operations, state transitions, speech, and integration pipeline steps.
