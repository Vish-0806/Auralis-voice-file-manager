@echo off
REM Auralis Backend Module Verification Script
REM Verifies all imports and module structure

echo.
echo ================================
echo Auralis Backend Verification
echo ================================
echo.

REM Navigate to backend directory
cd /d %~dp0

echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found
    exit /b 1
)
echo OK: Python found
echo.

echo Checking __init__.py files...
for %%D in (api ai_engine file_engine voice_engine utils automation tests app) do (
    if exist %%D\__init__.py (
        echo OK: %%D/__init__.py exists
    ) else (
        echo ERROR: %%D/__init__.py missing
        exit /b 1
    )
)
echo.

echo Testing module imports...
python -c "from api.routes import router; print('  OK: api.routes')" || (echo   ERROR: api.routes & exit /b 1)
python -c "from api.voice_routes import router as voice_router; print('  OK: api.voice_routes')" || (echo   ERROR: api.voice_routes & exit /b 1)
python -c "from api.listener_routes import router as listener_router; print('  OK: api.listener_routes')" || (echo   ERROR: api.listener_routes & exit /b 1)
python -c "from ai_engine.command_parser import parse_command; print('  OK: ai_engine.command_parser')" || (echo   ERROR: ai_engine.command_parser & exit /b 1)
python -c "from file_engine.file_operations import execute_action; print('  OK: file_engine.file_operations')" || (echo   ERROR: file_engine.file_operations & exit /b 1)
python -c "from voice_engine.speech_to_text import listen; print('  OK: voice_engine.speech_to_text')" || (echo   ERROR: voice_engine.speech_to_text & exit /b 1)
python -c "from utils.logger import get_logger; print('  OK: utils.logger')" || (echo   ERROR: utils.logger & exit /b 1)
python -c "from main import app; print(f'  OK: main.app ({len(app.routes)} routes)')" || (echo   ERROR: main.app & exit /b 1)
echo.

echo Testing FastAPI app...
python -c "from main import app; print(f'App title: {app.title}'); print(f'App version: {app.version}'); print(f'Total routes: {len(app.routes)}'); print('Routes:'); [print(f'''  {', '.join(route.methods or ['GET']):6} {route.path}''') for route in sorted(app.routes, key=lambda r: str(r.path))]"
echo.

echo ================================
echo All verifications passed!
echo ================================
echo.
echo Next steps:
echo   1. Install dependencies: pip install -r requirements.txt
echo   2. Start backend: uvicorn main:app --reload
echo   3. Test endpoint: curl http://localhost:8000/
echo.
