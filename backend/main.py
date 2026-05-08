from fastapi import FastAPI
from api.routes import router

app = FastAPI(
    title="Auralis API",
    version="1.0.0"
)

app.include_router(router)

@app.get("/")
def root():
    return {
        "message": "Auralis Backend Running 🚀"
    }