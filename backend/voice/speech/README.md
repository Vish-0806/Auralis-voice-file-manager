# Speech Recognition Engine

The Speech Recognition Engine is a modular, independent subsystem of the Auralis voice framework. Its primary responsibility is to capture spoken audio from a microphone, process/normalize the signal, detect endpointing (silence), and transcribe the speech into lowercased text.

## Architecture

```
Microphone  ──[Raw PCM Chunks]──>  Audio Processor  ──[WAV Audio Buffer]──>  Speech To Text  ──[Transcribed Text]──>  SpeechResult
```

- **Microphone**: Direct interface to hardware capturing audio via `pyaudio`. Handles selecting devices and opening/closing/reading streams safely.
- **Audio Processor**: Performs signal-level operations using `audioop`. Normalizes amplitude, monitors RMS values for silence/speech endpointing, translates channel layouts/sample rates, and structures bytes into standard WAV chunks.
- **Speech To Text**: Coordinates the lifecycle of a voice recognition request, supporting dynamic fallback logic. Uses offline `faster-whisper` if installed; falls back to standard `SpeechRecognition` (Google Speech Web API) if offline components are unavailable.

## Configuration & Data Models

Refer to [models.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/voice/speech/models.py):
- `SpeechConfiguration`: Fine-tunes backend preference, model sizing, timeout boundaries, silence detection threshold, and input sample specifications.
- `SpeechRequest`: Bundles binary audio blocks alongside formatting metadata.
- `SpeechResult`: Holds text transcriptions, latency stats, success indicators, and failure messages.

## Usage

### Simple Voice Capture & Transcription

```python
from voice.speech import Microphone, SpeechToText, SpeechConfiguration

# Initialize subsystem with default parameters (timeout = 10s, fallback enabled)
config = SpeechConfiguration(backend="faster-whisper", model_size="base")
stt_engine = SpeechToText(config)
mic = Microphone(device_index=config.device_index)

# Listen and transcribe
result = stt_engine.recognize(mic)

if result.success:
    print(f"Transcription: {result.text} (Latency: {result.latency:.2f}s)")
else:
    print(f"Error: {result.error}")
```

### Direct Buffer Transcription

```python
from voice.speech import SpeechToText, SpeechRequest

stt_engine = SpeechToText()

# Package a WAV byte buffer (e.g. read from an uploaded file)
request = SpeechRequest(
    audio_data=my_wav_bytes,
    sample_rate=16000,
    sample_width=2,
    channels=1
)

result = stt_engine.transcribe(request)
if result.success:
    print(f"Recognized text: {result.text}")
```
