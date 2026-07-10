# Window Management Subsystem

## Purpose
Manages OS application windows through the Auralis execution pipeline. Supports actions to minimize, maximize, restore, focus, close, and list application windows, as well as show the desktop.

## Architecture

- **`models.py`**: Declares structured Pydantic contracts for window properties.
- **`window_manager.py`**: Interacts with the host OS window API using `pygetwindow`, `win32gui`, and `psutil`.
- **`window_resolver.py`**: Resolves text queries to target window instances (e.g. by title, process name, or active status).
- **`window_service.py`**: High-level application service that coordinates resolver queries and executes safe window operations.

## Safety and Security boundaries

- **Protected Windows**: The subsystem protects system components (like Taskbar, Program Manager, Start menu, Cortana) and the Auralis process itself from window actions.
- **Existence Verification**: Targets are resolved and verified to exist before window actions are executed.
