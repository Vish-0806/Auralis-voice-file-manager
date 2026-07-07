# Voice Experience (UX) Subsystem

The Voice UX subsystem regulates states, chimes, and interaction notifications to create a responsive voice experience. It is fully modular, isolated from core assistant business logic, and designed for easy integration.

## Subsystem Layout

```
                                 FeedbackManager (Facade)
                                            │
        ┌───────────────────────────────────┼──────────────────────────────────┐
        ▼                                   ▼                                  ▼
  StatusManager                       SoundManager                       NotificationManager
  (Tracks Active state)               (Plays chimes / cues)              (Publishes text alerts)
```

- **StatusManager**: Keeps thread-safe status records using the `AssistantStatus` Enum and registers transition listeners.
- **SoundManager**: Coordinates audio cues for state transitions. Uses platform-native async Windows chimes (`winsound`).
- **NotificationManager**: Exposes text notifications (e.g., "Listening...", "Processing...", "Done.", "Error") and handles UI observer registration.
- **FeedbackManager**: Facade manager combining all three components under a single `transition_to(self, status)` endpoint.

## Assistant Status States

We track status updates via `AssistantStatus`:
- **SLEEPING**: Idle, waiting for wake phrase.
- **WAKE_DETECTED**: Triggered immediately when wake word matches.
- **LISTENING**: Actively recording microphone.
- **PROCESSING**: Executing parsed instructions.
- **SPEAKING**: TTS audio playing.
- **WAITING**: Follow-up delay checking for subsequent commands.
- **ERROR**: Timed out or failed.

## Usage

### Orchestrating Status Transitions

```python
from voice.ux import FeedbackManager, AssistantStatus, UXNotification

# 1. Instantiate the coordinator
ux_coordinator = FeedbackManager()

# 2. Register a subscriber callback for UI/logs
def on_ui_notification(notification: UXNotification):
    print(f"UI UPDATE: [{notification.status.name}] -> {notification.message}")

ux_coordinator.notification_manager.register_listener(on_ui_notification)

# 3. Transition states
ux_coordinator.transition_to(AssistantStatus.LISTENING)
# Output:
# UI UPDATE: [LISTENING] -> Listening...
# Plays a SystemQuestion alert chime asynchronously
```
