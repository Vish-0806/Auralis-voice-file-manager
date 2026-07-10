# Desktop Capability

## Purpose
Manages native desktop applications through the Auralis execution pipeline, providing capabilities to launch, close, restart, and inspect process status safely.

## Architecture

- **`desktop_capability.py`**: Integrates with the Auralis Dispatcher, validating execution plans and mapping user intents to application operations.
- **`application/application_service.py`**: Coordinates the resolver and process manager to carry out high-level commands.
- **`application/application_resolver.py`**: Resolves application names (e.g. Chrome, VS Code) to their system executable paths, searching program files, local app data, and system PATH environment variables.
- **`application/process_manager.py`**: Interfaces directly with the OS using `subprocess` and `psutil` to control processes.
- **`application/models.py`**: Declares structured data contracts for applications and processes.

## Safety and Security boundaries

- **Protected Processes**: The capability explicitly blocks requests to terminate core system processes (e.g. `explorer.exe`, `svchost.exe`, etc.) and the backend's own process (`os.getpid()`) to prevent system crashes or denial-of-service.
- **Path Validation**: Application resolvers validate executable paths and ensure targets are real files on disk before launching.

## Supported Applications
- Chrome
- Microsoft Edge
- Firefox
- VS Code
- Notepad
- Calculator
- Spotify
- Terminal
