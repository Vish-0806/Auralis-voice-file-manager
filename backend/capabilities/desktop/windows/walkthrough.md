# Walkthrough - Window Management Capability

I have implemented Step 4.2 of Phase 4: Window Management. All implementation tasks have been completed, verified via unit/integration tests, and integrated into the Desktop Capability.

## Changes Made

### 1. Core Orchestration Updates
- **`backend/core/intents.py`**: Added StrEnum intents:
  - `MINIMIZE_WINDOW`
  - `MAXIMIZE_WINDOW`
  - `RESTORE_WINDOW`
  - `FOCUS_WINDOW`
  - `CLOSE_WINDOW`
  - `SHOW_DESKTOP`
  - `LIST_WINDOWS`
- **`backend/core/dispatcher.py`**: Registered the new window intents in `_SUPPORTED_INTENTS` and configured `_intent_to_capability_name` to route these intents to the `"desktop"` capability.
- **`backend/core/planner.py`**: Updated the keyword planner to detect window intents, extract target window names, and assign confidence scores. Configured heuristics to distinguish `CLOSE_WINDOW` (e.g. for "Close Calculator") from `CLOSE_APPLICATION` (e.g. for "Close Notepad").

### 2. Dependency Configuration
- Added `pygetwindow==0.0.9` to both root `requirements.txt` and `backend/requirements.txt`.

### 3. Desktop Capability Updates
- **`backend/capabilities/desktop/desktop_capability.py`**: Imported `WindowService`, registered window intents in `_SUPPORTED_INTENTS`, and routed window control intents to the window service.

### 4. Window Capability Subsystem
Created the new module package under `backend/capabilities/desktop/windows/`:
- **`models.py`**: Declares structured `WindowDetails` Pydantic model for window property representation.
- **`window_manager.py`**: Interfaces directly with the Windows OS using `pygetwindow`, `win32gui`, and `psutil`. Protects critical system components (e.g., Taskbar, Start, Program Manager) and the Auralis process window.
- **`window_resolver.py`**: Matches window queries by matching active window states, window titles, or application names.
- **`window_service.py`**: Coordinates resolution and verification, and executes window control actions.
- **`README.md`**: Explains window capability architecture and safety boundaries.

---

## Verification Results

### Automated Tests
I created a comprehensive test suite in `backend/tests/test_window_management.py` containing 6 unit and integration tests. The tests verify:
- Window resolution by title, app name, and active state.
- System process and current process window protection rules.
- Listing active titled visible windows.
- Desktop capability execution and dispatch routing.
- End-to-end integration pipeline execution of the requested window commands:
  1. *Maximize VS Code*
  2. *Minimize Chrome*
  3. *Restore Notepad*
  4. *Focus Spotify*
  5. *Close Calculator*
  6. *Show Desktop*
  7. *List open windows*

All tests run and pass successfully:

```bash
venv\Scripts\pytest backend\tests\test_window_management.py
============================== 6 passed in 0.85s ==============================
```

The entire system test suite passes successfully:

```bash
venv\Scripts\pytest
======================= 295 passed, 1 warning in 2.01s ========================
```
