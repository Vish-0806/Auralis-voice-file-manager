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


# pyrefly: ignore [missing-import]
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


@app.on_event("startup")
async def startup_event():
    """Initializes assistant dependencies and active memory providers on application startup."""
    import logging
    import sys
    from api.assistant_routes import get_assistant_dependency
    from memory.providers.provider_factory import ProviderFactory

    logger = logging.getLogger("auralis.startup")

    # Check if running under pytest to avoid seeding database/polluting tests
    if "pytest" in sys.modules:
        logger.info("Pytest detected; skipping Postgres provider initialization during API startup.")
        get_assistant_dependency()
        return

    # 1. Resolve active provider and log selection
    try:
        provider = ProviderFactory.get_provider()
        provider_name = provider.__class__.__name__
        logger.info(f"Memory provider selected: {provider_name}")

        # 2. Initialize PostgresProvider if selected
        if provider_name == "PostgresProvider":
            logger.info("Memory provider initialization started.")
            await provider.initialize()
            logger.info("Memory provider initialization successful.")
    except Exception as e:
        logger.error(f"Memory provider initialization failed: {e}", exc_info=True)
        raise e

    # 3. Build assistant dependency
    get_assistant_dependency()