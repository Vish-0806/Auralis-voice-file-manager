# Auralis Audio Setup Guide

## Overview

Auralis uses two key audio libraries for voice recognition:
- **SpeechRecognition**: Speech-to-text conversion using Google Speech Recognition API
- **PyAudio**: Microphone input handling (cross-platform)

## Installation

### For Windows Users

PyAudio installation on Windows can be tricky due to compilation requirements. We provide an automated setup script with fallback mechanisms.

#### Option 1: Automated Setup (Recommended)

Run the provided PowerShell setup script:

```powershell
cd .\scripts
.\setup_audio_windows.ps1
```

This script will:
1. Attempt standard `pip install pyaudio`
2. If that fails, automatically use `pipwin` as fallback
3. Verify both PyAudio and SpeechRecognition installations
4. Provide manual instructions if all automated methods fail

#### Option 2: Manual Installation

If the automated script fails, follow these steps:

**Step 1: Verify Python**
```powershell
python --version
# Should show Python 3.8+
```

**Step 2: Download PyAudio Wheel**
- Visit: https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
- Download the wheel file matching your Python version
  - Example: `PyAudio‑0.2.13‑cp311‑cp311‑win_amd64.whl` (for Python 3.11, 64-bit)

**Step 3: Install from Wheel**
```powershell
pip install "C:\path\to\PyAudio-0.2.13-cp311-cp311-win_amd64.whl"
```

**Step 4: Verify Installation**
```powershell
python -c "import pyaudio; print(f'PyAudio: {pyaudio.__version__}')"
python -c "import speech_recognition; print('SpeechRecognition OK')"
```

#### Option 3: Using pipwin

If you prefer manual control:

```powershell
# Install pipwin
pip install pipwin

# Install PyAudio via pipwin
pipwin install pyaudio

# Verify
python -c "import pyaudio"
```

### For Linux/Mac Users

Standard pip installation works:

```bash
pip install pyaudio speech_recognition
```

On Linux, you may need system audio libraries:
```bash
# Ubuntu/Debian
sudo apt-get install python3-pyaudio

# macOS
brew install portaudio
pip install pyaudio
```

## Complete Backend Setup

After audio dependencies are installed:

```powershell
# Navigate to backend directory
cd backend

# Install all dependencies
pip install -r requirements.txt

# Start the backend server
uvicorn main:app --reload
```

## Verification

Test the audio setup:

```powershell
# Quick test
python -c "
import pyaudio
import speech_recognition as sr

print('✓ PyAudio:', pyaudio.__version__)
print('✓ SpeechRecognition: OK')

# List available microphones
r = sr.Recognizer()
with sr.Microphone() as source:
    print('✓ Microphone detected and accessible')
"
```

## Troubleshooting

### Issue: "No module named 'pyaudio'"

**Solution:**
1. Verify installation: `pip show pyaudio`
2. If not installed, retry automated setup: `.\scripts\setup_audio_windows.ps1`
3. If using virtual environment, ensure it's activated

### Issue: "ModuleNotFoundError: No module named '_portaudio'"

**Windows Solution:**
- This indicates PyAudio compilation failed
- Download pre-built wheel from https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
- Install from wheel file (see Manual Installation steps)

### Issue: Microphone Not Detected

**Verification Steps:**
```powershell
python -c "
import pyaudio

p = pyaudio.PyAudio()
print(f'Device count: {p.get_device_count()}')

for i in range(p.get_device_count()):
    info = p.get_device_info_by_index(i)
    print(f'{i}: {info[\"name\"]} (channels: {int(info[\"maxInputChannels\"])})')
"
```

**Solutions:**
- Check Windows audio settings: Settings → Sound → Volume and device preferences
- Verify microphone is not muted in Sounds control panel
- Test microphone in Windows Voice Recorder app first
- Update audio drivers from hardware manufacturer

### Issue: Network Error During Speech Recognition

**Cause:** Google Speech Recognition API requires internet connection

**Solution:**
- Verify internet connection
- Check firewall settings - ensure Python can access network
- Try again after a few seconds (API may be temporarily unavailable)

## API Usage

Once setup is complete, test the voice endpoint:

### Test with curl
```bash
# GET /voice/listen - captures microphone and processes command
curl http://localhost:8000/voice/listen

# Response example:
{
  "status": "success",
  "command": "open downloads",
  "parsed_action": {
    "action": "open",
    "target": "downloads"
  },
  "result": "Opened downloads"
}
```

### Test with Python
```python
import requests

response = requests.get('http://localhost:8000/voice/listen')
print(response.json())
```

## Environment Requirements

- **Python**: 3.8 or higher
- **OS**: Windows 10+, macOS 10.13+, or Linux (Ubuntu 18.04+)
- **Microphone**: USB or built-in microphone
- **Internet**: Required for Google Speech Recognition API
- **RAM**: 512MB+ (for speech processing)

## Dependencies

See [requirements.txt](../backend/requirements.txt) for complete list:

| Package | Version | Purpose |
|---------|---------|---------|
| SpeechRecognition | 3.16.1 | Speech-to-text conversion |
| PyAudio | 0.2.13 | Microphone input handling |
| FastAPI | 0.136.1 | Web framework |
| pyttsx3 | 2.99 | Text-to-speech (optional) |

## Next Steps

- [Read API Documentation](../docs/api_reference.md)
- [Learn Command Parser Syntax](../backend/ai_engine/command_parser.py)
- [Explore Architecture](../docs/architecture.md)

## Support

For issues or questions:
1. Check Troubleshooting section above
2. Review logs: `backend/logs/auralis_*.log`
3. Check GitHub issues
