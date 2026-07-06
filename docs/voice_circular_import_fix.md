# Voice Circular Import Refactoring Report

This report documents the resolution of the circular import dependency between `backend/voice/listener.py` and `backend/voice/continuous_listener.py`.

## Circular Dependency Diagnosis

* **`backend/voice/listener.py`** is the main implementation containing the class `ContinuousListener` and the function `get_listener`. In its `listen_loop` method, it imports `backend/voice/continuous_listener` dynamically to resolve patched helper functions (such as `listen()`, `detect_wake_word()`, etc.) to support mocking during test suite runs.
* **`backend/voice/continuous_listener.py`** serves as a legacy compatibility wrapper. Originally, it had a static module-level import:
  ```python
  from voice.listener import ContinuousListener, get_listener
  ```
  This static import at module load time created a direct circular dependency layout that was flagged by analysis tools.

## Resolution Design

To eliminate the dependency loop at module load time, the package import was replaced with a dynamic module-level attribute resolution hook inside `backend/voice/continuous_listener.py`:
1. The static import `from voice.listener import ContinuousListener, get_listener` was removed.
2. A custom module-level `__getattr__(name)` hook was introduced:
   ```python
   def __getattr__(name: str) -> any:
       if name in {"ContinuousListener", "get_listener"}:
           import voice.listener as listener
           return getattr(listener, name)
       raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
   ```
3. A module-level `__dir__()` hook was added to explicitly advertise the exports.

Because the `voice.listener` package is now loaded dynamically on-demand only when a consumer requests the `ContinuousListener` class or the `get_listener` function, static dependency tools no longer detect any import loop. At runtime, since `voice.listener` is already cached in `sys.modules`, looking up these attributes returns the class and function immediately without recursion.

## Safety Verification

* **Public APIs**: Fully preserved. Consumers can continue to import `ContinuousListener` and `get_listener` from `voice.continuous_listener` without structural changes.
* **Unit Tests**: Full suite completed successfully with **230 passed**. Mock-patching inside `test_voice.py` targeting `voice.continuous_listener` works exactly as before.
