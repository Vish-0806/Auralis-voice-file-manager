# Input Automation Engine Subsystem

## Purpose
Manages operating system mouse moves, clicks, scrolls, drag-drops, keyboard text writes, hotkeys, custom shortcuts, and compound macros through the Auralis execution pipeline.

## Architecture

- **`input_service.py`**: High-level interface coordinating keyboard, mouse, shortcuts, and macros.
- **`keyboard_controller.py`**: Interacts with PyAutoGUI keyboard writes and hotkeys.
- **`mouse_controller.py`**: Interacts with PyAutoGUI cursor controls and coordinate limits.
- **`shortcut_manager.py`**: Manages configured shortcut label lookups (e.g. Save, Copy, Desktop).
- **`macro_executor.py`**: Executes compound automation sequences (e.g. Save File macro).
- **`models.py`**: Declares coordinate schemas.
