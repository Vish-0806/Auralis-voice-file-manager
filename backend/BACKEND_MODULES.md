# Auralis Backend - Module Structure & Import Guide

## Overview

The Auralis backend is organized into modular Python packages with proper namespace isolation. Each package is initialized with `__init__.py` files to enable clean imports.

## Directory Structure

```
backend/
├── __pycache__/
├── ai_engine/              # Natural Language Processing
│   ├── __init__.py
│   ├── command_parser.py
│   ├── entity_extractor.py
│   ├── intent_classifier.py
│   └── response_generator.py
├── api/                    # FastAPI Routes
│   ├── __init__.py
│   ├── routes.py           # POST /command endpoint
│   ├── voice_routes.py     # GET /voice/listen endpoint
│   └── file_routes.py
├── app/                    # Application State
│   ├── __init__.py
│   ├── controller.py
│   └── state_manager.py
├── automation/             # Task Automation
│   ├── __init__.py
│   ├── task_runner.py
│   └── workflow_manager.py
├── file_engine/            # File System Operations
│   ├── __init__.py
│   ├── file_operations.py
│   ├── path_resolver.py
│   ├── permissions.py
│   └── search_engine.py
├── logs/                   # Application Logs
├── tests/                  # Unit & Integration Tests
│   ├── __init__.py
│   ├── test_ai.py
│   ├── test_file_ops.py
│   └── test_voice.py
├── utils/                  # Shared Utilities
│   ├── __init__.py
│   ├── constants.py
│   ├── helpers.py
│   ├── logger.py
│   └── validators.py
├── voice_engine/           # Voice Recognition
│   ├── __init__.py
│   ├── speech_to_text.py   # Microphone input → text
│   ├── text_to_speech.py
│   └── wake_word.py
├── config.yaml
├── main.py                 # FastAPI app entry point
├── requirements.txt
└── MODULE_STRUCTURE.py     # This guide
```

## Package Descriptions

### 🎤 `voice_engine/`
**Speech recognition and synthesis**
- `speech_to_text.py`: Captures microphone input and converts to text
- `text_to_speech.py`: Converts text to spoken audio
- `wake_word.py`: Wake word detection (future feature)

**Key Exports:**
```python
from voice_engine.speech_to_text import listen
text = listen()  # Blocks until microphone input is processed
```

### 🧠 `ai_engine/`
**Natural language processing and command parsing**
- `command_parser.py`: Extracts action and target from text
- `intent_classifier.py`: Classifies command intent
- `entity_extractor.py`: Extracts named entities
- `response_generator.py`: Generates response text

**Key Exports:**
```python
from ai_engine.command_parser import parse_command
action = parse_command("open downloads")
# Returns: {"action": "open", "target": "downloads"}
```

### 📁 `file_engine/`
**File system operations**
- `file_operations.py`: Execute create/open/delete actions
- `path_resolver.py`: Resolve paths (home, desktop, etc.)
- `permissions.py`: Check file permissions
- `search_engine.py`: Search files and folders

**Key Exports:**
```python
from file_engine.file_operations import execute_action
result = execute_action({"action": "open", "target": "downloads"})
```

### 🌐 `api/`
**FastAPI route handlers**
- `routes.py`: Text command endpoint (`POST /command`)
- `voice_routes.py`: Voice command endpoint (`GET /voice/listen`)
- `file_routes.py`: File operations endpoints (optional)

**Key Exports:**
```python
from api.routes import router
from api.voice_routes import router as voice_router
```

### 🛠️ `utils/`
**Shared utilities across the project**
- `logger.py`: Centralized logging configuration
- `helpers.py`: Utility functions
- `validators.py`: Input validation
- `constants.py`: Application constants

**Key Exports:**
```python
from utils.logger import get_logger
logger = get_logger(__name__)
logger.info("Message")
```

### 📋 `tests/`
**Unit and integration tests**
- `test_ai.py`: AI engine tests
- `test_file_ops.py`: File operation tests
- `test_voice.py`: Voice recognition tests

### ⚙️ `app/`
**Application state and control**
- `controller.py`: Main application controller
- `state_manager.py`: Manage application state

### 🔄 `automation/`
**Task automation and workflows**
- `task_runner.py`: Run automated tasks
- `workflow_manager.py`: Manage multi-step workflows

## Import Patterns

### ✅ Correct Imports (from backend directory)

```python
# Voice
from voice_engine.speech_to_text import listen

# Commands
from ai_engine.command_parser import parse_command

# File Operations
from file_engine.file_operations import execute_action

# Utilities
from utils.logger import get_logger

# API
from api.routes import router
from api.voice_routes import router as voice_router
```

### ❌ Incorrect Imports

```python
# Don't use absolute imports from project root
from backend.api.routes import router  # ✗ Wrong

# Don't use relative imports from different packages
from ..ai_engine import command_parser  # ✗ Avoid

# Don't skip package names
from command_parser import parse_command  # ✗ Wrong
```

