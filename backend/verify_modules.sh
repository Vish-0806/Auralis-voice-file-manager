#!/bin/bash
# Auralis Backend Module Verification Script (Linux/macOS)
# Verifies all imports and module structure

echo ""
echo "================================"
echo "Auralis Backend Verification"
echo "================================"
echo ""

# Check Python installation
if ! command -v python &> /dev/null; then
    echo "ERROR: Python not found"
    exit 1
fi

echo "Checking Python installation..."
python --version
echo ""

echo "Checking __init__.py files..."
for dir in api ai voice utils automation tests app capabilities; do
    if [ -f "$dir/__init__.py" ]; then
        echo "  OK: $dir/__init__.py exists"
    else
        echo "  ERROR: $dir/__init__.py missing"
        exit 1
    fi
done
echo ""

echo "Testing module imports..."
python << 'EOF'
try:
    from api.routes import router
    print('  OK: api.routes')
    from api.voice_routes import router as voice_router
    print('  OK: api.voice_routes')
    from api.listener_routes import router as listener_router
    print('  OK: api.listener_routes')
    from ai.command_parser import parse_command
    print('  OK: ai.command_parser')
    from capabilities.files.file_operations import execute_action
    print('  OK: capabilities.files.file_operations')
    from voice.speech_to_text import listen
    print('  OK: voice.speech_to_text')
    from utils.logger import get_logger
    print('  OK: utils.logger')
    from main import app
    print(f'  OK: main.app ({len(app.routes)} routes)')
except Exception as e:
    print(f'  ERROR: {e}')
    exit(1)
EOF

if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: Module import test failed"
    exit 1
fi
echo ""

echo "Testing FastAPI app..."
python << 'EOF'
from main import app
print(f'App title: {app.title}')
print(f'App version: {app.version}')
print(f'Total routes: {len(app.routes)}')
print('Routes:')
for route in sorted(app.routes, key=lambda r: str(r.path)):
    methods = ', '.join(route.methods or ['GET'])
    print(f'  {methods:6} {route.path}')
EOF
echo ""

echo "================================"
echo "All verifications passed!"
echo "================================"
echo ""
echo "Next steps:"
echo "  1. Install dependencies: pip install -r requirements.txt"
echo "  2. Start backend: uvicorn main:app --reload"
echo "  3. Test endpoint: curl http://localhost:8000/"
echo ""
