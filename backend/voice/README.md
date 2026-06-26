# Auralis Voice Subsystem

This package implements speech recognition, speech synthesis, wake word pattern matching, and continuous microphone background monitoring.

---

## 1. Modular Subsystem Architecture

The package is organized to enforce modular boundaries, separating hardware interaction, vendor integrations, data structures, and orchestrating loops.

```
backend/voice/
├── interfaces.py          # Abstract interfaces for all sub-components (ABC)
├── models.py              # Data structures (WakeWordResult, VoiceSession, VoiceConfig)
├── audio_stream.py        # Microphones and hardware capture streams
├── recognizer.py          # Entry point for speech-to-text recognition
├── synthesizer.py         # Entry point for text-to-speech playbacks
├── voice_session.py       # Manages transaction logs and confirmations states
├── manager.py             # VoiceManager (coordinates recognizer, synthesizer, wake word, sessions)
├── listener.py            # ContinuousListener background thread loop
├── providers/             # Specific vendor/engine drivers
│   ├── rule_wake_word.py      # Regex-based wake phrase parsing
│   ├── google_recognizer.py   # SpeechRecognition Google service interface
│   └── pyttsx3_synthesizer.py # pyttsx3 speech synthesis driver
└── README.md              # Subsystem documentation
```

---

## 2. Core Components

### 2.1 VoiceManager
Coordinates all active voice workflows. Located in `manager.py`. It is a facade that handles high-level operations:
* `.listen()`: Captures microphone audio and converts speech to text.
* `.speak(text)`: Converts text to audio.
* `.detect_wake_word(text)`: Scans for wake phrases.
* `.get_pending_action()`: Fetches confirmation states.

### 2.2 ContinuousListener
A background service (in `listener.py`) that continuously monitors the microphone stream. When the wake word (e.g., *"Hey Auralis"*) is matched, it parses and executes the parsed action using the central dispatcher.

### 2.3 Providers (`providers/`)
Concrete implementations conforming to voice interfaces:
* `RuleWakeWordDetector` matches wake phrases (e.g. *"Hey Auralis"*, *"Hello Auralis"*) and extracts the command text.
* `GoogleSpeechRecognizer` handles ambient noise adjustments and makes Google Speech API calls.
* `Pyttsx3Synthesizer` wraps `pyttsx3` offline speech synthesis driver ensuring safe thread locks and sapi5 configuration on Windows.

---

## 3. Legacy Compatibility Wrappers
The original files (`speech_to_text.py`, `text_to_speech.py`, `wake_word.py`, `continuous_listener.py`) have been updated to serve as backward-compatible delegation endpoints. External modules and existing test suites can import from them without breakage.
