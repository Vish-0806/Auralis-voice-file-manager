# 🎙️ Auralis – Voice-Controlled File Manager

Auralis is a smart desktop application that allows users to manage files and folders using voice commands. It combines speech recognition and natural language processing (NLP) to provide a hands-free file management experience.

---

## 🚀 Features

- 🎤 Voice-based file and folder operations  
- 📁 Create, delete, rename, and open files using voice  
- 🔍 Smart command recognition  
- ⚡ Fast and efficient file handling  
- 🧠 NLP-powered command processing  

---

## 🛠️ Tech Stack

### Frontend
- HTML, CSS, JavaScript, Electron

### Backend
- Python / Node.js *(update based on your project)*

### Libraries Used
- SpeechRecognition  
- Pyttsx3 (Text-to-Speech)  
- OS / File System modules  

---

## 📦 Installation

```bash
# Clone the repository
git clone https://github.com/your-username/auralis.git

# Navigate into the project folder
cd auralis

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

### 🎙️ Audio Setup (Windows)

PyAudio requires special handling on Windows. Use the automated setup script:

```powershell
cd .\scripts
.\setup_audio_windows.ps1
```

This script will:
- Attempt standard pip installation
- Fallback to `pipwin` if needed
- Verify microphone access
- Provide manual installation instructions if automated methods fail

For detailed audio setup instructions, see [AUDIO_SETUP.md](docs/AUDIO_SETUP.md).

**Requirements:**
- Microphone (USB or built-in)
- Python 3.8+
- Internet connection (for Google Speech Recognition API)
