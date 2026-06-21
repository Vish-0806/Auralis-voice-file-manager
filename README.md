# 🎙️ Auralis — Voice File Manager

[![CI](https://github.com/your-username/auralis/actions/workflows/ci.yml/badge.svg)](https://github.com/your-username/auralis/actions) [![Coverage](https://img.shields.io/codecov/c/github/your-username/auralis.svg)](https://codecov.io/gh/your-username/auralis) [![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE) [![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/) [![Node.js](https://img.shields.io/badge/node-16%2B-green.svg)](https://nodejs.org/)

Auralis is a voice-enabled file manager that provides hands-free file and folder operations using speech recognition and NLP.

---

## 🚀 Highlights

- Voice commands for creating, renaming, deleting, moving, copying, and opening files
- NLP-based command parsing and intent handling
- Rule-based search parsing for commands like `find`, `search for`, `locate`, and `where is`
- Location-aware folder creation for commands like `create a folder in documents called notes`
- Modular backend API and a **Vite + React frontend with a dark glassmorphic UI**
- Cross-platform audio setup helpers for Windows

---

## What Has Been Done So Far

### 🎨 Frontend & UI Architecture
- **Vite + React Setup:** Configured standard package scripts, build targets, and environment variables.
- **Glassmorphic Styling System:** Implemented a pure Vanilla CSS theme (`global.css`) utilizing modern font typography (Plus Jakarta Sans, Space Grotesk), translucent glass panels with blur effects, neon status tags, and animations (glowing ripples, floating icons, rotating spinners).
- **Core UI Components:**
  - `VoiceButton`: Circular microphone button displaying animated SVG soundwave bars when recording.
  - `StatusIndicator`: Real-time state indicator reflecting connecting phases alongside background listener toggles.
  - `SearchResults`: File card grids displaying extension-mapped icons (PDFs, images, code, archives) with quick click-to-open and click-to-delete actions.
  - `CommandCard`: A structured activity log mapping operations with color-coded intent pills.
- **useVoiceCommands State Hook:** A state management machine syncing continuous background listener statuses via periodic polling (every 3 seconds), handling user response prompts, and tracking activity histories.
- **Reverse Proxy Integration:** Setup local Vite proxy configurations mapping API targets to backend port `8000` to completely eliminate local development CORS issues.

### ⚙️ Backend & Command Processing
- Refactored the command parsing flow into a modular NLP pipeline in `backend/ai_engine/`
- Added a reusable command normalization layer for cleaning filler words and standardizing folder names
- Split intent detection and entity extraction into separate, rule-based components
- Extended parser support for search-style commands such as `find`, `search for`, `locate`, and `where is`
- Added location extraction for create-folder commands so the parser can return both `target` and `location`
- Kept the existing `parse_command()` API compatible for the backend routes and file execution flow
- Implemented a recursive file search engine scanning `Desktop`, `Documents`, and `Downloads`
- Optimized search traversal with early exit limits (capping at the first 20 matches)
- Handled folder permission errors (`PermissionError`, `OSError`) gracefully during recursive scanning
- Exposed search capability via a `GET /files/search` API endpoint and integrated it into the `/command` pipeline
- Modularized voice feedback by adding a unified `format_speak_message` utility to yield context-aware TTS voice notifications (counts, locations, fallbacks)
- Implemented interactive confirmation workflows for destructive operations (`delete`, `move`, and `organize`) to protect against accidental operations
- Enhanced `delete` with dynamic path resolution (using `resolve_source`) so files can be deleted by name matching alone after user confirmation
- Created a centralized `StateManager` (`backend/app/state_manager.py`) to track pending actions (`pending_action`, `pending_target`, `pending_destination`, `timestamp`) and handle multi-step automated workflows
- Added comprehensive pytest coverage for parser, search, state manager, and operation confirmation/cancellation flows

---

## 🛠️ Tech Stack

- **Backend:** Python, FastAPI, Uvicorn
- **Frontend:** Vite, React, Vanilla CSS, Lucide Icons
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
The frontend dev server starts at `http://localhost:5173`. By default, Vite proxies requests from the frontend app to the backend FastAPI server running at `http://localhost:8000`.

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

Examples supported by the parser (can be typed into the frontend console or spoken via mic):

```bash
# Find / Search
find report.pdf

# Create Folder with Location
create a folder called notes in documents

# Move File
move report.pdf to documents

# Copy File
copy resume.pdf to desktop
```

---

## Project Structure (selected)

- `backend/` — FastAPI backend, AI engine, file engine, and API routes
- `frontend/` — Vite + React UI
  - `src/components/` — UI components (`VoiceButton`, `StatusIndicator`, `CommandCard`, `SearchResults`)
  - `src/hooks/` — Custom hook `useVoiceCommands` for state management & status polling
  - `src/services/` — Frontend fetch-based HTTP service handler (`api.js`)
  - `src/pages/` — Main dashboard layout (`Dashboard.jsx`)
  - `src/styles/` — Global glassmorphic stylesheet (`global.css`)
- `scripts/` — Helper scripts for audio and setup
- `docs/` — Architecture and deployment notes

---

## Development & Testing

- Run backend tests: `pytest backend/tests`
- Run frontend build verification: `npm run build` inside `frontend/`
