# Conversation Manager Subsystem

The Conversation Manager is an independent orchestration layer of the Auralis voice system. It regulates the active lifecycle of a voice session, tracks conversation context across multiple user inputs, transitions states, handles inactivity timeouts, and filters out explicit exit commands.

## Architecture & States

```
                ┌─────────────────────────────────┐
                │             SLEEPING            │◄──────────────────────┐
                └────────────────┬────────────────┘                       │
                                 │ Wake Word Detected                     │
                                 ▼                                        │
                ┌─────────────────────────────────┐                       │
                │            LISTENING            │                       │
                └────────────────┬────────────────┘                       │
                                 │ Audio Captured                         │
                                 ▼                                        │ Inactivity Timeout
                ┌─────────────────────────────────┐                       │ OR Exit Command
                │            PROCESSING           │                       │ ("goodbye", "exit",
                └────────────────┬────────────────┘                       │  etc.)
                                 │ Response Generated                     │
                                 ▼                                        │
                ┌─────────────────────────────────┐                       │
                │             SPEAKING            │                       │
                └────────────────┬────────────────┘                       │
                                 │ Speech Synthesized                     │
                                 ▼                                        │
                ┌─────────────────────────────────┐                       │
                │       WAITING_FOR_RESPONSE      ├───────────────────────┘
                └─────────────────────────────────┘
```

The system cycles through the following `ConversationState` phases:
- **SLEEPING**: Default monitoring state.
- **LISTENING**: Actively recording microphone input.
- **PROCESSING**: Invoking external execution delegate to execute parsed commands.
- **SPEAKING**: Synthesizing responses back via text-to-speech.
- **WAITING_FOR_RESPONSE**: Follow-up delay state allowing the session to stay alive for consecutive instructions.
- **ERROR**: Internal exception handler state.

## Context Tracking

The `ConversationContext` class persists parameters between back-to-back voice instructions:
- `current_file`: Name or path of the last edited/referenced file.
- `current_folder`: Directory target of the last operation.
- `last_command`: The text string of the previous instruction.
- `last_response`: The text string of the previous output announcement.
- `pending_confirmation`: Dictionary details for actions requesting confirm/cancel confirmation.

## Exit Commands

If a user speaks any of the following exit commands (case-insensitive), the session will immediately synthesize a parting phrase (e.g. "Goodbye") and transition to the `SLEEPING` state:
- *goodbye*
- *exit*
- *stop listening*
- *cancel*
- *never mind*
- *thank you*

## Usage

### Orchestrating Session Control

The `SessionManager` utilizes callback dependency injection, ensuring it contains **no business logic** or direct coupling with Assistant APIs:

```python
from voice.conversation import SessionManager, ConversationContext
from voice.speech import SpeechResult

# 1. Define delegates
def on_wake_word(text: str) -> dict:
    # Check if text contains "hey auralis"
    if "auralis" in text.lower():
        return {"activated": True, "cleaned_command": text.lower().replace("auralis", "")}
    return {"activated": False, "cleaned_command": ""}

def on_capture() -> SpeechResult:
    # Record and return a SpeechResult
    return SpeechResult(text="open download folder", success=True)

def on_execute(command: str, context: ConversationContext) -> tuple[str, dict]:
    # Process instruction and return response message + context updates
    return "Opened download folder", {"current_folder": "downloads"}

def on_speak(text: str) -> None:
    # Synthesize speech
    print(f"TTS: {text}")

# 2. Instantiate Manager
manager = SessionManager(
    wake_word_detector=on_wake_word,
    speech_recognizer=on_capture,
    command_executor=on_execute,
    tts_speaker=on_speak,
    timeout_seconds=30.0
)

# 3. Process incoming text or run step loops
manager.handle_input("hey auralis open download folder")
# This triggers start_conversation(), speaks greeting, transitions state to PROCESSING,
# calls on_execute, transitions state to SPEAKING, speaks "Opened download folder",
# updates context.current_folder to "downloads", and enters WAITING_FOR_RESPONSE.
```
