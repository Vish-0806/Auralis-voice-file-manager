# Clipboard Automation Subsystem

## Purpose
Manages operating system clipboard interaction through the Auralis execution pipeline, providing copy, paste, clear, export, format detection, and bounded session history operations.

## Architecture

- **`clipboard_service.py`**: High-level interface managing operations and session history tracking.
- **`clipboard_manager.py`**: Interacts with the OS clipboard using `win32clipboard`.
- **`clipboard_history.py`**: Maintains in-memory temporary history using a FIFO deque.
- **`models.py`**: Declares structured Pydantic schemas.