## Running the Application

### From Backend Directory

```bash
cd backend
uvicorn main:app --reload
```

**Output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
```

### From Project Root

```bash
cd backend
uvicorn main:app --reload
```

Or use the shell script:
```bash
./scripts/run_dev.sh
```

### Production Mode

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Endpoints

### Text Command
```http
POST /command
Content-Type: application/json

{
  "command": "open downloads"
}
```

**Response:**
```json
{
  "status": "success",
  "command": "open downloads",
  "parsed_action": {
    "action": "open",
    "target": "downloads"
  },
  "result": "Opened downloads"
}
```

### Voice Command
```http
GET /voice/listen
```

**Response:**
```json
{
  "status": "success",
  "command": "open downloads",
  "parsed_action": {
    "action": "open",
    "target": "downloads"
  },
  "result": "Opened downloads"
}
```

### Health Check
```http
GET /
```

**Response:**
```json
{
  "message": "Auralis Backend Running 🚀"
}
```

## Module Dependencies

### Between Modules

```
main.py
  ↓
api/
  ├── routes.py → ai_engine, file_engine
  └── voice_routes.py → voice_engine, ai_engine, file_engine

voice_engine/
  └── speech_to_text.py → utils/logger

ai_engine/
  └── command_parser.py (standalone)

file_engine/
  └── file_operations.py (standalone)

utils/
  └── logger.py (standalone)
```

### No Circular Dependencies
- Each module can be imported independently
- No circular imports between packages
- Clean separation of concerns

## Adding New Modules

### Step 1: Create Package Directory
```bash
mkdir backend/new_package
touch backend/new_package/__init__.py
```

### Step 2: Add Package Documentation
```python
# backend/new_package/__init__.py
"""
Auralis New Package
Description of what this package does.
"""
```

### Step 3: Create Module Files
```python
# backend/new_package/my_module.py
def my_function():
    pass
```

### Step 4: Use Correct Imports
```python
# From other packages
from new_package.my_module import my_function
```

## Troubleshooting

### Import Error: "ModuleNotFoundError: No module named 'api'"

**Solution:** Ensure you're running from the backend directory:
```bash
cd backend
uvicorn main:app --reload
```

### Import Error: "No module named 'utils.logger'"

**Cause:** Missing `__init__.py` file in utils directory

**Solution:** Verify all packages have `__init__.py`:
```bash
find backend -type d -exec touch {}/__init__.py \;
```

### "ImportError: cannot import name 'parse_command'"

**Cause:** Function doesn't exist or typo in import

**Solution:** Verify function exists:
```bash
grep -n "def parse_command" backend/ai_engine/command_parser.py
```

## Testing Imports

Quick test to verify all imports work:

```bash
cd backend
python -c "
from api.routes import router
from api.voice_routes import router as voice_router
from ai_engine.command_parser import parse_command
from file_engine.file_operations import execute_action
from voice_engine.speech_to_text import listen
from utils.logger import get_logger
from main import app
print('✓ All imports successful')
"
```

## Configuration

### Environment Variables
Set in `config.yaml` or as environment variables:
```yaml
LOG_LEVEL: INFO
MAX_FILE_SIZE: 1000000
VOICE_TIMEOUT: 10
```

### Logging
Logs are written to `backend/logs/auralis_YYYYMMDD.log`

Adjust in `utils/logger.py`:
```python
LOG_FILE = os.path.join(LOGS_DIR, f"auralis_{datetime.now().strftime('%Y%m%d')}.log")
```

## Best Practices

1. **Always use package-relative imports** from the backend directory
2. **Keep modules focused** - one responsibility per module
3. **Use logging instead of print** for debugging
4. **Add docstrings** to all functions and classes
5. **Write unit tests** for each module
6. **Avoid circular imports** - restructure if needed
7. **Use __init__.py** to expose public API

## Related Documentation

- [API Reference](../docs/api_reference.md)
- [Architecture Guide](../docs/architecture.md)
- [Audio Setup](../docs/AUDIO_SETUP.md)
- [Deployment Guide](../docs/deployment.md)

## Quick Reference

```python
# Voice Recognition
from voice_engine.speech_to_text import listen
text = listen()

# Parse Commands
from ai_engine.command_parser import parse_command
action_dict = parse_command(text)

# Execute Actions
from file_engine.file_operations import execute_action
result = execute_action(action_dict)

# Logging
from utils.logger import get_logger
logger = get_logger(__name__)
logger.info("Info message")
logger.error("Error message")
```

## Version Info

- Python: 3.8+
- FastAPI: 0.136.1
- Uvicorn: 0.46.0
- SpeechRecognition: 3.16.1
- PyAudio: 0.2.13

---

Last updated: May 10, 2026
