# mlxui/mlxui/backend/server.py
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

from mlxui.backend.config import config as app_config
from mlxui.backend.api.models import router as models_router
from mlxui.backend.api.generation import router as generation_router
from mlxui.backend.api.performance import router as performance_router
from mlxui.backend.api.config import router as config_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("mlxui.backend.server")

app = FastAPI(
    title="MLXUI API",
    description="API for the MLXUI application, a direct frontend for mlx-lm models.",
    version=__import__('mlxui').__version__,
)

# Configure CORS
# Allow all origins for development, restrict in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Or specify your frontend URL: ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(models_router, prefix="/api/models", tags=["Models"])
app.include_router(generation_router, prefix="/api/generate", tags=["Generation"])
app.include_router(performance_router, prefix="/api/performance", tags=["Performance"])
app.include_router(config_router, prefix="/api/config", tags=["Configuration"])


@app.get("/api/health", tags=["Health"])
async def health_check():
    logger.info("Health check endpoint requested by client.")
    # In the future, this could check mlx_adapter status or other dependencies.
    return {"status": "ok", "version": app.version}

# static serving option
# from fastapi.staticfiles import StaticFiles
# frontend_build_dir = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
# if frontend_build_dir.exists():
#     app.mount("/", StaticFiles(directory=str(frontend_build_dir), html=True), name="static-frontend")
#     logger.info(f"Serving static frontend from: {frontend_build_dir}")
# else:
#     logger.warning(f"Frontend build directory not found at {frontend_build_dir}. Frontend will not be served by FastAPI.")