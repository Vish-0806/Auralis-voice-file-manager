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
python -c "
try:
    from api.routes import router
    print('  OK: api.routes')
except Exception as e:
    print(f'  ERROR: api.routes - {e}')
    exit(1)

try:
    from api.voice_routes import router as voice_router
    print('  OK: api.voice_routes')
except Exception as e:
    print(f'  ERROR: api.voice_routes - {e}')
    exit(1)

try:
    from ai_engine.command_parser import parse_command
    print('  OK: ai_engine.command_parser')
except Exception as e:
    print(f'  ERROR: ai_engine.command_parser - {e}')
    exit(1)

try:
    from file_engine.file_operations import execute_action
    print('  OK: file_engine.file_operations')
except Exception as e:
    print(f'  ERROR: file_engine.file_operations - {e}')
    exit(1)

try:
    from voice_engine.speech_to_text import listen
    print('  OK: voice_engine.speech_to_text')
except Exception as e:
    print(f'  ERROR: voice_engine.speech_to_text - {e}')
    exit(1)

try:
    from utils.logger import get_logger
    print('  OK: utils.logger')
except Exception as e:
    print(f'  ERROR: utils.logger - {e}')
    exit(1)

try:
    from main import app
    print(f'  OK: main.app ({len(app.routes)} routes)')
except Exception as e:
    print(f'  ERROR: main.app - {e}')
    exit(1)
" || (
    echo.
    echo ERROR: Module import test failed
    exit /b 1
)
echo.

echo Testing FastAPI app...
python -c "
from main import app
print(f'App title: {app.title}')
print(f'App version: {app.version}')
print(f'Total routes: {len(app.routes)}')
print(f'Routes:')
for route in sorted(app.routes, key=lambda r: str(r.path)):
    methods = ', '.join(route.methods or ['GET'])
    print(f'  {methods:6} {route.path}')
"
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
