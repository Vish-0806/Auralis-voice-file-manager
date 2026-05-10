# Windows Audio Dependencies Setup for Auralis Voice Engine
# This script handles PyAudio installation with fallback to pipwin

Write-Host "================================" -ForegroundColor Cyan
Write-Host "Auralis Windows Audio Setup" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
Write-Host "Checking Python installation..." -ForegroundColor Yellow
python --version | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Python found" -ForegroundColor Green
Write-Host ""

# Step 1: Try standard pip installation
Write-Host "Step 1: Attempting standard pip installation of PyAudio..." -ForegroundColor Yellow
pip install pyaudio==0.2.13 2>&1 | Tee-Object -Variable pipOutput | Out-Null

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ PyAudio installed successfully via pip" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host "⚠ Standard pip installation failed (expected on Windows)" -ForegroundColor Yellow
    Write-Host ""
    
    # Step 2: Fallback to pipwin
    Write-Host "Step 2: Attempting installation via pipwin (Windows package manager)..." -ForegroundColor Yellow
    Write-Host ""
    
    # Check if pipwin is installed
    pipwin --version | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Installing pipwin..." -ForegroundColor Yellow
        pip install pipwin
        if ($LASTEXITCODE -ne 0) {
            Write-Host "ERROR: Failed to install pipwin" -ForegroundColor Red
            Write-Host ""
            Write-Host "Manual Installation Instructions:" -ForegroundColor Yellow
            Write-Host "1. Download PyAudio wheel for your Python version from:" -ForegroundColor White
            Write-Host "   https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio" -ForegroundColor Cyan
            Write-Host "2. Run: pip install <path-to-wheel-file>" -ForegroundColor White
            Write-Host "3. Verify: python -c 'import pyaudio'" -ForegroundColor White
            exit 1
        }
    }
    
    Write-Host "✓ pipwin is ready" -ForegroundColor Green
    Write-Host ""
    
    # Install PyAudio via pipwin
    Write-Host "Installing PyAudio via pipwin..." -ForegroundColor Yellow
    pipwin install pyaudio
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to install PyAudio via pipwin" -ForegroundColor Red
        Write-Host ""
        Write-Host "Manual Installation Instructions:" -ForegroundColor Yellow
        Write-Host "1. Download PyAudio wheel for your Python version from:" -ForegroundColor White
        Write-Host "   https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio" -ForegroundColor Cyan
        Write-Host "2. Run: pip install <path-to-wheel-file>" -ForegroundColor White
        Write-Host "3. Verify: python -c 'import pyaudio'" -ForegroundColor White
        exit 1
    }
    Write-Host "✓ PyAudio installed successfully via pipwin" -ForegroundColor Green
    Write-Host ""
}

# Step 3: Verify PyAudio installation
Write-Host "Step 3: Verifying PyAudio installation..." -ForegroundColor Yellow
python -c "import pyaudio; print(f'PyAudio version: {pyaudio.__version__}')" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ PyAudio verification successful" -ForegroundColor Green
} else {
    Write-Host "ERROR: PyAudio verification failed" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Step 4: Verify SpeechRecognition
Write-Host "Step 4: Verifying SpeechRecognition installation..." -ForegroundColor Yellow
python -c "import speech_recognition; print(f'SpeechRecognition version: {speech_recognition.__version__}')" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ SpeechRecognition verification successful" -ForegroundColor Green
} else {
    Write-Host "ERROR: SpeechRecognition verification failed" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Summary
Write-Host "================================" -ForegroundColor Cyan
Write-Host "✓ All audio dependencies installed!" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Install remaining backend dependencies: pip install -r requirements.txt" -ForegroundColor White
Write-Host "2. Start backend: uvicorn backend.main:app --reload" -ForegroundColor White
Write-Host "3. Test voice endpoint: GET http://localhost:8000/voice/listen" -ForegroundColor White
