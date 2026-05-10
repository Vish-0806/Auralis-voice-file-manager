"""
Auralis Backend Module Structure

This file documents the Python package structure and module organization.
All packages are properly initialized with __init__.py files for modular imports.
"""

# Package Structure
# ================

BACKEND_ROOT = "backend/"

PACKAGES = {
    "api": {
        "description": "API endpoints and routing",
        "modules": [
            "routes.py - POST /command endpoint",
            "voice_routes.py - GET /voice/listen endpoint",
            "file_routes.py - File API endpoints (optional)",
        ],
        "exports": ["router", "voice_router"],
    },
    "ai_engine": {
        "description": "Natural language processing and command parsing",
        "modules": [
            "command_parser.py - Parse text commands into action + target",
            "intent_classifier.py - Classify command intent",
            "entity_extractor.py - Extract entities from commands",
            "response_generator.py - Generate response text",
        ],
        "exports": ["parse_command"],
    },
    "file_engine": {
        "description": "File system operations",
        "modules": [
            "file_operations.py - Execute open/create/delete actions",
            "path_resolver.py - Resolve target paths",
            "permissions.py - Check file permissions",
            "search_engine.py - Search files and folders",
        ],
        "exports": ["execute_action"],
    },
    "voice_engine": {
        "description": "Voice recognition and synthesis",
        "modules": [
            "speech_to_text.py - Recognize speech from microphone",
            "text_to_speech.py - Convert text to speech (pyttsx3)",
            "wake_word.py - Wake word detection (future feature)",
        ],
        "exports": ["listen"],
    },
    "utils": {
        "description": "Shared utilities",
        "modules": [
            "logger.py - Centralized logging configuration",
            "helpers.py - Helper functions",
            "validators.py - Input validation",
            "constants.py - Application constants",
        ],
        "exports": ["get_logger"],
    },
    "app": {
        "description": "Application state and control",
        "modules": [
            "controller.py - Application controller",
            "state_manager.py - Manage app state",
        ],
        "exports": [],
    },
    "automation": {
        "description": "Task automation and workflows",
        "modules": [
            "task_runner.py - Run automated tasks",
            "workflow_manager.py - Manage workflows",
        ],
        "exports": [],
    },
    "tests": {
        "description": "Unit and integration tests",
        "modules": [
            "test_ai.py - AI engine tests",
            "test_file_ops.py - File operations tests",
            "test_voice.py - Voice recognition tests",
        ],
        "exports": [],
    },
}

# Import Paths (from backend directory)
# ====================================

IMPORT_EXAMPLES = {
    "Parse a command": "from ai_engine.command_parser import parse_command",
    "Execute file action": "from file_engine.file_operations import execute_action",
    "Listen to voice": "from voice_engine.speech_to_text import listen",
    "Get logger": "from utils.logger import get_logger",
    "API routes": "from api.routes import router",
    "Voice routes": "from api.voice_routes import router as voice_router",
}

# Running the Application
# =======================

RUN_COMMANDS = {
    "From backend directory": {
        "command": "uvicorn main:app --reload",
        "description": "Start server with auto-reload",
    },
    "From project root": {
        "command": "cd backend && uvicorn main:app --reload",
        "description": "Navigate to backend, then start server",
    },
    "Production mode": {
        "command": "uvicorn main:app --host 0.0.0.0 --port 8000",
        "description": "Run on all interfaces, port 8000",
    },
}

# Testing Endpoints
# =================

ENDPOINTS = {
    "Text Command": {
        "method": "POST",
        "path": "/command",
        "body": {"command": "open downloads"},
    },
    "Voice Command": {
        "method": "GET",
        "path": "/voice/listen",
        "description": "Listens to microphone and processes command",
    },
    "Health Check": {
        "method": "GET",
        "path": "/",
        "description": "Returns status message",
    },
}

if __name__ == "__main__":
    print("Auralis Backend Module Structure Reference")
    print("=" * 50)
    print("\nPackages:")
    for pkg, info in PACKAGES.items():
        print(f"\n{pkg}/")
        print(f"  Description: {info['description']}")
        if info['exports']:
            print(f"  Exports: {', '.join(info['exports'])}")
    
    print("\n\nImport Examples:")
    for desc, imp in IMPORT_EXAMPLES.items():
        print(f"\n{desc}:")
        print(f"  {imp}")
    
    print("\n\nRunning the Application:")
    for env, cmd in RUN_COMMANDS.items():
        print(f"\n{env}:")
        print(f"  $ {cmd['command']}")
        print(f"  ({cmd['description']})")
