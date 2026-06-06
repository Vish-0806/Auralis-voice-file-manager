# 🎙️ Auralis — Voice File Manager

[![CI](https://github.com/your-username/auralis/actions/workflows/ci.yml/badge.svg)](https://github.com/your-username/auralis/actions) [![Coverage](https://img.shields.io/codecov/c/github/your-username/auralis.svg)](https://codecov.io/gh/your-username/auralis) [![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE) [![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/) [![Node.js](https://img.shields.io/badge/node-16%2B-green.svg)](https://nodejs.org/)

Auralis is a voice-enabled file manager that provides hands-free file and folder operations using speech recognition and NLP.

---

## 🚀 Highlights

- Voice commands for creating, renaming, deleting, moving, and opening files
- NLP-based command parsing and intent handling
- Rule-based search parsing for commands like `find`, `search for`, `locate`, and `where is`
- Location-aware folder creation for commands like `create a folder in documents called notes`
- Modular backend API and a Vite + React frontend
- Cross-platform audio setup helpers for Windows

---

## What Has Been Done So Far

- Refactored the command parsing flow into a modular NLP pipeline in `backend/ai_engine/`
- Added a reusable command normalization layer for cleaning filler words and standardizing folder names
- Split intent detection and entity extraction into separate, rule-based components
- Extended parser support for search-style commands such as `find`, `search for`, `locate`, and `where is`
- Added location extraction for create-folder commands so the parser can return both `target` and `location`
- Kept the existing `parse_command()` API compatible for the backend routes and file execution flow
- Added comprehensive pytest coverage for intent detection, target extraction, and normalization behavior

---

## 🛠️ Tech Stack

- **Backend:** Python, FastAPI
- **Frontend:** Vite, React
- **Audio / Voice:** speech-to-text and TTS modules (see `backend/` and `frontend/`)

---

## Quick Start

Prerequisites: Python 3.8+, Node.js (16+), and a microphone.

1) Start the backend

```bash
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

2) Start the frontend

```bash
cd frontend
npm install
npm run dev
```

3) Audio setup (Windows)

```powershell
cd scripts
.\setup_audio_windows.ps1
```

The backend exposes a FastAPI service at `http://localhost:8000` by default.

---

## Usage

Quick examples for interacting with the running backend:

- Check backend health:

```bash
curl http://localhost:8000/
```

- Send a text command to be parsed and executed:

```bash
curl -s -X POST http://localhost:8000/command \
	-H "Content-Type: application/json" \
	-d '{"command":"create folder Projects"}'
```

Examples supported by the parser:

```bash
curl -s -X POST http://localhost:8000/command \
	-H "Content-Type: application/json" \
	-d '{"command":"find report.pdf"}'

curl -s -X POST http://localhost:8000/command \
	-H "Content-Type: application/json" \
	-d '{"command":"create a folder called notes in documents"}'
```

The parser returns structured output such as:

```json
{
	"action": "create_folder",
	"target": "notes",
	"location": "documents"
}
```

- Trigger voice listening (backend will capture microphone input):

```bash
curl http://localhost:8000/voice/listen
```

Notes:
- Replace `your-username/auralis` in the badge URLs with your repository owner/name to enable real CI/coverage badges.
- The `/voice/listen` endpoint requires microphone access on the machine running the backend and proper audio setup.
- Search commands are parsed by the backend, but actual file-search execution is not implemented yet.

## Project Structure (selected)

- `backend/` — FastAPI backend, AI engine, file engine, and API routes
- `frontend/` — Vite + React UI
- `scripts/` — helper scripts for audio and setup
- `docs/` — architecture and deployment notes

---

## Development & Testing

- Run backend tests: `pytest backend/tests` (if tests present)
- Linting/format: use your preferred tools (e.g., `black`, `flake8`)

---

## Contributing

Contributions welcome. Open an issue or submit a pull request with a clear description of changes and tests where appropriate.

---

## License

See the `LICENSE` file in the repository root.

---

If you'd like a different tone, more details, or badges (CI, coverage), tell me what to add and I will update the README accordingly.
