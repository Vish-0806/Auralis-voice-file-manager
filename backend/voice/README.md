# Voice Engine Pipeline

## Purpose of this Module
Decoupled voice capture, recognition, synthesis, and wake word matching.

## Future Responsibility
Initializing local audio loops, processing DSP filters, wake word monitoring, and generating offline text-to-speech voiceovers.

## What Should Belong Here
- Whisper STT adaptors, wake word configs (OpenWakeWord/Snowboy), local TTS synthesis APIs, noise filters.

## What Should NOT Belong Here
- SQLite connection pools, document OCR helpers, file cataloging logic.
