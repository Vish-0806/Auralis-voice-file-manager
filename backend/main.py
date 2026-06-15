import os
import sys

# Ensure backend directory is in python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi import FastAPI
from api.routes import router
from api.voice_routes import router as voice_router
from api.listener_routes import router as listener_router

app = FastAPI(
    title="Auralis API",
    version="1.0.0"
)

app.include_router(router)
app.include_router(voice_router)
app.include_router(listener_router)

@app.get("/")
def root():
    return {
        "message": "Auralis Backend Running 🚀"
    }