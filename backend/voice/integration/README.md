# Voice Integration Pipeline

The Voice Integration Pipeline connects every modular Voice subsystem developed for Auralis into a unified, end-to-end OS Assistant execution flow. It coordinates microphone signals, state transitions, speech translation, and context awareness, bridging inputs to the Core Assistant capability dispatcher.

## Subsystem Dataflow

```
Wake Word Listener  ──[Wake phrase matched]──>  Conversation Manager (Session start)
                                                          │
                                                          ▼
  Text-to-Speech  ◄──  Feedback (UX transitions)  ◄──  Speech Recognition
         │                                                │
         ▼                                                ▼
   Audio Output  ◄───  Capability Executor  ◄───  Context Resolution
```

1. **Wake Word Engine**: Listens for the wake phrase (e.g. "Hey Auralis") to trigger session start.
2. **Conversation Manager**: Starts/stops active conversation sessions and coordinates inactivity timeouts.
3. **Speech Recognition**: Transcribes microphone audio command to text.
4. **Context Resolution**: Swaps natural pronouns/nouns/ordinals for actual directory/file strings, catching references and checking duplicates before dispatcher execution.
5. **Core Assistant**: Passes the command to the **Planner**, matches intent, routes to **Dispatcher**, and runs the corresponding **Capability** (e.g. file operations), returning the output payload.
6. **Text-To-Speech**: Synthesizes the response message and plays chimes/voice asynchronously via the sound controller.

## Modules

- **VoicePipeline**: The core orchestrator stitch-point. Bridges command execution to the `AuralisAssistant` and formats context update fields.
- **PipelineController**: Operates background thread lifecycles and controls safe, non-blocking step executions.
- **EventRouter**: Simple pub-sub event bus allowing modules to listen for state boundaries (e.g. `WAKE_WORD_DETECTED`, `SPEECH_RECOGNIZED`, `EXECUTION_STARTED`) without direct code coupling.

## Error Recovery Policies

- **Microphone disconnect**: Catches hardware PyAudio/stream `IOError` or `RuntimeError` instances. Transitions UX to `ERROR`, prints disconnect warnings, backs off for 5.0 seconds, and retries reconnection.
- **Recognition failure**: Catches transcription errors. Prompts recovery chimes and TTS instructions ("I couldn't hear you clearly, please repeat") while keeping the session active.
- **Planner failure**: Recovers from assistant parsing `PlanningException` instances, announces formulation failures, and returns to waiting mode.
- **Capability failure**: Catch `DispatchException` / `CapabilityException` execution faults, speaks warning, and resets state for follow-ups.
- **Speech interruption**: Calling `audio_output.stop()` at the beginning of `process_command` instantly cancels active TTS chimes/audio when the user starts speaking a new command.

## Usage

```python
from core.assistant import get_assistant_dependency
from voice.speech import SpeechToText, Microphone
from voice.wake_word import WakeWordDetector
from voice.conversation import SessionManager
from voice.context import ContextManager
from voice.tts import TextToSpeech
from voice.ux import FeedbackManager
from voice.integration import EventRouter, VoicePipeline, PipelineController

# 1. Initialize Collaborators
assistant = get_assistant_dependency()
router = EventRouter()
mic = Microphone()

stt = SpeechToText()
tts = TextToSpeech()
ux = FeedbackManager()
cm = ContextManager()

# Wake word
detector = WakeWordDetector()

# Inactivity and session
def on_ww_check(text: str) -> dict:
    match = detector.detect_in_text(text)
    return {"activated": match is not None, "cleaned_command": text.replace("Auralis", "") if match else ""}

def on_exec(cmd: str, ctx) -> tuple[str, dict]:
    # Handled by VoicePipeline directly, stubbed on manager
    return "", {}

sm = SessionManager(
    wake_word_detector=on_ww_check,
    speech_recognizer=stt.recognize,
    command_executor=on_exec,
    tts_speaker=tts.speak
)

# 2. Stitch Pipeline
pipeline = VoicePipeline(
    assistant=assistant,
    wake_word_detector=detector,
    conversation_manager=sm,
    speech_to_text=stt,
    context_manager=cm,
    text_to_speech=tts,
    feedback_manager=ux,
    event_router=router,
    microphone=mic
)

# 3. Spawn Lifecycle Controller
controller = PipelineController(pipeline)
controller.start()  # Runs loops on daemon thread
```
