import os
import sys

# Ensure backend directory is in python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Monkeypatch standard library os to recognize the local os folder as a package
local_os_path = os.path.join(backend_dir, "os")
if os.path.isdir(local_os_path):
    os.__path__ = [local_os_path]


from fastapi import FastAPI
from api.assistant_routes import router as assistant_router
from api.routes import router
from api.voice_routes import router as voice_router
from api.listener_routes import router as listener_router
from api.file_routes import router as file_router

app = FastAPI(
    title="Auralis API",
    version="1.0.0"
)

app.include_router(router)
app.include_router(assistant_router)
app.include_router(voice_router)
app.include_router(listener_router)
app.include_router(file_router)

@app.get("/")
def root():
    return {
        "message": "Auralis Backend Running 🚀"
    }