# Backend Import Issues - Troubleshooting Guide

## Overview

Python modules must be properly organized with `__init__.py` files for imports to work correctly. This guide helps diagnose and fix import issues in the Auralis backend.

## Issue: ModuleNotFoundError

### Error Message
```
ModuleNotFoundError: No module named 'api'
```

### Cause
- Missing `__init__.py` files in package directories
- Running uvicorn from wrong directory
- Python path not configured correctly

### Solution

#### Check 1: Verify __init__.py Files Exist
```bash
cd backend

# Windows
dir /s __init__.py

# Linux/macOS
find . -name "__init__.py"
```

**Should show:**
```
api/__init__.py
ai_engine/__init__.py
file_engine/__init__.py
voice_engine/__init__.py
utils/__init__.py
automation/__init__.py
tests/__init__.py
app/__init__.py
```

If missing, create them:
```bash
# Windows
for %D in (api ai_engine file_engine voice_engine utils automation tests app) do (
    type nul > %D\__init__.py
)

# Linux/macOS
for dir in api ai_engine file_engine voice_engine utils automation tests app; do
    touch "$dir/__init__.py"
done
```

#### Check 2: Run from Backend Directory
```bash
# Correct
cd backend
uvicorn main:app --reload

# Incorrect
cd project-root
uvicorn backend.main:app --reload
```

#### Check 3: Verify Python Path
```bash
python -c "import sys; print('\n'.join(sys.path))"
```

Should include your backend directory.

## Issue: ImportError - Cannot Import Name

### Error Message
```
ImportError: cannot import name 'parse_command' from 'ai_engine.command_parser'
```

### Cause
- Function doesn't exist in module
- Typo in function name
- Module syntax error

### Solution

#### Verify Function Exists
```bash
# Check if function exists
grep -n "def parse_command" ai_engine/command_parser.py

# Or use Python
python -c "from ai_engine.command_parser import parse_command; print(parse_command)"
```

#### Check for Syntax Errors
```bash
python -m py_compile ai_engine/command_parser.py
```

If this fails, there's a syntax error in the module.

#### Verify Module Can Be Imported
```bash
python -c "import ai_engine.command_parser; print(dir(ai_engine.command_parser))"
```

## Issue: Running from Wrong Directory

### Error
```
ModuleNotFoundError: No module named 'api'
```

### Solution

**Always run from backend directory:**

```bash
# Navigate to backend
cd d:\Auralis-voice-file-manager\backend

# Then run uvicorn
uvicorn main:app --reload
```

**Not from project root:**

```bash
# DON'T do this
cd d:\Auralis-voice-file-manager
uvicorn backend.main:app --reload  # ✗ Wrong path syntax
```

## Issue: Circular Imports

### Error
```
ImportError: cannot import name 'X' from partially initialized module 'Y'
```

### Cause
Two modules try to import each other, creating a circular dependency.

### Solution

**Avoid circular imports by:**

1. **Moving shared code to utils:**
   ```python
   # Instead of: ai_engine imports file_engine
   # And: file_engine imports ai_engine
   
   # Do this:
   # utils/shared.py - shared functions
   # ai_engine imports from utils
   # file_engine imports from utils
   ```

2. **Using local imports in functions:**
   ```python
   # Instead of top-level import
   def my_function():
       from other_module import something  # Import only when needed
       return something()
   ```

3. **Restructure modules if needed:**
   ```
   Old (circular):
   ai_engine → file_engine → ai_engine
   
   New (linear):
   ai_engine → utils
   file_engine → utils
   ```

## Verification Script

Run the verification script to check everything:

### Windows
```bash
cd backend
verify_modules.bat
```

### Linux/macOS
```bash
cd backend
bash verify_modules.sh
```

