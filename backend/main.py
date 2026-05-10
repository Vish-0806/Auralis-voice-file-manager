from fastapi import FastAPI
from api.routes import router
from api.voice_routes import router as voice_router

app = FastAPI(
    title="Auralis API",
    version="1.0.0"
)

app.include_router(router)
app.include_router(voice_router)

@app.get("/")
def root():
    return {
        "message": "Auralis Backend Running 🚀"
    }