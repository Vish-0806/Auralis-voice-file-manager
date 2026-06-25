# Desktop Capability
## Purpose
Native desktop interaction and UI window automation.

## Architecture
- `applications.py`: Launches registered applications.
- `windows.py`: Controls OS window dimensions and focus states.
- `clipboard.py`: Reads and writes clipboard text.
- `notifications.py`: Emits native OS tray notifications.
- `screenshots.py`: Captures screens and detects displays.

## Relationships
- **Core:** The Dispatcher triggers app launches or layout changes.
- **Events:** Publishes alerts when screenshots are captured.
- **OS Layer:** Interfaces with GUI ports (win32/cocoa) to control windows.