**Expected Output:**
```
================================
Auralis Backend Verification
================================

Checking Python installation...
OK: Python found

Checking __init__.py files...
  OK: api/__init__.py exists
  OK: ai_engine/__init__.py exists
  ... (all 8 packages)

Testing module imports...
  OK: api.routes
  OK: api.voice_routes
  OK: ai_engine.command_parser
  OK: file_engine.file_operations
  OK: voice_engine.speech_to_text
  OK: utils.logger
  OK: main.app (7 routes)

Testing FastAPI app...
App title: Auralis API
App version: 1.0.0
Total routes: 7
Routes:
  GET    /
  GET    /voice/listen
  POST   /command
  ... (other routes)

================================
All verifications passed!
================================
```

## Quick Import Checklist

Before attempting imports, verify:

- [ ] Running from backend directory
- [ ] All packages have `__init__.py` files
- [ ] No syntax errors in modules (`python -m py_compile module.py`)
- [ ] Function exists in module (`grep -n "def function_name" module.py`)
- [ ] No circular dependencies between modules
- [ ] Python version is 3.8+ (`python --version`)
- [ ] Virtual environment is activated (if using venv)

## Import Patterns - Reference

### ✅ Correct

```python
# From backend directory, import packages directly
from api.routes import router
from ai_engine.command_parser import parse_command
from file_engine.file_operations import execute_action
from voice_engine.speech_to_text import listen
from utils.logger import get_logger
```

### ❌ Incorrect

```python
# Don't prefix with 'backend'
from backend.api.routes import router  # ✗

# Don't use relative imports between packages
from ..api import routes  # ✗ Avoid

# Don't skip package names
from command_parser import parse_command  # ✗

# Don't use __main__ syntax unless in __main__.py
if __name__ == "__main__":
    from main import app  # ✗ Avoid
```

## Common Issues and Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| `ModuleNotFoundError: No module named 'api'` | Missing `__init__.py` or wrong directory | Run from `backend/` or create `__init__.py` |
| `ImportError: cannot import name 'X'` | Function doesn't exist or typo | Check function exists with `grep` |
| `SyntaxError` in module | Python syntax error in file | Run `python -m py_compile module.py` |
| Circular import error | Two modules import each other | Restructure: move common code to utils |
| `AttributeError: module has no attribute 'X'` | Module doesn't export the name | Check module's `__all__` or function definition |

## Debug Tips

### Print Import Path
```bash
python -c "
import sys
print('Python path:')
for p in sys.path:
    print(f'  {p}')
"
```

### List Module Contents
```bash
python -c "
import ai_engine.command_parser
print(dir(ai_engine.command_parser))
"
```

### Test Single Import
```bash
python -c "from api.routes import router; print(router)"
```

### Check Module Syntax
```bash
python -m py_compile api/routes.py
```

### View Module Source
```bash
python -c "
import inspect
from ai_engine.command_parser import parse_command
print(inspect.getsource(parse_command))
"
```

## Module Structure

```
backend/
├── api/
│   ├── __init__.py                    ← Required
│   ├── routes.py
│   └── voice_routes.py
├── ai_engine/
│   ├── __init__.py                    ← Required
│   └── command_parser.py
├── file_engine/
│   ├── __init__.py                    ← Required
│   └── file_operations.py
├── voice_engine/
│   ├── __init__.py                    ← Required
│   └── speech_to_text.py
├── utils/
│   ├── __init__.py                    ← Required
│   └── logger.py
├── main.py
└── MODULE_STRUCTURE.py                ← Reference guide
```

## Getting Help

1. **Check logs:** `backend/logs/auralis_*.log`
2. **Run verification script:** `verify_modules.bat` or `verify_modules.sh`
3. **Read module guide:** `BACKEND_MODULES.md`
4. **Test imports:** Use examples in [BACKEND_MODULES.md](BACKEND_MODULES.md)
5. **Review code:** Check `MODULE_STRUCTURE.py`

## Related Documentation

- [Backend Modules Guide](BACKEND_MODULES.md)
- [Module Structure Reference](MODULE_STRUCTURE.py)
- [Architecture](../docs/architecture.md)
- [Deployment](../docs/deployment.md)

---

**Last Updated:** May 10, 2026
