# Screenshot & Screen Utilities Subsystem

## Purpose
Manages operating system screen captures (fullscreen, window, display selection, and delayed triggers), image annotation overlays, and basic screen recording operations through the Auralis execution pipeline.

## Architecture

- **`screenshot_service.py`**: High-level interface managing captures, unique file paths, folder shortcut translation, and clipboard transfers.
- **`capture_manager.py`**: Interacts with the OS displays using `mss` and `Pillow`.
- **`annotation.py`**: Performs image drawings, blurring, highlighting, and overlay text.
- **`screen_recorder.py`**: Implements state management for screen recording (start, pause, stop).
- **`models.py`**: Declares structured metadata schemas.
